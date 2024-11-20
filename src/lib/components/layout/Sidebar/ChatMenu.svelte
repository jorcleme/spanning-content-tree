<script lang="ts">
	import type { ChatTag, i18nType } from '$lib/types';
	import { createEventDispatcher, getContext } from 'svelte';
	import { addTagById, deleteTagById, getTagsById } from '$lib/apis/chats';
	import { flyAndScale } from '$lib/utils/transitions';
	import { DropdownMenu } from 'bits-ui';
	import Tags from '$lib/components/chat/Tags.svelte';
	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import ArchiveBox from '$lib/components/icons/ArchiveBox.svelte';
	import Bookmark from '$lib/components/icons/Bookmark.svelte';
	import BookmarkSlash from '$lib/components/icons/BookmarkSlash.svelte';
	import DocumentDuplicate from '$lib/components/icons/DocumentDuplicate.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import Pencil from '$lib/components/icons/Pencil.svelte';
	import Share from '$lib/components/icons/Share.svelte';

	const dispatch = createEventDispatcher();

	const i18n: i18nType = getContext('i18n');

	export let shareHandler: Function;
	export let cloneChatHandler: Function;
	export let archiveChatHandler: Function;
	export let renameHandler: Function;
	export let deleteHandler: Function;
	export let onClose: Function;

	export let chatId = '';

	let show = false;
	let pinned: boolean | ChatTag = false;

	const pinHandler = async () => {
		if (pinned) {
			await deleteTagById(localStorage.token, chatId, 'pinned');
		} else {
			await addTagById(localStorage.token, chatId, 'pinned');
		}
		dispatch('change');
	};

	const checkPinned = async () => {
		const tags =
			(await getTagsById(localStorage.token, chatId).catch(async (error) => {
				return [];
			})) ?? [];
		pinned = tags.find((tag) => tag.name === 'pinned') || false;
	};

	$: if (show) {
		checkPinned();
	}
</script>

<Dropdown
	bind:show
	on:change={(e) => {
		if (e.detail === false) {
			onClose();
		}
	}}
>
	<Tooltip content={$i18n.t('More')}>
		<slot />
	</Tooltip>

	<div slot="content">
		<DropdownMenu.Content
			class="w-full max-w-[180px] rounded-xl px-1 py-1.5 border border-gray-300/30 dark:border-gray-700/50 z-50 bg-white dark:bg-gray-850 dark:text-white shadow"
			sideOffset={-2}
			side="bottom"
			align="start"
			transition={flyAndScale}
		>
			<DropdownMenu.Item
				class="flex gap-2 items-center px-3 py-2 text-sm  font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
				on:click={() => {
					pinHandler();
				}}
			>
				{#if pinned}
					<BookmarkSlash strokeWidth="2" />
					<div class="flex items-center">{$i18n.t('Unpin')}</div>
				{:else}
					<Bookmark strokeWidth="2" />
					<div class="flex items-center">{$i18n.t('Pin')}</div>
				{/if}
			</DropdownMenu.Item>

			<DropdownMenu.Item
				class="flex gap-2 items-center px-3 py-2 text-sm  font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
				on:click={() => {
					renameHandler();
				}}
			>
				<Pencil strokeWidth="2" />
				<div class="flex items-center">{$i18n.t('Rename')}</div>
			</DropdownMenu.Item>

			<DropdownMenu.Item
				class="flex gap-2 items-center px-3 py-2 text-sm  font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
				on:click={() => {
					cloneChatHandler();
				}}
			>
				<DocumentDuplicate strokeWidth="2" />
				<div class="flex items-center">{$i18n.t('Clone')}</div>
			</DropdownMenu.Item>

			<DropdownMenu.Item
				class="flex gap-2 items-center px-3 py-2 text-sm  font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
				on:click={() => {
					archiveChatHandler();
				}}
			>
				<ArchiveBox strokeWidth="2" />
				<div class="flex items-center">{$i18n.t('Archive')}</div>
			</DropdownMenu.Item>

			<DropdownMenu.Item
				class="flex gap-2 items-center px-3 py-2 text-sm  font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800  rounded-md"
				on:click={() => {
					shareHandler();
				}}
			>
				<Share />
				<div class="flex items-center">{$i18n.t('Share')}</div>
			</DropdownMenu.Item>

			<DropdownMenu.Item
				class="flex  gap-2  items-center px-3 py-2 text-sm  font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
				on:click={() => {
					deleteHandler();
				}}
			>
				<GarbageBin strokeWidth="2" />
				<div class="flex items-center">{$i18n.t('Delete')}</div>
			</DropdownMenu.Item>

			<hr class="border-gray-100 dark:border-gray-800 mt-2.5 mb-1.5" />

			<div class="flex p-1">
				<Tags
					{chatId}
					on:close={() => {
						show = false;
						onClose();
					}}
				/>
			</div>
		</DropdownMenu.Content>
	</div>
</Dropdown>
