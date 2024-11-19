<script lang="ts">
	import { v4 as uuidv4 } from 'uuid';
	import { toast } from 'svelte-sonner';
	import mermaid from 'mermaid';
	import { getContext, onDestroy, onMount, tick } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import type { Writable } from 'svelte/store';
	import { type i18n as i18nType } from 'i18next';
	import { fly } from 'svelte/transition';
	import { OLLAMA_API_BASE_URL, OPENAI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
	import {
		chatId,
		chats,
		config,
		type Model,
		models,
		settings,
		showSidebar,
		tags as _tags,
		WEBUI_NAME,
		banners,
		user,
		socket,
		showCallOverlay,
		tools,
		activeArticle
	} from '$lib/stores';
	import {
		convertMessagesToHistory,
		copyToClipboard,
		extractSentencesForAudio,
		getUserPosition,
		promptTemplate,
		splitStream
	} from '$lib/utils';
	import { generateChatCompletion, generateTextCompletion } from '$lib/apis/ollama';
	import {
		addTagById,
		createNewChat,
		deleteTagById,
		getAllChatTags,
		getChatById,
		getChatList,
		getTagsById,
		updateChatById
	} from '$lib/apis/chats';
	import { generateOpenAIChatCompletion, generateOpenAIChatCompletionQuestions } from '$lib/apis/openai';
	import { createNewArticle } from '$lib/apis/articles';
	import { runWebSearch } from '$lib/apis/rag';
	import { createOpenAITextStream } from '$lib/apis/streaming';
	import { queryMemory } from '$lib/apis/memories';
	import { getAndUpdateUserLocation, getUserSettings } from '$lib/apis/users';
	import { chatCompleted, generateTitle, generateSearchQuery, chatAction } from '$lib/apis';
	import Banner from '../common/Banner.svelte';
	import MessageInput from '$lib/components/chat/MessageInput.svelte';
	import Messages from '$lib/components/chat/Messages.svelte';
	import Navbar from '$lib/components/layout/Navbar.svelte';
	import CallOverlay from './MessageInput/CallOverlay.svelte';
	import ChatControls from './ChatControls.svelte';
	import EventConfirmDialog from '../common/ConfirmDialog.svelte';
	import ClarificationCard from './Messages/ClarificationCard.svelte';
	import type { ChatResponse, Message, MessageHistory, ClientFile, ChatTagListResponse, Article } from '$lib/types';
	import { isErrorWithDetail } from '$lib/utils';

	const i18n: Writable<i18nType> = getContext('i18n');
	const eventTarget = new EventTarget();

	export let chatIdProp = '';

	let loaded = false;
	let showControls = false;
	let stopResponseFlag = false;
	let autoScroll = true;
	let processing = '';
	let messagesContainerElement: HTMLDivElement;

	let showEventConfirmation = false;
	let eventConfirmationTitle = '';
	let eventConfirmationMessage = '';
	let eventConfirmationInput = false;
	let eventConfirmationInputPlaceholder = '';
	let eventCallback: Function | null = null;

	let showModelSelector = true;
	let selectedModels = [''];
	let atSelectedModel: Model | undefined;
	let selectedModelIds = [];
	$: selectedModelIds = atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;

	// Custom replacer to handle circular references, particularly for $socket
	const jsonCircularReplacer = () => {
		const seen = new WeakSet();
		return (key: string, value: any) => {
			if (typeof value === 'object' && value !== null) {
				if (seen.has(value)) {
					return '[Circular]';
				}
				seen.add(value);
			}
			return value;
		};
	};

	let selectedToolIds: string[] = [];
	let webSearchEnabled = false;

	let chat: ChatResponse | null = null;
	let tags: ChatTagListResponse = [];

	let title = '';
	let prompt = '';

	let chatFiles: ClientFile[] = [];
	let files: ClientFile[] = [];
	let messages: Message[] = [];

	let history: MessageHistory = {
		messages: {},
		currentId: null
	};

	let params: { [x: string]: any } = {
		proficiency: 0
	};
	let valves = {};

	$: _availableToolIds = selectedModelIds.reduce((a, e, i, arr) => {
		const model = $models.find((m) => m.id === e);
		if (model && model.info && model.info.meta && model.info.meta.toolIds) {
			return [...new Set([...a, ...model.info.meta.toolIds])];
		}
		return a;
	}, [] as string[]);

	//////////////////////////////

	// ClarificationCard variables

	//////////////////////////////

	let clarificationVisible = false;
	let awaitingClarification = false;
	let clarificationQuestion = '';
	// export let selectedOptionsString = '';
	// export let selectedNotOptionsString = '';
	let clarificationOptions = [];
	let clarificationNotOptions = [];
	// export let question = '';
	// export let option = '';
	// export let notOption = '';
	// export let options = [];
	let keepContext = false;
	let clarificationNeeded = false;
	let selectedOption = '';
	let notOptions = [];

	let userMessage = null;

	/////////////////////////
	//
	// 	(Cisco) ClarificationCard functions
	//
	/////////////////////////

	// const generateQuestions = async (responseMessage, previousQuestions) => {
	// 	console.log('Chat.svelte -> generateQuestions -> responseMessage', responseMessage);

	// 	console.log('Chat.svelte -> generateQuestions -> previousQuestions', previousQuestions);

	// 	const prompt_template = `Generate 3 (and only 3) questions based on the following text.
	// 	do not provide any explainations about the questions. each between 3-5 words long:
	// 		1. [3-5 word(s)]
	// 		2. [3-5 word(s)]
	// 		3. [3-5 word(s)]

	// 		Avoid generating questions similar to the provided examples:\n\n`;
	// 	const exampleQuestions = previousQuestions.join('\n');
	// 	const prompt = `${prompt_template}${responseMessage.content}\n\nExample questions to avoid:\n${exampleQuestions}\n\nNew questions:`;

	// 	try {
	// 		// Send a request to the LLM with the prompt
	// 		const res = await generateTextCompletion(localStorage.token, selectedModels[0], prompt);

	// 		// Check status of the response
	// 		// console.log('hey corey the res', res);

	// 		if (res && res.ok) {
	// 			const reader = res
	// 				.body!.pipeThrough(new TextDecoderStream())
	// 				.pipeThrough(splitStream('\n'))
	// 				.getReader();

	// 			let data = '';

	// 			while (true) {
	// 				const { value, done } = await reader.read();
	// 				if (done) {
	// 					break;
	// 				}

	// 				const lines = value.split('\n');
	// 				for (const line of lines) {
	// 					if (line !== '') {
	// 						const parsedLine = JSON.parse(line);
	// 						if (parsedLine.response) {
	// 							data += parsedLine.response;
	// 						}
	// 					}
	// 				}
	// 			}

	// 			console.log('hey corey the data', data);

	// 			const questions = data.trim().split('\n').slice(1);
	// 			const filteredQuestions = questions
	// 				.map((q) => q.replace(/^\d+\.\s*/, ''))
	// 				.filter((q) => q.trim() !== '' && !q.includes('Note:') && !q.includes('Please note'));
	// 			responseMessage.questions = filteredQuestions;
	// 			messages = [...messages]; // Update the messages array to trigger reactivity

	// 			return { success: true, data: filteredQuestions };
	// 		} else {
	// 			const error = await res!.text(); // Get the error as text instead of JSON
	// 			toast.error(error);
	// 			console.log('hey corey the error', error);
	// 			return { success: false, data: '' };
	// 		}
	// 	} catch (error) {
	// 		console.error('Failed to query LLM:', error);
	// 		toast.error(`${error}`);
	// 		return { success: false, data: '' };
	// 	}
	// };

	// const checkClarificationNeeded = async (
	// 	userMessage: string
	// ): Promise<{ question: string; options: { label: string; value: string }[] } | null> => {
	// 	// Send a request to the LLM to generate clarification options
	// 	const clarificationOptionsFromLLM = await getClarificationOptions(userMessage);

	// 	if (clarificationOptionsFromLLM && clarificationOptionsFromLLM.success) {
	// 		let parsedOptions = parseclarificationOptionsFromLLM(clarificationOptionsFromLLM.data);
	// 		if (parsedOptions.length > 0) {
	// 			// Reset the selected option if it's a new clarification request and context is not being kept
	// 			if (!clarificationNeeded || !keepContext) {
	// 				selectedOption = '';
	// 				notOptions = []; // Reset notOptions to an empty array
	// 			}

	// 			// Remove the 'keep_context' option from the visible options
	// 			parsedOptions = parsedOptions.filter((option) => option.label !== 'keep_context');

	// 			return {
	// 				question: 'Please clarify your request:',
	// 				options: parsedOptions
	// 			};
	// 		}
	// 	}

	// 	// If the LLM response fails or doesn't provide any options, use default options
	// 	return {
	// 		question: 'Please provide more details for your request:',
	// 		options: [
	// 			{ label: 'Option 1', value: 'option1' },
	// 			{ label: 'Option 2', value: 'option2' },
	// 			{ label: 'Option 3', value: 'option3' }
	// 		]
	// 	};
	// };

	// // Helper function to query the LLM and get a response
	// const getClarificationOptions = async (
	// 	prompt: string
	// ): Promise<{ success: boolean; data: string }> => {
	// 	console.log('Hey corey, the selectedModels', selectedModels[0], 'and the prompt is ', prompt);

	// 	const modifiedPrompt = `Please provide exactly 3 short, concise options (2-3 words each) for clarifying the user's request. Limit your response to only the options in the following format, without any additional text or explanations:

	// 		Option 1: [word(s)]
	// 		Option 2: [word(s)]
	// 		Option 3: [word(s)]

	// 		Based on the user's request: "${prompt}", provide the 3 clarifying options now.`;

	// 	try {
	// 		// Send a request to the LLM with the prompt
	// 		const res = await generateTextCompletion(
	// 			localStorage.token,
	// 			selectedModels[0],
	// 			modifiedPrompt
	// 		);

	// 		// Check status of the response
	// 		console.log('hey corey the res', res);
	// 		if (res && res.ok) {
	// 			const reader = res.body
	// 				.pipeThrough(new TextDecoderStream())
	// 				.pipeThrough(splitStream('\n'))
	// 				.getReader();

	// 			let data = '';
	// 			while (true) {
	// 				const { value, done } = await reader.read();
	// 				if (done) {
	// 					break;
	// 				}

	// 				const lines = value.split('\n');
	// 				for (const line of lines) {
	// 					if (line !== '') {
	// 						console.log(line);
	// 						const parsedLine = JSON.parse(line);
	// 						if (parsedLine.response) {
	// 							data += parsedLine.response;
	// 						}
	// 					}
	// 				}
	// 			}

	// 			// console.log('hey corey the data', data);
	// 			return { success: true, data };
	// 		} else {
	// 			const error = await res.text(); // Get the error as text instead of JSON
	// 			// console.log('hey corey the error', error);
	// 			return { success: false, data: '' };
	// 		}
	// 	} catch (error) {
	// 		console.error('Failed to query LLM:', error);
	// 		return { success: false, data: '' };
	// 	}
	// };

	// // Helper function to parse the LLM response and extract the clarification options
	// const parseclarificationOptionsFromLLM = (
	// 	responseData: string
	// ): { label: string; value: string }[] => {
	// 	// console.log('hey corey the responseData from parseclarificationOptionsFromLLM', responseData);

	// 	const lines = responseData.split('\n').map((line) => line.trim());
	// 	const options = lines
	// 		.filter((line) => line.startsWith('Option'))
	// 		.map((line) => {
	// 			const [_, label] = line.split(':').map((part) => part.trim());
	// 			const value = label.toLowerCase().replace(/\s+/g, '_');
	// 			return { label, value };
	// 		});

	// 	if (options.length === 0) {
	// 		// If no valid options are found, return an empty array
	// 		return [];
	// 	}

	// 	return options;
	// };
	// export let _user;
	// export let promptNotIncluded = [];

	// const handleClarificationSubmit = (
	// 	selectedOptionsString = [],
	// 	notOptionsString = '[]',
	// 	inputValue = '',
	// 	originalUserPrompt = ''
	// ) => {
	// 	let selectedOptions = [];
	// 	let notOptions = [];
	// 	console.log(
	// 		'hey corey from handleClarificationSubmit the originalUserPrompt is',
	// 		originalUserPrompt
	// 	);

	// 	if (selectedOptionsString.length !== 0) {
	// 		console.log(
	// 			'corey after checking selectedOptions in handleClarificationSubmit selectedOptionsString is',
	// 			selectedOptionsString
	// 		);
	// 		selectedOptions = JSON.parse(selectedOptionsString);
	// 	}

	// 	console.log(
	// 		'corey after checking selectedOptions in handleClarificationSubmit notOptionsString is',
	// 		notOptionsString
	// 	);

	// 	if (notOptionsString.length !== 0) {
	// 		console.log(
	// 			'corey after checking notOptionsString in handleClarificationSubmit notOptionsString is',
	// 			selectedOptionsString
	// 		);
	// 		notOptions = JSON.parse(notOptionsString);
	// 	}

	// 	if (selectedOptions.length > 0 || notOptions.length > 0 || inputValue.trim() !== '') {
	// 		const includedOptions = selectedOptions.length > 0 ? selectedOptions.join(', ') : '';
	// 		const excludedOptions = notOptions.length > 0 ? notOptions.join(', ') : '';
	// 		const userDirection = inputValue.trim() !== '' ? inputValue.trim() : '';

	// 		let clarifiedPrompt = `${originalUserPrompt}\n`;

	// 		if (includedOptions) {
	// 			clarifiedPrompt += `\nSelected Options: ${includedOptions}\n`;
	// 		}

	// 		if (excludedOptions) {
	// 			clarifiedPrompt += `Excluded Options: ${excludedOptions}\n`;
	// 		}

	// 		if (userDirection) {
	// 			clarifiedPrompt += `User Direction: ${userDirection}\n`;
	// 		}

	// 		console.log('Clarified Prompt:', clarifiedPrompt);

	// 		// Submit the clarified prompt
	// 		submitPrompt(clarifiedPrompt);

	// 		// Reset clarification state
	// 		selectedOption = '';
	// 		notOptions = '';
	// 		clarificationVisible = false;
	// 		clarificationQuestion = '';
	// 		clarificationOptions = [];
	// 		clarificationNeeded = false;
	// 	} else {
	// 		// Submit the clarified prompt
	// 		submitPrompt(originalUserPrompt);

	// 		// Reset clarification state
	// 		selectedOption = '';
	// 		notOptions = '';
	// 		clarificationVisible = false;
	// 		clarificationQuestion = '';
	// 		clarificationOptions = [];
	// 		clarificationNeeded = false;
	// 	}
	// };

	// export function handleSelect(selectedOptions) {
	// 	console.log('Selected options:', selectedOptions);

	// 	notOptions = notOptions.filter((option) => !selectedOptions.includes(option));
	// 	const deselectedOptions = options
	// 		.filter((option) => !selectedOptions.includes(option.label))
	// 		.map((option) => option.label);
	// 	notOptions = [...notOptions, ...deselectedOptions];
	// 	console.log('Updated notOptions:', notOptions);
	// }

	/////////////////////////
	//
	// Reactive Statements
	//
	/////////////////////////

	$: if (history.currentId !== null) {
		let _messages = [];

		let currentMessage: Message | null = history.messages[history.currentId];
		while (currentMessage !== null) {
			_messages.unshift({ ...currentMessage });
			currentMessage = currentMessage.parentId !== null ? history.messages[currentMessage.parentId!] : null;
		}
		messages = _messages;
	} else {
		messages = [];
	}

	$: if (chatIdProp) {
		(async () => {
			console.log(`[chatIdProp:Chat.svelte] -> ${chatIdProp}`);
			if (chatIdProp && (await loadChat())) {
				await tick();
				loaded = true;

				window.setTimeout(() => scrollToBottom(), 0);
				const chatInput = document.getElementById('chat-textarea');
				chatInput?.focus();
			} else {
				await goto('/');
			}
		})();
	}

	// Cisco Logging
	$: {
		console.log(`[selectedModels:Chat.svelte] -> ${JSON.stringify(selectedModels, null, 2)}`);
		console.log(`[selectedModelIds:Chat.svelte] -> ${selectedModelIds}`);
		console.log(`[$page:Chat.svelte] -> ${JSON.stringify($page, null, 2)}`);
		// console.log(`[$socket:Chat.svelte] -> ${JSON.stringify($socket, jsonCircularReplacer(), 2)}`);
		console.log('[files:Chat.svelte] ->', files);
	}

	const chatEventHandler = async (event: { chat_id: string; message_id: string; data?: any }, cb: Function) => {
		console.log(`[chatEventHandler(event):Chat.svelte] -> Event is: ${event}`);
		if (event.chat_id === $chatId) {
			await tick();
			console.log(event);
			let message = history.messages[event.message_id];

			const type = event?.data?.type ?? null;
			const data = event?.data?.data ?? null;

			if (type === 'status') {
				if (message?.statusHistory) {
					message.statusHistory.push(data);
				} else {
					message.statusHistory = [data];
				}
			} else if (type === 'citation') {
				if (message?.citations) {
					message.citations.push(data);
				} else {
					message.citations = [data];
				}
			} else if (type === 'message' || type === 'replace') {
				message.content += data.content;
			} else if (type === 'confirmation') {
				eventCallback = cb;

				eventConfirmationInput = false;
				showEventConfirmation = true;

				eventConfirmationTitle = data.title;
				eventConfirmationMessage = data.message;
			} else if (type === 'input') {
				eventCallback = cb;

				eventConfirmationInput = true;
				showEventConfirmation = true;

				eventConfirmationTitle = data.title;
				eventConfirmationMessage = data.message;
				eventConfirmationInputPlaceholder = data.placeholder;
			} else {
				console.log('Unknown message type', data);
			}

			messages = messages;
		}
	};

	const onMessageHandler = async (event: MessageEvent) => {
		if (event.origin === window.origin) {
			console.log('Message received from iframe:', event.data);
			if (event.data.type === 'input:prompt') {
				console.log(event.data.text);

				const inputElement = document.getElementById('chat-textarea');

				if (inputElement) {
					prompt = event.data.text;
					inputElement.focus();
				}
			}

			if (event.data.type === 'action:submit') {
				console.log(event.data.text);

				if (prompt !== '') {
					await tick();
					await submitPrompt(prompt);
				}
			}

			if (event.data.type === 'input:prompt:submit') {
				console.log(event.data.text);

				if (prompt !== '') {
					await tick();
					await submitPrompt(event.data.text);
				}
			}
		}
	};

	onMount(async () => {
		window.addEventListener('message', onMessageHandler);

		$socket?.on('chat-events', chatEventHandler);

		if (!$chatId) {
			chatId.subscribe(async (value) => {
				if (!value) {
					await initNewChat();
				}
			});
		} else {
			if (!($settings.saveChatHistory ?? true)) {
				await goto('/');
			}
		}
	});

	onDestroy(() => {
		window.removeEventListener('message', onMessageHandler);

		$socket?.off('chat-events');
	});

	//////////////////////////
	// Cisco functions
	//////////////////////////
	import { promptStore, variablesStore, explanationStore } from '$lib/stores';
	import PromptTemplateGenerator from '$lib/components/cisco/components/PromptTemplateGenerator.svelte';
	export let isTextareaTruthy = false;
	export let showPromptTemplateGenerator = false;

	let originalUserPrompt = '';
	export let showPromptTemplate: boolean = false;
	export let showPromptIntro = false;
	export let generatedPrompt = '';
	let messageInputComponent;

	let explanationText = '';
	let clarifiedPrompt;
	let template;

	let isGeneratingPrompt: boolean;

	//dispatch
	import { createEventDispatcher } from 'svelte';
	import About from './Settings/About.svelte';
	const dispatch = createEventDispatcher();

	async function generatePrompt(existingText: string = '') {
		console.log('Generating prompt with existing text:', existingText);

		showPromptTemplateGenerator = true;

		if (existingText.trim()) {
			showPromptTemplate = true;
			isTextareaTruthy = true;
			isGeneratingPrompt = true;

			try {
				const result = await fetchAndProcessData(existingText);
				console.log('Raw result:', result);

				// Check if result exists and contains necessary data
				if (result) {
					// Safely retrieve variables and explanation
					const { prompt = 'No prompt generated.', explanation = 'No explanation provided.', variables = [] } = result;

					// Create an object from the variables array
					const variablesObject = variables.reduce((acc: { [key: string]: any }, varName: string) => {
						acc[varName] = ''; // Initialize with empty string
						return acc;
					}, {});

					// Update stores with validated data
					promptStore.set(prompt as string);
					explanationStore.set(explanation as string);
					variablesStore.set(variablesObject);

					// Console log them to ensure visibility
					console.log('Generated prompt:', $promptStore);
					console.log('Explanation:', $explanationStore);
					console.log('Variables:', $variablesStore);

					// Force update of the GeneratePromptComponent
					showPromptTemplate = false;
					await tick();
					showPromptTemplate = true;
				} else {
					console.error('Error: No valid result returned from fetchAndProcessData');
				}
			} catch (error) {
				console.error('Error generating prompt:', error);
				promptStore.set(existingText);
				explanationStore.set('');
				variablesStore.set({});
			} finally {
				isGeneratingPrompt = false;
			}
		} else {
			console.log('No text found in text area from generatePrompt');
			showPromptIntro = true;
			showPromptTemplateGenerator = true;
		}
	}

	async function fetchAndProcessData(template: string) {
		if (!template || typeof template !== 'string') {
			console.error('Invalid or empty prompt text', template);
			console.error('typeof template is', typeof template);
			return;
		}

		const promptTemplate = `
			You are an AI assistant specialized in creating prompts based on user descriptions. Your task is to generate a prompt that aligns with the user's specified requirements while keeping it grounded and practical.

			First, carefully read and analyze the user's description of the prompt they want to create:

			<prompt_type_description>
			${template}
			</prompt_type_description>

			Now, follow these steps to generate an appropriate prompt:

			1. Analyze the user's description, focusing on:
			- The main purpose or goal of the prompt
			- Specific requirements or constraints
			- Style, tone, or format preferences

			2. Based on your analysis, identify common-sense variables that could make the prompt more flexible and reusable. These should be elements that might need customization or could vary in different use cases.

			3. Craft a prompt that:
			- Clearly communicates the main goal or task
			- Incorporates all relevant requirements and constraints
			- Effectively utilizes the identified variables
			- Ensures variables are properly isolated in the text with spaces before and after
			- Remains grounded and practical
			- Is appropriate for the intended audience or context

			4. Ensure the prompt is:
			- Concise and clear
			- Specific enough to guide responses effectively
			- Open-ended enough to allow for creativity (unless otherwise specified)
			- Free from ambiguity or potential misinterpretation

			5. If the user's description lacks crucial details, make minimal, common-sense assumptions to fill gaps.

			6. Avoid including any harmful, unethical, or illegal content in the prompt.

			7. Include your identified variables in the prompt, encasing them in [[double square brackets]] .

			Before presenting your generated prompt, list only the variable names as comma-separated strings within <variables> tags. Do not include any explanations, examples, or parenthetical information.

			Mind the XML structure and formatting to ensure proper parsing and display of the generated content.

			EXAMPLE OUTPUT:
			<variables>
			variable1, variable2, variable3
			</variables>

			<prompt>
			This is a [[variable1]] prompt designed to [[variable2]] while considering [[variable3]]. [Rest of the prompt text with variables incorporated]
			</prompt>

			<explanation>
			This prompt is designed to [explain purpose]. It addresses the user's requirements by [explanation]. The variables [[variable1]], [[variable2]], and [[variable3]] allow for customization of [explain what each variable customizes], enhancing the prompt's flexibility and reusability.
			</explanation>
			`;

		const stringWithoutOllama = 'phi3';
		console.log('hey corey the template is right before generateTextCompletion', promptTemplate, stringWithoutOllama);
		const res = await generateTextCompletion(localStorage.token, stringWithoutOllama, promptTemplate);
		console.log('hey corey the res', res);

		if (res && res.ok) {
			const reader = res.body!.pipeThrough(new TextDecoderStream()).pipeThrough(splitStream('\n')).getReader();

			let data = '';

			while (true) {
				const { value, done } = await reader.read();
				if (done) {
					break;
				}

				const lines = value.split('\n');
				for (const line of lines) {
					if (line !== '') {
						try {
							const parsedLine = JSON.parse(line);
							if (parsedLine.response) {
								data += parsedLine.response;
							}
						} catch (error) {
							console.error('Error parsing JSON:', error);
						}
					}
				}
			}
			console.log(data);

			// Use the extractPromptAndVariables function to process the response
			const { prompt, explanation, variables } = extractPromptAndVariables(data);

			// Return both the prompt and variables
			return { prompt, explanation, variables };
		} else {
			const error = await res!.text();
			console.log('hey corey the error', error);
			throw new Error(`HTTP error! status: ${res!.status}`);
		}
	}

	function handleVariableUpdate(event: CustomEvent) {
		console.log('handleVariableUpdate event', event);
		console.log('Variable Store', $variablesStore);
		// const { name, value } = event.detail;
		// variablesStore.update((vars) => ({ ...vars, [name]: value }));
	}
	function handleGeneratePromptClick(event: CustomEvent<{ existingText: string }>) {
		const { existingText } = event.detail;
		generatePrompt(existingText);
	}
	function handleGeneratePromptFromChild(event: CustomEvent<{ existingText: string }>) {
		const { existingText } = event.detail;
		showPromptTemplate = true;
		showPromptTemplateGenerator = true;
		// Any other necessary logic
	}
	function setVariables(variables: string[]) {
		const variablesObject: { [key: string]: string } = variables.reduce((acc, varName) => {
			acc[varName] = ''; // Initialize with empty string
			return acc;
		}, {} as Record<string, string>);

		variablesStore.set(variablesObject);
	}
	// Helper function to extract prompt and variables
	function extractPromptAndVariables(response: string) {
		const promptRegex = /<prompt>([\s\S]*?)<\/prompt>/;
		const explanationRegex = /<explanation>([\s\S]*?)(?:<\/explanation>|$)/;
		const variablesRegex = /<variables>([\s\S]*?)<\/variables>/;

		const promptMatch = response.match(promptRegex);
		const explanationMatch = response.match(explanationRegex);
		const variablesMatch = response.match(variablesRegex);

		const prompt = promptMatch ? promptMatch[1].trim() : null;
		const explanation = explanationMatch ? explanationMatch[1].trim() : null;
		const variables = variablesMatch ? variablesMatch[1].split(',').map((v) => v.trim()) : [];

		return { prompt, explanation, variables };
	}

	function parseReceivedPrompt(rawPrompt: { prompt: string; explanation: string; variables: string[] }) {
		if (typeof rawPrompt === 'object' && rawPrompt.prompt && rawPrompt.explanation && rawPrompt.variables) {
			// If rawPrompt is already in the expected format, return it directly
			return rawPrompt;
		}

		let promptText = typeof rawPrompt === 'string' ? rawPrompt : JSON.stringify(rawPrompt);

		const variablesRegex = new RegExp('<variables>(.*?)</variables>', 's');
		const promptRegex = new RegExp('<prompt>([\\\\s\\\\S]*?)</prompt>');
		const explanationRegex = new RegExp('<explanation>([\\\\s\\\\S]*?)</explanation>');

		const variablesMatch = promptText.match(variablesRegex);
		const promptMatch = promptText.match(promptRegex);
		const explanationMatch = promptText.match(explanationRegex);

		const variables = variablesMatch ? variablesMatch[1].split(',').map((v) => v.trim()) : [];
		const prompt = promptMatch ? promptMatch[1].trim() : '';
		const explanation = explanationMatch ? explanationMatch[1].trim() : '';

		return { prompt, explanation, variables };
	}

	function extractVariablesFromPrompt(prompt: string) {
		const regex = /\[\[(.*?)\]\]/g;
		const matches = [...prompt.matchAll(regex)];
		return matches.reduce((acc, match) => {
			if (match[1]) {
				acc[match[1]] = '';
			}
			return acc;
		}, {} as Record<string, string>);
	}
	function updateTemplate(newTemplate: string) {
		template = newTemplate;
		// If you need to inform the parent component about the template change:
		dispatch('templateUpdate', { template: newTemplate });
	}
	function handleClosePromptTemplate(event: CustomEvent) {
		console.log('ClosePromptTemplate event', event);
		const { state } = event.detail;
		showPromptTemplate = state;
		showPromptIntro = true;
		showPromptTemplateGenerator = false;
		console.log('ShowPromptTemplate is set to: ', showPromptTemplate);
		console.log('ShowPromptIntro is set to: ', showPromptIntro);
	}

	function handleSubmit(event: CustomEvent) {
		const { customizedPrompt, promptTemplate, explanation } = event.detail;
		// Handle the submission of the customized prompt
		if (typeof submitPrompt === 'function') {
			submitPrompt(customizedPrompt);
		} else {
			console.error('submitPrompt is not a function', submitPrompt);
		}
		showPromptTemplate = false;
	}

	//////////////////////////
	// Web functions
	//////////////////////////

	const initNewChat = async () => {
		window.history.replaceState(history.state, '', `/`);
		chatId.set('');

		autoScroll = true;

		title = '';
		messages = [];
		history = {
			messages: {},
			currentId: null
		};

		chatFiles = [];
		params = {};

		if ($page.url.searchParams.get('models')) {
			selectedModels = $page.url.searchParams.get('models')?.split(',') as string[];
		} else if ($settings?.models) {
			selectedModels = $settings?.models;
		} else if ($config?.default_models) {
			console.log($config?.default_models.split(',') ?? '');
			selectedModels = $config?.default_models.split(',');
		} else {
			selectedModels = [''];
		}

		if ($page.url.searchParams.get('q')) {
			prompt = $page.url.searchParams.get('q') ?? '';

			if (prompt) {
				await tick();
				submitPrompt(prompt);
			}
		}

		selectedModels = selectedModels.map((modelId) => ($models.map((m) => m.id).includes(modelId) ? modelId : ''));

		const userSettings = await getUserSettings(localStorage.token);

		if (userSettings) {
			settings.set(userSettings.ui);
		} else {
			settings.set(JSON.parse(localStorage.getItem('settings') ?? '{}'));
		}

		const chatInput = document.getElementById('chat-textarea');
		setTimeout(() => chatInput?.focus(), 0);
	};

	const loadChat = async () => {
		chatId.set(chatIdProp);
		chat = await getChatById(localStorage.token, $chatId).catch(async (error) => {
			await goto('/');
			return null;
		});

		if (chat) {
			tags = await getTags();
			const chatContent = chat.chat;

			if (chatContent) {
				console.log(chatContent);
				selectedModels = chatContent?.models !== undefined && chatContent?.models !== null ? chatContent.models : [''];

				history =
					(chatContent?.history ?? undefined) !== undefined
						? chatContent.history
						: convertMessagesToHistory(chatContent.messages);

				console.log('loaded chat history', history);
				title = chatContent.title;

				const userSettings = await getUserSettings(localStorage.token);

				if (userSettings) {
					settings.set(userSettings.ui);
				} else {
					settings.set(JSON.parse(localStorage.getItem('settings') ?? '{}'));
				}

				params = chatContent?.params ?? {};
				chatFiles = chatContent?.files ?? [];

				autoScroll = true;
				await tick();

				if (messages.length > 0) {
					history.messages[messages.at(-1)!.id].done = true;
				}
				await tick();

				if (chatContent.article) {
					await tick();
					toast.message('Redirecting to article...');
					window.setTimeout(() => {
						goto(`/article/${chatContent.article}`);
					}, 2000);
				}

				return true;
			} else {
				return null;
			}
		}
	};

	const scrollToBottom = async () => {
		await tick();
		if (messagesContainerElement) {
			messagesContainerElement.scrollTop = messagesContainerElement.scrollHeight;
		}
	};

	const createMessagesList = (responseMessageId: string): Message[] => {
		const message = history.messages[responseMessageId];
		if (message.parentId) {
			return [...createMessagesList(message.parentId), message];
		} else {
			return [message];
		}
	};

	// const createMessagesList = (responseMessageId: string): Message[] => {
	// 	const message = history.messages[responseMessageId];
	// 	if (message.parentId) {
	// 		const parentMessages = createMessagesList(message.parentId);
	// 		const unique = new Set(parentMessages.map((m) => m.id));
	// 		if (!unique.has(message.id)) {
	// 			return [...parentMessages, message];
	// 		} else {
	// 			return parentMessages.map((m) => (m.id === message.id ? message : m));
	// 		}
	// 	} else {
	// 		return [message];
	// 	}
	// };

	const chatCompletedHandler = async (
		chatId: string,
		modelId: string,
		responseMessageId: string,
		messages: Message[]
	) => {
		await mermaid.run({
			querySelector: '.mermaid'
		});

		const res = await chatCompleted(localStorage.token, {
			model: modelId,
			messages: messages.map((m) => ({
				id: m.id,
				role: m.role,
				content: m.content,
				info: m.info ? m.info : undefined,
				timestamp: m.timestamp
			})),
			chat_id: chatId,
			session_id: $socket?.id,
			id: responseMessageId
		}).catch((error) => {
			toast.error(error);
			messages.at(-1)!.error = { content: error };

			return null;
		});

		if (res !== null) {
			// Update chat history with the new messages
			for (const message of res.messages) {
				history.messages[message.id] = {
					...history.messages[message.id],
					...(history.messages[message.id].content !== message.content
						? { originalContent: history.messages[message.id].content }
						: {}),
					...message
				};
			}
		}

		if ($chatId == chatId) {
			if ($settings.saveChatHistory ?? true) {
				await updateChatById(localStorage.token, chatId, {
					models: selectedModels,
					messages: messages,
					history: history,
					params: params,
					files: chatFiles
				});
				chats.set(await getChatList(localStorage.token));
			}
		}
	};

	const chatActionHandler = async (chatId: string, actionId: string, modelId: string, responseMessageId: string) => {
		const res = await chatAction(localStorage.token, actionId, {
			model: modelId,
			messages: messages.map((m) => ({
				id: m.id,
				role: m.role,
				content: m.content,
				info: m.info ? m.info : undefined,
				timestamp: m.timestamp
			})),
			chat_id: chatId,
			session_id: $socket?.id,
			id: responseMessageId
		}).catch((error) => {
			toast.error(error);
			messages.at(-1)!.error = { content: error };
			return null;
		});

		if (res !== null) {
			// Update chat history with the new messages
			for (const message of res.messages) {
				history.messages[message.id] = {
					...history.messages[message.id],
					...(history.messages[message.id].content !== message.content
						? { originalContent: history.messages[message.id].content }
						: {}),
					...message
				};
			}
		}

		if ($chatId == chatId) {
			if ($settings.saveChatHistory ?? true) {
				chat = await updateChatById(localStorage.token, chatId, {
					models: selectedModels,
					messages: messages,
					history: history,
					params: params,
					files: chatFiles
				});
				chats.set(await getChatList(localStorage.token));
			}
		}
	};

	const getChatEventEmitter = async (modelId: string, chatId: string = '') => {
		return setInterval(() => {
			$socket?.emit('usage', {
				action: 'chat',
				model: modelId,
				chat_id: chatId
			});
		}, 1000);
	};

	//////////////////////////
	// Cisco Edited functions
	//////////////////////////

	//////////////////////////
	// Cisco modified Ollama functions
	//////////////////////////

	// const submitPrompt = async (userPrompt, _user = null, _messages = null) => {
	// 	console.log('corey userPrompt is ', userPrompt);

	// 	selectedModels = selectedModels.map((modelId) =>
	// 		$models.map((m) => m.id).includes(modelId) ? modelId : ''
	// 	);

	// 	if (selectedModels.includes('')) {
	// 		toast.error($i18n.t('Model not selected'));
	// 		return;
	// 	}

	// 	// Reset chat message textarea height
	// 	document.getElementById('chat-textarea').style.height = '';

	// 	// Set clarificationNeeded to true before checking for clarification
	// 	// clarificationNeeded = true;

	// 	// Check if clarification is needed before sending the prompt
	// 	if (!clarificationNeeded) {
	// 		// document.getElementById('chat-textarea')?.setAttribute('disabled', '');
	// 		const clarification = await checkClarificationNeeded(userPrompt);
	// 		console.log('Corey userPrompt from the await checkClarificationNeeded is', userPrompt);

	// 		if (clarification) {
	// 			clarificationNeeded = true;

	// 			originalUserPrompt = userPrompt;

	// 			clarificationQuestion = `Help me get you the best answer: "${userPrompt}"<br><br>${clarification.question}`;

	// 			clarificationOptions = clarification.options;

	// 			clarificationVisible = true;
	// 			return;
	// 		}
	// 	} else {
	// 		let clarificationMessageId = uuidv4();
	// 		console.log('wake up corey files is:', files);

	// 		const clarificationString = `
	//            ${userPrompt || 'N/A'}
	// 		    ${promptNotIncluded && promptNotIncluded.length > 0 ? promptNotIncluded.join(', ') : ''}`;

	// 		console.log('hey corey clarificationString is ', clarificationString);
	// 		const clarificationMessage = {
	// 			id: clarificationMessageId,
	// 			parentId: messages.length !== 0 ? messages.at(-1).id : null,
	// 			childrenIds: [],
	// 			role: 'user',
	// 			user: _user ?? undefined,
	// 			content: clarificationString,
	// 			timestamp: Math.floor(Date.now() / 1000)
	// 		};

	// 		// Add clarification message to history and messages array
	// 		history.messages[clarificationMessageId] = clarificationMessage;
	// 		messages = [...messages, clarificationMessage];
	// 		history.currentId = clarificationMessageId;

	// 		clarificationNeeded = false;
	// 		originalUserPrompt = '';
	// 		// Hide the clarification card
	// 		clarificationVisible = false;
	// 		console.log('');
	// 	}

	// 	// const clarifiedPrompt = handleClarificationSubmit(
	// 	// 	selectedOptionsString,
	// 	// 	notOptionsString,
	// 	// 	inputValue
	// 	// );

	// 	// if (clarifiedPrompt) {
	// 	// 	userPrompt = clarifiedPrompt;
	// 	// }

	// 	// Create the clarificationMessage object

	// 	// clarificationNeeded = false;
	// 	// originalUserPrompt = '';
	// 	// // Hide the clarification card
	// 	// clarificationVisible = false;

	// 	// Wait until history/message have been updated
	// 	await tick();

	// 	// Create new chat if only one message in messages
	// 	if (messages.length === 1) {
	// 		if ($settings.saveChatHistory ?? true) {
	// 			chat = await createNewChat(localStorage.token, {
	// 				id: $chatId,
	// 				title: $i18n.t('New Chat'),
	// 				models: selectedModels,
	// 				system: $settings.system ?? undefined,
	// 				options: {
	// 					...($settings.options ?? {})
	// 				},
	// 				messages: messages,
	// 				history: history,
	// 				tags: [],
	// 				timestamp: Date.now()
	// 			});
	// 			await chats.set(await getChatList(localStorage.token));
	// 			await chatId.set(chat.id);
	// 		} else {
	// 			await chatId.set('local');
	// 		}
	// 		await tick();
	// 	}
	// 	scrollToBottom();
	// 	// Reset chat input textarea
	// 	document.getElementById('chat-textarea')?.setAttribute('enabled', '');
	// 	prompt = '';
	// 	files = [];
	// 	selectedOption = '';
	// 	notOptions = [];

	// 	if (Array.isArray(messages) && messages.length > 0) {
	// 		let content = messages.at(-1).content;
	// 		console.log('hey Corey content is', content);
	// 		if (typeof content === 'string') {
	// 			console.log('corey content is ', content);
	// 			await sendPrompt(content, messages.at(-1).id);
	// 		} else {
	// 			console.error('corey Content is not a string:', typeof content);
	// 		}
	// 	} else {
	// 		console.error('corey Messages is not an array or is empty:', messages);
	// 		// Handle the case when messages is not an array or is empty
	// 		// You can show an error message or take appropriate action
	// 		return; // Early return to prevent further execution
	// 	}
	// };

	//////////////////////////
	// Ollama functions
	//////////////////////////

	// const sendPrompt = async (prompt: string, parentId: string | null = null) => {
	// 	const _chatId = JSON.parse(JSON.stringify($chatId));

	// 	await Promise.all(
	// 		selectedModels.map(async (modelId) => {
	// 			const model = $models.filter((m) => m.id === modelId).at(0);

	// 			if (model) {
	// 				// Create response message
	// 				let responseMessageId = uuidv4();
	// 				let responseMessage = {
	// 					parentId: parentId,
	// 					id: responseMessageId,
	// 					childrenIds: [],
	// 					role: 'assistant',
	// 					content: '',
	// 					model: model.id,
	// 					timestamp: Math.floor(Date.now() / 1000) // Unix epoch
	// 				};

	// 				// Add message to history and Set currentId to messageId
	// 				history.messages[responseMessageId] = responseMessage;
	// 				history.currentId = responseMessageId;

	// 				// Append messageId to childrenIds of parent message
	// 				if (parentId !== null && history.messages[parentId]) {
	// 					history.messages[parentId].childrenIds = [
	// 						...(history.messages[parentId].childrenIds || []),
	// 						responseMessageId
	// 					];
	// 				}

	// 				if (model?.external) {
	// 					await sendPromptOpenAI(model, prompt, responseMessageId, _chatId);
	// 				} else if (model) {
	// 					await sendPromptOllama(model, prompt, responseMessageId, _chatId);
	// 				}
	// 			} else {
	// 				toast.error($i18n.t(`Model {{modelId}} not found`, { modelId }));
	// 			}
	// 		})
	// 	);

	// 	await chats.set(await getChatList(localStorage.token));
	// };

	//////////////////////////
	// Chat functions
	//////////////////////////

	const submitPrompt = async (userPrompt: string, { _raw = false } = {}) => {
		let _responses: string[] = [];
		console.log('submitPrompt', $chatId);
		console.log('userPrompt from submitPrompt', userPrompt);
		selectedModels = selectedModels.map((modelId) => ($models.map((m) => m.id).includes(modelId) ? modelId : ''));

		if (selectedModels.includes('')) {
			toast.error($i18n.t('Model not selected'));
		} else if (messages.length != 0 && messages.at(-1)?.done != true) {
			// Response not done
			console.log('wait');
		} else if (messages.length != 0 && messages.at(-1)?.error) {
			// Error in response
			toast.error($i18n.t(`Oops! There was an error in the previous response. Please try again or contact admin.`));
			// File object shape:
			// -------------------
			// collection_name: "2a1113258f84e36ba0f4734b33092836936e538c539b2c741218fa9bc7aef13"
			// error: ""
			// file: {id: '362ec854-789f-4563-8981-92c0f196cd47', user_id: 'b7ad0b4d-972a-4225-8cbf-b592b4a51a90', filename: '362ec854-789f-4563-8981-92c0f196cd47_auto-surveillance-vlan-catalyst-1200-1300-switches.pdf', meta: {…}, created_at: 1724870348}
			// id: "362ec854-789f-4563-8981-92c0f196cd47"
			// name: "auto-surveillance-vlan-catalyst-1200-1300-switches.pdf"
			// status: "processed"
			// type: "file"
			// url: "/api/v1/files/362ec854-789f-4563-8981-92c0f196cd47"
			// -------------------
		} else if (
			files.length > 0 &&
			files.filter((file) => file.type !== 'image' && file.status !== 'processed').length > 0
		) {
			// Upload not done
			toast.error(
				$i18n.t(
					`Oops! Hold tight! Your files are still in the processing oven. We're cooking them up to perfection. Please be patient and we'll let you know once they're ready.`
				)
			);
		} else {
			// Reset chat input textarea
			const chatTextAreaElement = document.getElementById('chat-textarea') as unknown as HTMLTextAreaElement;

			if (chatTextAreaElement) {
				chatTextAreaElement.value = '';
				chatTextAreaElement.style.height = '';
			}

			const _files: ClientFile[] = JSON.parse(JSON.stringify(files));
			console.log('[submitPrompt:Chat.svelte] -> _files: ', _files);
			chatFiles.push(..._files.filter((item) => ['doc', 'file', 'collection'].includes(item.type as string)));
			chatFiles = chatFiles.filter(
				// Remove duplicates
				(item, index, array) => array.findIndex((i) => JSON.stringify(i) === JSON.stringify(item)) === index
			);

			// Reset files
			files = [];
			// Reset prompt
			prompt = '';

			// Create user message
			let userMessageId = uuidv4();
			let userMessage = {
				id: userMessageId,
				parentId: messages.length !== 0 ? messages.at(-1)!.id : null,
				childrenIds: [],
				role: 'user',
				content: userPrompt,
				files: _files.length > 0 ? _files : undefined,
				timestamp: Math.floor(Date.now() / 1000), // Unix epoch in seconds
				models: selectedModels.filter((m, mIdx) => selectedModels.indexOf(m) === mIdx)
			};

			// Add message to history and Set currentId to messageId
			history.messages[userMessageId] = userMessage;
			history.currentId = userMessageId;

			// Append messageId to childrenIds of parent message
			if (messages.length !== 0 && messages.at(-1)) {
				(history.messages[messages.at(-1)!.id].childrenIds ?? []).push(userMessageId);
			}
			// Wait until history/message have been updated
			await tick();

			if (isGeneratingNewArticle) {
				isGeneratingNewArticle = !isGeneratingNewArticle;
				_responses = await sendPromptForArticleGen(userPrompt, userMessageId, { newChat: true });
			} else {
				_responses = await sendPrompt(userPrompt, userMessageId, { newChat: true });
			}
		}

		return _responses;
	};

	const sendPromptForArticleGen = async (
		prompt: string,
		parentId: string,
		{ modelId = null, newChat = false }: { modelId?: string | null; newChat?: boolean } = {}
	) => {
		let _responses: string[] = [];
		let refinedPrompt = prompt;
		let refinementCount = 0;
		let selectedModelIds = modelId ? [modelId] : atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;

		const responseMessageIds: { [id: string]: string } = {};

		for (const modelId of selectedModelIds) {
			const model = $models.filter((m) => m.id === modelId).at(0);

			if (model) {
				let responseMessageId = uuidv4();
				let responseMessage = {
					parentId: parentId,
					id: responseMessageId,
					childrenIds: [],
					role: 'assistant',
					content: '',
					model: model.id,
					modelName: model.name ?? model.id,
					userContext: null,
					timestamp: Math.floor(Date.now() / 1000) // Unix epoch
				};

				history.messages[responseMessageId] = responseMessage;
				history.currentId = responseMessageId;

				if (parentId !== null) {
					history.messages[parentId].childrenIds = [
						...(history.messages[parentId].childrenIds ?? []),
						responseMessageId
					];
				}
				responseMessageIds[modelId] = responseMessageId;
			}
		}

		await tick();

		const refinePrompt = (currentPrompt: string) => {
			const template = `You work for Cisco Systems, a multinational technology conglomerate that designs, manufactures, and sells networking equipment. Your team is responsible for managing the company's knowledge base, which includes a vast collection of articles on various networking devices. You need to refine the user-provided query to ensure it aligns with the search terms and keywords typically used in this domain.

Steps:
1. Review the user-provided article configuration query.
2. Rewrite the query to improve its clarity and alignment with typical search terms and keywords used in this domain.
3. Ensure the refined query removes the Device Name to improve results.
4. Use decomposition to simplify the query and improve search results.

User's article configuration: {{QUERY}}

Please rewrite the query for optimal search results. Return only the refined query and nothing else.
`;
			const systemPrompt = template.replace('{{QUERY}}', currentPrompt);

			return systemPrompt;
		};

		refinedPrompt = refinePrompt(prompt);

		if (newChat) {
			if ($settings.saveChatHistory ?? true) {
				chat = await createNewChat(localStorage.token, {
					id: $chatId,
					title: $i18n.t('New Chat'),
					models: selectedModels,
					system: $settings.system ?? undefined,
					params: params,
					messages: messages,
					history: history,
					tags: [],
					timestamp: Date.now()
				});
				chats.set(await getChatList(localStorage.token));
				if (chat) chatId.set(chat.id);
			} else {
				chatId.set('local');
			}
			await tick();
		}

		const _chatId: string = JSON.parse(JSON.stringify($chatId));

		await Promise.all(
			selectedModelIds.map(async (modelId) => {
				console.log('modelId', modelId);
				const model = $models.filter((m) => m.id === modelId).at(0);

				if (model) {
					// If there are image files, check if model is vision capable
					const hasImages = messages.some((message) => message.files?.some((file) => file.type === 'image'));

					if (hasImages && !(model.info?.meta?.capabilities?.vision ?? true)) {
						toast.error(
							$i18n.t('Model {{modelName}} is not vision capable', {
								modelName: model.name ?? model.id
							})
						);
					}

					let responseMessageId = responseMessageIds[modelId];
					let responseMessage = history.messages[responseMessageId];

					let userContext = null;
					if ($settings?.memory ?? false) {
						if (userContext === null) {
							const res = await queryMemory(localStorage.token, prompt).catch((error) => {
								toast.error(error);
								return null;
							});
							if (res) {
								if (res.documents[0].length > 0) {
									userContext = res.documents[0].reduce((acc, doc, index) => {
										const createdAtTimestamp = res.metadatas[0][index].created_at;
										const createdAtDate = new Date(createdAtTimestamp * 1000).toISOString().split('T')[0];
										return `${acc}${index + 1}. [${createdAtDate}]. ${doc}\n`;
									}, '');
								}

								console.log(userContext);
							}
						}
					}
					if ((params && params?.proficiency) ?? false) {
						if (userContext === null) {
							userContext = `Network Proficiency Level: ${params.proficiency}\n`;
						} else {
							userContext += `Network Proficiency Level: ${params.proficiency}\n`;
						}
					}

					responseMessage.userContext = userContext;

					const chatEventEmitter = await getChatEventEmitter(model.id, _chatId);

					let _response: string | null | undefined = null;
					if (model?.owned_by === 'openai') {
						console.log('Sending via OpenAI Model');
						_response = await sendPromptArticleGenOpenAI(model, refinedPrompt, responseMessageId, _chatId);
					} else if (model.owned_by === 'ollama') {
						console.log('Sending via Ollama Model');
						_response = await sendPromptOllama(model, prompt, responseMessageId, _chatId);
					}
					_responses.push(_response as string);

					if (chatEventEmitter) clearInterval(chatEventEmitter);
				} else {
					toast.error($i18n.t(`Model {{modelId}} not found`, { modelId }));
				}
			})
		);

		chats.set(await getChatList(localStorage.token));
		return _responses;
	};

	const sendPromptArticleGenOpenAI = async (
		model: Model,
		prompt: string,
		responseMessageId: string,
		_chatId: string
	) => {
		let _response = null;
		const responseMessage = history.messages[responseMessageId];

		let files = JSON.parse(JSON.stringify(chatFiles));
		if (model?.info?.meta?.knowledge ?? false) {
			files.push(...model.info?.meta.knowledge);
		}
		if (responseMessage?.files) {
			files.push(...responseMessage?.files.filter((item) => item.type && ['web_search_results'].includes(item.type)));
		}

		scrollToBottom();

		eventTarget.dispatchEvent(
			new CustomEvent('chat:start', {
				detail: {
					id: responseMessageId
				}
			})
		);
		await tick();

		const messagesBody = [...[{ role: 'user', content: prompt }]].filter((message) => message?.content?.trim());

		console.log('messagesBody', messagesBody);
		const refinedQuery = await generateOpenAIChatCompletionQuestions(localStorage.token, {
			stream: false,
			model: model.id,
			messages: messagesBody,
			temperature: 0
		}).catch((error) => {
			console.error(error);
			responseMessage.error = { content: error };
			return null;
		});
		await tick();
		await scrollToBottom();
		if (refinedQuery) {
			responseMessage.content = `We have refined your query to: ${refinedQuery}`;
			messages = createMessagesList(responseMessageId);
			await chatCompletedHandler(_chatId, model.id, responseMessageId, messages);
			_response = responseMessage.content;
		}
		responseMessage.done = true;
		await tick();

		let lastSentence = extractSentencesForAudio(responseMessage.content)?.at(-1) ?? '';
		if (lastSentence) {
			eventTarget.dispatchEvent(
				new CustomEvent('chat', {
					detail: { id: responseMessageId, content: lastSentence }
				})
			);
		}

		eventTarget.dispatchEvent(
			new CustomEvent('chat:finish', {
				detail: {
					id: responseMessageId,
					content: responseMessage.content
				}
			})
		);

		if (autoScroll) {
			await scrollToBottom();
		}

		if (messages.length > 2 && selectedModels[0] === model.id) {
			window.history.replaceState(history.state, '', `/c/${_chatId}`);

			const _title = await generateChatTitle(prompt);
			await setChatTitle(_chatId, _title);
		}

		const article = await createNewArticle(localStorage.token, responseMessage.content, seriesName);
		if ($chatId == _chatId) {
			if ($settings.saveChatHistory ?? true) {
				chat = await updateChatById(localStorage.token, _chatId, {
					models: selectedModels,
					messages: messages,
					history: history,
					params: params,
					files: chatFiles,
					article: article.id
				});
				chats.set(await getChatList(localStorage.token));
			}
		}
		_stopGeneratingArticle = false;
		activeArticle.set(article);
		console.log('article', article);
		console.log('activeArticle', $activeArticle);
		await goto(`/article/${article.id}`);
		return _response;
	};

	const sendPrompt = async (
		prompt: string,
		parentId: string,
		{ modelId = null, newChat = false }: { modelId?: string | null; newChat?: boolean } = {}
	) => {
		let _responses: string[] = [];

		// If modelId is provided, use it, else use selected model
		let selectedModelIds = modelId ? [modelId] : atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;

		// Create response messages for each selected model
		const responseMessageIds: { [x: string]: string } = {};
		for (const modelId of selectedModelIds) {
			const model = $models.filter((m) => m.id === modelId).at(0);

			if (model) {
				let responseMessageId = uuidv4();
				let responseMessage = {
					parentId: parentId,
					id: responseMessageId,
					childrenIds: [],
					role: 'assistant',
					content: '',
					model: model.id,
					modelName: model.name ?? model.id,
					userContext: null,
					timestamp: Math.floor(Date.now() / 1000) // Unix epoch
				};

				// Add message to history and Set currentId to messageId
				history.messages[responseMessageId] = responseMessage;
				history.currentId = responseMessageId;

				// Append messageId to childrenIds of parent message
				if (parentId !== null) {
					history.messages[parentId].childrenIds = [
						...(history.messages[parentId].childrenIds ?? []),
						responseMessageId
					];
				}

				responseMessageIds[modelId] = responseMessageId;
			}
		}
		await tick();

		// Create new chat if only one message in messages
		if (newChat && messages.length == 2) {
			if ($settings.saveChatHistory ?? true) {
				chat = await createNewChat(localStorage.token, {
					id: $chatId,
					title: $i18n.t('New Chat'),
					models: selectedModels,
					system: $settings.system ?? undefined,
					params: params,
					messages: messages,
					history: history,
					tags: [],
					timestamp: Date.now()
				});
				chats.set(await getChatList(localStorage.token));
				if (chat) chatId.set(chat.id);
			} else {
				chatId.set('local');
			}
			await tick();
		}

		const _chatId: string = JSON.parse(JSON.stringify($chatId));

		await Promise.all(
			selectedModelIds.map(async (modelId) => {
				console.log('modelId', modelId);
				const model = $models.filter((m) => m.id === modelId).at(0);

				if (model) {
					// If there are image files, check if model is vision capable
					const hasImages = messages.some((message) => message.files?.some((file) => file.type === 'image'));

					if (hasImages && !(model.info?.meta?.capabilities?.vision ?? true)) {
						toast.error(
							$i18n.t('Model {{modelName}} is not vision capable', {
								modelName: model.name ?? model.id
							})
						);
					}

					let responseMessageId = responseMessageIds[modelId];
					let responseMessage = history.messages[responseMessageId];

					let userContext = null;
					if ($settings?.memory ?? false) {
						if (userContext === null) {
							const res = await queryMemory(localStorage.token, prompt).catch((error) => {
								toast.error(error);
								return null;
							});
							if (res) {
								if (res.documents[0].length > 0) {
									userContext = res.documents[0].reduce((acc, doc, index) => {
										const createdAtTimestamp = res.metadatas[0][index].created_at;
										const createdAtDate = new Date(createdAtTimestamp * 1000).toISOString().split('T')[0];
										return `${acc}${index + 1}. [${createdAtDate}]. ${doc}\n`;
									}, '');
								}

								console.log(userContext);
							}
						}
					}
					if ((params && params?.proficiency) ?? false) {
						if (userContext === null) {
							userContext = `Network Proficiency Level: ${params.proficiency}\n`;
						} else {
							userContext += `Network Proficiency Level: ${params.proficiency}\n`;
						}
					}

					responseMessage.userContext = userContext;

					const chatEventEmitter = await getChatEventEmitter(model.id, _chatId);
					if (webSearchEnabled) {
						await getWebSearchResults(model.id, parentId, responseMessageId);
					}

					let _response: string | null | undefined = null;
					if (model.owned_by === 'openai') {
						console.log('Sending via OpenAI Model');
						_response = await sendPromptOpenAI(model, prompt, responseMessageId, _chatId);
					} else if (model.owned_by === 'ollama') {
						console.log('Sending via Ollama Model');
						_response = await sendPromptOllama(model, prompt, responseMessageId, _chatId);
					}
					_responses.push(_response as string);

					if (chatEventEmitter) clearInterval(chatEventEmitter);
				} else {
					toast.error($i18n.t(`Model {{modelId}} not found`, { modelId }));
				}
			})
		);

		chats.set(await getChatList(localStorage.token));
		return _responses;
	};

	const sendPromptOllama = async (model: Model, userPrompt: string, responseMessageId: string, _chatId: string) => {
		let _response = null;

		const responseMessage = history.messages[responseMessageId];

		// Wait until history/message have been updated
		await tick();

		// Scroll down
		scrollToBottom();

		const messagesBody: Array<Partial<Message>> = [
			params?.system || $settings.system || (responseMessage?.userContext ?? null)
				? ({
						role: 'system',
						content: `${promptTemplate(
							params?.system ?? $settings?.system ?? '',
							$user?.name,
							$settings?.userLocation ? await getAndUpdateUserLocation(localStorage.token) : undefined
						)}${responseMessage?.userContext ?? null ? `\n\nUser Context:\n${responseMessage?.userContext ?? ''}` : ''}`
				  } as Partial<Message>)
				: undefined,
			...messages
		]
			.filter((message) => message?.content?.trim())
			.map((message, idx, arr) => {
				// Prepare the base message object
				const baseMessage: { role?: string; content?: string; images?: string[] } = {
					role: message?.role,
					content: message?.content
				};

				// Extract and format image URLs if any exist
				const imageUrls = message?.files
					?.filter((file) => file.type === 'image')
					.map((file) => file.url!.slice(file.url!.indexOf(',') + 1));

				// Add images array only if it contains elements
				if (imageUrls && imageUrls.length > 0 && message!.role === 'user') {
					baseMessage.images = imageUrls;
				}
				return baseMessage;
			});

		let lastImageIndex = -1;

		// Find the index of the last object with images
		messagesBody.forEach((item, index) => {
			if (item.images) {
				lastImageIndex = index;
			}
		});

		// Remove images from all but the last one
		messagesBody.forEach((item, index) => {
			if (index !== lastImageIndex) {
				delete item.images;
			}
		});

		let files = JSON.parse(JSON.stringify(chatFiles));
		if (model?.info?.meta?.knowledge ?? false) {
			files.push(...model.info!.meta.knowledge);
		}
		if (responseMessage?.files) {
			files.push(...responseMessage?.files.filter((item) => ['web_search_results'].includes(item.type as string)));
		}

		eventTarget.dispatchEvent(
			new CustomEvent('chat:start', {
				detail: {
					id: responseMessageId
				}
			})
		);

		await tick();

		const [res, controller]: [Response | null, AbortController] = await generateChatCompletion(localStorage.token, {
			stream: true,
			model: model.id,
			messages: messagesBody,
			options: {
				...(params ?? $settings.params ?? {}),
				stop:
					params?.stop ?? $settings?.params?.stop ?? undefined
						? (params?.stop ?? $settings.params?.stop).map((str: string) =>
								decodeURIComponent(JSON.parse('"' + str.replace(/\"/g, '\\"') + '"'))
						  )
						: undefined,
				num_predict: params?.max_tokens ?? $settings?.params?.max_tokens ?? undefined,
				repeat_penalty: params?.frequency_penalty ?? $settings?.params?.frequency_penalty ?? undefined
			},
			format: $settings.requestFormat ?? undefined,
			keep_alive: $settings.keepAlive ?? undefined,
			tool_ids: selectedToolIds.length > 0 ? selectedToolIds : undefined,
			files: files.length > 0 ? files : undefined,
			...(Object.keys(valves).length ? { valves } : {}),
			session_id: $socket?.id,
			chat_id: $chatId,
			id: responseMessageId
		});

		if (res === null) {
			toast.error($i18n.t(`Uh-oh! There was an issue connecting to {{provider}}.`, { provider: 'Ollama' }));
			responseMessage.error = {
				content: $i18n.t(`Uh-oh! There was an issue connecting to {{provider}}.`, {
					provider: 'Ollama'
				})
			};
		}

		if (res && res.ok) {
			console.log('controller', controller);

			const response = res as { body: ReadableStream<Uint8Array> };

			const reader = response.body.pipeThrough(new TextDecoderStream()).pipeThrough(splitStream('\n')).getReader();

			while (true) {
				const { value, done } = await reader.read();
				if (done || stopResponseFlag || _chatId !== $chatId) {
					responseMessage.done = true;
					messages = messages;

					if (stopResponseFlag) {
						controller.abort('User: Stop Response');
					} else {
						const messages = createMessagesList(responseMessageId);
						await chatCompletedHandler(_chatId, model.id, responseMessageId, messages);
					}

					_response = responseMessage.content;
					break;
				}

				try {
					let lines = value.split('\n');
					console.log(lines);
					for (const line of lines) {
						if (line !== '') {
							console.log(line);
							let data = JSON.parse(line);

							if ('citations' in data) {
								responseMessage.citations = data.citations;
								continue;
							}

							if ('detail' in data) {
								throw data;
							}

							if (data.done == false) {
								if (responseMessage.content == '' && data.message.content == '\n') {
									continue;
								} else {
									responseMessage.content += data.message.content;

									const sentences = extractSentencesForAudio(responseMessage.content);
									sentences.pop();

									// dispatch only last sentence and make sure it hasn't been dispatched before
									if (sentences.length > 0 && sentences[sentences.length - 1] !== responseMessage.lastSentence) {
										responseMessage.lastSentence = sentences[sentences.length - 1];
										eventTarget.dispatchEvent(
											new CustomEvent('chat', {
												detail: { id: responseMessageId, content: sentences[sentences.length - 1] }
											})
										);
									}

									messages = messages;
								}
							} else {
								responseMessage.done = true;

								if (responseMessage.content == '') {
									responseMessage.error = {
										code: 400,
										content: `Oops! No text generated from Ollama, Please try again.`
									};
								}

								responseMessage.context = data.context ?? null;
								responseMessage.info = {
									total_duration: data.total_duration,
									load_duration: data.load_duration,
									sample_count: data.sample_count,
									sample_duration: data.sample_duration,
									prompt_eval_count: data.prompt_eval_count,
									prompt_eval_duration: data.prompt_eval_duration,
									eval_count: data.eval_count,
									eval_duration: data.eval_duration
								};
								messages = messages;

								if ($settings.notificationEnabled && !document.hasFocus()) {
									const notification = new Notification(`${model.id}`, {
										body: responseMessage.content,
										icon: `${WEBUI_BASE_URL}/static/favicon.png`
									});
								}

								if ($settings?.responseAutoCopy ?? false) {
									copyToClipboard(responseMessage.content);
								}

								if ($settings.responseAutoPlayback && !$showCallOverlay) {
									await tick();
									document.getElementById(`speak-button-${responseMessage.id}`)?.click();
								}
							}
						}
					}
				} catch (error) {
					console.log(error);
					if (isErrorWithDetail(error)) {
						toast.error(error.detail);
					}
					// if ('detail' in error) {
					// 	toast.error(error.detail);
					// }
					break;
				}

				if (autoScroll) {
					scrollToBottom();
				}
			}

			if ($chatId == _chatId) {
				if ($settings.saveChatHistory ?? true) {
					chat = await updateChatById(localStorage.token, _chatId, {
						messages: messages,
						history: history,
						models: selectedModels,
						params: params,
						files: chatFiles
					});
					chats.set(await getChatList(localStorage.token));
				}
			}
		} else {
			if (res !== null) {
				const error = await res.json();
				console.log(error);
				if (isErrorWithDetail(error)) {
					toast.error(error.detail);
					responseMessage.error = { content: error.detail };
				} else {
					toast.error(error.error);
					responseMessage.error = { content: error.error };
				}
			} else {
				toast.error($i18n.t(`Uh-oh! There was an issue connecting to {{provider}}.`, { provider: 'Ollama' }));
				responseMessage.error = {
					content: $i18n.t(`Uh-oh! There was an issue connecting to {{provider}}.`, {
						provider: 'Ollama'
					})
				};
			}
			responseMessage.done = true;
			messages = messages;
		}

		stopResponseFlag = false;
		await tick();

		let lastSentence = extractSentencesForAudio(responseMessage.content)?.at(-1) ?? '';
		if (lastSentence) {
			eventTarget.dispatchEvent(
				new CustomEvent('chat', {
					detail: { id: responseMessageId, content: lastSentence }
				})
			);
		}
		eventTarget.dispatchEvent(
			new CustomEvent('chat:finish', {
				detail: {
					id: responseMessageId,
					content: responseMessage.content
				}
			})
		);

		if (autoScroll) {
			scrollToBottom();
		}

		if (messages.length == 2 && messages.at(1)!.content !== '' && selectedModels[0] === model.id) {
			window.history.replaceState(history.state, '', `/c/${_chatId}`);
			const _title = await generateChatTitle(userPrompt);
			await setChatTitle(_chatId, _title);
		}

		return _response;
	};

	const sendPromptOpenAI = async (model: Model, userPrompt: string, responseMessageId: string, _chatId: string) => {
		let _response = null;
		const responseMessage = history.messages[responseMessageId];

		let files = JSON.parse(JSON.stringify(chatFiles));
		if (model?.info?.meta?.knowledge ?? false) {
			files.push(...model.info?.meta.knowledge);
		}
		if (responseMessage?.files) {
			files.push(...responseMessage?.files.filter((item) => item.type && ['web_search_results'].includes(item.type)));
		}

		scrollToBottom();

		eventTarget.dispatchEvent(
			new CustomEvent('chat:start', {
				detail: {
					id: responseMessageId
				}
			})
		);
		await tick();
		const messagesBody = [
			params?.system || $settings.system || (responseMessage?.userContext ?? null)
				? {
						role: 'system',
						content: `${promptTemplate(
							params?.system ?? $settings?.system ?? '',
							$user?.name,
							$settings?.userLocation ? await getAndUpdateUserLocation(localStorage.token) : undefined
						)}${responseMessage?.userContext ?? null ? `\n\nUser Context:\n${responseMessage?.userContext ?? ''}` : ''}`
				  }
				: undefined,
			...messages
		]
			.filter((message) => message?.content?.trim())
			.map((message, idx, arr) => ({
				role: message!.role,
				...('files' in message! &&
				(message?.files?.filter((file) => file.type === 'image')?.length ?? 0 > 0 ?? false) &&
				message.role === 'user'
					? {
							content: [
								{
									type: 'text',
									text: arr.length - 1 !== idx ? message!.content : message?.raContent ?? message!.content
								},
								...message!
									.files!.filter((file) => file.type === 'image')
									.map((file) => ({
										type: 'image_url',
										image_url: {
											url: file.url
										}
									}))
							]
					  }
					: {
							content:
								// @ts-ignore
								arr.length - 1 !== idx ? message?.content : message?.raContent ?? message!.content
					  })
			}));

		console.log('messagesBody', messagesBody);

		try {
			const [res, controller] = await generateOpenAIChatCompletion(
				localStorage.token,
				{
					stream: true,
					model: model.id,
					stream_options:
						model.info?.meta?.capabilities?.usage ?? false
							? {
									include_usage: true
							  }
							: undefined,
					messages: messagesBody,
					seed: params?.seed ?? $settings?.params?.seed ?? undefined,
					stop:
						params?.stop ?? $settings?.params?.stop ?? undefined
							? (params?.stop ?? $settings.params?.stop).map((str: string) =>
									decodeURIComponent(JSON.parse('"' + str.replace(/\"/g, '\\"') + '"'))
							  )
							: undefined,
					temperature: params?.temperature ?? $settings?.params?.temperature ?? undefined,
					top_p: params?.top_p ?? $settings?.params?.top_p ?? undefined,
					frequency_penalty: params?.frequency_penalty ?? $settings?.params?.frequency_penalty ?? undefined,
					max_tokens: params?.max_tokens ?? $settings?.params?.max_tokens ?? undefined,
					tool_ids: selectedToolIds.length > 0 ? selectedToolIds : undefined,
					files: files.length > 0 ? files : undefined,
					...(Object.keys(valves).length ? { valves } : {}),
					session_id: $socket?.id,
					chat_id: $chatId,
					id: responseMessageId
				},
				`${WEBUI_BASE_URL}/api`
			);

			// Wait until history/message have been updated
			await tick();

			scrollToBottom();
			console.log('[Chat.svelte] $settings.splitLargeChunks: ', $settings.splitLargeChunks);
			if (res && res.ok && res.body) {
				const stream = await createOpenAITextStream(res.body, $settings.splitLargeChunks ?? true);
				let lastUsage = null;

				for await (const update of stream) {
					const { value, done, citations, error, usage } = update;
					if (error) {
						await handleOpenAIError(error, null, model, responseMessage);
						break;
					}
					if (done || stopResponseFlag || _chatId !== $chatId) {
						responseMessage.done = true;
						messages = messages;

						if (stopResponseFlag) {
							controller.abort('User: Stop Response');
						} else {
							const messages = createMessagesList(responseMessageId);

							await chatCompletedHandler(_chatId, model.id, responseMessageId, messages);
						}

						_response = responseMessage.content;

						break;
					}

					if (usage) {
						lastUsage = usage;
					}

					if (citations) {
						responseMessage.citations = citations;
						continue;
					}

					if (responseMessage.content == '' && value == '\n') {
						continue;
					} else {
						responseMessage.content += value;

						const sentences = extractSentencesForAudio(responseMessage.content);
						sentences.pop();

						// dispatch only last sentence and make sure it hasn't been dispatched before
						if (sentences.length > 0 && sentences[sentences.length - 1] !== responseMessage.lastSentence) {
							responseMessage.lastSentence = sentences[sentences.length - 1];
							eventTarget.dispatchEvent(
								new CustomEvent('chat', {
									detail: { id: responseMessageId, content: sentences[sentences.length - 1] }
								})
							);
						}

						messages = messages;
					}

					if (autoScroll) {
						scrollToBottom();
					}
				}

				if ($settings.notificationEnabled && !document.hasFocus()) {
					const notification = new Notification(`${model.id}`, {
						body: responseMessage.content,
						icon: `${WEBUI_BASE_URL}/static/favicon.png`
					});
				}

				if ($settings.responseAutoCopy) {
					copyToClipboard(responseMessage.content);
				}

				if ($settings.responseAutoPlayback && !$showCallOverlay) {
					await tick();

					document.getElementById(`speak-button-${responseMessage.id}`)?.click();
				}

				if (lastUsage) {
					responseMessage.info = { ...lastUsage, openai: true };
				}

				if ($chatId == _chatId) {
					if ($settings.saveChatHistory ?? true) {
						chat = await updateChatById(localStorage.token, _chatId, {
							models: selectedModels,
							messages: messages,
							history: history,
							params: params,
							files: chatFiles
						});
						chats.set(await getChatList(localStorage.token));
					}
				}
			} else {
				await handleOpenAIError(null, res, model, responseMessage);
			}
		} catch (error) {
			await handleOpenAIError(error, null, model, responseMessage);
		}
		messages = messages;

		stopResponseFlag = false;
		await tick();

		let lastSentence = extractSentencesForAudio(responseMessage.content)?.at(-1) ?? '';
		if (lastSentence) {
			eventTarget.dispatchEvent(
				new CustomEvent('chat', {
					detail: { id: responseMessageId, content: lastSentence }
				})
			);
		}

		eventTarget.dispatchEvent(
			new CustomEvent('chat:finish', {
				detail: {
					id: responseMessageId,
					content: responseMessage.content
				}
			})
		);

		if (autoScroll) {
			scrollToBottom();
		}

		if (messages.length == 2 && selectedModels[0] === model.id) {
			window.history.replaceState(history.state, '', `/c/${_chatId}`);

			const _title = await generateChatTitle(userPrompt);
			await setChatTitle(_chatId, _title);
		}

		return _response;
	};

	const handleOpenAIError = async (error: any, res: Response | null, model: Model, responseMessage: Message) => {
		let errorMessage = '';
		let innerError;

		if (error) {
			innerError = error;
		} else if (res !== null) {
			innerError = await res.json();
		}
		console.error(innerError);
		if ('detail' in innerError) {
			toast.error(innerError.detail);
			errorMessage = innerError.detail;
		} else if ('error' in innerError) {
			if ('message' in innerError.error) {
				toast.error(innerError.error.message);
				errorMessage = innerError.error.message;
			} else {
				toast.error(innerError.error);
				errorMessage = innerError.error;
			}
		} else if ('message' in innerError) {
			toast.error(innerError.message);
			errorMessage = innerError.message;
		}

		responseMessage.error = {
			content:
				$i18n.t(`Uh-oh! There was an issue connecting to {{provider}}.`, {
					provider: model.name ?? model.id
				}) +
				'\n' +
				errorMessage
		};
		responseMessage.done = true;

		messages = messages;
	};

	const stopResponse = () => {
		stopResponseFlag = true;
		console.log('stopResponse');
	};

	const stopArticleGeneration = () => {
		_stopGeneratingArticle = true;
		console.log('stopArticleGeneration');
	};

	const regenerateResponse = async (message: Message) => {
		console.log('regenerateResponse');

		if (messages.length != 0 && message.parentId) {
			let userMessage = history.messages[message.parentId];
			let userPrompt = userMessage.content;

			if ((userMessage?.models ?? [...selectedModels]).length == 1) {
				// If user message has only one model selected, sendPrompt automatically selects it for regeneration
				await sendPrompt(userPrompt, userMessage.id);
			} else {
				// If there are multiple models selected, use the model of the response message for regeneration
				// e.g. many model chat
				await sendPrompt(userPrompt, userMessage.id, { modelId: message.model });
			}
		}
	};

	const continueGeneration = async () => {
		console.log('continueGeneration');
		const _chatId = JSON.parse(JSON.stringify($chatId));
		let modelId;

		if (messages.length != 0 && messages.at(-1)?.done == true) {
			const responseMessage = history.messages[history.currentId!];
			responseMessage.done = false;
			await tick();

			const model = $models.filter((m) => m.id === responseMessage.model).at(0);

			if (model) {
				if (model?.owned_by === 'openai') {
					await sendPromptOpenAI(
						model,
						history.messages[responseMessage.parentId!].content,
						responseMessage.id,
						_chatId
					);
				} else
					await sendPromptOllama(
						model,
						history.messages[responseMessage.parentId!].content,
						responseMessage.id,
						_chatId
					);
			}
		} else {
			toast.error($i18n.t(`Model {{modelId}} not found`, { modelId }));
		}
	};

	const generateChatTitle = async (userPrompt: string) => {
		if ($settings?.title?.auto ?? true) {
			const title = await generateTitle(localStorage.token, selectedModels[0], userPrompt, $chatId).catch((error) => {
				console.error(error);
				return 'New Chat';
			});

			return title;
		} else {
			return `${userPrompt}`.slice(0, 20) + '...';
		}
	};

	const setChatTitle = async (_chatId: string, _title: string) => {
		if (_chatId === $chatId) {
			title = _title;
		}

		if ($settings.saveChatHistory ?? true) {
			chat = await updateChatById(localStorage.token, _chatId, { title: _title });
			chats.set(await getChatList(localStorage.token));
		}
	};

	const getWebSearchResults = async (model: string, parentId: string, responseId: string) => {
		const responseMessage = history.messages[responseId];
		const userMessage = history.messages[parentId];

		responseMessage.statusHistory = [
			{
				done: false,
				action: 'web_search',
				description: $i18n.t('Generating search query')
			}
		];
		messages = messages;

		const prompt = userMessage.content;
		let searchQuery = await generateSearchQuery(localStorage.token, model, messages, prompt).catch((error) => {
			console.log(error);
			return prompt;
		});

		if (!searchQuery) {
			toast.warning($i18n.t('No search query generated'));
			responseMessage.statusHistory.push({
				done: true,
				error: true,
				action: 'web_search',
				description: 'No search query generated'
			});

			messages = messages;
		}

		responseMessage.statusHistory.push({
			done: false,
			action: 'web_search',
			description: $i18n.t(`Searching "{{searchQuery}}"`, { searchQuery })
		});
		messages = messages;

		const results = await runWebSearch(localStorage.token, searchQuery).catch((error) => {
			console.log(error);
			toast.error(error);

			return null;
		});

		if (results) {
			responseMessage.statusHistory.push({
				done: true,
				action: 'web_search',
				description: $i18n.t('Searched {{count}} sites', { count: results.filenames.length }),
				query: searchQuery,
				urls: results.filenames
			});

			if (responseMessage?.files ?? undefined === undefined) {
				responseMessage.files = [];
			}

			responseMessage.files?.push({
				collection_name: results.collection_name,
				name: searchQuery,
				type: 'web_search_results',
				urls: results.filenames
			});

			messages = messages;
		} else {
			responseMessage.statusHistory.push({
				done: true,
				error: true,
				action: 'web_search',
				description: 'No search results found'
			});
			messages = messages;
		}
	};

	const getTags = async () => {
		try {
			const tags = await getTagsById(localStorage.token, $chatId);
			return tags ? tags : [];
		} catch (error: unknown) {
			return [];
		}
	};

	const processChatAction = async (content: string, type?: string) => {
		let _responses: string[] = [];
		console.log('openConfig -> chatId', $chatId);
		selectedModels = selectedModels.map((modelId) => ($models.map((m) => m.id).includes(modelId) ? modelId : ''));

		if (selectedModels.includes('')) {
			toast.error($i18n.t('Model not selected'));
		} else if (messages.length != 0 && messages.at(-1)?.done != true) {
			// Response not done
			console.log('wait');
		} else if (messages.length != 0 && messages.at(-1)?.error) {
			// Error in response
			toast.error($i18n.t(`Oops! There was an error in the previous response. Please try again or contact admin.`));
		} else if (
			files.length > 0 &&
			files.filter((file) => file.type !== 'image' && file.status !== 'processed').length > 0
		) {
			// Upload not done
			toast.error(
				$i18n.t(
					`Oops! Hold tight! Your files are still in the processing oven. We're cooking them up to perfection. Please be patient and we'll let you know once they're ready.`
				)
			);
		} else {
			// Reset chat input textarea
			const chatTextAreaElement = document.getElementById('chat-textarea') as unknown as HTMLTextAreaElement;

			if (chatTextAreaElement) {
				chatTextAreaElement.value = '';
				chatTextAreaElement.style.height = '';
				chatTextAreaElement.disabled = type === 'device-selector';
			}

			const _files: ClientFile[] = JSON.parse(JSON.stringify(files));
			console.log('[processChatAction:Chat.svelte] -> _files: ', _files);
			chatFiles.push(..._files.filter((item) => ['doc', 'file', 'collection'].includes(item.type as string)));
			chatFiles = chatFiles.filter(
				// Remove duplicates
				(item, index, array) => array.findIndex((i) => JSON.stringify(i) === JSON.stringify(item)) === index
			);

			// Reset files
			files = [];
			// Reset prompt
			prompt = '';

			// Create user message
			let assistantId = uuidv4();
			let assistantMessage = {
				id: assistantId,
				parentId: messages.length !== 0 ? messages.at(-1)!.id : null,
				childrenIds: [],
				role: 'assistant',
				type: type,
				content: content,
				files: _files.length > 0 ? _files : undefined,
				timestamp: Math.floor(Date.now() / 1000), // Unix epoch in seconds
				models: selectedModels.filter((m, mIdx) => selectedModels.indexOf(m) === mIdx),
				model: $models.filter((m) => m.id === selectedModels.at(0)).at(0)?.id,
				done: true
			};

			// Add message to history and Set currentId to messageId
			history.messages[assistantId] = assistantMessage;
			history.currentId = assistantId;

			// Append messageId to childrenIds of parent message
			if (messages.length !== 0 && messages.at(-1)) {
				(history.messages[messages.at(-1)!.id].childrenIds ?? []).push(assistantId);
			}

			// Wait until history/message have been updated
			await tick();
			messages = messages;
		}
		await scrollToBottom();
		return _responses;
	};

	const openConfigAssistant = async () => {
		if (
			messages.length > 0 &&
			messages.filter((message) => message.type && ['device-selector'].includes(message.type)).length > 0
		) {
			toast.info($i18n.t('Config Assist mode is already enabled'));
		} else {
			return await processChatAction(JSON.stringify({ value: seriesName }), 'device-selector');
		}
	};

	let seriesId = '';
	let seriesName = '';

	const handleDeviceConfirm = async (event: CustomEvent<{ device: string; name: string }>) => {
		const { device, name } = event.detail;
		console.log('Device selected:', device, name);
		seriesId = device;
		seriesName = name;
		variablesStore.update((vars) => ({ ...vars, device: name }));
		// Update the device-selector message content for chat reload
		const deviceMessage = messages.filter((m) => m.type && ['device-selector'].includes(m.type)).at(-1);
		if (deviceMessage) {
			history.messages[deviceMessage.id].content = JSON.stringify({ value: seriesName });
			messages = messages;
			toast.success($i18n.t('Device updated successfully'));
		}
		const publishArticleMessage = messages.filter((m) => m.type && ['published-articles'].includes(m.type)).at(-1);
		if (publishArticleMessage) {
			history.messages[publishArticleMessage.id].content = JSON.stringify({ seriesId });
			messages = messages;
		} else {
			return await processChatAction(JSON.stringify({ seriesId }), 'published-articles');
		}
	};

	let isGeneratingNewArticle: boolean = false;
	let _stopGeneratingArticle: boolean = false;

	const generateNewArticle = async () => {
		// Move to the next slide
		const message = 'Given the device you selected, describe what you would like the article to be about.';
		isGeneratingNewArticle = true;
		return await processChatAction(message);
	};

	$: reducedModels = selectedModelIds.reduce<Model[]>((a, e) => {
		const model = $models.find((m) => m.id === e);
		if (model) {
			return [...a, model];
		}
		return a;
	}, []);
</script>

<svelte:head>
	<title>
		{title ? `${title.length > 30 ? `${title.slice(0, 30)}...` : title} | ${$WEBUI_NAME}` : `${$WEBUI_NAME}`}
	</title>
</svelte:head>

<audio id="audioElement" src="" style="display: none;" />

<EventConfirmDialog
	bind:show={showEventConfirmation}
	title={eventConfirmationTitle}
	message={eventConfirmationMessage}
	input={eventConfirmationInput}
	inputPlaceholder={eventConfirmationInputPlaceholder}
	on:confirm={(e) => {
		if (e.detail && eventCallback) {
			eventCallback(e.detail);
		} else {
			if (eventCallback) eventCallback(true);
		}
	}}
	on:cancel={() => {
		if (eventCallback) eventCallback(false);
	}}
/>

{#if $showCallOverlay}
	<CallOverlay
		{submitPrompt}
		{stopResponse}
		bind:files
		modelId={selectedModelIds?.at(0) ?? null}
		chatId={$chatId}
		{eventTarget}
	/>
{/if}

{#if !chatIdProp || (loaded && chatIdProp)}
	<div
		class="h-screen max-h-[100dvh] {$showSidebar ? 'md:max-w-[calc(100%-260px)]' : ''} w-full max-w-full flex flex-col"
	>
		{#if $settings?.backgroundImageUrl ?? null}
			<div
				class="absolute {$showSidebar
					? 'md:max-w-[calc(100%-260px)] md:translate-x-[260px]'
					: ''} top-0 left-0 w-full h-full bg-cover bg-center bg-no-repeat"
				style="background-image: url({$settings.backgroundImageUrl})  "
			/>

			<div
				class="absolute top-0 left-0 w-full h-full bg-gradient-to-t from-white to-white/85 dark:from-gray-900 dark:to-[#171717]/90 z-0"
			/>
		{/if}

		<Navbar
			{title}
			bind:selectedModels
			bind:showModelSelector
			bind:showControls
			shareEnabled={messages.length > 0}
			{chat}
			{initNewChat}
		/>

		{#if $banners.length > 0 && messages.length === 0 && !$chatId && selectedModels.length <= 1}
			<div
				class="absolute top-[4.25rem] w-full {$showSidebar ? 'md:max-w-[calc(100%-260px)]' : ''} {showControls
					? 'lg:pr-[24rem]'
					: ''} z-20"
			>
				<div class=" flex flex-col gap-1 w-full">
					{#each $banners.filter( (b) => (b.dismissible ? !JSON.parse(localStorage.getItem('dismissedBannerIds') ?? '[]').includes(b.id) : true) ) as banner}
						<Banner
							{banner}
							on:dismiss={(e) => {
								const bannerId = e.detail;

								localStorage.setItem(
									'dismissedBannerIds',
									JSON.stringify(
										[bannerId, ...JSON.parse(localStorage.getItem('dismissedBannerIds') ?? '[]')].filter((id) =>
											$banners.find((b) => b.id === id)
										)
									)
								);
							}}
						/>
					{/each}
				</div>
			</div>
		{/if}

		<div class="flex flex-col flex-auto z-10">
			<div
				class=" pb-2.5 flex flex-col justify-between w-full flex-auto overflow-auto h-0 max-w-full z-10 scrollbar-hidden {showControls
					? 'lg:pr-[24rem]'
					: ''}"
				id="messages-container"
				bind:this={messagesContainerElement}
				on:scroll={(e) => {
					autoScroll =
						messagesContainerElement.scrollHeight - messagesContainerElement.scrollTop <=
						messagesContainerElement.clientHeight + 5;
				}}
			>
				<div class=" h-full w-full flex flex-col {chatIdProp ? 'py-4' : 'pt-2 pb-4'}">
					<Messages
						chatId={$chatId}
						{selectedModels}
						{processing}
						bind:history
						bind:messages
						bind:autoScroll
						bind:prompt
						bottomPadding={files.length > 0}
						{sendPrompt}
						{continueGeneration}
						{regenerateResponse}
						{chatActionHandler}
						{handleDeviceConfirm}
						{seriesId}
						{seriesName}
						{generateNewArticle}
					/>
				</div>
			</div>
			<!-- <ClarificationCard
				question={clarificationQuestion}
				options={clarificationOptions}
				notOptions={clarificationOptions}
				onSelect={handleSelect}
				onSubmit={handleClarificationSubmit}
				{messages}
				visible={clarificationVisible}
				{originalUserPrompt}
			/> -->
			<div class={showControls ? 'lg:pr-[24rem]' : ''}>
				<MessageInput
					bind:files
					bind:prompt
					bind:autoScroll
					bind:selectedToolIds
					bind:webSearchEnabled
					bind:atSelectedModel
					availableToolIds={_availableToolIds}
					transparentBackground={$settings?.backgroundImageUrl ?? false}
					{selectedModels}
					{messages}
					bind:this={messageInputComponent}
					{generatePrompt}
					{submitPrompt}
					{stopResponse}
					{openConfigAssistant}
				/>
			</div>
		</div>
		{#if showPromptTemplateGenerator}
			<PromptTemplateGenerator
				bind:showPromptTemplate
				bind:showPromptIntro
				bind:isGeneratingPrompt
				bind:generatedPrompt={$promptStore}
				explanation={$explanationStore}
				{isTextareaTruthy}
				bind:showPromptTemplateGenerator
				{fetchAndProcessData}
				{generatePrompt}
				{extractVariablesFromPrompt}
				{originalUserPrompt}
				{updateTemplate}
				on:close={handleClosePromptTemplate}
				on:submit={handleSubmit}
				on:variableUpdate={handleVariableUpdate}
			/>
		{/if}

		<ChatControls models={reducedModels} bind:show={showControls} bind:chatFiles bind:params bind:valves />
	</div>
{/if}
