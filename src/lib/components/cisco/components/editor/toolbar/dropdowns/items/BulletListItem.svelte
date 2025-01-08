<script lang="ts">
	import type { BlockTypeContext, i18nType } from '$lib/types';
	import { getContext } from 'svelte';
	import { formatParagraph, getEditor } from '$lib/utils/editor';
	import { INSERT_UNORDERED_LIST_COMMAND } from '@lexical/list';
	import DropDownItem from '../DropdownItem.svelte';
	import { List } from 'lucide-svelte';

	const blockType: BlockTypeContext = getContext('blockType');
	const editor = getEditor();
	const i18n: i18nType = getContext('i18n');

	const formatBulletList = () => {
		if ($blockType !== 'bullet') {
			editor.dispatchCommand(INSERT_UNORDERED_LIST_COMMAND, void 0);
		} else {
			formatParagraph(editor);
		}
	};
</script>

<DropDownItem
	class="mx-2 p-2 text-gray-700 dark:text-gray-50 cursor-pointer leading-5 flex content-center shrink-0 bg-neutral-50 dark:bg-gray-800 hover:bg-neutral-100 border-none rounded-md max-w-[250px] min-w-100px w-[calc(100%-16px)] {$blockType ===
	'bullet'
		? 'bg-neutral-100 dark:bg-gray-900'
		: ''}"
	on:click={formatBulletList}
>
	<List class="w-4 h-4 mr-2" />
	<span class="text">{$i18n.t('Bullet list')}</span>
</DropDownItem>
