<script lang="ts">
	import type { _CiscoArticleMessage, Model } from '$lib/stores';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import type { Instance } from 'tippy.js';

	import tippy from 'tippy.js';
	import { createEventDispatcher, onMount, getContext, tick } from 'svelte';
	import { v4 as uuidv4 } from 'uuid';
	import { toast } from 'svelte-sonner';
	import { slide, fly, fade, crossfade } from 'svelte/transition';
	import { quintInOut, cubicInOut } from 'svelte/easing';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import {
		mostRecentStep,
		mountedArticleSteps,
		mountedArticlePreambleObjective,
		mountedArticlePreambleDevices,
		ciscoArticleMessages,
		isSupportWidgetOpen,
		activeSupportSection,
		activeSupportStep,
		activeArticleId,
		settings,
		models,
		config,
		activeArticle,
		globalMessages,
		socket
	} from '$lib/stores';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { splitStream, approximateToHumanReadable } from '$lib/utils';
	import { queryDoc, queryCollection } from '$lib/apis/rag';
	import { X } from 'lucide-svelte';
	import {
		generateOpenAIChatCompletionQuestions,
		generateOpenAIChatCompletionAnswers,
		generateOpenAIChatCompletion
	} from '$lib/apis/openai';
	import { createOpenAITextStream } from '$lib/apis/streaming';
	import { generateOllamaChatCompletion, generateChatCompletion } from '$lib/apis/ollama';
	import { getArticleById, updateArticleStep } from '$lib/apis/articles';
	import { stripHtml, isErrorWithDetail, isErrorWithMessage, isErrorAsString } from '$lib/utils';
	import { page } from '$app/stores';
	import { flip } from 'svelte/animate';

	type QuestionButton = { id: string; text: string; clicked: boolean };

	const i18n: Writable<i18nType> = getContext('i18n');
	const STATIC_IDS = ['static_1', 'static_2', 'static_3'];
	const DYNAMIC_IDS = ['dynamic_1', 'dynamic_2', 'dynamic_3'];

	$: {
		console.log(activeStepSection);
	}

	let staticQuestionBtns: QuestionButton[] = [];
	let dynamicQuestionBtns: QuestionButton[] = [];
	let selectedModels = [''];
	let atSelectedModel: Model | undefined;
	let activeStepMatch;
	let activeStepNum = 0;
	let isLoading = false;
	let questions: QuestionButton[] = [];
	let currentQuestion: string;

	let _stopResponseFlag = false;

	let tooltipInstance: Instance[] | null = null;
	$: activeStepSection = $activeSupportSection;
	$: activeStepNum = $mostRecentStep;

	$: selectedModelIds = atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;
	$: if ($page.url.searchParams.get('models')) {
		selectedModels = $page.url.searchParams.get('models')?.split(',') as string[];
	} else if ($settings?.models) {
		selectedModels = $settings?.models;
	} else if ($config?.default_models) {
		console.log($config?.default_models.split(',') ?? '');
		selectedModels = $config?.default_models.split(',');
	} else {
		selectedModels = [''];
	}
	$: model = $models.find((m) => m.id === selectedModels.at(0));

	$: history = {};

	async function loadQuestions(stepNumber: number) {
		const articleId = $activeArticleId;
	}

	const generateLocalStorageKey = (id: string, stepNumber: number) => `questions-${id}-step-${stepNumber}`;

	const getQuestionsFromStorage = (id: string, stepNumber: number) => {
		const key = generateLocalStorageKey(id, stepNumber);
		const questions = localStorage.getItem(key);
		if (questions) {
			console.log('Retrieving questions from local storage', JSON.parse(questions));
		}
		return questions ? JSON.parse(questions) : null;
	};

	const saveQuestionsToStorage = (id: string, stepNumber: number, questions: string[]) => {
		const key = generateLocalStorageKey(id, stepNumber);
		localStorage.setItem(key, JSON.stringify(questions));
	};

	const getRecentStepByIndex = (index: number) => {
		return $mountedArticleSteps.at(index);
	};

	// let messages = [
	// 	{
	// 		role: 'system',
	// 		content:
	// 			'You are a TAC engineer and an expert at explaining technology in easy to understand terms. You are helping the user to understand how the objective ties into the step of the configuration step they are currently on. Use the previous steps as a context to inform what steps to take nextb ut most importantly pay attention to the latest step in the configuration. Keep in mind users are not able to respond to your messages, so do not ask the user any questions at all. Do not ask them to let you know how it turned out. Messages should be self contained and not require a response from the user.'
	// 	},
	// 	{ role: 'user', content: "Hi, I'm having trouble with my switch." }
	// ];

	let messages: _CiscoArticleMessage[] = [];
	$: messages = $ciscoArticleMessages;

	let _globalMessages: Map<number, _CiscoArticleMessage[]> = new Map();
	$: _globalMessages = $globalMessages;

	onMount(() => {
		activeStepMatch = $activeSupportSection && $activeSupportSection.match(/Step (\d+)/g);
		if (activeStepMatch) {
			activeStepNum = Number(activeStepMatch[0].replace(/Step/g, '').trim());
		}
	});
	$: questionsGenerated =
		$mostRecentStep > -1 &&
		$activeArticle?.steps[$mostRecentStep].qna_pairs?.length === STATIC_IDS.length + DYNAMIC_IDS.length;

	const dispatch = createEventDispatcher();

	const generateContext = () => {
		if (activeStepNum > -1 && Array.isArray($mountedArticleSteps)) {
			return $mountedArticleSteps
				.slice(0, activeStepNum + 1)
				.map((s, i) => `Step ${i + 1}: ${stripHtml(s.text)}`)
				.join('\n');
		}
		return '';
	};

	const generateQuestionPrompt = () => {
		if (activeStepNum > -1 && Array.isArray($mountedArticleSteps)) {
			const stepsText = generateContext();

			return `${stepsText}\n Given all this context, what are three questions a user may have about the most recent step? Return only the questions.`;
		}
		return null;
	};

	const updateMessages = (newMessage: _CiscoArticleMessage) => {
		const unique = new Set(messages.map((m) => m.id));
		if (!unique.has(newMessage.id)) {
			return [...messages, newMessage];
		} else {
			return messages.map((m) => (m.id === newMessage.id ? newMessage : m));
		}
	};

	const setMessages = (index: number) => {
		if (index > -1) {
			messages = _globalMessages.has(index) ? _globalMessages.get(index)! : [...messages];
		}
	};

	$: if ($activeArticle) {
		// For Generated Articles, set the default static buttons
		// Articles saved in the database will have these set already but generated articles will not
		// Article.svelte will set the default QNA Pairs for generated articles + Insert the generated article into the database
		// This is just a backup in case the default QNA Pairs are not set
		staticQuestionBtns =
			activeStepNum > -1
				? $activeArticle.steps[activeStepNum].qna_pairs
						?.filter((pair) => STATIC_IDS.includes(pair.id))
						.map((pair) => ({ id: pair.id, text: pair.question, clicked: false })) ?? [
						{ id: 'static_1', text: "I don't understand this step", clicked: false },
						{ id: 'static_2', text: 'Help me troubleshoot', clicked: false },
						{ id: 'static_3', text: 'Show best practices', clicked: false }
				  ]
				: [
						{ id: 'static_1', text: "I don't understand this step", clicked: false },
						{ id: 'static_2', text: 'Help me troubleshoot', clicked: false },
						{ id: 'static_3', text: 'Show best practices', clicked: false }
				  ];

		dynamicQuestionBtns =
			activeStepNum > -1
				? $activeArticle.steps[activeStepNum].qna_pairs
						?.filter((pair) => DYNAMIC_IDS.includes(pair.id))
						.map((pair) => ({ id: pair.id, text: pair.question, clicked: false })) ?? []
				: [];

		questions = [...staticQuestionBtns, ...dynamicQuestionBtns];
		console.log('questions', questions);
		// Update messages
		// Messages are stored in globalMessages store
		// Messages must be reset every time a user scrolls the page to a new section
		// Due to this, we must find the most recent message for the current section / step number
		setMessages(activeStepNum);
	}

	const startGenerateDynamicQuestions = async (e: Event & { currentTarget: HTMLDetailsElement }) => {
		if (e.currentTarget.open) {
			questions = [...staticQuestionBtns];
			selectedModels = selectedModels.map((modelId) => ($models.map((m) => m.id).includes(modelId) ? modelId : ''));
			let selectedModel = selectedModels.at(0);
			if (selectedModels.includes('')) {
				toast.error($i18n.t('Model not selected'));
			} else if (
				$activeArticle &&
				$activeArticle.steps.at(activeStepNum)?.qna_pairs?.some((pair) => DYNAMIC_IDS.includes(pair.id))
			) {
				console.log("We've already generated the questions");
				questions = [...staticQuestionBtns, ...dynamicQuestionBtns];
			} else {
				console.log('Generating questions...');
				const prompt = generateQuestionPrompt();
				console.log('Prompt:', prompt);
				if (prompt) {
					const responses = await sendGeneratedDynamicQuestions(prompt, selectedModel);
					questions = [...questions, ...responses];
					console.log('questions', questions);
					const updatedArticle = await updateArticleStep(localStorage.token, $activeArticle?.id ?? $activeArticleId, {
						step_index: activeStepNum,
						step: {
							...$mountedArticleSteps[activeStepNum],
							qna_pairs: questions.map(({ id, text }) => {
								return { id, question: text, answer: null };
							})
						}
					});
					activeArticle.set(updatedArticle);
					console.log('updated article', updatedArticle);
				}
			}
		} else {
			dispatch('closeDialog', { open: false });
		}
	};

	const scrollToBottom = () => {
		const messagesWell = document.getElementById('messages-well');
		if (messagesWell) {
			messagesWell.scrollTop = messagesWell.scrollHeight;
		}
	};

	const sendGeneratedDynamicQuestions = async (
		prompt: string,
		modelId?: string | null
	): Promise<{ id: string; text: string; clicked: boolean }[]> => {
		// If modelId is provided, use it, else use selected model
		let selectedModelId = modelId ? modelId : atSelectedModel !== undefined ? atSelectedModel.id : selectedModels.at(0);
		const model = $models.filter((m) => m.id === selectedModelId).at(0);
		let _responses: any[] = [];
		if (model) {
			if (model.owned_by === 'openai') {
				console.log('Generating questions with OpenAI');
				_responses = await generateDynamicQuestionsOpenAI(prompt, model);
			} else if (model.owned_by === 'ollama') {
				console.log('Generating questions with Ollama');
				_responses = await generateDynamicQuestionsOllama(prompt, model);
			} else {
				console.log('Generating questions with Ollama');
				_responses = await generateDynamicQuestionsOllama(prompt, model);
			}
		} else {
			toast.error($i18n.t(`Model {{modelId}} not found`, { selectedModelId }));
			_responses = [];
		}
		return _responses;
	};

	const generateDynamicQuestionsOpenAI = async (prompt: string, model: Model) => {
		let _responses: any[] = [];

		try {
			const data = await generateOpenAIChatCompletionQuestions(localStorage.token, {
				stream: false,
				model: model.id,
				messages: [
					messages.at(0) ? { role: messages[0].role, content: messages[0].content } : undefined,
					{ role: 'user', content: prompt }
				].filter((m) => m?.content?.trim()),
				temperature: 0
			}).catch((e) => {
				throw e;
			});
			_responses = data
				.split(/[\n;]|1\.\s*|2\.\s*|3\.\s*/)
				.filter((x) => x)
				.map((x) => x.replace(/^-+\s*/, ''))
				.slice(0, 3)
				.map((text, i) => ({ id: `dynamic_${i + 1}`, text, clicked: false }));
			// _responses = data.map((text, i) => ({ id: `dynamic_${i + 1}`, text, clicked: false }));
		} catch (error) {
			console.error(error);
			if (isErrorWithDetail(error)) {
				toast.error(error.detail);
			} else if (isErrorWithMessage(error)) {
				toast.error(error.message);
			} else {
				toast.error('An error occurred');
			}
			_responses = [];
		} finally {
			isLoading = false;
		}
		return _responses;
	};

	const generateDynamicQuestionsOllama = async (prompt: string, model: Model) => {
		let _responses: any[] = [];
		let userPrompt = `${prompt} Return as a numbered list of questions and only the questions text. VERY IMPORTANT: Do not include any other text. Example: 1. How do I connect the console cable? 2. Do I need a special cable? 3. What is a console port?`;
		try {
			const data = await generateOllamaChatCompletion(localStorage.token, {
				stream: false,
				model: model.id,
				messages: [
					messages.at(0) ? { role: messages[0].role, content: messages[0].content } : undefined,
					{ role: 'user', content: userPrompt }
				].filter((m) => m?.content?.trim())
			}).catch((error) => {
				throw error;
			});
			console.log('Response from Ollama:', data);
			_responses = data.map((text, i) => ({ id: `dynamic_${i + 1}`, text, clicked: false }));
		} catch (error) {
			console.error(error);
			if (isErrorWithDetail(error)) {
				toast.error(error.detail);
			} else if (isErrorWithMessage(error)) {
				toast.error(error.message);
			} else {
				toast.error('An error occurred');
			}
			_responses = [];
		} finally {
			isLoading = false;
		}
		return _responses;
	};

	const generateLLMAnswer = async (i: number, btnId: string, question: string) => {
		isLoading = true;
		// send the latest message to the LLM
		selectedModels = selectedModels.map((modelId) => ($models.map((m) => m.id).includes(modelId) ? modelId : ''));
		let selectedModel = selectedModels.at(0);
		const model = $models.filter((m) => m.id === selectedModel).at(0);
		if (questions.at(i)) {
			questions = questions.map((q) => (q.id === questions[i].id ? { ...q, clicked: true } : q));
		}
		currentQuestion = question.slice(0);
		messages = updateMessages({
			id: uuidv4(),
			role: 'user',
			content: question,
			timestamp: Math.floor(Date.now() / 1000),
			model: model?.id ?? selectedModel ?? selectedModels.at(0)!,
			associatedQuestion: null
		});

		if ($activeArticle && $activeArticle.steps.at(activeStepNum)?.qna_pairs) {
			const pairs = $activeArticle.steps.at(activeStepNum)?.qna_pairs ?? [];
			const match = pairs.find((pair) => pair.id.trim().toLowerCase() === btnId.trim().toLowerCase());
			if (match && match.answer !== null) {
				await tick();

				messages = updateMessages({
					id: uuidv4(),
					role: 'assistant',
					content: match.answer,
					timestamp: Math.floor(Date.now() / 1000),
					model: model?.id ?? selectedModels.at(0)!,
					sources: match.sources,
					associatedQuestion: question,
					qnaBtnId: btnId,
					done: true
				});
				isLoading = false;
				return;
			}
		}

		try {
			const context = generateContext();
			let directions: string;
			let needsContextFlag: boolean = false;

			switch (i) {
				case 0:
					directions = `The devices the user is performing the configuration on: ${$mountedArticlePreambleDevices}\nBelow is the context of all steps leading to the current step. The most recent step is the most important to pay attention to.\n<objective>\n\t${$mountedArticlePreambleObjective}\n</objective>\n\n<article-steps>:\n\t${context}\n</article-steps>\nThe user doesn't understand the latest step, use the context of the previous article steps to explain in simple language how the latest step ties into the objective of the article. Keep your answer simple, easy to understand and limited to answering the question about the most recent step only. Do not direct the user in other steps.`;
					break;
				case 1:
					directions = `You are a one-shot troubleshooting helper. The article objective, devices, steps and context will be labelled within XML-Style tags. Use the context and/or prior article steps to answer the users questions. If you can't find the answer in the context below, just say "Hmm, I'm not sure." Don't try to make up an answer. Use the previous steps as context to inform what steps to take next but most importantly pay attention to the latest step in the configuration.\n\n<objective>\n\t${mountedArticlePreambleObjective}\n</objective>\n\n<devices>\n\t${mountedArticlePreambleDevices}\n</devices>\n\n<article-steps>:\n\t${context}\n</article-steps>\n\n<Question>\n\tI need help troubleshooting\n</Question>\n\n<context>\n\t[[context]]\n</context>\n\nBe sure to cite the articles content when responding. Keep your answer simple, easy to understand and limited to answering the question about the most recent step only. Do not direct the user in other steps.`;
					needsContextFlag = true;
					break;
				case 2:
					directions = `You are a Cisco TAC engineer and an expert at explaining technology in easy to understand terms. You are helping the user to understand how the objective ties into the step of the configuration step they are currently on. Help the user understand the factors to think about when applying best practices. Use the previous steps as a context to inform what steps to take next but most importantly pay attention to the latest step in the configuration.\nAlso of importance is the devices they are performing the configuration on: ${$mountedArticlePreambleDevices}\nBelow is the context of all steps leading to the current step. The last step is the most important to pay attention to.\nThe objective of this article is ${$mountedArticlePreambleObjective}\n<context>:\n\t${context}\n</context>\nPlease provide any best practices related to the current step and the overall article context. If there are no best practices applicable to this step, just tell the user that there are no best practices to consider for this step. Keep your answer simple, easy to understand and limited to answering the question about the most recent step only. Do not direct the user in other steps.`;
					break;
				default:
					directions = `You are a Cisco TAC engineer and an expert at explaining technology in easy to understand terms. Use the previous article steps to understand the context of the article. Use the step-context and the context XML Tags to answer the users question and inform what steps to take next but most importantly pay attention to the latest step in the configuration.\nAlso of importance is the devices they are performing the configuration on: ${$mountedArticlePreambleDevices}\nBelow is the context of all steps leading to the current step. The last step is the most important to pay attention to.\nThe objective of this article is ${$mountedArticlePreambleObjective}\n\n<step-context>\n\t${context}\n</step-context>\n\n<context>\n\t[[context]]\n</context>\n\n<question>\n\t${question}}\n</question>\n\nKeep your answer simple, easy to understand and limited to answering the question about the most recent step only. Do not direct the user in other steps.`;
					needsContextFlag = true;
					break;
			}
			let distances: number[] | null = null;
			let documents: string[] | null = null;
			let metadatas: Record<string, any>[] | null = null;

			if (needsContextFlag) {
				const res = await queryCollection(
					localStorage.token,
					['catalyst_1200_admin_guide', 'catalyst_1200_cli_guide'],
					question
				);
				// const test = await queryDocWithSmallChunks(localStorage.token, 'catalyst_1200_cli_guide', question);
				// console.log('test', test);
				distances = res.distances?.flat(1) ?? null;
				documents = res.documents?.flat(1) ?? null;
				metadatas = res.metadatas?.flat(1) ?? null;
				directions = directions.replace(/\[\[context\]\]/g, documents?.join('\n\n') ?? '');
			}

			if (model) {
				console.log('directions', directions);
				const assistantMessageId = uuidv4();
				let systemMessage = {
					id: `system_${assistantMessageId}`,
					role: 'system',
					content: directions,
					timestamp: Math.floor(Date.now() / 1000),
					model: model.id,
					associatedQuestion: null
				};
				messages = updateMessages(systemMessage);
				console.log('messages after system message', messages);
				// wait for messages to update
				await tick();
				// Keep responseMessage here as if user stops generation, then continues, we can use the same responseMessage
				let responseMessage: _CiscoArticleMessage = {
					id: assistantMessageId,
					role: 'assistant',
					content: '',
					timestamp: Math.floor(Date.now() / 1000),
					model: model.id,
					associatedQuestion: question,
					qnaBtnId: btnId,
					sources: metadatas?.map((m, i) => ({ ...m, content: documents?.at(i) }))
				};
				if (model.owned_by === 'openai') {
					responseMessage = await sendPromptOpenAI(systemMessage, { model, responseMessage });
				} else if (model.owned_by === 'ollama') {
					responseMessage = await sendPromptOllama(systemMessage, { model, responseMessage });
				} else {
					responseMessage = await sendPromptOllama(systemMessage, { model, responseMessage });
				}
				await tick();
				console.log('response message', responseMessage);
				messages = updateMessages(responseMessage);
				// await sendUpdateArticle(responseMessage, id);
				// const updatedArticle = await updateArticleStep(localStorage.token, $activeArticleId, {
				// 	step_index: activeStepNum,
				// 	step: $activeArticle
				// 		? {
				// 				...$activeArticle.steps[activeStepNum],
				// 				qna_pairs: $activeArticle.steps.at(activeStepNum)?.qna_pairs?.map((pair) => {
				// 					if (pair.id.trim().toLowerCase() === btnId.trim().toLowerCase()) {
				// 						return {
				// 							...pair,
				// 							answer: responseMessage.content === '' ? null : responseMessage.content,
				// 							sources: metadatas?.map((m, i) => ({ ...m, content: documents?.at(i) })),
				// 							model: model.id
				// 						};
				// 					}
				// 					return pair;
				// 				})
				// 		  }
				// 		: {
				// 				...$activeArticle.steps[activeStepNum],
				// 				qna_pairs: step.qna_pairs?.map((pair) => {
				// 					if (pair.id.trim().toLowerCase() === btnId.trim().toLowerCase()) {
				// 						return {
				// 							...pair,
				// 							answer: responseMessage.content === '' ? null : responseMessage.content,
				// 							sources: metadatas?.map((m, i) => ({ ...m, content: documents?.at(i) })),
				// 							model: model.id
				// 						};
				// 					}
				// 					return pair;
				// 				})
				// 		  }
				// });
				// activeArticle.set(updatedArticle);
				// console.log('updated article', updatedArticle);
			}
		} catch (err) {
			if (isErrorWithDetail(err)) {
				toast.error(err.detail);
			} else if (isErrorWithMessage(err)) {
				toast.error(err.message);
			} else if (isErrorAsString(err)) {
				toast.error(err);
			} else {
				toast.error('An error occurred finding the answer. Please try your request again.');
			}
		} finally {
			// catch all for any errors
			isLoading = false;
		}
	};

	type SendPromptOptions = {
		model: Model;
		responseMessage: _CiscoArticleMessage;
	};

	const sendPromptOpenAI = async (sysMsg: _CiscoArticleMessage, { model, responseMessage }: SendPromptOptions) => {
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
					messages: [sysMsg].map((m) => ({ role: m.role, content: m.content })),
					temperature: 0,
					session_id: $socket?.id
				},
				`${WEBUI_BASE_URL}/api`
			);
			await tick();
			scrollToBottom();

			if (res && res.ok && res.body) {
				const stream = await createOpenAITextStream(res.body, $settings.splitLargeChunks ?? true);
				for await (const update of stream) {
					const { value, done, error, usage } = update;
					if (error) {
						await handleOpenAIError(error, null, model, responseMessage);
						break;
					}

					if (usage) {
						responseMessage.info = { ...usage, openai: true };
					}

					if (done || _stopResponseFlag) {
						responseMessage.done = true;

						if (_stopResponseFlag) {
							controller.abort('User: Stop Response');
						}
						messages = updateMessages(responseMessage);
						await renderStyling();
						break;
					}

					if (responseMessage.content == '' && value == '\n') {
						continue;
					} else {
						// First chunk means we have a response, stop whowing Spinner and stream
						isLoading = false;
						responseMessage.content += value;
						messages = updateMessages(responseMessage);
					}
				}

				if ($settings.notificationEnabled && !document.hasFocus()) {
					const notification = new Notification(`${model.id}`, {
						body: responseMessage.content,
						icon: `${WEBUI_BASE_URL}/static/favicon.png`
					});
				}
				scrollToBottom();
			} else {
				await handleOpenAIError(null, res, model, responseMessage);
			}
		} catch (error) {
			await handleOpenAIError(error, null, model, responseMessage);
		}
		await tick();
		_stopResponseFlag = false;
		scrollToBottom();
		messages = updateMessages(responseMessage);
		return responseMessage;
	};

	const sendPromptOllama = async (message: _CiscoArticleMessage, { model, responseMessage }: SendPromptOptions) => {
		const [res, controller] = await generateChatCompletion(localStorage.token, {
			stream: true,
			model: model.id,
			messages: [message].map((m) => ({ role: m.role, content: m.content })),
			session_id: $socket?.id,
			id: message.id
		});
		if (res === null) {
			toast.error($i18n.t(`Uh-oh! There was an issue connecting to {{provider}}.`, { provider: 'Ollama' }));
			message.error = {
				content: $i18n.t(`Uh-oh! There was an issue connecting to {{provider}}.`, {
					provider: 'Ollama'
				})
			};
		}
		await tick();
		scrollToBottom();

		if (res && res.ok && res.body) {
			const reader = res.body.pipeThrough(new TextDecoderStream()).pipeThrough(splitStream('\n')).getReader();
			while (true) {
				const { value, done } = await reader.read();
				console.log(value);
				if (done || _stopResponseFlag) {
					responseMessage.done = true;

					if (_stopResponseFlag) {
						controller.abort('User: Stop Response');
					}

					messages = updateMessages(responseMessage);
					break;
				}

				try {
					let lines = value.split('\n');

					for (const line of lines) {
						if (line !== '') {
							console.log(line);
							let data = JSON.parse(line);

							if ('detail' in data) {
								throw data;
							}

							if (data.done == false) {
								if (responseMessage.content == '' && data.message.content == '\n') {
									continue;
								} else {
									responseMessage.content += data.message.content;

									messages = updateMessages(responseMessage);
								}
							} else {
								isLoading = false;
								responseMessage.done = true;

								if (responseMessage.content == '') {
									responseMessage.error = {
										code: 400,
										content: `Oops! No text generated from Ollama, Please try again.`
									};
								}

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
								messages = updateMessages(responseMessage);

								if ($settings.notificationEnabled && !document.hasFocus()) {
									const notification = new Notification(`${model.id}`, {
										body: responseMessage.content,
										icon: `${WEBUI_BASE_URL}/static/favicon.png`
									});
								}
							}
						}
					}
				} catch (error) {
					console.log(error);
					if (isErrorWithDetail(error)) {
						toast.error(error.detail);
					}
					break;
				} finally {
					isLoading = false;
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
			messages = updateMessages(responseMessage);
		}
		await tick();
		_stopResponseFlag = false;
		isLoading = false;
		return responseMessage;
	};

	const handleOpenAIError = async (
		error: any,
		res: Response | null,
		model: Model,
		responseMessage: _CiscoArticleMessage
	) => {
		let errorMessage = '';
		let innerError;

		if (error) {
			innerError = error;
		} else if (res !== null) {
			innerError = await res.json();
		}
		console.error(innerError);
		if (isErrorWithDetail(innerError)) {
			toast.error(innerError.detail);
			errorMessage = innerError.detail;
		} else if ('error' in innerError) {
			if (isErrorWithMessage(innerError.error)) {
				toast.error(innerError.error.message);
				errorMessage = innerError.error.message;
			} else {
				toast.error(innerError.error);
				errorMessage = innerError.error;
			}
		} else if (isErrorWithMessage(innerError)) {
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

		messages = updateMessages(responseMessage);
	};

	const renderStyling = async () => {
		await tick();
		if (messages.at(-1) && messages.at(-1)?.role === 'assistant') {
			const message = messages.at(-1)!;
			console.log('Component is rendering styling for message', message.id);
			if (tooltipInstance && tooltipInstance !== null) {
				tooltipInstance[0]?.destroy();
			}

			if (message.info) {
				let tooltipContent = '';
				if (message.info?.openai) {
					tooltipContent = `prompt_tokens: ${message.info.prompt_tokens ?? 'N/A'}<br/>
								  completion_tokens: ${message.info.completion_tokens ?? 'N/A'}<br/>
								  total_tokens: ${message.info.total_tokens ?? 'N/A'}`;
					console.log('tooltipContent', tooltipContent);
				} else {
					const responseTokens =
						message.info.eval_duration !== undefined && message.info.eval_duration !== 0
							? `${
									Math.round(((message.info.eval_count ?? 0) / (message.info.eval_duration / 1000000000)) * 100) / 100
							  } tokens`
							: 'N/A';

					const promptTokens =
						message.info.prompt_eval_duration !== undefined && message.info.prompt_eval_duration !== 0
							? `${
									Math.round(
										((message.info.prompt_eval_count ?? 0) / (message.info.prompt_eval_duration / 1000000000)) * 100
									) / 100
							  } tokens`
							: 'N/A';

					const totalDuration =
						message.info.total_duration !== undefined && message.info.total_duration !== 0
							? `${Math.round(((message.info.total_duration ?? 0) / 1000000) * 100) / 100}ms`
							: 'N/A';

					const loadDuration =
						message.info.load_duration !== undefined && message.info.load_duration !== 0
							? `${Math.round(((message.info.load_duration ?? 0) / 1000000) * 100) / 100}ms`
							: 'N/A';

					const promptEvalDuration =
						message.info.prompt_eval_duration !== undefined && message.info.prompt_eval_duration !== 0
							? `${Math.round(((message.info.prompt_eval_duration ?? 0) / 1000000) * 100) / 100}ms`
							: 'N/A';

					const evalDuration =
						message.info.eval_duration !== undefined && message.info.eval_duration !== 0
							? `${Math.round(((message.info.eval_duration ?? 0) / 1000000) * 100) / 100}ms`
							: 'N/A';

					tooltipContent = `response_token/s: ${responseTokens}<br/>
								prompt_token/s: ${promptTokens}<br/>
								total_duration: ${totalDuration}<br/>
								load_duration: ${loadDuration}<br/>
								prompt_eval_count: ${message.info.prompt_eval_count ?? 'N/A'}<br/>
								prompt_eval_duration: ${promptEvalDuration}<br/>
								eval_count: ${message.info.eval_count ?? 'N/A'}<br/>
								eval_duration: ${evalDuration}<br/>
								approximate_total: ${approximateToHumanReadable(message.info?.total_duration ?? 0)}`;
				}
				tooltipInstance = tippy(`#info-${message.id}`, {
					content: `<span class="text-xs" id="tooltip-${message.id}">${tooltipContent}</span>`,
					allowHTML: true,
					theme: 'dark',
					arrow: false,
					offset: [0, 4]
				});
			}
		}
	};

	function handleClose() {
		console.log('close button clicked');
		dispatch('closeDialog', { open: false });
	}

	export let open;

	const [send, recieve] = crossfade({
		duration: (d) => Math.sqrt(d * 200),
		fallback(node, params) {
			const style = getComputedStyle(node);
			const transform = style.transform === 'none' ? '' : style.transform;

			return {
				duration: 600,
				easing: cubicInOut,
				css: (t) => `
					transform: ${transform} scale(${t});
					opacity: ${t}
				`
			};
		}
	});
</script>

{#if !open}
	<Spinner />
{:else}
	<details
		on:toggle={startGenerateDynamicQuestions}
		transition:slide={{ duration: 1000, easing: quintInOut }}
		{open}
		class="detailsGetSupport hover:shadow-[0_4px_20px_0_rgba(0,0,0,0.2)] bg-gray-50 text-[#414344] p-4 bg-white border border-[#d6d6d6] rounded-lg shadow-lg"
		data-section="Objective"
	>
		<summary class="flex items-center justify-between mb-4">
			<div class="flex items-center space-x-2">
				<span
					id="stepNumberBreadcrumb"
					class="inline flex items-center justify-center size-8 bg-[#0d274d] font-bold rounded-full text-gray-50"
					>{$activeSupportStep}</span
				>
				<h3 class="inline ml-2">
					Get Support <strong>&gt;</strong>
					<p class="text-[#999899] inline">{activeStepSection}</p>
				</h3>
			</div>
			<button on:click={handleClose} class="cursor-pointer bg-none text-xl">×</button>
		</summary>
		<div class="messageWell overflow-auto p-4 pb-20 min-h-[30dvh] max-h-[35dvh] h-auto">
			<h1 class="text-2xl text-center">Need Answers?</h1>
			<h3 class="text-2xl text-center -mt-4 mb-10">choose from our options below</h3>
			{#each messages as message, index (index)}
				{#if message && message.role === 'user' && index !== 1}
					<div class="question user bg-[rgba(155,215,255,0.5)] text-[#2b5592] w-fit p-4 my-4 rounded-lg">
						{@html message.content}
					</div>
				{:else if message.role === 'assistant' && index !== 0}
					<div class="assistant bg-[#f2f2f2] rounded-lg p-4 w-fit mb-0 relative text-[#414344]">
						<p>
							{@html message.content
								?.replace(/\n/g, '<br>')
								.replace(
									/(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/gi,
									(match) => `<a href="${match}">${match}</a>`
								)}
						</p>
					</div>
				{/if}
			{/each}
			{#if isLoading}
				<div
					style="text-align: center; margin-top: 2.5em;"
					in:fly={{ y: 25, duration: 1000 }}
					out:fly={{ y: -25, duration: 1000 }}
				>
					<Spinner />
				</div>
			{/if}
		</div>
		<div class="flex items-start gap-4 justify-evenly s-5e5kg2sOboz_">
			<details class="rounded-bl-md rounded-br-md border border-[#d2d2d2] p-4" id="detailsFaqlike" open>
				<summary class="s-5e5kg2sOboz_" />
				<div class="flex items-start justify-evenly flex-wrap gap-4">
					{#key questions}
						{#each questions as btn, i (i)}
							<button
								in:recieve={{ key: i, delay: i * 100 }}
								out:send={{ key: i, delay: i * 100 }}
								animate:flip={{ duration: 200 }}
								on:click={async () => await generateLLMAnswer(i, btn.id, btn.text)}
								disabled={btn.clicked}
								class="button text-base py-2 px-4 rounded-md hover:cursor-pointer qna-button-{i}"
								class:clicked={btn.clicked}
								id={btn.id}
								tabindex="0"
								data-index={i}
								data-clicked={btn.clicked}>{btn.text}</button
							>
						{/each}
					{/key}
				</div>
			</details>
		</div>
	</details>
{/if}

<style>
	.author-name {
		margin-left: 1em;
		text-align: center;
		font-size: 20px;
		color: #333;
	}

	.icon-article {
		background-color: #4caf50; /* Green color for article */
	}

	.icon-guide {
		/* background-color: #2196f3; */

		border-left: #2196f3 5px solid;
	}

	.icon-video {
		background-color: #f44336; /* Red color for video */
	}

	.icon-cli-guide {
		background-color: #9c27b0; /* Purple color for CLI guide */
	}
	.icon-band {
		padding: 0.5em 0 0 1em;
	}

	details summary::marker {
		display: none;
		content: '';
	}

	summary::marker {
		appearance: none;
	}

	.messageWell h1 {
		font-family: 'CiscoSansTT', sans-serif;
		font-size: var(--font-size-md);
		color: #333;
		max-width: 1500px;
		line-height: 2.8em;
		font-weight: 700;
		margin: 0em 0 0 0;
		background: -webkit-linear-gradient(left, #1d69cc, #2196f3);
		background-clip: text;
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	details > div.messageWell {
		background-image: radial-gradient(
				75.83% 78.18% at 51.72% 100%,
				rgba(56, 96, 190, 0.03) 0%,
				rgba(100, 187, 227, 0.03) 65.24%,
				rgba(223, 223, 223, 0) 100%
			),
			conic-gradient(from 180deg at 50% 50%, rgba(56, 96, 190, 0) 0deg, rgba(56, 96, 190, 0.02) 360deg);
	}

	.button {
		display: inline;
		text-align: center;
		text-decoration: none;
		color: #2b5592;
		border: 1px solid #2b5592;
		background-color: transparent;
		transition: all 0.5s ease-in-out;
		font-family: 'CiscoSansThin';
		transform-origin: center center;
		will-change: transform;
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
	}
</style>
