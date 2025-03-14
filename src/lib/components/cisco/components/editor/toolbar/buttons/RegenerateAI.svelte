<script lang="ts">
	import type { AdvancedModelParams, ClientFile, i18nType } from '$lib/types';

	import { getContext, onMount, tick } from 'svelte';
	import { toast } from 'svelte-sonner';

	import { transcribeAudio } from '$lib/apis/audio';
	import { uploadFile } from '$lib/apis/files';
	import { generateChatCompletion } from '$lib/apis/ollama';
	import { generateOpenAIChatCompletion } from '$lib/apis/openai';
	import { processDocToVectorDB } from '$lib/apis/rag';
	import { createOpenAITextStream } from '$lib/apis/streaming';
	import { getAndUpdateUserLocation } from '$lib/apis/users';
	import { SUPPORTED_FILE_EXTENSIONS, SUPPORTED_FILE_TYPE, WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
	import { type Model, mobile, models, settings, showSidebar, socket, user } from '$lib/stores';
	import { blobToFile, findWordIndices, isErrorWithDetail, promptTemplate, splitStream } from '$lib/utils';
	import type { LexicalEditor } from 'lexical';
	import { $getRoot as getRoot, $getSelection as getSelection } from 'lexical';
	import { v4 as uuidv4 } from 'uuid';

	import InputMenu from '$lib/components/chat/MessageInput/InputMenu.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';

	import { Brain, File as FileIcon } from 'lucide-svelte';

	export let editor: LexicalEditor;
	export let params: AdvancedModelParams;
	export let chatInputPlaceholder: string = 'Send your directions...';
	export let autoScroll: boolean = true;

	const i18n = getContext<i18nType>('i18n');

	let webSearchEnabled: boolean = false;
	let selectedToolIds: string[] = [];
	let _tools: { [id: string]: any } = {};
	const onClose = (e: CustomEvent) => {
		console.log(e);
	};

	let files: ClientFile[] = [];

	type Source = {
		type: string;
		collection_name: string;
		name: string;
		title: string;
		filename: string;
		content: Record<string, any>;
		user_id: string;
		timestamp: number;
		status: string;
	};

	type Document = string[];
	type Metadata = {
		file_id: string;
		name: string;
		page: number;
		source: string;
		start_index: number;
	};
	type Citation = {
		source: Source;
		document: Document;
		metadata: Metadata[];
	};
	type _FileType = {
		type: string;
		url: string;
	};

	type Message = {
		id: string;
		parentId: string | null;
		childrenIds: string[];
		role: string; // 'user' | 'assistant'
		content: string;
		done?: boolean;
		error?: {
			code?: number;
			content: string;
		};
		files?: any[];
		images?: any;
		citations?: Citation[];
		info?: Record<string, any>;
		models?: string[];
		context?: Record<string, any> | null;
		timestamp: number;
	};
	type MessageHistory = {
		messages: { [x: string]: Message };
		currentId: string | null;
		state: Record<string, any>;
	};

	let show: boolean = false;
	let prompt: string = '';
	let messages: Message[] = [];

	let history: MessageHistory = {
		messages: {},
		currentId: null,
		state: {}
	};

	let chatFiles: _FileType[] = [];

	let selectedModels = [''];
	let atSelectedModel: Model | undefined;
	$: selectedModelIds = atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;
	let visionCapableModels = [];
	$: visionCapableModels = [...(atSelectedModel ? [atSelectedModel] : selectedModels)].filter(
		(model) => $models.find((m) => m.id === model)?.info?.meta?.capabilities?.vision ?? true
	);
	$: console.log('selectedModels', selectedModels);

	// $: if (selectedModels.length === 1 && selectedModels.at(0) === '') {
	// 	selectedModels[0] = $models.at(0)?.id ?? '';
	// } else {

	// }

	let chatTextAreaElement: HTMLTextAreaElement;
	let messagesContainerElement: HTMLDivElement;

	let stopResponseFlag: boolean = false;

	onMount(() => {
		window.setTimeout(() => chatTextAreaElement?.focus(), 0);

		if (!selectedModels || selectedModels.length === 0 || selectedModels.at(0) === '') {
			selectedModels = ['gpt-4o'];
		}
		prompt = `You will be given text from a Cisco Product Documentation Article that guides a user through a configuration. This article has not yet been published and is currently being reviewed by a Cisco Technical Writer / Expert. The text being sent to you is currently incorrect for one reason or another, or may contain mistakes, among other things. Review the text, then review the editors directions as well as the documents they have provided you. Correct the text and return only the corrected text as your response.
		
		<text>
			{{TEXT}}
		</text>

		
		<documents>
			{{DOCUMENT}}
		</documents>

		`;
	});

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

	const submitPrompt = async (userPrompt: string, { _raw = false } = {}) => {
		let _responses: string[] = [];
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

			const _files: _FileType[] = JSON.parse(JSON.stringify(files));
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

			_responses = await sendPrompt(userPrompt, userMessageId);
		}

		return _responses;
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

					let _response: string | null | undefined = null;
					if (model.owned_by === 'openai') {
						console.log('Sending via OpenAI Model');
						_response = await sendPromptOpenAI(model, prompt, responseMessageId);
					} else if (model.owned_by === 'ollama') {
						console.log('Sending via Ollama Model');
						_response = await sendPromptOllama(model, prompt, responseMessageId);
					} else {
						toast.error($i18n.t(`Only OpenAI and Ollama models are supported at this time...`));
					}
					_responses.push(_response as string);
				} else {
					toast.error($i18n.t(`Model {{modelId}} not found`, { modelId }));
				}
			})
		);
		return _responses;
	};

	const sendPromptOllama = async (model: Model, userPrompt: string, responseMessageId: string) => {
		let _response = null;

		const responseMessage = history.messages[responseMessageId];

		// Wait until history/message have been updated
		await tick();

		// Scroll down
		scrollToBottom();

		const messagesBody: Array<Partial<Message>> = [
			params?.system || $settings.system
				? ({
						role: 'system',
						content: `${promptTemplate(
							params?.system ?? $settings?.system ?? '',
							$user?.name,
							$settings?.userLocation ? await getAndUpdateUserLocation(localStorage.token) : undefined
						)}`
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
			files.push(...(model.info!.meta.knowledge ?? []));
		}
		if (responseMessage?.files) {
			files.push(...responseMessage?.files.filter((item) => ['web_search_results'].includes(item.type as string)));
		}

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
			tool_ids: undefined,
			files: files.length > 0 ? files : undefined,
			session_id: $socket?.id,
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
				if (done || stopResponseFlag) {
					responseMessage.done = true;
					messages = messages;

					if (stopResponseFlag) {
						controller.abort('User: Stop Response');
					} else {
						const messages = createMessagesList(responseMessageId);
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
							}
						}
					}
				} catch (error) {
					console.log(error);
					if ('detail' in (error as unknown as any)) {
						if (typeof error === 'object' && error !== null && 'detail' in error) {
							toast.error((error as { detail: string }).detail);
						}
					}
					break;
				}

				if (autoScroll) {
					scrollToBottom();
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

		if (autoScroll) {
			scrollToBottom();
		}

		return _response;
	};

	const sendPromptOpenAI = async (model: Model, userPrompt: string, responseMessageId: string) => {
		let _response = null;
		const responseMessage = history.messages[responseMessageId];

		let files = JSON.parse(JSON.stringify(chatFiles));
		if (model?.info?.meta?.knowledge ?? false) {
			files.push(...model.info!.meta!.knowledge!);
		}
		if (responseMessage?.files) {
			files.push(...responseMessage?.files.filter((item) => item.type && ['web_search_results'].includes(item.type)));
		}

		scrollToBottom();

		await tick();
		const messagesBody = [
			params?.system || $settings.system
				? {
						role: 'system',
						content: `${promptTemplate(
							params?.system ?? $settings?.system ?? '',
							$user?.name,
							$settings?.userLocation ? await getAndUpdateUserLocation(localStorage.token) : undefined
						)}`
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
									text: arr.length - 1 !== idx ? message!.content : ''
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
			const body = {
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
				tool_ids: undefined,
				files: files.length > 0 ? files : undefined,
				session_id: $socket?.id,
				id: responseMessageId
			};
			console.log('body', body);
			const [res, controller] = await generateOpenAIChatCompletion(localStorage.token, body, `${WEBUI_BASE_URL}/api`);

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
					if (done || stopResponseFlag) {
						responseMessage.done = true;
						messages = messages;

						if (stopResponseFlag) {
							controller.abort('User: Stop Response');
						} else {
							const messages = createMessagesList(responseMessageId);
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
					}

					if (autoScroll) {
						scrollToBottom();
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

		if (autoScroll) {
			scrollToBottom();
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

	const joinDocuments = (documents: string[]) => {
		return documents.join('\n');
	};

	const onRegenerateTextClick = async () => {
		show = true;
		let text = '';
		editor.read(() => {
			const root = getRoot();
			const rootText = root.getTextContent();
			console.log('Regenerating text:', rootText);
			const selection = getSelection();
			console.log('Selection:', selection?.getTextContent());
			if (selection) {
				text = selection.getTextContent();
			} else {
				text = rootText; // Note: rootText should be defined above in your scope
			}
		});
		prompt = prompt.replace('{{TEXT}}', text).replace('{{DOCUMENT}}', '');
		if (selectedModels.length === 0 || selectedModels.at(0) === '') {
			selectedModels = ['gpt-4o'];
		}
		let _response = await submitPrompt(prompt);

		// Handle the response if necessary
		if (_response) {
			console.log('Response received:', _response);
		} else {
			console.error('No response received.');
		}
	};

	const onTextAreaKeydown = async (
		e: KeyboardEvent & {
			currentTarget: EventTarget & HTMLTextAreaElement;
		}
	) => {
		const isCtrlPressed = e.ctrlKey || e.metaKey; // metaKey is for Cmd key on Mac

		// Check if Ctrl + R is pressed
		if (prompt === '' && isCtrlPressed && e.key.toLowerCase() === 'r') {
			e.preventDefault();
			console.log('regenerate');

			const regenerateButton = [...document.getElementsByClassName('regenerate-response-button')]?.at(
				-1
			) as HTMLButtonElement;

			regenerateButton?.click();
		}

		if (prompt === '' && e.key == 'ArrowUp') {
			e.preventDefault();

			const userMessageElement = [...document.getElementsByClassName('user-message')]?.at(-1);

			const editButton = [...document.getElementsByClassName('edit-user-message-button')]?.at(-1) as HTMLButtonElement;

			console.log(userMessageElement);

			userMessageElement?.scrollIntoView({ block: 'center' });
			editButton?.click();
		}

		// if (['/', '#', '@'].includes(prompt.charAt(0)) && e.key === 'ArrowUp') {
		// 	e.preventDefault();

		// 	(promptsElement || documentsElement || modelsElement).selectUp();

		// 	const commandOptionButton = [...document.getElementsByClassName('selected-command-option-button')]?.at(-1);
		// 	commandOptionButton?.scrollIntoView({ block: 'center' });
		// }

		// if (['/', '#', '@'].includes(prompt.charAt(0)) && e.key === 'ArrowDown') {
		// 	e.preventDefault();

		// 	(promptsElement || documentsElement || modelsElement).selectDown();

		// 	const commandOptionButton = [...document.getElementsByClassName('selected-command-option-button')]?.at(-1);
		// 	commandOptionButton?.scrollIntoView({ block: 'center' });
		// }

		if (['/', '#', '@'].includes(prompt.charAt(0)) && e.key === 'Enter') {
			e.preventDefault();

			const commandOptionButton = [...document.getElementsByClassName('selected-command-option-button')]?.at(
				-1
			) as HTMLButtonElement;

			if (e.shiftKey) {
				prompt = `${prompt}\n`;
			} else if (commandOptionButton) {
				commandOptionButton?.click();
			} else {
				document.getElementById('send-message-button')?.click();
			}
		}

		if (['/', '#', '@'].includes(prompt.charAt(0)) && e.key === 'Tab') {
			e.preventDefault();

			const commandOptionButton = [...document.getElementsByClassName('selected-command-option-button')]?.at(
				-1
			) as HTMLButtonElement;

			commandOptionButton?.click();
		} else if (e.key === 'Tab') {
			const words = findWordIndices(prompt);

			if (words.length > 0) {
				const word = words.at(0) ?? words[0];
				// const word = words.at(0);
				const fullPrompt = prompt;

				prompt = prompt.substring(0, word?.endIndex + 1);
				await tick();

				e.currentTarget.scrollTop = e.currentTarget.scrollHeight;
				prompt = fullPrompt;
				await tick();

				e.preventDefault();
				e.currentTarget.setSelectionRange(word?.startIndex, word.endIndex + 1);
			}

			e.currentTarget.style.height = '';
			e.currentTarget.style.height = Math.min(e.currentTarget.scrollHeight, 200) + 'px';
		}

		if (e.key === 'Escape') {
			console.log('Escape');
			atSelectedModel = undefined;
		}
	};

	const uploadFileHandler = async (file: File) => {
		console.log(file);
		// Check if the file is an audio file and transcribe/convert it to text file
		if (['audio/mpeg', 'audio/wav'].includes(file['type'])) {
			const res = await transcribeAudio(localStorage.token, file).catch((error) => {
				toast.error(error);
				return null;
			});

			if (res) {
				console.log(res);
				const blob = new Blob([res.text], { type: 'text/plain' });
				file = blobToFile(blob, `${file.name}.txt`);
			}
		}

		// Upload the file to the server
		const uploadedFile = await uploadFile(localStorage.token, file).catch((error) => {
			toast.error(error);
			return null;
		});

		if (uploadedFile) {
			const fileItem: ClientFile = {
				type: 'file',
				file: uploadedFile,
				id: uploadedFile.id,
				url: `${WEBUI_API_BASE_URL}/files/${uploadedFile.id}`,
				name: file.name,
				collection_name: '',
				status: 'uploaded',
				error: ''
			};
			files = [...files, fileItem];

			// TODO: Check if tools & functions have files support to skip this step to delegate file processing
			// Default Upload to VectorDB
			if (
				SUPPORTED_FILE_TYPE.includes(file.type) ||
				SUPPORTED_FILE_EXTENSIONS.includes(file.name.split('.').at(-1) ?? '')
			) {
				console.log(`[MessageInput.svelte] Supported file type: ${file.type}`);
				await processFileItem(fileItem);
			} else {
				toast.error(
					$i18n.t(`Unknown file type '{{file_type}}'. Proceeding with the file upload anyway.`, {
						file_type: file.type
					})
				);
				await processFileItem(fileItem);
			}
		}
	};

	const processFileItem = async (fileItem: ClientFile) => {
		console.log(`[MessageInput.svelte] processFileItem (fileItem) => fileItem is: `, fileItem);
		try {
			const res = await processDocToVectorDB(localStorage.token, fileItem.id as string);

			if (res) {
				fileItem.status = 'processed';
				fileItem.collection_name = res.collection_name;
				files = [...files];
			}
		} catch (e) {
			// Remove the failed doc from the files array
			files = files.filter((f) => f.id !== fileItem.id);
			toast.error(e as string);
			fileItem.status = 'processed';
			files = [...files];
		}
	};

	let filesInputElement: HTMLInputElement;
	let inputFiles: FileList;
</script>

<Tooltip className="flex shrink-0" content={$i18n.t('Use AI to regenerate the text')}>
	<button
		on:click={() => onRegenerateTextClick()}
		class="flex items-center mr-1 justify-between bg-gray-50 rounded-md p-2.5 text-gray-500 dark:text-gray-50 dark:bg-gray-850 hover:bg-neutral-100 dark:hover:bg-neutral-800 border-none cursor-pointer align-middle shrink-0"
	>
		<span><Brain class="w-4 h-4 text-gray-500 mr-2" /></span>
		<span>Use AI</span>
	</button>
</Tooltip>

<Modal bind:show size="lg">
	<div class="p-4">
		<div class="app relative">
			<div
				class=" text-gray-700 dark:text-gray-100 bg-white dark:bg-gray-900 h-screen max-h-[100dvh] overflow-auto flex flex-row"
			>
				<div class="h-screen max-h-[100dvh] w-full max-w-full flex flex-col z-10">
					<div class="flex flex-col items-center justify-center w-full p-2">
						<h2 class="text-xl font-semibold">Regenerative AI</h2>
						<p class="mt-2">Upload files, and provide a prompt to generate a new answer</p>
					</div>
					<hr class="dark:border-gray-850 my-2" />
					<div
						class="pb-2.5 flex flex-col justify-between w-full flex-auto overflow-auto h-0 max-w-full z-10 scrollbar-hidden"
						id="messages-container"
						bind:this={messagesContainerElement}
						on:scroll={(e) => {
							autoScroll =
								messagesContainerElement.scrollHeight - messagesContainerElement.scrollTop <=
								messagesContainerElement.clientHeight + 5;
						}}
					>
						<div class="h-full w-full flex flex-col pt-2 pb-4">
							<div>Messages Placeholder</div>
						</div>
					</div>
					<hr class="dark:border-gray-850 my-2" />

					<div class="flex items-center inset-x-0 w-full">
						<textarea
							id="chat-textarea"
							bind:this={chatTextAreaElement}
							class="scrollbar-hidden bg-gray-50 dark:bg-gray-850 dark:text-gray-100 outline-none w-full py-3 px-1 rounded-xl resize-none h-[96px]"
							placeholder={chatInputPlaceholder !== '' ? chatInputPlaceholder : $i18n.t('Send your directions...')}
							bind:value={prompt}
							on:keypress={(e) => {
								if (
									!$mobile ||
									!('ontouchstart' in window || navigator.maxTouchPoints > 0 || navigator.msMaxTouchPoints > 0)
								) {
									// Prevent Enter key from creating a new line
									if (e.key === 'Enter' && !e.shiftKey) {
										e.preventDefault();
									}

									// Submit the prompt when Enter key is pressed
									if (prompt !== '' && e.key === 'Enter' && !e.shiftKey) {
										submitPrompt(prompt);
									}
								}
							}}
							on:keydown={onTextAreaKeydown}
							rows="1"
							on:input={(e) => {
								e.currentTarget.style.height = '';
								e.currentTarget.style.height = Math.min(e.currentTarget.scrollHeight, 200) + 'px';
							}}
							on:focus={(e) => {
								e.currentTarget.style.height = '';
								e.currentTarget.style.height = Math.min(e.currentTarget.scrollHeight, 200) + 'px';
							}}
							on:paste={(e) => {
								const clipboardData = e.clipboardData || window.clipboardData;

								if (clipboardData && clipboardData.items) {
									for (const item of clipboardData.items) {
										if (item.type.indexOf('image') !== -1) {
											const blob = item.getAsFile();
											const reader = new FileReader();

											reader.onload = function (e) {
												files = [
													...files,
													{
														type: 'image',
														url: `${e.target?.result}`
													}
												];
											};

											reader.readAsDataURL(blob);
										}
									}
								}
							}}
						/>
					</div>
					<div class="flex w-full pb-1">
						<div class="ml-0.5 self-end flex h-full items-center justify-center space-x-1">
							<input
								class="hidden"
								bind:this={filesInputElement}
								bind:files={inputFiles}
								type="file"
								multiple
								on:change={async () => {
									console.log('clicked');
									if (inputFiles && inputFiles.length > 0) {
										const _inputFiles = Array.from(inputFiles);
										_inputFiles.forEach((file) => {
											if (['image/gif', 'image/webp', 'image/jpeg', 'image/png'].includes(file.type)) {
												if (visionCapableModels.length === 0) {
													toast.error(
														$i18n.t('Selected model(s) {{models}} do not support image inputs', {
															models: selectedModels.join(', ')
														})
													);
													return;
												}
												let reader = new FileReader();
												reader.onload = (event) => {
													files = [
														...files,
														{
															type: 'image',
															url: `${event.target?.result}`
														}
													];
												};
												reader.readAsDataURL(file);
											} else {
												uploadFileHandler(file);
											}
										});
									} else {
										toast.error($i18n.t(`File not found.`));
									}

									filesInputElement.value = '';
								}}
							/>
							<InputMenu
								bind:webSearchEnabled
								bind:selectedToolIds
								tools={_tools}
								uploadFilesHandler={() => {
									filesInputElement.click();
								}}
								onClose={async () => {
									await tick();
									chatTextAreaElement?.focus();
								}}
								side="bottom"
								align="start"
							>
								<button
									class="bg-gray-50 hover:bg-gray-100 text-gray-800 dark:bg-gray-850 dark:text-white dark:hover:bg-gray-800 transition rounded-full p-2 outline-none focus:outline-none"
									type="button"
								>
									<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" class="size-5">
										<path
											d="M8.75 3.75a.75.75 0 0 0-1.5 0v3.5h-3.5a.75.75 0 0 0 0 1.5h3.5v3.5a.75.75 0 0 0 1.5 0v-3.5h3.5a.75.75 0 0 0 0-1.5h-3.5v-3.5Z"
										/>
									</svg>
								</button>
							</InputMenu>
						</div>
					</div>
					<div class="flex justify-end mt-4">
						<button
							class="regenerate-response-button py-2.5 px-4 bg-[#007bff] text-white font-bold rounded-md cursor-pointer hover:bg-[#0056b3]"
							on:click={async () => {
								await onRegenerateTextClick();
								show = false;
							}}
						>
							Regenerate
						</button>
					</div>
				</div>
			</div>
		</div>
	</div></Modal
>
