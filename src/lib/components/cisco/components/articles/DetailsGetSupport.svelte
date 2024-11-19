<script lang="ts">
	import type { Article, ArticleStep } from '$lib/types';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import type { Model, _CiscoArticleMessage } from '$lib/stores';
	import type { MarkedOptions, TokensList } from 'marked';
	import type { Instance } from 'tippy.js';

	import tippy from 'tippy.js';
	import { ThumbsUp, ThumbsDown, FileText, FileCode, SquareCode } from 'lucide-svelte';
	import dayjs from 'dayjs';
	import { marked } from 'marked';
	import { settings, config } from '$lib/stores';
	import { generateOpenAIChatCompletionQuestions, generateOpenAIChatCompletion } from '$lib/apis/openai';
	import { v4 as uuidv4 } from 'uuid';
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, getContext, tick, onMount, afterUpdate } from 'svelte';
	import { flip } from 'svelte/animate';
	import { slide, fly, fade, crossfade } from 'svelte/transition';
	import { cubicIn, cubicInOut, quintInOut } from 'svelte/easing';
	import {
		activeArticleId,
		mountedArticleSteps,
		mountedArticlePreambleDevices,
		mountedArticlePreambleObjective,
		models,
		user,
		ciscoArticleMessages,
		activeArticle,
		socket,
		activeSupportStep,
		globalMessages
	} from '$lib/stores';
	import {
		approximateToHumanReadable,
		isErrorAsString,
		replaceTokens,
		sanitizeResponseContent,
		revertSanitizedResponseContent,
		isErrorWithDetail,
		isErrorWithMessage,
		stripHtml,
		titleizeWords,
		splitStream,
		copyToClipboard,
		extractSentences
	} from '$lib/utils';

	import { WEBUI_BASE_URL } from '$lib/constants';
	import mermaid from 'mermaid';
	import { queryDoc, queryCollection, queryDocWithSmallChunks } from '$lib/apis/rag';
	import { updateArticleStep } from '$lib/apis/articles';
	import { synthesizeOpenAISpeech } from '$lib/apis/audio';
	import { createOpenAITextStream } from '$lib/apis/streaming';
	import { generateChatCompletion, generateOllamaChatCompletion } from '$lib/apis/ollama';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Feedback from './Feedback.svelte';
	import ProfileImage from '$lib/components/chat/Messages/ProfileImage.svelte';
	import Name from '$lib/components/chat/Messages/Name.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Skeleton from '$lib/components/chat/Messages/Skeleton.svelte';
	import CodeBlock from '$lib/components/chat/Messages/CodeBlock.svelte';

	export let currentStepStr: string;
	export let index: number;
	export let open: boolean;
	export let step: ArticleStep;
	export let readOnly: boolean = false;
	export let selectedModels: string[];

	const i18n: Writable<i18nType> = getContext('i18n');
	const dispatch = createEventDispatcher();
	const renderer = new marked.Renderer();

	const STATIC_IDS = ['static_1', 'static_2', 'static_3'];
	const DYNAMIC_IDS = ['dynamic_1', 'dynamic_2', 'dynamic_3'];

	let history: { messages: { [id: string]: Record<string, any> }; currentId: string | null } = {
		messages: {},
		currentId: null
	};

	let edit: boolean = false;
	let editedContent = '';
	let editTextAreaElement: HTMLTextAreaElement;

	let questions: Array<{ id: string; text: string; clicked: boolean }> = [];
	let questionsGenerated = false;
	let isLoading = false;
	let currentQuestion: string;

	let show: boolean = false;

	let thumbsUpOpen = false;
	let thumbsDownOpen = false;

	let atSelectedModel: Model | undefined;
	let selectedModelIds: string[] = [];

	let staticQuestionBtns: Array<{ id: string; text: string; clicked: boolean }> = [];
	let dynamicQuestionBtns: Array<{ id: string; text: string; clicked: boolean }> = [];
	let tooltipInstance: Instance[] | null = null;

	let sentencesAudio: { [key: number]: HTMLAudioElement | null } = {};
	let speaking: boolean | null = null;
	let speakingIdx: number | null = null;
	let loadingSpeech = false;

	let _stopResponseFlag: boolean = false;

	$: selectedModelIds = atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;
	$: model = $models.find((m) => m.id === selectedModels.at(0));

	let messages: _CiscoArticleMessage[] = [
		{
			id: 'system-1',
			role: 'system',
			content:
				'You are a Cisco TAC Engineer assisting a user in configuring their network device. You are to explain the steps clearly and in easy-to-understand terms. Do not ask the user how it went or if they have any questions. You are to provide the user with the information they need to complete the task. Messages should be self-contained and not require the user to remember previous messages.',
			timestamp: Math.floor(Date.now() / 1000),
			model: model?.name ?? selectedModels.at(0)!
		},
		{
			id: 'generic-user-1',
			role: 'user',
			content: "Hi, I'm having trouble with my switch.",
			timestamp: Math.floor(Date.now() / 1000),
			model: model?.name ?? selectedModels.at(0)!
		}
	];

	const generateTokens = (message: _CiscoArticleMessage) => {
		const initTokens: TokensList = [] as unknown as TokensList;
		initTokens.links = {};

		if (message.role === 'assistant') {
			const messageTokens = marked.lexer(
				replaceTokens(sanitizeResponseContent(message.content), model?.name, $user?.name)
			) as TokensList;
			initTokens.push(...messageTokens);
			Object.assign(initTokens.links, messageTokens.links);
		}
		return initTokens;
	};
	let tokenMap: { [id: string]: TokensList } = {};
	$: messages.forEach((m) => {
		if (m.role === 'assistant') {
			tokenMap[m.id] = generateTokens(m);
		}
	});

	$: if (currentQuestion) {
		currentQuestion = titleizeWords(currentQuestion);
	}

	$: if ($activeArticle) {
		// For Generated Articles, set the default static buttons
		// Articles saved in the database will have these set already but generated articles will not
		// Article.svelte will set the default QNA Pairs for generated articles + Insert the generated article into the database
		// This is just a backup in case the default QNA Pairs are not set
		staticQuestionBtns = $activeArticle.steps[index].qna_pairs
			?.filter((pair) => STATIC_IDS.includes(pair.id))
			.map((pair) => ({ id: pair.id, text: pair.question, clicked: false })) ?? [
			{ id: 'static_1', text: "I don't understand this step", clicked: false },
			{ id: 'static_2', text: 'Help me troubleshoot', clicked: false },
			{ id: 'static_3', text: 'Show best practices', clicked: false }
		];

		dynamicQuestionBtns =
			$activeArticle.steps[index].qna_pairs
				?.filter((pair) => DYNAMIC_IDS.includes(pair.id))
				.map((pair) => ({ id: pair.id, text: pair.question, clicked: false })) ?? [];

		questions = [...staticQuestionBtns, ...dynamicQuestionBtns];
		console.log('questions', questions);
	}

	// For code blocks with simple backticks
	renderer.codespan = (code) => {
		return `<code>${code.replaceAll('&amp;', '&')}</code>`;
	};

	// Open all links in a new tab/window (from https://github.com/markedjs/marked/issues/655#issuecomment-383226346)
	const origLinkRenderer = renderer.link;
	renderer.link = (href, title, text) => {
		const html = origLinkRenderer.call(renderer, href, title, text);
		return html.replace(/^<a /, '<a target="_blank" rel="nofollow" ');
	};

	renderer.paragraph = (text) => {
		return `<p>${marked.parseInline(text, { renderer })}`;
	};

	const { extensions, ...defaults } = marked.getDefaults() as MarkedOptions & {
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		extensions: any;
	};

	function handleEdit(event: any) {
		console.log('edit', event);
		messages = messages.map((m) => (m.id === event.detail.message.id ? event.detail.message : m));
	}

	const stopResponse = () => {
		_stopResponseFlag = true;
		console.log('stopResponse');
	};

	const continueGeneration = async (messageId: string) => {
		console.log('continueGeneration');
		console.log('messages at continueGeneration', messages);
		const message = messages.find((m) => m.id === messageId);
		let modelId;

		if (message && message.done) {
			message.done = false;
			await tick();

			const model = $models.filter((m) => m.id === message.model).at(0);

			if (model) {
				modelId = model.id;
				let systemMessage = messages.find((m) => {
					if (m.role === 'system') {
						const id = m.id.split('_').at(-1);
						return id && id.trim() === messageId.trim();
					}
				});
				if (systemMessage) {
					let responseMessage: _CiscoArticleMessage = {
						...message
					};
					if (model.owned_by === 'openai') {
						responseMessage = await sendPromptOpenAI(systemMessage, {
							model,
							responseMessage
						});
					} else if (model.owned_by === 'ollama') {
						responseMessage = await sendPromptOllama(systemMessage, {
							model,
							responseMessage
						});
					}
					const updatedArticle = await updateArticleStep(localStorage.token, $activeArticleId, {
						step_index: index,
						step: $activeArticle
							? {
									...$activeArticle.steps[index],
									qna_pairs: $activeArticle.steps.at(index)?.qna_pairs?.map((pair) => {
										if (pair.id.trim().toLowerCase() === message.qnaBtnId?.trim().toLowerCase()) {
											return {
												...pair,
												answer: responseMessage.content === '' ? null : responseMessage.content,
												sources: message.sources,
												model: model.id
											};
										}
										return pair;
									})
							  }
							: {
									...step,
									qna_pairs: step.qna_pairs?.map((pair) => {
										if (pair.id.trim().toLowerCase() === message.associatedQuestion?.trim().toLowerCase()) {
											return {
												...pair,
												answer: responseMessage.content === '' ? null : responseMessage.content,
												sources: message.sources,
												model: model.id
											};
										}
										return pair;
									})
							  }
					});
					activeArticle.set(updatedArticle);
					console.log('updated article', updatedArticle);
				} else {
					toast.error($i18n.t('System message not found'));
				}
			}
		} else {
			const model = selectedModelIds.at(0) ?? selectedModels.at(0) ?? atSelectedModel?.id ?? modelId;
			toast.error($i18n.t(`Model {{modelId}} not found`, { modelId: model }));
		}
	};

	const regenerateResponse = async (message: _CiscoArticleMessage) => {
		const { id, qnaBtnId, associatedQuestion } = message;
		const btnIndex = questions.findIndex((q) => q.id === qnaBtnId);
		if (btnIndex === -1 || !qnaBtnId || !associatedQuestion) {
			toast.error($i18n.t('Oops! Something went wrong. Please try your request again.'));
			return;
		}

		if (!$activeArticle) {
			toast.error($i18n.t('Article not found'));
			return;
		}

		activeArticle.update((article) => {
			if (!article) {
				return article;
			}

			const qnaBtn = article.steps[index].qna_pairs?.find((pair) => pair.id === qnaBtnId);
			if (qnaBtn) {
				qnaBtn.answer = null;
			}

			article.steps[index] = step;
			return article;
		});
		await tick();
		await generateLLMAnswer(btnIndex, qnaBtnId, associatedQuestion);

		// Find the associated system message in messages
		let systemMessage = messages.find((m) => m.id.trim() === `system_${id.trim()}`);
		if (systemMessage) {
			systemMessage = {
				...systemMessage,
				content: `You are being asked to regenerate your response to the following question: '${associatedQuestion}'. The user is confused or doesn't understand. Compare your original response and make any necessary changes. Do not ask the user questions or how it turned out.\n\n<original>\n\t${systemMessage.content}\n</original>\n\nEvaluate the original response and make any necessary changes.`,
				timestamp: Math.floor(Date.now() / 1000)
			};
			const selectedModelId = selectedModelIds.at(0) ?? selectedModels.at(0) ?? atSelectedModel?.id ?? model?.id;
			if (selectedModelId) {
				const model = $models.find((m) => m.id === selectedModelId);
				if (model) {
					let responseMessage: _CiscoArticleMessage = {
						...message,
						role: 'assistant',
						originalContent: message.content,
						content: '',
						done: false,
						timestamp: Math.floor(Date.now() / 1000),
						model: model.id
					};
					messages = updateMessages(responseMessage);
					await tick();
					responseMessage.id = uuidv4();
					if (model.owned_by === 'openai') {
						responseMessage = await sendPromptOpenAI(systemMessage, {
							model,
							responseMessage
						});
					} else if (model.owned_by === 'ollama') {
						responseMessage = await sendPromptOllama(systemMessage, {
							model,
							responseMessage
						});
					}
					await sendUpdateArticle(responseMessage, qnaBtnId);
				}
			}
		}
	};

	const editMessageHandler = async (content: string) => {
		edit = true;
		editedContent = content;

		await tick();

		editTextAreaElement.style.height = '';
		editTextAreaElement.style.height = `${editTextAreaElement.scrollHeight}px`;
	};

	const copyToClipboardWithToast = async (text: string) => {
		const res = await copyToClipboard(text);
		if (res) {
			toast.success($i18n.t('Copying to clipboard was successful!'));
		}
	};

	const playAudio = (idx: number): Promise<Event> => {
		return new Promise((res) => {
			speakingIdx = idx;
			const audio = sentencesAudio[idx];
			if (audio) {
				audio.play();
				audio.onended = async (e) => {
					await new Promise((r) => setTimeout(r, 300));

					if (Object.keys(sentencesAudio).length - 1 === idx) {
						speaking = null;
					}

					res(e);
				};
			}
		});
	};

	const toggleSpeakMessage = async (content: string = '') => {
		if (speaking && speakingIdx) {
			try {
				speechSynthesis.cancel();
				sentencesAudio[speakingIdx]?.pause();
				sentencesAudio[speakingIdx]!.currentTime = 0;
			} catch {}

			speaking = null;
			speakingIdx = null;
		} else {
			if ((content ?? '').trim() !== '') {
				speaking = true;

				if ($config?.audio?.tts?.engine === 'openai') {
					loadingSpeech = true;

					const sentences = extractSentences(content).reduce((mergedTexts, currentText) => {
						const lastIndex = mergedTexts.length - 1;
						if (lastIndex >= 0) {
							const previousText = mergedTexts[lastIndex];
							const wordCount = previousText.split(/\s+/).length;
							if (wordCount < 2) {
								mergedTexts[lastIndex] = previousText + ' ' + currentText;
							} else {
								mergedTexts.push(currentText);
							}
						} else {
							mergedTexts.push(currentText);
						}
						return mergedTexts;
					}, [] as string[]);

					console.log(sentences);

					if (sentences.length > 0) {
						sentencesAudio = sentences.reduce<{ [key: number]: HTMLAudioElement | null }>((a, e, i, arr) => {
							a[i] = null;
							return a;
						}, {});

						let lastPlayedAudioPromise = Promise.resolve(new Event('')); // Initialize a promise that resolves immediately

						for (const [idx, sentence] of sentences.entries()) {
							const res = await synthesizeOpenAISpeech(
								localStorage.token,
								$settings?.audio?.tts?.voice ?? $config?.audio?.tts?.voice,
								sentence
							).catch((error) => {
								toast.error(error);

								speaking = null;
								loadingSpeech = false;

								return null;
							});

							if (res) {
								const blob = await res.blob();
								const blobUrl = URL.createObjectURL(blob);
								const audio = new Audio(blobUrl);
								sentencesAudio[idx] = audio;
								loadingSpeech = false;
								lastPlayedAudioPromise = lastPlayedAudioPromise.then(() => playAudio(idx));
							}
						}
					} else {
						speaking = null;
						loadingSpeech = false;
					}
				} else {
					let voices = [];
					const getVoicesLoop = setInterval(async () => {
						voices = speechSynthesis.getVoices();
						if (voices.length > 0) {
							clearInterval(getVoicesLoop);

							const voice =
								voices
									?.filter((v) => v.voiceURI === ($settings?.audio?.tts?.voice ?? $config?.audio?.tts?.voice))
									?.at(0) ?? undefined;

							console.log(voice);

							const speak = new SpeechSynthesisUtterance(content);

							console.log(speak);

							speak.onend = () => {
								speaking = null;
								if ($settings.conversationMode) {
									document.getElementById('voice-input-button')?.click();
								}
							};

							if (voice) {
								speak.voice = voice;
							}

							speechSynthesis.speak(speak);
						}
					}, 100);
				}
			} else {
				toast.error($i18n.t('No content to speak'));
			}
		}
	};

	const sendUpdateArticle = async (updatedMessage: _CiscoArticleMessage, btnId?: string) => {
		// Use mountedArticleSteps as its a derived store and will always be up to date each time activeArticle changes
		const updatedArticle = await updateArticleStep(localStorage.token, $activeArticleId, {
			step_index: index,
			step: {
				...$mountedArticleSteps[index],
				qna_pairs: $mountedArticleSteps.at(index)?.qna_pairs?.map((pair) => {
					const id = btnId
						? btnId
						: pair.id.trim().toLowerCase() === updatedMessage.qnaBtnId?.trim().toLowerCase()
						? pair.id
						: null;
					if (id && id.trim().toLowerCase() === pair.id.trim().toLowerCase()) {
						return {
							...pair,
							answer: updatedMessage.content,
							original_answer: updatedMessage.originalContent ?? undefined,
							sources: updatedMessage.sources ?? undefined,
							annotation: updatedMessage.annotation ? { ...updatedMessage.annotation } : undefined
						};
					}

					return pair;
				})
			}
		});
		if (updatedArticle) {
			activeArticle.set(updatedArticle);
		}
	};

	const updateMessages = (newMessage: _CiscoArticleMessage) => {
		const unique = new Set(messages.map((m) => m.id));
		console.log(unique);
		if (!unique.has(newMessage.id)) {
			return [...messages, newMessage];
		} else {
			return messages.map((m) => (m.id === newMessage.id ? newMessage : m));
		}
	};

	const confirmEditResponseMessage = async (messageId: string, content: string) => {
		const message = messages.find((m) => m.id === messageId);
		if (message) {
			const updatedMessage = {
				...message,
				originalContent: message.content,
				content
			};
			messages = updateMessages(updatedMessage);
			await sendUpdateArticle(updatedMessage);
		}
	};

	const cancelEditMessage = async () => {
		edit = false;
		editedContent = '';
		await tick();
		await renderStyling();
	};

	const editMessageConfirmHandler = async (messageId: string) => {
		if (editedContent === '') {
			editedContent = ' ';
		}

		confirmEditResponseMessage(messageId, editedContent);

		edit = false;
		editedContent = '';

		await tick();
		renderStyling();
	};

	const rateMessage = async (messageId: string, rating: number) => {
		const message = messages.find((m) => m.id === messageId);
		console.log('rateMessage found message ?: ', message);
		if (message) {
			const updatedMessage = {
				...message,
				annotation: message.annotation ? { ...message.annotation, rating } : { rating }
			};
			messages = updateMessages(updatedMessage);
			await sendUpdateArticle(updatedMessage);
		}
	};

	const scrollToBottom = () => {
		const messagesWell = document.getElementById('messages-well');
		if (messagesWell) {
			messagesWell.scrollTop = messagesWell.scrollHeight;
		}
	};

	const generateContext = () => {
		if (index > -1 && Array.isArray($mountedArticleSteps)) {
			return $mountedArticleSteps
				.slice(0, index + 1)
				.map((s, i) => `Step ${i + 1}: ${stripHtml(s.text)}`)
				.join('\n');
		}
		return '';
	};

	const generateQuestionPrompt = () => {
		if (index > -1 && Array.isArray($mountedArticleSteps)) {
			const stepsText = generateContext();

			return `Below you will be provided with an network article objective, the applicable devices, and the configuration steps in between XML-Style tags. Please review these steps to understand the actions taken up to this point. Based on the latest step provided, return 3 questions a user might have about the latest step. Return only these 3 questions.\n\n<objective>\n\t${$mountedArticlePreambleObjective}\n</objective>\n\n<devices>\n\t${$mountedArticlePreambleDevices}\n</devices>\n\n<steps>\n\t${stepsText}\n</steps>\n\nRemember, the user is focused on the latest step. Return only the questions a user may have about the latest step. No other text is necessary.`;
		}
		return null;
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

	const startGenerateDynamicQuestions = async (e: Event & { currentTarget: HTMLDetailsElement }) => {
		if (e.currentTarget.open && !questionsGenerated) {
			dispatch('openStepSupport', { index });
			questionsGenerated = true;
			selectedModels = selectedModels.map((modelId) => ($models.map((m) => m.id).includes(modelId) ? modelId : ''));
			let selectedModel = selectedModels.at(0);
			if (selectedModels.includes('')) {
				toast.error($i18n.t('Model not selected'));
			} else if (
				$activeArticle &&
				$activeArticle.steps.at(index)?.qna_pairs?.some((pair) => DYNAMIC_IDS.includes(pair.id))
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
						step_index: index,
						step: {
							...step,
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
			dispatch('closeStepSupport', { index });
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
		// If the user had opened the feedback form, close it
		if (show) {
			show = false;
		}
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

		if ($activeArticle && $activeArticle.steps.at(index)?.qna_pairs) {
			const pairs = $activeArticle.steps.at(index)?.qna_pairs ?? [];
			const match = pairs.find((pair) => pair.id.trim().toLowerCase() === btnId.trim().toLowerCase());
			if (match && match.answer !== null && match.answer !== '') {
				await tick();

				messages = updateMessages({
					id: uuidv4(),
					role: 'assistant',
					content: match.answer,
					timestamp: Math.floor(Date.now() / 1000),
					model: model?.id ?? selectedModels.at(0)!,
					sources: match.sources ?? [],
					associatedQuestion: question,
					qnaBtnId: btnId,
					done: true
				});
				isLoading = false;
				console.log('messages', messages);
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
				console.log('messages after response message', messages);
				const updatedArticle = await updateArticleStep(localStorage.token, $activeArticleId, {
					step_index: index,
					step: $activeArticle
						? {
								...$activeArticle.steps[index],
								qna_pairs: $activeArticle.steps.at(index)?.qna_pairs?.map((pair) => {
									if (pair.id.trim().toLowerCase() === btnId.trim().toLowerCase()) {
										return {
											...pair,
											answer: responseMessage.content === '' ? null : responseMessage.content,
											sources: metadatas?.map((m, i) => ({ ...m, content: documents?.at(i) })),
											model: model.id
										};
									}
									return pair;
								})
						  }
						: {
								...step,
								qna_pairs: step.qna_pairs?.map((pair) => {
									if (pair.id.trim().toLowerCase() === btnId.trim().toLowerCase()) {
										return {
											...pair,
											answer: responseMessage.content === '' ? null : responseMessage.content,
											sources: metadatas?.map((m, i) => ({ ...m, content: documents?.at(i) })),
											model: model.id
										};
									}
									return pair;
								})
						  }
				});
				activeArticle.set(updatedArticle);
				console.log('updated article', updatedArticle);
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
						messages = messages;
						await renderStyling();
						break;
					}

					if (responseMessage.content == '' && value == '\n') {
						continue;
					} else {
						// First chunk means we have a response, stop whowing Spinner and stream
						isLoading = false;
						responseMessage.content += value;
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
		messages = messages;
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

									messages = messages;
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
								messages = messages;

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
		}
		await tick();
		_stopResponseFlag = false;
		isLoading = false;
		return responseMessage;
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

	onMount(async () => {
		await tick();
		await mermaid.run({
			querySelector: '.mermaid'
		});
	});

	// $: if (messages.length > 2) {
	// 	ciscoArticleMessages.set(messages);
	// 	globalMessages.update((store) => {
	// 		store.set(index, messages);
	// 		return store;
	// 	});
	// }

	let latest: HTMLDivElement | null;

	$: if (latest) {
		latest.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
	}

	afterUpdate(async () => {
		await renderStyling();
		scrollToBottom();
	});
</script>

<details
	on:toggle={startGenerateDynamicQuestions}
	bind:open
	transition:slide={{ duration: 1000, easing: quintInOut }}
	class="detailsGetSupport p-4 border border-gray-400 transition-all duration-250 ease-in rounded-tr-none rounded-tl-none rounded-br-lg rounded-bl-lg bg-gray-100 max-w-[1100px] shadow-md hover:shadow-lg"
>
	<summary tabindex="-1" class="flex items-center gap-2 cursor-pointer">
		<span id="stepNumberBreadcrumb" class="bg-blue-500 text-white w-8 h-8 flex items-center justify-center rounded-full"
			>?</span
		>
		<h3 class="inline text-base font-bold">
			Get Support &gt; <p class="text-gray-500 inline">{currentStepStr}</p>
		</h3></summary
	>

	<div
		class="messageWell max-h-[50vh] min-h-[30vh] overflow-auto p-4 bg-white rounded-t-lg text-base pt-8"
		id="messages-well"
	>
		<h1 class="text-2xl mt-4 text-center">Need Answers?</h1>
		<h3 class="text-2xl -mt-2.5 mb-20 text-center">Choose from our options below</h3>

		{#each messages as message, i (message.id)}
			{#key message.id}
				{#if message && message.role === 'user' && i !== 1}
					<ProfileImage
						src={model?.info?.meta?.profile_image_url ??
							($i18n.language === 'dg-DG' ? `/doge.png` : `${WEBUI_BASE_URL}/static/favicon.png`)}
					/>
					<div
						id="message-{message.id}"
						class="message-{message.id} question {message.role} rounded-lg p-4 ml-2 w-fit mb-1 dark:prose-invert whitespace-pre-line"
						dir={$settings.chatDirection}
					>
						<h4>{message.content}</h4>
					</div>
				{:else if message.role === 'assistant' && i !== 0}
					<Name _classes="mt-1">
						{model?.name ?? message.model}

						{#if message.timestamp}
							<span class=" self-center group-hover:visible text-gray-400 text-xs font-medium uppercase">
								{dayjs(message.timestamp * 1000).format($i18n.t('h:mm a'))}
							</span>
						{/if}
					</Name>
					{#if edit}
						<div class="w-full bg-gray-50 dark:bg-gray-800 rounded-3xl px-5 py-3 my-2">
							<textarea
								id="message-edit-{message.id}"
								bind:this={editTextAreaElement}
								class=" bg-transparent outline-none w-full resize-none"
								bind:value={editedContent}
								on:input={(e) => {
									e.currentTarget.style.height = '';
									e.currentTarget.style.height = `${e.currentTarget.scrollHeight}px`;
								}}
								on:keydown={(e) => {
									if (e.key === 'Escape') {
										document.getElementById('close-edit-message-button')?.click();
									}

									const isCmdOrCtrlPressed = e.metaKey || e.ctrlKey;
									const isEnterPressed = e.key === 'Enter';

									if (isCmdOrCtrlPressed && isEnterPressed) {
										document.getElementById('save-edit-message-button')?.click();
									}
								}}
							/>

							<div class=" mt-2 mb-1 flex justify-end space-x-1.5 text-sm font-medium">
								<button
									id="close-edit-message-button"
									class="px-4 py-2 bg-white hover:bg-gray-100 text-gray-800 transition rounded-3xl"
									on:click={() => {
										cancelEditMessage();
									}}
								>
									{$i18n.t('Cancel')}
								</button>

								<button
									id="save-edit-message-button"
									class=" px-4 py-2 bg-gray-900 hover:bg-gray-850 text-gray-100 transition rounded-3xl"
									on:click={() => {
										editMessageConfirmHandler(message.id);
									}}
								>
									{$i18n.t('Save')}
								</button>
							</div>
						</div>
					{:else}
						<div
							bind:this={latest}
							id="message-{message.id}"
							class="message-{message.id} {message.role} dark:prose-invert bg-slate-100 rounded-lg p-4 text-gray-700 ml-2 w-fit mb-1 space-y-1 whitespace-pre-line flex flex-col"
						>
							{#if message.content === '' && !message.error}
								<Skeleton />
							{:else if message.content && message.error !== true}
								<!-- always show message contents even if there's an error -->
								<!-- unless message.error === true which is legacy error handling, where the error message is stored in message.content -->
								{#each tokenMap[message.id] as token, tokenIdx}
									{#if token.type === 'code'}
										{#if token.lang === 'mermaid'}
											<pre class="mermaid">{revertSanitizedResponseContent(token.text)}</pre>
										{:else}
											<CodeBlock
												id={`${message.id}-${tokenIdx}`}
												lang={token?.lang ?? ''}
												code={revertSanitizedResponseContent(token?.text ?? '')}
											/>
										{/if}
									{:else}
										{@html marked.parse(token.raw, {
											...defaults,
											gfm: true,
											breaks: true,
											renderer
										})}
									{/if}
								{/each}
							{/if}
							{#if message.error}
								<div
									class="flex mt-2 mb-4 space-x-2 border px-4 py-3 border-red-800 bg-red-800/30 font-medium rounded-lg"
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										fill="none"
										viewBox="0 0 24 24"
										stroke-width="1.5"
										stroke="currentColor"
										class="w-5 h-5 self-center"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
										/>
									</svg>

									<div class=" self-center">
										{message?.error?.content ?? message.content}
									</div>
								</div>
							{/if}

							{#if message.done}
								{@const isLastMessage = messages.length - 1 === i}
								<div class="w-full ml-2">
									<div class=" flex justify-start overflow-x-auto buttons text-gray-600 dark:text-gray-500">
										{#if !readOnly}
											<Tooltip content={$i18n.t('Edit')} placement="bottom">
												<button
													class="{isLastMessage
														? 'visible'
														: 'invisible group-hover:visible'} p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition"
													on:click={async () => {
														await editMessageHandler(message.content);
													}}
												>
													<svg
														xmlns="http://www.w3.org/2000/svg"
														fill="none"
														viewBox="0 0 24 24"
														stroke-width="2.3"
														stroke="currentColor"
														class="w-4 h-4"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125"
														/>
													</svg>
												</button>
											</Tooltip>
										{/if}

										<Tooltip content={$i18n.t('Copy')} placement="bottom">
											<button
												class="{isLastMessage
													? 'visible'
													: 'invisible group-hover:visible'} p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition copy-response-button"
												on:click={() => {
													copyToClipboardWithToast(message.content);
												}}
											>
												<svg
													xmlns="http://www.w3.org/2000/svg"
													fill="none"
													viewBox="0 0 24 24"
													stroke-width="2.3"
													stroke="currentColor"
													class="w-4 h-4"
												>
													<path
														stroke-linecap="round"
														stroke-linejoin="round"
														d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184"
													/>
												</svg>
											</button>
										</Tooltip>

										<Tooltip content={$i18n.t('Read Aloud')} placement="bottom">
											<button
												id="speak-button-{message.id}"
												class="{isLastMessage
													? 'visible'
													: 'invisible group-hover:visible'} p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition"
												on:click={() => {
													if (!loadingSpeech) {
														toggleSpeakMessage(message.content);
													}
												}}
											>
												{#if loadingSpeech}
													<svg
														class=" w-4 h-4"
														fill="currentColor"
														viewBox="0 0 24 24"
														xmlns="http://www.w3.org/2000/svg"
														><style>
															.spinner_S1WN {
																animation: spinner_MGfb 0.8s linear infinite;
																animation-delay: -0.8s;
															}
															.spinner_Km9P {
																animation-delay: -0.65s;
															}
															.spinner_JApP {
																animation-delay: -0.5s;
															}
															@keyframes spinner_MGfb {
																93.75%,
																100% {
																	opacity: 0.2;
																}
															}
														</style><circle class="spinner_S1WN" cx="4" cy="12" r="3" /><circle
															class="spinner_S1WN spinner_Km9P"
															cx="12"
															cy="12"
															r="3"
														/><circle class="spinner_S1WN spinner_JApP" cx="20" cy="12" r="3" /></svg
													>
												{:else if speaking}
													<svg
														xmlns="http://www.w3.org/2000/svg"
														fill="none"
														viewBox="0 0 24 24"
														stroke-width="2.3"
														stroke="currentColor"
														class="w-4 h-4"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															d="M17.25 9.75 19.5 12m0 0 2.25 2.25M19.5 12l2.25-2.25M19.5 12l-2.25 2.25m-10.5-6 4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z"
														/>
													</svg>
												{:else}
													<svg
														xmlns="http://www.w3.org/2000/svg"
														fill="none"
														viewBox="0 0 24 24"
														stroke-width="2.3"
														stroke="currentColor"
														class="w-4 h-4"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"
														/>
													</svg>
												{/if}
											</button>
										</Tooltip>

										{#key message.info}
											{#if message.info}
												<Tooltip content={$i18n.t('Generation Info')} placement="bottom">
													<button
														class=" {isLastMessage
															? 'visible'
															: 'invisible group-hover:visible'} p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition whitespace-pre-wrap"
														on:click={() => {
															console.log(message);
														}}
														id="info-{message.id}"
													>
														<svg
															xmlns="http://www.w3.org/2000/svg"
															fill="none"
															viewBox="0 0 24 24"
															stroke-width="2.3"
															stroke="currentColor"
															class="w-4 h-4"
														>
															<path
																stroke-linecap="round"
																stroke-linejoin="round"
																d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
															/>
														</svg>
													</button>
												</Tooltip>
											{/if}
										{/key}
										{#if isLastMessage}
											<Tooltip content={$i18n.t('Continue Response')} placement="bottom">
												<button
													type="button"
													class="{isLastMessage
														? 'visible'
														: 'invisible group-hover:visible'} p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition regenerate-response-button"
													on:click={() => {
														continueGeneration(message.id);
													}}
												>
													<svg
														xmlns="http://www.w3.org/2000/svg"
														viewBox="0 0 24 24"
														fill="none"
														class="w-4 h-4"
														stroke="currentColor"
													>
														<path
															fill-rule="evenodd"
															d="M15.97 2.47a.75.75 0 0 1 1.06 0l4.5 4.5a.75.75 0 0 1 0 1.06l-4.5 4.5a.75.75 0 1 1-1.06-1.06l3.22-3.22H7.5a.75.75 0 0 1 0-1.5h11.69l-3.22-3.22a.75.75 0 0 1 0-1.06Zm-7.94 9a.75.75 0 0 1 0 1.06l-3.22 3.22H16.5a.75.75 0 0 1 0 1.5H4.81l3.22 3.22a.75.75 0 1 1-1.06 1.06l-4.5-4.5a.75.75 0 0 1 0-1.06l4.5-4.5a.75.75 0 0 1 1.06 0Z"
															clip-rule="evenodd"
														/>
													</svg>
												</button>
											</Tooltip>
											{#if !readOnly}
												<Tooltip content={$i18n.t('Regenerate')} placement="bottom">
													<button
														type="button"
														class="{isLastMessage
															? 'visible'
															: 'invisible group-hover:visible'} p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition regenerate-response-button"
														on:click={async () => {
															show = false;
															await regenerateResponse(message);
														}}
													>
														<svg
															xmlns="http://www.w3.org/2000/svg"
															fill="none"
															viewBox="0 0 24 24"
															stroke-width="2.3"
															stroke="currentColor"
															class="w-4 h-4"
														>
															<path
																stroke-linecap="round"
																stroke-linejoin="round"
																d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
															/>
														</svg>
													</button>
												</Tooltip>
											{/if}

											<!-- {#each model?.actions ?? [] as action}
													<Tooltip content={action.name} placement="bottom">
														<button
															type="button"
															class="{isLastMessage
																? 'visible'
																: 'invisible group-hover:visible'} p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition regenerate-response-button"
															on:click={() => {
																dispatch('action', action.id);
															}}
														>
															{#if action.icon_url}
																<img
																	src={action.icon_url}
																	class="w-4 h-4 {action.icon_url.includes('svg') ? 'dark:invert-[80%]' : ''}"
																	style="fill: currentColor;"
																	alt={action.name}
																/>
															{:else}
																<Sparkles strokeWidth="2.1" className="size-4" />
															{/if}
														</button>
													</Tooltip>
												{/each} -->
										{/if}
									</div>
								</div>
								{#if message.sources && message.sources.length > 0}
									<details
										class="sources bg-slate-100 rounded-lg p-4 mt-4 cursor-pointer"
										on:toggle={(e) => {
											let icon = document.querySelector('.square-code-icon');
											if (e.currentTarget.open) {
												icon?.classList.add('rotate');
											} else {
												icon?.classList.remove('rotate');
											}
										}}
									>
										<summary
											id="source-summary"
											class="flex flex-row items-center justify-start space-x-3 transition-transform"
										>
											<h4 class="font-bold">Sources</h4>
											<SquareCode
												class="square-code-icon w-6 h-6 transition-transform"
												stroke="currentColor"
											/></summary
										>
										<h3 class="mb-2">How did we use AI and Cisco experts to provide this answer?</h3>
										<div class="flex flex-col space-y-3 items-start mt-2">
											<div class="flex flex-col gap-y-2 divide-slate-300" id="sourcescontentcontainer">
												<p>
													We search our content database for similar text to the question and context. We then use small
													chunks of the broader text to summarize or pick and choose which chunks are relevant. In the
													end Generative AI uses the chunks to arrive at the answer. The answer produced is then
													reviewed for accuracy and relevancy by Cisco experts.
												</p>
												<div class="space-y-2">
													<a
														target="_blank"
														href="https://www.cisco.com/site/us/en/solutions/artificial-intelligence/responsible-ai/index.html"
														class="text-blue-500">Cisco's Responsible AI Framework</a
													>
													<a
														target="_blank"
														href="https://www.cisco.com/c/en/us/about/legal/privacy-full.html"
														class="text-blue-500">Privacy Policy</a
													>
												</div>
												<svg
													xmlns="http://www.w3.org/2000/svg"
													id="a"
													style="width: 6em; height: auto; fill: transparent; transform: rotate(90deg);"
													viewBox="0 0 80 80"
													class="self-center"
													stroke="currentColor"
													><path
														d="M16.61133,38.93262c-.27466,.25714-.5332,.52881-.7771,.81171-.11157,.12817-.20752,.26715-.3125,.40009-.12402,.15875-.25244,.31415-.36719,.47931-.151,.21576-.28516,.44122-.41943,.66736-.05408,.09192-.11157,.18158-.16284,.27496-.13379,.24207-.25354,.49048-.36768,.74261-.04102,.09052-.08179,.18054-.12036,.27216-.104,.24835-.19873,.49982-.28357,.75641-.0387,.11603-.07263,.23315-.1073,.35052-.06885,.23553-.13501,.47119-.1875,.7124-.03955,.17798-.06665,.35828-.09692,.53839-.03137,.19092-.0686,.37964-.08972,.5733-.04333,.38721-.06921,.77722-.06921,1.1698,0,.32526,.01978,.64679,.04895,.96619,.00916,.10132,.02209,.20129,.03406,.30176,.0271,.22467,.06128,.44714,.10229,.66791,.01904,.10303,.0365,.20636,.05859,.30835,.06384,.29456,.1366,.5863,.22473,.87231,.02234,.07269,.0509,.1424,.07471,.21442,.07385,.22235,.15344,.44214,.24133,.65826,.04419,.10822,.09131,.21442,.13879,.32086,.08362,.18738,.17297,.37158,.26697,.55347,.04834,.09326,.0946,.18732,.14563,.27899,.14526,.26129,.29895,.51752,.46545,.76532,.02832,.04199,.05994,.08118,.08875,.12274,.14734,.21265,.30225,.41962,.46472,.62103,.06042,.07489,.12292,.14764,.1853,.22089,.14478,.16974,.2948,.33453,.45007,.49506,.06409,.06628,.12659,.13361,.19238,.19818,.21448,.21051,.43542,.41479,.66785,.60712,.04321,.03571,.0896,.0672,.1333,.10223,.18884,.15112,.3822,.29681,.58179,.43536,.1123,.07825,.22803,.15137,.34326,.22528,.13232,.08423,.26587,.16602,.40234,.24469,.14136,.08191,.28296,.16223,.42822,.23773,.09985,.05164,.20288,.09833,.30469,.14697,.16113,.07733,.31934,.15961,.48486,.22894-.10986,.55402-.16528,1.11041-.16528,1.66052,0,4.7998,3.90479,8.70459,8.70459,8.70459,.21777,0,.44629-.01398,.68494-.03473,.13367-.0105,.26624-.02362,.39832-.0401l.02319-.00232-.00024-.00122c.13745-.01752,.27344-.03864,.40869-.0625,1.06604,2.44189,3.45508,4.05005,6.16675,4.05005,3.72217,0,6.75-3.02783,6.75-6.75v-7.25h11.43945l-2.71973,2.71973,1.06055,1.06055,4-4c.29297-.29297,.29297-.76758,0-1.06055l-4-4-1.06055,1.06055,2.71973,2.71973h-11.43945v-14.5h21.43945l-2.71973,2.71973,1.06055,1.06055,4-4c.29297-.29297,.29297-.76758,0-1.06055l-4-4-1.06055,1.06055,2.71973,2.71973h-21.43945v-14.5h11.43945l-2.71973,2.71973,1.06055,1.06055,4-4c.29297-.29297,.29297-.76758,0-1.06055l-4-4-1.06055,1.06055,2.71973,2.71973h-11.43945v-7.25c0-3.72217-3.02783-6.75-6.75-6.75-2.9043,0-5.49072,1.89844-6.40137,4.60449-.08472-.01038-.1709-.00806-.2561-.01575l.00073-.00818c-.23291-.021-.46777-.03516-.70703-.03516-4.27344,0-7.75,3.47656-7.75,7.75,0,1.02148,.20508,2.03564,.59814,2.97852-.01062,.00391-.0199,.01001-.03052,.01398-.40881,.1535-.80542,.33105-1.18262,.54169l-.01965,.01202c-.33875,.19031-.66003,.40631-.96887,.63873-.06201,.04657-.125,.09106-.18579,.13916-.29297,.23279-.57092,.48254-.83142,.75043-.06531,.06708-.12512,.138-.18835,.20715-.21143,.23175-.41028,.47406-.59595,.7276-.04968,.06781-.10303,.13214-.15063,.20135-.20947,.30377-.39648,.62305-.56653,.95294-.04407,.08551-.08386,.17236-.12512,.2594-.15015,.31659-.28467,.64136-.39648,.97742-.01245,.03796-.02905,.07391-.04102,.11212-.11694,.36871-.20251,.75018-.26965,1.13824-.01599,.09198-.02942,.18396-.04236,.27686-.05542,.39612-.09399,.79749-.09399,1.20862,0,.36279,.02979,.72089,.07373,1.07587,.0083,.06671,.01526,.13312,.02515,.19958,.05078,.34564,.12085,.6864,.2124,1.021,.01514,.05573,.03369,.11011,.04993,.16547,.09351,.31708,.20276,.62866,.33191,.93256,.01501,.03546,.02686,.07184,.04248,.10706,.1355,.3075,.29395,.60455,.46533,.89532,.02588,.04419,.04382,.0921,.07056,.13586l.00854-.00525c.18225,.29736,.37646,.58844,.59546,.86462-.37329,.2674-.72217,.55884-1.05298,.86597l-.00659-.00708Zm.61816,1.51617c.0592-.06274,.1189-.125,.18018-.18634,.52661-.52484,1.11841-.99615,1.77881-1.39233,.19678-.11768,.32861-.31885,.35791-.54639,.02979-.22705-.04639-.45557-.20605-.61963-.42456-.43622-.78052-.92053-1.07764-1.43463-.10669-.18506-.20544-.3739-.29468-.56696-.03394-.07288-.07031-.14459-.10156-.21857-.11182-.26471-.20947-.53491-.28857-.81091-.01501-.052-.02515-.10541-.03882-.15778-.06226-.23651-.11182-.47626-.14954-.71851-.01196-.0766-.02405-.15308-.03357-.23022-.03613-.29272-.06055-.58759-.06055-.88489,0-.37201,.03711-.73627,.09229-1.09503,.01001-.06494,.01807-.13037,.02979-.1947,.06213-.34161,.14819-.67548,.25732-.99988,.021-.06244,.04517-.12335,.06775-.18506,.12085-.32935,.25793-.65155,.42419-.95746,.00708-.01312,.01599-.02515,.02319-.03815,.16211-.29395,.34961-.57196,.55054-.83978,.04187-.05573,.08179-.11285,.12524-.1673,.20776-.26086,.43408-.50677,.67676-.73694,.04773-.04541,.09717-.08887,.14624-.133,.26343-.23645,.53967-.46008,.83765-.65668l.00732-.00439c.65771-.4328,1.39465-.76343,2.19189-.96576l.00098-.00055c.5686-.14471,1.16052-.22992,1.77344-.22992,2.22119,0,4.28467,1.00195,5.66162,2.74854l1.17773-.92871c-1.66309-2.10986-4.15576-3.31982-6.83936-3.31982-.52698,0-1.04053,.05487-1.54199,.14502-.36853-.81012-.57178-1.68781-.57178-2.57666,0-3.44629,2.80371-6.25,6.25-6.25,.45361,0,.90527,.04834,1.34326,.14453,.40527,.09033,.80469-.16797,.89258-.57178,.52441-2.38623,2.68066-4.11816,5.12793-4.11816,2.89502,0,5.25,2.35498,5.25,5.25v23.25h-6.93311c-3.23145,0-6.14551-1.91748-7.42334-4.88574l-1.37793,.59375c1.51562,3.51855,4.97021,5.79199,8.80127,5.79199h6.93311v23.25c0,2.89502-2.35498,5.25-5.25,5.25-2.03345,0-3.84058-1.15833-4.71094-2.94232,3.33911-1.21808,5.73389-4.41608,5.73389-8.17145h-1.5c0,3.66162-2.7478,6.68738-6.28857,7.13971v-.00055c-.30078,.03857-.60498,.06543-.91602,.06543-3.97266,0-7.20459-3.23193-7.20459-7.20459,0-.39197,.04602-.78845,.11414-1.18555,.8446,.21704,1.72449,.34473,2.63586,.34473,1.43262,0,2.82227-.28076,4.13135-.83398l-.58398-1.38184c-1.12305,.4751-2.31689,.71582-3.54736,.71582-1.05908,0-2.07227-.19092-3.01855-.5246-.5896-.20721-1.14514-.47382-1.66675-.78656-.09058-.05469-.18262-.10736-.27136-.16504-.1156-.07495-.22717-.15479-.33875-.23456-.11243-.08069-.22363-.16296-.33215-.24854-.09436-.07416-.18787-.14917-.27893-.22681-.12842-.10956-.25232-.22394-.37439-.34033-.06775-.06451-.13806-.12689-.20374-.19342-.1814-.18396-.35571-.37463-.52112-.5733-.04529-.05438-.08594-.11243-.12988-.16785-.12085-.15222-.2384-.30713-.34949-.46698-.05908-.08533-.11499-.17285-.17126-.26013-.08899-.13782-.17444-.27814-.25598-.42096-.0542-.09491-.10815-.19-.15894-.28687-.08057-.15363-.15479-.31104-.22668-.46967-.03906-.08618-.08179-.17047-.11829-.258-.0979-.23529-.18591-.47571-.26416-.72046-.02905-.0907-.05164-.1839-.07788-.2757-.04907-.17175-.09521-.3446-.13403-.52032-.02295-.10291-.04285-.20673-.06226-.31067-.03345-.18042-.06104-.36279-.08362-.54675-.01135-.09229-.02454-.1842-.03308-.27722-.02539-.27667-.04248-.55585-.04248-.83905,0-.36975,.02759-.73419,.07031-1.09454,.01221-.10205,.03113-.20227,.04663-.30341,.04053-.26489,.09058-.52692,.15369-.78479,.0249-.10229,.05103-.20416,.07947-.3053,.07715-.27344,.16748-.54181,.26953-.8053,.02686-.06964,.04968-.14093,.07837-.20984,.27722-.66626,.63501-1.29486,1.06384-1.87653,.05383-.07306,.11267-.14307,.16882-.21472,.17297-.22015,.35498-.4339,.54883-.63843Z"
													/><path
														d="M35.99121,46.75879v-1.5c-3.71729,0-6.74121,3.02393-6.74121,6.74121h1.5c0-2.89014,2.35107-5.24121,5.24121-5.24121Z"
													/><path
														d="M26.75195,42.01074h-1.5c0,2.896-2.35596,5.25195-5.25195,5.25195v1.5c3.72314,0,6.75195-3.02881,6.75195-6.75195Z"
													/><path
														d="M38.75098,15.98145h-1.5c0,2.89551-2.35547,5.25098-5.25098,5.25098v1.5c3.72266,0,6.75098-3.02832,6.75098-6.75098Z"
													/></svg
												>
											</div>
											<hr class="bg-slate-300 w-full" />
											{#each message.sources as source, i (i)}
												{#if source.doc_type === 'AdminGuide'}
													<div
														class="admin-guide flex flex-col gap-y-2 border-l-4 border-green-500 bg-gray-50 px-2 py-2 rounded-md w-full divide-slate-700"
													>
														<div class="flex flex-row items-center gap-2">
															<div>
																<FileText />
															</div>
															<div>
																<ul class="py-2">
																	<li class="ml-2">Type: {source.doc_type}</li>
																	<li class="ml-2">Chapter: {source.title}</li>
																	<li class="ml-2">Topic: {source.topic}</li>
																</ul>
															</div>
														</div>
														<div>
															<a
																class="hover:underline dark:text-gray-200 text-blue-600 p-2"
																href={source.source}
																target="_blank">View {source.concept} Admin Guide</a
															>
														</div>
													</div>
												{:else if source.doc_type === 'CLIGuide'}
													<div
														class="cli-guide flex flex-col gap-y-2 border-l-4 border-indigo-500 bg-gray-50 px-2 py-2 rounded-md w-full"
													>
														<div class="flex flex-row items-center gap-2">
															<div>
																<FileCode />
															</div>
															<div>
																<ul class="py-2">
																	<li class="ml-2">Type: {source.doc_type}</li>
																	<li class="ml-2">Chapter: {source.title}</li>
																	<li class="ml-2">Topic: {source.topic}</li>
																</ul>
															</div>
														</div>
														<div>
															<a
																class="hover:underline dark:text-gray-200 text-blue-600 p-2"
																href={source.source}
																target="_blank">View {source.concept} CLI Guide</a
															>
														</div>
													</div>
												{/if}
											{/each}
										</div>
									</details>
								{/if}
								<div
									class="flex flex-col justify-center items-end mt-2 gap-2"
									in:fade={{ duration: 1000, easing: cubicIn }}
								>
									<h4 class="my-2">Helpful?</h4>
									<div class="flex flex-row items-center space-x-3">
										<button
											on:click={async () => {
												await rateMessage(message.id, 1);
												activeSupportStep.set(index + 1);
												await tick();
												if (message.associatedQuestion) {
													currentQuestion = message.associatedQuestion;
												}
												show = true;
												window.setTimeout(() => {
													document.getElementById(`message-feedback-${message.id}`)?.scrollIntoView();
												}, 0);
											}}
											class="flex items-center rounded-md py-2 px-3 text-center bg-blue-500"
										>
											<ThumbsUp style="color:white;" />
										</button>
										<button
											on:click={async () => {
												await rateMessage(message.id, -1);
												activeSupportStep.set(index + 1);
												await tick();
												if (message.associatedQuestion) {
													currentQuestion = message.associatedQuestion;
												}
												show = true;
												window.setTimeout(() => {
													document.getElementById(`message-feedback-${message.id}`)?.scrollIntoView();
												}, 0);
											}}
											class="flex items-center rounded-md py-2 px-3 text-center bg-blue-500 text-white"
										>
											<ThumbsDown />
										</button>
									</div>
								</div>
							{/if}
							{#if !message.done}
								<div class="relative flex justify-end w-full">
									<div class="absolute bottom-0 right-0 flex items-center mb-1.5">
										<button
											class="bg-white hover:bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-white dark:hover:bg-gray-800 transition rounded-full p-1.5"
											on:click={() => {
												stopResponse();
											}}
										>
											<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-6">
												<path
													fill-rule="evenodd"
													d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm6-2.438c0-.724.588-1.312 1.313-1.312h4.874c.725 0 1.313.588 1.313 1.313v4.874c0 .725-.588 1.313-1.313 1.313H9.564a1.312 1.312 0 01-1.313-1.313V9.564z"
													clip-rule="evenodd"
												/>
											</svg>
										</button>
									</div>
								</div>
							{/if}
						</div>
						<Feedback
							messageId={message.id}
							{message}
							bind:show
							btnText={currentQuestion}
							on:submit={async () => {
								await sendUpdateArticle(message);
							}}
						/>
					{/if}
				{/if}
			{/key}
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
	<div class="genericSupportButtons s-5e5kg2sOboz_">
		<details class="custom-details p-4" id="detailsFaqlike" style="border:#d2d2d2 1px solid; margin:0;" open>
			<summary class="s-5e5kg2sOboz_" />
			<div class="buttonWell">
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

<style>
	details:not(.detailsGetSupport):not(.custom-details):not(.sources) {
		color: #333;
		padding: 1em;
		border: #d2d2d2 1px solid;
		-webkit-transition: all 0.25s ease-in;
		-o-transition: all 0.25s ease-in;
		transition: all 0.25s ease-in;
		margin: 1em 0;
		border-radius: 0 16px 16px 0;
		position: relative;
		background-color: var(--menu-background-gray);
		max-width: 1100px;
		cursor: pointer;
	}

	/* Rotate animation for the SquareCode icon */
	.rotate {
		transform: rotateY(360deg);
		transition: transform 0.5s ease;
	}

	.custom-details {
		border: 1px solid #d2d2d2;
		border-radius: 5px;
		transition: all 0.25s ease-in;
		background: white;
		width: 100%;
	}

	details[open] > summary {
		margin-bottom: 1em;
	}

	.detailsGetSupport {
		border-radius: 16px;
		/* background-color: white;
		background-image: radial-gradient(
				75.83% 78.18% at 51.72% 100%,
				rgba(56, 96, 190, 0.03) 0%,
				rgba(100, 187, 227, 0.03) 65.24%,
				rgba(223, 223, 223, 0) 100%
			),
			conic-gradient(from 180deg at 50% 50%, rgba(56, 96, 190, 0) 0deg, rgba(56, 96, 190, 0.02) 360deg); */
		/* margin-left: 10px; */
		transition: all 0.3s ease-in-out;
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.07), 0 4px 8px rgba(0, 0, 0, 0.07),
			0 8px 16px rgba(0, 0, 0, 0.07), 0 16px 32px rgba(0, 0, 0, 0.07), 0 32px 64px rgba(0, 0, 0, 0.07);
	}

	.detailsGetSupport:hover {
		box-shadow: 0px 4px 20px rgb(0 0 0 / 15%);
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

	.genericSupportButtons {
		display: flex;
		align-items: flex-start;
		gap: 1em;
		justify-content: space-evenly;
	}

	.buttonWell {
		display: flex;
		align-items: center;
		flex-direction: row;
		justify-content: space-evenly;
		flex-wrap: wrap;
		gap: 1em;
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

	.button:hover {
		background-color: rgba(155, 215, 255, 0.5);
		color: #2b5592;
		border: #2b5592 1px solid;
		box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
	}

	.button.clicked {
		color: rgb(136, 136, 136);
		border: 1px solid rgb(136, 136, 136);
	}

	.question.user {
		background: rgba(155, 215, 255, 0.5);
		color: #2b5592 !important;
	}
</style>
