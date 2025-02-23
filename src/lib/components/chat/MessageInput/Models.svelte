<script lang="ts">
	import type { Message, i18nType } from '$lib/types';
	import { createEventDispatcher } from 'svelte';
	import { getContext, tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { generatePrompt } from '$lib/apis/ollama';
	import type { Model, SessionUser } from '$lib/stores';
	import { models } from '$lib/stores';
	import { splitStream } from '$lib/utils';
	import { isErrorWithDetail, isErrorWithError } from '$lib/utils';

	const i18n: i18nType = getContext('i18n');

	const dispatch = createEventDispatcher();

	export let prompt = '';
	export let user: SessionUser | null = null;

	export let chatInputPlaceholder = '';
	export let messages: Message[] = [];

	let selectedIdx = 0;
	let filteredModels: Model[] = [];

	$: filteredModels = $models
		.filter((p) => p.name.toLowerCase().includes(prompt.toLowerCase().split(' ')?.at(0)?.substring(1) ?? ''))
		.sort((a, b) => a.name.localeCompare(b.name));

	$: if (prompt) {
		selectedIdx = 0;
	}

	export const selectUp = () => {
		selectedIdx = Math.max(0, selectedIdx - 1);
	};

	export const selectDown = () => {
		selectedIdx = Math.min(selectedIdx + 1, filteredModels.length - 1);
	};

	const confirmSelect = async (model: Model) => {
		prompt = '';
		dispatch('select', model);
	};

	const confirmSelectCollaborativeChat = async (model: Model) => {
		// dispatch('select', model);
		prompt = '';
		user = JSON.parse(JSON.stringify(model.name));
		await tick();

		chatInputPlaceholder = $i18n.t('{{modelName}} is thinking...', { modelName: model.name });

		const chatInputElement = document.getElementById('chat-textarea') as HTMLTextAreaElement;

		await tick();
		chatInputElement?.focus();
		await tick();

		const convoText = messages.reduce((a, message, i, arr) => {
			return `${a}### ${message.role.toUpperCase()}\n${message.content}\n\n`;
		}, '');

		const res = await generatePrompt(localStorage.token, model.name, convoText);

		if (res && res.ok && res.body) {
			const reader = res.body.pipeThrough(new TextDecoderStream()).pipeThrough(splitStream('\n')).getReader();

			while (true) {
				const { value, done } = await reader.read();
				if (done) {
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

							if ('id' in data) {
								console.log(data);
							} else {
								if (data.done == false) {
									if (prompt == '' && data.response == '\n') {
										continue;
									} else {
										prompt += data.response;
										console.log(data.response);
										chatInputElement.scrollTop = chatInputElement.scrollHeight;
										await tick();
									}
								}
							}
						}
					}
				} catch (error) {
					console.log(error);
					if (isErrorWithDetail(error)) {
						toast.error(error.detail);
					} else if (isErrorWithError(error)) {
						toast.error(error.error);
					} else {
						toast.error(error as string);
					}
					break;
				}
			}
		} else {
			if (res !== null) {
				const error = await res.json();
				console.log(error);
				if (isErrorWithDetail(error)) {
					toast.error(error.detail);
				} else if (isErrorWithError(error)) {
					toast.error(error.error);
				} else {
					toast.error(error as string);
				}
			} else {
				toast.error($i18n.t('Uh-oh! There was an issue connecting to {{provider}}.', { provider: 'llama' }));
			}
		}

		chatInputPlaceholder = '';

		console.log(user);
	};
</script>

{#if prompt.charAt(0) === '@'}
	{#if filteredModels.length > 0}
		<div class="pl-1 pr-12 mb-3 text-left w-full absolute bottom-0 left-0 right-0 z-10">
			<div class="flex w-full dark:border dark:border-gray-850 rounded-lg">
				<div class=" bg-gray-50 dark:bg-gray-850 w-10 rounded-l-lg text-center">
					<div class=" text-lg font-semibold mt-2">@</div>
				</div>

				<div class="max-h-60 flex flex-col w-full rounded-r-lg bg-white dark:bg-gray-900 dark:text-gray-100">
					<div class="m-1 overflow-y-auto p-1 rounded-r-lg space-y-0.5 scrollbar-hidden">
						{#each filteredModels as model, modelIdx}
							<button
								class=" px-3 py-1.5 rounded-xl w-full text-left {modelIdx === selectedIdx
									? '  bg-gray-50 dark:bg-gray-850  selected-command-option-button'
									: ''}"
								type="button"
								on:click={() => {
									confirmSelect(model);
								}}
								on:mousemove={() => {
									selectedIdx = modelIdx;
								}}
								on:focus={() => {}}
							>
								<div class=" font-medium text-black dark:text-gray-100 line-clamp-1">
									{model.name}
								</div>

								<!-- <div class=" text-xs text-gray-600 line-clamp-1">
								{doc.title}
							</div> -->
							</button>
						{/each}
					</div>
				</div>
			</div>
		</div>
	{/if}
{/if}
