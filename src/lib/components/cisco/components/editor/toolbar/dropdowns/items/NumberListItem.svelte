<script lang="ts">
	import type { BlockTypeContext, i18nType } from '$lib/types';
	import { getContext } from 'svelte';
	import { formatParagraph, getEditor } from '$lib/utils/editor';
	import { INSERT_ORDERED_LIST_COMMAND } from '@lexical/list';
	import DropdownItem from '../DropdownItem.svelte';
	import { ListOrdered } from 'lucide-svelte';

	const blockType: BlockTypeContext = getContext('blockType');
	const editor = getEditor();
	const i18n: i18nType = getContext('i18n');

	const formatNumberedList = () => {
		if ($blockType !== 'number') {
			editor.dispatchCommand(INSERT_ORDERED_LIST_COMMAND, void 0);
		} else {
			formatParagraph(editor);
		}
	};
</script>

<DropdownItem
	class="mx-2 p-2 text-gray-700 dark:text-gray-50 cursor-pointer leading-5 flex content-center shrink-0 bg-neutral-50 dark:bg-gray-800 hover:bg-neutral-100 border-none rounded-md max-w-[250px] min-w-100px w-[calc(100%-16px)] {$blockType ===
	'number'
		? 'bg-neutral-100 dark:bg-gray-900'
		: ''}"
	on:click={formatNumberedList}
>
	<ListOrdered class="w-4 h-4 mr-2" />
	<span class="text">{$i18n.t('Numbered List')}</span>
</DropdownItem>
