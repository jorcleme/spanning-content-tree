<script lang="ts">
	import type { BlockTypeContext, i18nType } from '$lib/types';
	import { getContext } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import { $createCodeNode as createCodeNode } from '@lexical/code';
	import { $setBlocksType as setBlocksType } from '@lexical/selection';
	import { $getSelection as getSelection, $isRangeSelection as isRangeSelection } from 'lexical';
	import DropdownItem from '../DropdownItem.svelte';
	import { Code } from 'lucide-svelte';

	const blockType: BlockTypeContext = getContext('blockType');
	const editor = getEditor();
	const i18n: i18nType = getContext('i18n');

	const formatCode = () => {
		if ($blockType !== 'code') {
			editor.update(() => {
				let selection = getSelection();
				if (selection !== null) {
					if (selection.isCollapsed()) {
						setBlocksType(selection, () => createCodeNode());
					} else {
						const textContent = selection.getTextContent();
						const codeNode = createCodeNode();
						selection.insertNodes([codeNode]);
						selection = getSelection();
						if (isRangeSelection(selection)) selection.insertRawText(textContent);
					}
				}
			});
		}
	};
</script>

<DropdownItem
	class="mx-2 p-2 text-gray-700 dark:text-gray-50 cursor-pointer leading-5 flex content-center shrink-0 bg-neutral-50 dark:bg-gray-800 hover:bg-neutral-100 border-none rounded-md max-w-[250px] min-w-100px w-[calc(100%-16px)] {$blockType ===
	'code'
		? 'bg-neutral-100 dark:bg-gray-900'
		: ''}"
	on:click={formatCode}
>
	<Code class="w-4 h-4 mr-2" />
	<span class="text">{$i18n.t('Code Block')}</span>
</DropdownItem>
