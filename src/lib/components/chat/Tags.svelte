<script lang="ts">
	import type { ChatTagListResponse } from '$lib/types';
	import { createEventDispatcher, onMount } from 'svelte';
	import {
		addTagById,
		deleteTagById,
		getAllChatTags,
		getChatList,
		getChatListByTagName,
		getTagsById,
		updateChatById
	} from '$lib/apis/chats';
	import { tags as _tags, chats, pinnedChats } from '$lib/stores';
	import Tags from '../common/Tags.svelte';

	const dispatch = createEventDispatcher();

	export let chatId = '';
	let tags: ChatTagListResponse = [];

	const getTags = async () => {
		return ((await getTagsById(localStorage.token, chatId)) ?? []).filter((tag) => tag.name !== 'pinned');
	};

	const addTag = async (tagName: string) => {
		const res = await addTagById(localStorage.token, chatId, tagName);
		tags = await getTags();

		await updateChatById(localStorage.token, chatId, {
			tags: tags
		});

		_tags.set(await getAllChatTags(localStorage.token));
		pinnedChats.set((await getChatListByTagName(localStorage.token, 'pinned')) ?? []);
	};

	const deleteTag = async (tagName: string) => {
		const res = await deleteTagById(localStorage.token, chatId, tagName);
		tags = await getTags();

		await updateChatById(localStorage.token, chatId, {
			tags: tags
		});

		console.log($_tags);
		_tags.set(await getAllChatTags(localStorage.token));

		console.log($_tags);

		if ($_tags.map((t) => t.name).includes(tagName)) {
			if (tagName === 'pinned') {
				pinnedChats.set((await getChatListByTagName(localStorage.token, 'pinned')) ?? []);
			} else {
				chats.set((await getChatListByTagName(localStorage.token, tagName)) ?? []);
			}

			if ($chats.find((chat) => chat.id === chatId)) {
				dispatch('close');
			}
		} else {
			chats.set(await getChatList(localStorage.token));
			pinnedChats.set((await getChatListByTagName(localStorage.token, 'pinned')) ?? []);
		}
	};

	onMount(async () => {
		if (chatId) {
			tags = await getTags();
		}
	});
</script>

<Tags {tags} {deleteTag} {addTag} />
