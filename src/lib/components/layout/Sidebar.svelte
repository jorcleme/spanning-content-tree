<script lang="ts">
	import type { ChatListResponse, i18nType } from '$lib/types';
	import { getContext, onMount, tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import {
		archiveChatById,
		cloneChatById,
		deleteChatById,
		getAllChatTags,
		getChatById,
		getChatList,
		getChatListByTagName,
		updateChatById
	} from '$lib/apis/chats';
	import { updateUserSettings } from '$lib/apis/users';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import {
		chatId,
		chats,
		mobile,
		pinnedChats,
		settings,
		showArchivedChats,
		showSidebar,
		tags,
		user
	} from '$lib/stores';
	import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import ArchivedChatsModal from './Sidebar/ArchivedChatsModal.svelte';
	import ChatItem from './Sidebar/ChatItem.svelte';
	import UserMenu from './Sidebar/UserMenu.svelte';

	const i18n: i18nType = getContext('i18n');

	const BREAKPOINT = 768;

	let navElement;
	let search = '';

	let shiftKey = false;

	let selectedChatId: string | null = null;
	let deleteChat: { id: string; title: string } | null = null;

	let showDeleteConfirm = false;
	let showDropdown = false;

	let filteredChatList = [];

	$: filteredChatList =
		$chats?.filter((chat) => {
			if (search === '') {
				return true;
			} else {
				let title = chat.title.toLowerCase();
				const query = search.toLowerCase();

				let contentMatches = false;
				// Access the messages within chat.chat.messages
				if (chat.chat && chat.chat.messages && Array.isArray(chat.chat.messages)) {
					contentMatches = chat.chat.messages.some((message) => {
						// Check if message.content exists and includes the search query
						return message.content && message.content.toLowerCase().includes(query);
					});
				}

				return title.includes(query) || contentMatches;
			}
		}) ?? [];
	// @ts-ignore
	onMount(async () => {
		mobile.subscribe((e) => {
			if ($showSidebar && e) {
				showSidebar.set(false);
			}

			if (!$showSidebar && !e) {
				showSidebar.set(true);
			}
		});

		showSidebar.set(window.innerWidth > BREAKPOINT);

		pinnedChats.set((await getChatListByTagName(localStorage.token, 'pinned')) as ChatListResponse);
		chats.set(await getChatList(localStorage.token));

		let touchstart: { screenX: number; clientX: number };
		let touchend: { screenX: number; clientX: number };

		function checkDirection() {
			const screenWidth = window.innerWidth;
			const swipeDistance = Math.abs(touchend.screenX - touchstart.screenX);
			if (touchstart.clientX < 40 && swipeDistance >= screenWidth / 8) {
				if (touchend.screenX < touchstart.screenX) {
					showSidebar.set(false);
				}
				if (touchend.screenX > touchstart.screenX) {
					showSidebar.set(true);
				}
			}
		}

		const onTouchStart = (e: TouchEvent) => {
			touchstart = e.changedTouches[0];
			console.log(touchstart.clientX);
		};

		const onTouchEnd = (e: TouchEvent) => {
			touchend = e.changedTouches[0];
			checkDirection();
		};

		const onKeyDown = (e: KeyboardEvent) => {
			if (e.key === 'Shift') {
				shiftKey = true;
			}
		};

		const onKeyUp = (e: KeyboardEvent) => {
			if (e.key === 'Shift') {
				shiftKey = false;
			}
		};

		const onFocus = () => {};

		const onBlur = () => {
			shiftKey = false;
			selectedChatId = null;
		};

		window.addEventListener('keydown', onKeyDown);
		window.addEventListener('keyup', onKeyUp);

		window.addEventListener('touchstart', onTouchStart);
		window.addEventListener('touchend', onTouchEnd);

		window.addEventListener('focus', onFocus);
		window.addEventListener('blur', onBlur);

		return () => {
			window.removeEventListener('keydown', onKeyDown);
			window.removeEventListener('keyup', onKeyUp);

			window.removeEventListener('touchstart', onTouchStart);
			window.removeEventListener('touchend', onTouchEnd);

			window.removeEventListener('focus', onFocus);
			window.removeEventListener('blur', onBlur);
		};
	});

	// Helper function to fetch and add chat content to each chat
	const enrichChatsWithContent = async (chatList: ChatListResponse) => {
		const enrichedChats = await Promise.all(
			chatList.map(async (chat) => {
				const chatDetails = await getChatById(localStorage.token, chat.id).catch((error) => null); // Handle error or non-existent chat gracefully
				if (chatDetails) {
					chat.chat = chatDetails.chat; // Assuming chatDetails.chat contains the chat content
				}
				return chat;
			})
		);

		chats.set(enrichedChats);
	};

	const saveSettings = async (updated: object) => {
		settings.set({ ...$settings, ...updated });
		await updateUserSettings(localStorage.token, { ui: $settings });
		location.href = '/';
	};

	const deleteChatHandler = async (id: string) => {
		const res = await deleteChatById(localStorage.token, id).catch((error) => {
			toast.error(error);
			return null;
		});

		if (res) {
			if ($chatId === id) {
				chatId.set('');
				await tick();
				goto('/');
			}
			chats.set(await getChatList(localStorage.token));
			pinnedChats.set((await getChatListByTagName(localStorage.token, 'pinned')) as ChatListResponse);
		}
	};
</script>

<ArchivedChatsModal
	bind:show={$showArchivedChats}
	on:change={async () => {
		chats.set(await getChatList(localStorage.token));
	}}
/>

<DeleteConfirmDialog
	bind:show={showDeleteConfirm}
	title={$i18n.t('Delete chat?')}
	on:confirm={() => {
		deleteChatHandler(deleteChat?.id ?? '');
	}}
>
	<div class=" text-sm text-gray-500">
		{$i18n.t('This will delete')} <span class="  font-semibold">{deleteChat?.title}</span>.
	</div>
</DeleteConfirmDialog>

<!-- svelte-ignore a11y-no-static-element-interactions -->

{#if $showSidebar}
	<div
		class=" fixed md:hidden z-40 top-0 right-0 left-0 bottom-0 bg-black/60 w-full min-h-screen h-screen flex justify-center overflow-hidden overscroll-contain"
		on:mousedown={() => {
			showSidebar.set(!$showSidebar);
		}}
	/>
{/if}

<div
	bind:this={navElement}
	id="sidebar"
	class="h-screen max-h-[100dvh] min-h-screen select-none {$showSidebar
		? 'md:relative w-[260px]'
		: '-translate-x-[260px] w-[0px]'} bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-200 text-sm transition fixed z-50 top-0 left-0 rounded-r-2xl
        "
	style="	background-color: linear-gradient(
		to bottom,
		transparent 0px,
		transparent 10px,
		#f4f5f6 30px
	) !important;"
	data-state={$showSidebar}
