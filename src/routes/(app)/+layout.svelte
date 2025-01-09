<script lang="ts">
	import type { i18nType } from '$lib/types';
	import { getContext, onMount, tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { getModels as _getModels } from '$lib/apis';
	import { getAllChatTags } from '$lib/apis/chats';
	import { getBanners } from '$lib/apis/configs';
	import { getDocs } from '$lib/apis/documents';
	import { getFunctions } from '$lib/apis/functions';
	import { getPrompts } from '$lib/apis/prompts';
	import { getTools } from '$lib/apis/tools';
	import { getUserSettings } from '$lib/apis/users';
	import {
		type Model,
		banners,
		config,
		documents,
		functions,
		models,
		prompts,
		settings,
		showCallOverlay,
		showChangelog,
		showSettings,
		tags,
		tools,
		user
	} from '$lib/stores';
	import fileSaver from 'file-saver';
	import { deleteDB, openDB } from 'idb';
	import type { IDBPDatabase } from 'idb';
	import ChangelogModal from '$lib/components/ChangelogModal.svelte';
	import SettingsModal from '$lib/components/chat/SettingsModal.svelte';
	import AccountPending from '$lib/components/layout/Overlay/AccountPending.svelte';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';

	const { saveAs } = fileSaver;

	const i18n: i18nType = getContext('i18n');

	let loaded = false;
	let DB: IDBPDatabase<unknown> | null = null;
	let localDBChats: any[] = [];

	const getModels = async () => {
		return _getModels(localStorage.token);
	};

	const getWebGPUInfo = () => {
		if (!navigator.gpu) {
			return { hasWebGPU: false, message: 'WebGPU not supported' };
		}
		return { hasWebGPU: true, message: 'WebGPU supported' };
	};

	onMount(async () => {
		const webGPUInfo = getWebGPUInfo();
		if ($user === undefined) {
			await goto('/auth');
		} else if (['user', 'admin'].includes($user.role)) {
			try {
				// Check if IndexedDB exists
				DB = (await openDB('Chats', 1)) as IDBPDatabase<unknown>;

				if (DB) {
					const chats = await DB.getAllFromIndex('chats', 'timestamp');
					localDBChats = chats.map((item, idx) => chats[chats.length - 1 - idx]);

					if (localDBChats.length === 0) {
						await deleteDB('Chats');
					}
				}

				console.log(DB);
			} catch (error) {
				// IndexedDB Not Found
			}

			const userSettings = await getUserSettings(localStorage.token).catch((error) => {
				console.error(error);
				return null;
			});

			if (userSettings) {
				settings.set(userSettings.ui);
			} else {
				settings.set(JSON.parse(localStorage.getItem('settings') ?? '{}'));
			}

			await Promise.all([
				(async () => {
					models.set(
						(await getModels()).filter((model) => {
							if (model.owned_by === 'onnx') {
								// Only show text-generation models
								// TODO: add webGPUInfo.hasWebGPU && to the condition to enable adding onnx models only if user has gpu hardware
								if (model.info?.meta?.task === 'text-generation') {
									return true;
								} else {
									// Otherwise, its not a text-generation model
									return false;
								}
							} else {
								// Else get all models
								return true;
							}
						})
					);
				})(),
				(async () => {
					prompts.set(await getPrompts(localStorage.token));
				})(),
				(async () => {
					documents.set(await getDocs(localStorage.token));
					console.log('documents: ', $documents);
				})(),
				(async () => {
					tools.set(await getTools(localStorage.token));
				})(),
				(async () => {
					functions.set(await getFunctions(localStorage.token));
				})(),
				(async () => {
					banners.set(await getBanners(localStorage.token));
				})(),
				(async () => {
					tags.set(await getAllChatTags(localStorage.token));
				})()
			]);

			document.addEventListener('keydown', function (event) {
				const isCtrlPressed = event.ctrlKey || event.metaKey; // metaKey is for Cmd key on Mac
				// Check if the Shift key is pressed
				const isShiftPressed = event.shiftKey;

				// Check if Ctrl + Shift + O is pressed
				if (isCtrlPressed && isShiftPressed && event.key.toLowerCase() === 'o') {
					event.preventDefault();
					console.log('newChat');
					document.getElementById('sidebar-new-chat-button')?.click();
				}

				// Check if Shift + Esc is pressed
				if (isShiftPressed && event.key === 'Escape') {
					event.preventDefault();
					console.log('focusInput');
					document.getElementById('chat-textarea')?.focus();
				}

				// Check if Ctrl + Shift + ; is pressed
				if (isCtrlPressed && isShiftPressed && event.key === ';') {
					event.preventDefault();
					console.log('copyLastCodeBlock');
					const button = [...document.getElementsByClassName('copy-code-button')]?.at(-1) as HTMLButtonElement;
					button?.click();
				}

				// Check if Ctrl + Shift + C is pressed
				if (isCtrlPressed && isShiftPressed && event.key.toLowerCase() === 'c') {
					event.preventDefault();
					console.log('copyLastResponse');
					const button = [...document.getElementsByClassName('copy-response-button')]?.at(-1) as HTMLButtonElement;
					console.log(button);
					button?.click();
				}

				// Check if Ctrl + Shift + S is pressed
				if (isCtrlPressed && isShiftPressed && event.key.toLowerCase() === 's') {
					event.preventDefault();
					console.log('toggleSidebar');
					document.getElementById('sidebar-toggle-button')?.click();
				}

				// Check if Ctrl + Shift + Backspace is pressed
				if (isCtrlPressed && isShiftPressed && event.key === 'Backspace') {
					event.preventDefault();
					console.log('deleteChat');
					document.getElementById('delete-chat-button')?.click();
				}

				// Check if Ctrl + . is pressed
				if (isCtrlPressed && event.key === '.') {
					event.preventDefault();
					console.log('openSettings');
					showSettings.set(!$showSettings);
				}

				// Check if Ctrl + / is pressed
				if (isCtrlPressed && event.key === '/') {
					event.preventDefault();
					console.log('showShortcuts');
					document.getElementById('show-shortcuts-button')?.click();
				}
			});

			if ($user.role === 'admin') {
				showChangelog.set(String(localStorage.version) !== $config?.version);
			}

			await tick();
		}

		loaded = true;
	});
</script>

<SettingsModal bind:show={$showSettings} />
<ChangelogModal bind:show={$showChangelog} />

<div class="app relative">
	<div
		class=" text-gray-700 dark:text-gray-100 bg-white dark:bg-gray-900 h-screen max-h-[100dvh] overflow-auto flex flex-row"
	>
		{#if loaded}
			{#if !['user', 'admin'].includes($user?.role ?? '')}
				<AccountPending />
			{:else if localDBChats.length > 0}
				<div class="fixed w-full h-full flex z-50">
					<div class="absolute w-full h-full backdrop-blur-md bg-white/20 dark:bg-gray-900/50 flex justify-center">
						<div class="m-auto pb-44 flex flex-col justify-center">
							<div class="max-w-md">
								<div class="text-center dark:text-white text-2xl font-medium z-50">
									Important Update<br /> Action Required for Chat Log Storage
								</div>

								<div class=" mt-4 text-center text-sm dark:text-gray-200 w-full">
									{$i18n.t(
										"Saving chat logs directly to your browser's storage is no longer supported. Please take a moment to download and delete your chat logs by clicking the button below. Don't worry, you can easily re-import your chat logs to the backend through"
									)}
									<span class="font-semibold dark:text-white"
										>{$i18n.t('Settings')} > {$i18n.t('Chats')} > {$i18n.t('Import Chats')}</span
									>. {$i18n.t(
										'This ensures that your valuable conversations are securely saved to your backend database. Thank you!'
									)}
								</div>

								<div class=" mt-6 mx-auto relative group w-fit">
									<button
										class="relative z-20 flex px-5 py-2 rounded-full bg-white border border-gray-100 dark:border-none hover:bg-gray-100 transition font-medium text-sm"
										on:click={async () => {
											let blob = new Blob([JSON.stringify(localDBChats)], {
												type: 'application/json'
											});
											saveAs(blob, `chat-export-${Date.now()}.json`);
											if (DB) {
												const tx = DB.transaction('chats', 'readwrite');
												await Promise.all([tx.store.clear(), tx.done]);
												await deleteDB('Chats');

												localDBChats = [];
											}
										}}
									>
										Download & Delete
									</button>

									<button
										class="text-xs text-center w-full mt-2 text-gray-400 underline"
										on:click={async () => {
											localDBChats = [];
										}}>{$i18n.t('Close')}</button
									>
								</div>
							</div>
						</div>
					</div>
				</div>
			{/if}

			<Sidebar />
			<slot />
		{/if}
	</div>
</div>
