<script lang="ts">
	import type { BlockTypeContext } from '$lib/types';
	import { SvelteComponent, getContext } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import { type HeadingTagType, $createHeadingNode as createHeadingNode } from '@lexical/rich-text';
	import { $setBlocksType as setBlocksType } from '@lexical/selection';
	import { $getSelection as getSelection } from 'lexical';
	import DropDownItem from '../DropdownItem.svelte';
	import { Heading1, Heading2, Heading3, Heading4, Heading5, Heading6 } from 'lucide-svelte';

	export let headingSize: HeadingTagType;

	const blockType: BlockTypeContext = getContext('blockType');
	const editor = getEditor();

	const formatHeading = (headingSize2: HeadingTagType) => {
		if ($blockType !== headingSize2) {
			editor.update(() => {
				const selection = getSelection();
				setBlocksType(selection, () => createHeadingNode(headingSize2));
			});
		}
	};

	const ITEM_ICONS: Record<HeadingTagType, any> = {
		h1: Heading1,
		h2: Heading2,
		h3: Heading3,
		h4: Heading4,
		h5: Heading5,
		h6: Heading6
	};
</script>

<DropDownItem
	class="mx-2 p-2 text-gray-700 dark:text-gray-50 cursor-pointer leading-5 flex content-center shrink-0 bg-neutral-50 dark:bg-gray-800 hover:bg-neutral-100 border-none rounded-md max-w-[250px] min-w-100px w-[calc(100%-16px)] {$blockType ===
	headingSize
		? 'bg-neutral-100 dark:bg-gray-900'
		: ''}"
	on:click={() => formatHeading(headingSize)}
>
	{#if headingSize.charAt(1) === '1'}
		<Heading1 class="w-4 h-4 text-neutral-500 mr-2" />
	{:else if headingSize.charAt(1) === '2'}
		<Heading2 class="w-4 h-4 text-neutral-500 mr-2" />
	{:else if headingSize.charAt(1) === '3'}
		<Heading3 class="w-4 h-4 text-neutral-500 mr-2" />
	{:else if headingSize.charAt(1) === '4'}
		<Heading4 class="w-4 h-4 text-neutral-500 mr-2" />
	{:else if headingSize.charAt(1) === '5'}
		<Heading5 class="w-4 h-4 text-neutral-500 mr-2" />
	{:else if headingSize.charAt(1) === '6'}
		<Heading6 class="w-4 h-4 text-neutral-500 mr-2" />
	{/if}
	<span class="flex leading-5 flex-1 min-w-[150px]">Heading {headingSize.charAt(1)}</span>
</DropDownItem>
