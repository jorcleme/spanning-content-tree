<script lang="ts">
	import type { Message } from '$lib/types';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { getContext } from 'svelte';
	import { models, settings, config } from '$lib/stores';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { toast } from 'svelte-sonner';
	import dayjs from 'dayjs';
	import { synthesizeOpenAISpeech } from '$lib/apis/audio';
	import { extractSentences } from '$lib/utils';
	import Select from '$lib/components/cisco/components/common/Select.svelte';
	import Name from './Name.svelte';
	import ProfileImage from './ProfileImage.svelte';
	import Image from '$lib/components/common/Image.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	const i18n: Writable<i18nType> = getContext('i18n');

	export let message: Message;
	export let siblings;
	export let isLastMessage = true;
	export let handleDeviceConfirm: (e: CustomEvent) => void;

	interface Device {
		[key: string]: string;
	}
	const devices: Device[] = [
		{ label: 'Catalyst 1200', value: 'Cisco Catalyst 1200 Series Switches', category: 'Switches' },
		{ label: 'Catalyst 1300', value: 'Cisco Catalyst 1300 Series Switches', category: 'Switches' },
		{ label: 'CBS110 Series', value: 'Cisco Business 110 Series Unmanaged Switches', category: 'Switches' },
		{ label: 'CBS220 Series', value: 'Cisco Business 220 Series Smart Switches', category: 'Switches' },
		{ label: 'CBS250 Series', value: 'Cisco Business 250 Series Smart Switches', category: 'Switches' },
		{ label: 'CBS350 Series', value: 'Cisco Business 350 Series Managed Switches', category: 'Switches' },
		{ label: '350 Series', value: 'Cisco 350 Series Managed Switches', category: 'Switches' },
		{ label: '350X Series', value: 'Cisco 350X Series Stackable Managed Switches', category: 'Switches' },
		{ label: '550X Series', value: 'Cisco 550X Series Stackable Managed Switches', category: 'Switches' },
		{ label: 'RV100 Series', value: 'RV100 Product Family', category: 'Routers' },
		{ label: 'RV320 Series', value: 'RV320 Product Family', category: 'Routers' },
		{ label: 'RV340 Series', value: 'RV340 Product Family', category: 'Routers' },
		{ label: 'RV160 VPN Series', value: 'RV160 VPN Router', category: 'Routers' },
		{ label: 'RV260 VPN Series', value: 'RV260 VPN Router', category: 'Routers' },
		{ label: 'CBW-AC', value: 'Cisco Business Wireless AC', category: 'Wireless' },
		{ label: 'CBW-AX', value: 'Cisco Business Wireless AX', category: 'Wireless' }
	];

	let model = null;
	$: model = $models.find((m) => m.id === message.model);

	let listOpen = false;
	let sentencesAudio: { [key: number]: HTMLAudioElement | null } = {};
	let speaking: boolean | null = null;
	let speakingIdx: number | null = null;
	let loadingSpeech = false;

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

	const toggleSpeakMessage = async () => {
		if (speaking && speakingIdx) {
			try {
				speechSynthesis.cancel();
				sentencesAudio[speakingIdx]?.pause();
				sentencesAudio[speakingIdx]!.currentTime = 0;
			} catch {}

			speaking = null;
			speakingIdx = null;
		} else {
			if ((message?.content ?? '').trim() !== '') {
				speaking = true;

				if ($config?.audio?.tts?.engine === 'openai') {
					loadingSpeech = true;

					const sentences = extractSentences(message.content).reduce((mergedTexts, currentText) => {
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
						voices = await speechSynthesis.getVoices();
						if (voices.length > 0) {
							clearInterval(getVoicesLoop);

							const voice =
								voices
									?.filter((v) => v.voiceURI === ($settings?.audio?.tts?.voice ?? $config?.audio?.tts?.voice))
									?.at(0) ?? undefined;

							console.log(voice);

							const speak = new SpeechSynthesisUtterance(message.content);

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

	const onToggleSelect = (e: CustomEvent<{ state: boolean }>) => {
		listOpen = e.detail.state;
	};
</script>

{#key message.id}
	<div class=" flex w-full message-{message.id}" id="message-{message.id}" dir={$settings.chatDirection}>
		<ProfileImage
			src={model?.info?.meta?.profile_image_url ??
				($i18n.language === 'dg-DG' ? `/doge.png` : `${WEBUI_BASE_URL}/static/favicon.png`)}
		/>

		<div class="w-full overflow-hidden pl-1">
			<Name>
				{model?.name ?? message.model}

				{#if message.timestamp}
					<span class=" self-center invisible group-hover:visible text-gray-400 text-xs font-medium uppercase">
						{dayjs(message.timestamp * 1000).format($i18n.t('h:mm a'))}
					</span>
				{/if}
			</Name>
			{#if message.files}
				{#if (message.files ?? []).filter((f) => f.type === 'image').length > 0}
					{#each message.files as file}
						<div>
							{#if file.type === 'image'}
								<Image src={file.url} />
							{/if}
						</div>
					{/each}
				{/if}
			{/if}

			<div class="prose chat-{message.role} w-full max-w-full dark:prose-invert {listOpen ? 'min-h-[14rem]' : ''}">
				<div>
					<div class="w-full">
						<div class="flex flex-col">
							<Select items={devices} on:confirm={handleDeviceConfirm} on:toggle={onToggleSelect} />
						</div>

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

						{#if message.done || siblings.length > 1}
							<div class=" flex justify-start overflow-x-auto buttons text-gray-600 dark:text-gray-500">
								{#if message.done}
									<Tooltip content={$i18n.t('Read Aloud')} placement="bottom">
										<button
											id="speak-button-{message.id}"
											class="{isLastMessage
												? 'visible'
												: 'invisible group-hover:visible'} p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition"
											on:click={() => {
												if (!loadingSpeech) {
													toggleSpeakMessage();
												}
											}}
										>
											{#if loadingSpeech}
												<svg class=" w-4 h-4" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"
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
								{/if}
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	</div>
{/key}
