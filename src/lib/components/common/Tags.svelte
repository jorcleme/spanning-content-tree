<script lang="ts">
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import TagInput from './Tags/TagInput.svelte';
	import TagList from './Tags/TagList.svelte';
	import { getContext } from 'svelte';

	const i18n: Writable<i18nType> = getContext('i18n');

	export let tags: string[] = [];

	export let deleteTag: Function;
	export let addTag: Function;
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