>
	<div
		class="py-2.5 my-auto flex flex-col justify-between h-screen max-h-[100dvh] w-[260px] z-50 {$showSidebar
			? ''
			: 'invisible'}"
	>
		<div class="px-2.5 flex justify-between space-x-1 text-gray-600 dark:text-gray-400">
			<a
				id="sidebar-new-chat-button"
				class="flex flex-1 justify-between rounded-xl px-2 py-2 hover:bg-gray-100 dark:hover:bg-gray-850 transition"
				href="/"
				draggable="false"
				on:click={async () => {
					selectedChatId = null;
					await goto('/');
					const newChatButton = document.getElementById('new-chat-button');
					setTimeout(() => {
						newChatButton?.click();
						if ($mobile) {
							showSidebar.set(false);
						}
					}, 0);
				}}
			>
				<div class="self-center mr-2">
					<svg
						width="20"
						height="20"
						viewBox="0 0 200 200"
						fill="none"
						xmlns="http://www.w3.org/2000/svg"
						style="overflow: visible;margin: right 0.1rem;rem"
					>
						<path
							d="M146.88 112.5C172.768 112.5 193.755 91.5134 193.755 65.625C193.755 39.7366 172.768 18.75 146.88 18.75C120.992 18.75 100.005 39.7367 100.005 65.625C100.005 91.5133 120.992 112.5 146.88 112.5Z"
							fill="url(#paint0_linear_143_1711)"
							id="greenHighlight"
							class="lens"
						/>
						<path
							fill-rule="evenodd"
							clip-rule="evenodd"
							d="M100.005 52.6417C73.829 52.6417 52.6092 73.8555 52.6092 100.024C52.6092 126.192 73.829 147.406 100.005 147.406C126.181 147.406 147.401 126.192 147.401 100.024C147.401 73.8555 126.181 52.6417 100.005 52.6417ZM18.755 100.024C18.755 55.1637 55.1319 18.7973 100.005 18.7973C144.878 18.7973 181.255 55.1637 181.255 100.024C181.255 144.884 144.878 181.251 100.005 181.251C55.1319 181.251 18.755 144.884 18.755 100.024Z"
							fill="url(#paint1_linear_143_1711)"
							id="bigCircle"
						/>
						<path
							fill-rule="evenodd"
							clip-rule="evenodd"
							d="M181.212 97.532C172.656 106.711 160.457 112.451 146.918 112.451C146.527 112.451 146.137 112.446 145.748 112.437C146.827 108.466 147.404 104.288 147.404 99.975C147.404 74.4205 127.173 53.591 101.854 52.6277C105.577 39.6475 114.757 28.9742 126.751 23.2491C157.75 34.0471 180.195 63.1 181.212 97.532Z"
							fill="url(#paint2_linear_143_1711)"
							id="lensTrack"
							class="lens"
						/>
						<path
							d="M146.856 112.5C172.744 112.5 193.731 91.5134 193.731 65.625C193.731 39.7366 172.744 18.75 146.856 18.75C120.967 18.75 99.9806 39.7367 99.9806 65.625C99.9806 91.5133 120.967 112.5 146.856 112.5Z"
							fill="url(#paint3_radial_143_1711)"
							id="lens"
							class="lens"
						/>

						<defs>
							<linearGradient
								id="paint0_linear_143_1711"
								x1="101.864"
								y1="18.75"
								x2="178.624"
								y2="95.5095"
								gradientUnits="userSpaceOnUse"
							>
								<stop stop-color="#0087EA" />
								<stop offset="1" stop-color="#63FFF7" />
							</linearGradient>
							<linearGradient
								id="paint1_linear_143_1711"
								x1="181.255"
								y1="18.7973"
								x2="18.8017"
								y2="181.297"
								gradientUnits="userSpaceOnUse"
							>
								<stop stop-color="#0051AF" />
								<stop offset="0.666238" stop-color="#0087EA" />
								<stop offset="1" stop-color="#00BCEB" />
							</linearGradient>
							<linearGradient
								id="paint2_linear_143_1711"
								x1="130.914"
								y1="49.9375"
								x2="174.369"
								y2="100.198"
								gradientUnits="userSpaceOnUse"
							>
								<stop stop-color="#74BF4B" stop-opacity="0" />
								<stop offset="1" stop-color="#74BF4B" />
							</linearGradient>
							<radialGradient
								id="paint3_radial_143_1711"
								cx="0"
								cy="0"
								r="1"
								gradientUnits="userSpaceOnUse"
								gradientTransform="translate(193.731 112.5) rotate(-135) scale(132.583 132.527)"
							>
								<stop stop-color="#00BCEB" stop-opacity="0" />
								<stop offset="0.666962" stop-color="#00BCEB" stop-opacity="0" />
								<stop offset="1" stop-color="#00BCEB" />
							</radialGradient>
						</defs>
					</svg>
				</div>
				<div class=" self-center font-medium text-sm text-gray-850 dark:text-white font-primary">
					{$i18n.t('New Chat')}
				</div>
				<div class="self-center ml-auto">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="url(#paint0_linear_30_740)" class="w-4 h-4">
						<path
							d="M5.433 13.917l1.262-3.155A4 4 0 017.58 9.42l6.92-6.918a2.121 2.121 0 013 3l-6.92 6.918c-.383.383-.84.685-1.343.886l-3.154 1.262a.5.5 0 01-.65-.65z"
						/>
						<path
							d="M3.5 5.75c0-.69.56-1.25 1.25-1.25H10A.75.75 0 0010 3H4.75A2.75 2.75 0 002 5.75v9.5A2.75 2.75 0 004.75 18h9.5A2.75 2.75 0 0017 15.25V10a.75.75 0 00-1.5 0v5.25c0 .69-.56 1.25-1.25 1.25h-9.5c-.69 0-1.25-.56-1.25-1.25v-9.5z"
						/>

						<defs>
							<linearGradient
								id="paint0_linear_30_740"
								x1="19.2803"
								y1="24.0741"
								x2="31.301"
								y2="0.278008"
								gradientUnits="userSpaceOnUse"
							>
								<stop stop-color="#3B76EA" />
								<stop offset="0.515625" stop-color="#00BCEB" />
								<stop offset="1" stop-color="#63FFF7" />
							</linearGradient>
						</defs>
					</svg>
				</div>
			</a>

			<button
				class=" cursor-pointer px-2 py-2 flex rounded-xl hover:bg-gray-100 dark:hover:bg-gray-850 transition"
				on:click={() => {
					showSidebar.set(!$showSidebar);
				}}
			>
				<div class=" m-auto self-center">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="2"
						stroke="currentColor"
						class="size-5"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
					</svg>
				</div>
			</button>
		</div>

		{#if $user?.role === 'admin'}
			<div class="px-2.5 flex justify-center text-gray-800 dark:text-gray-200">
				<a
					class="flex-grow flex rounded-xl px-2 py-2 hover:bg-gray-100 dark:hover:bg-gray-900 transition"
					href="/workspace"
					on:click={() => {
						selectedChatId = null;
						chatId.set('');

						if ($mobile) {
							showSidebar.set(false);
						}
					}}
					draggable="false"
				>
					<div class="self-center mr-2">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="2"
							stroke="currentColor"
							class="size-[1.1rem]"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M13.5 16.875h3.375m0 0h3.375m-3.375 0V13.5m0 3.375v3.375M6 10.5h2.25a2.25 2.25 0 0 0 2.25-2.25V6a2.25 2.25 0 0 0-2.25-2.25H6A2.25 2.25 0 0 0 3.75 6v2.25A2.25 2.25 0 0 0 6 10.5Zm0 9.75h2.25A2.25 2.25 0 0 0 10.5 18v-2.25a2.25 2.25 0 0 0-2.25-2.25H6a2.25 2.25 0 0 0-2.25 2.25V18A2.25 2.25 0 0 0 6 20.25Zm9.75-9.75H18a2.25 2.25 0 0 0 2.25-2.25V6A2.25 2.25 0 0 0 18 3.75h-2.25A2.25 2.25 0 0 0 13.5 6v2.25a2.25 2.25 0 0 0 2.25 2.25Z"
							/>
						</svg>
					</div>

					<div class="flex self-center">
						<div class=" self-center font-medium text-sm font-primary">{$i18n.t('Workspace')}</div>
					</div>
				</a>
			</div>
		{/if}

		<div class="relative flex flex-col flex-1 overflow-y-auto">
			{#if !($settings.saveChatHistory ?? true)}
				<div class="absolute z-40 w-full h-full bg-gray-50/90 dark:bg-black/90 flex justify-center">
					<div class=" text-left px-5 py-2">
						<div class=" font-medium">{$i18n.t('Chat History is off for this browser.')}</div>
						<div class="text-xs mt-2">
							{$i18n.t(
								"When history is turned off, new chats on this browser won't appear in your history on any of your devices."
							)}
							<span class=" font-semibold">{$i18n.t('This setting does not sync across browsers or devices.')}</span>
						</div>

						<div class="mt-3">
							<button
								class="flex justify-center items-center space-x-1.5 px-3 py-2.5 rounded-lg text-xs bg-gray-100 hover:bg-gray-200 transition text-gray-800 font-medium w-full"
								type="button"
								on:click={() => {
									saveSettings({
										saveChatHistory: true
									});
								}}
							>
								<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" class="w-3 h-3">
									<path
										fill-rule="evenodd"
										d="M8 1a.75.75 0 0 1 .75.75v6.5a.75.75 0 0 1-1.5 0v-6.5A.75.75 0 0 1 8 1ZM4.11 3.05a.75.75 0 0 1 0 1.06 5.5 5.5 0 1 0 7.78 0 .75.75 0 0 1 1.06-1.06 7 7 0 1 1-9.9 0 .75.75 0 0 1 1.06 0Z"
										clip-rule="evenodd"
									/>
								</svg>

								<div>{$i18n.t('Enable Chat History')}</div>
							</button>
						</div>
					</div>
				</div>
			{/if}

			<div class="px-2 mt-0.5 mb-2 flex justify-center space-x-2">
				<div class="flex w-full rounded-xl" id="chat-search">
					<div class="self-center pl-3 py-2 rounded-l-xl bg-transparent mr-2">
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
							<path
								fill-rule="evenodd"
								d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>

					<input
						class="w-full rounded-xl py-1.5 pl-2.5 pr-4 text-sm bg-transparent dark:text-gray-300 outline-none"
						placeholder={$i18n.t('Search')}
						bind:value={search}
						on:focus={() => {
							enrichChatsWithContent($chats);
						}}
					/>
				</div>
			</div>

			{#if $tags.filter((t) => t.name !== 'pinned').length > 0}
				<div class="px-2.5 mb-2 flex gap-1 flex-wrap">
					<button
						class="px-2.5 text-xs font-medium bg-gray-50 dark:bg-gray-900 dark:hover:bg-gray-800 transition rounded-full"
						on:click={async () => {
							chats.set(await getChatList(localStorage.token));
						}}
					>
						{$i18n.t('all')}
					</button>
					{#each $tags.filter((t) => t.name !== 'pinned') as tag}
						<button
							class="px-2.5 text-xs font-medium bg-gray-50 dark:bg-gray-900 dark:hover:bg-gray-800 transition rounded-full"
							on:click={async () => {
								let chatIds = await getChatListByTagName(localStorage.token, tag.name);
								if (chatIds && chatIds.length === 0) {
									tags.set(await getAllChatTags(localStorage.token));
									chatIds = await getChatList(localStorage.token);
								}
								if (chatIds) {
									chats.set(chatIds);
								}
							}}
						>
							{tag.name}
						</button>
					{/each}
				</div>
			{/if}

			{#if $pinnedChats.length > 0}
				<div class="pl-2 py-2 flex flex-col space-y-1">
					<div class="">
						<div class="w-full pl-2.5 text-xs text-gray-500 dark:text-gray-500 font-medium pb-1.5">
							{$i18n.t('Pinned')}
						</div>

						{#each $pinnedChats as chat, idx}
							<ChatItem
								{chat}
								{shiftKey}
								selected={selectedChatId === chat.id}
								on:select={() => {
									selectedChatId = chat.id;
								}}
								on:unselect={() => {
									selectedChatId = null;
								}}
								on:delete={(e) => {
									if ((e?.detail ?? '') === 'shift') {
										deleteChatHandler(chat.id);
									} else {
										deleteChat = chat;
										showDeleteConfirm = true;
									}
								}}
							/>
						{/each}
					</div>
				</div>
			{/if}

			<div class="pl-2 my-2 flex-1 flex flex-col space-y-1 overflow-y-auto scrollbar-hidden">
				{#each filteredChatList as chat, idx}
					{#if idx === 0 || (idx > 0 && chat.time_range !== filteredChatList[idx - 1].time_range)}
						<div
							class="w-full pl-2.5 text-xs text-gray-500 dark:text-gray-500 font-medium {idx === 0
								? ''
								: 'pt-5'} pb-0.5"
						>
							{$i18n.t(chat.time_range)}
							<!-- localisation keys for time_range to be recognized from the i18next parser (so they don't get automatically removed):
							{$i18n.t('Today')}
							{$i18n.t('Yesterday')}
							{$i18n.t('Previous 7 days')}
							{$i18n.t('Previous 30 days')}
							{$i18n.t('January')}
							{$i18n.t('February')}
							{$i18n.t('March')}
							{$i18n.t('April')}
							{$i18n.t('May')}
							{$i18n.t('June')}
							{$i18n.t('July')}
							{$i18n.t('August')}
							{$i18n.t('September')}
							{$i18n.t('October')}
							{$i18n.t('November')}
							{$i18n.t('December')}
							-->
						</div>
					{/if}

					<ChatItem
						{chat}
						{shiftKey}
						selected={selectedChatId === chat.id}
						on:select={() => {
							selectedChatId = chat.id;
						}}
						on:unselect={() => {
							selectedChatId = null;
						}}
						on:delete={(e) => {
							if ((e?.detail ?? '') === 'shift') {
								deleteChatHandler(chat.id);
							} else {
								deleteChat = chat;
								showDeleteConfirm = true;
							}
						}}
					/>
				{/each}
			</div>
		</div>

		<div class="px-2.5">
			<!-- <hr class=" border-gray-900 mb-1 w-full" /> -->

			<div class="flex flex-col font-primary">
				{#if $user !== undefined}
					<UserMenu
						role={$user.role}
						on:show={(e) => {
							if (e.detail === 'archived-chat') {
								showArchivedChats.set(true);
							}
						}}
					>
						<button
							class=" flex rounded-xl py-3 px-3.5 w-full hover:bg-gray-100 dark:hover:bg-gray-900 transition"
							on:click={() => {
								showDropdown = !showDropdown;
							}}
						>
							<div class=" self-center mr-3">
								<img src={$user.profile_image_url} class=" max-w-[30px] object-cover rounded-full" alt="User profile" />
							</div>
							<div class=" self-center font-medium">{$user.name}</div>
						</button>
					</UserMenu>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.scrollbar-hidden:active::-webkit-scrollbar-thumb,
	.scrollbar-hidden:focus::-webkit-scrollbar-thumb,
	.scrollbar-hidden:hover::-webkit-scrollbar-thumb {
		visibility: visible;
	}
	.scrollbar-hidden::-webkit-scrollbar-thumb {
		visibility: hidden;
	}

	#art {
		fill: #1990fa;
		width: 1.1rem;
		height: auto;
	}
</style>
