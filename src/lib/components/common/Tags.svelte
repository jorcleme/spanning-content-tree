<script lang="ts">
	import type { i18nType } from '$lib/types';
	import { getContext } from 'svelte';
	import TagInput from './Tags/TagInput.svelte';
	import TagList from './Tags/TagList.svelte';

	const i18n: i18nType = getContext('i18n');

	export let tags: Array<{ name: string }> = [];

	export let deleteTag: (tagName: string) => void;
	export let addTag: (tagName: string) => void;
</script>

<div class="flex flex-row items-center flex-wrap gap-1 line-clamp-1">
	<TagList
		{tags}
		on:delete={(e) => {
			deleteTag(e.detail);
		}}
	/>

	<TagInput
		label={tags.length == 0 ? $i18n.t('Add Tags') : ''}
		on:add={(e) => {
			addTag(e.detail);
		}}
	/>
</div>
