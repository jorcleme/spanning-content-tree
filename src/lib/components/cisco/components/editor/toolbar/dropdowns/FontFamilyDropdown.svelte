<script lang="ts">
	import type { FontFamilyContext } from '$lib/types';

	import { getContext } from 'svelte';

	import { getActiveEditor, getIsEditable } from '$lib/utils/editor';
	import { $patchStyleText as patchStyleText } from '@lexical/selection';
	import { $getSelection as getSelection } from 'lexical';

	import DropDownItem from './DropdownItem.svelte';
	import EditorDropdown from './EditorDropdown.svelte';

	const FONT_FAMILY_OPTIONS = [
		['CiscoSans', 'CiscoSans'],
		['CiscoSansLight', 'CiscoSansLight'],
		['CiscoSansItalic', 'CiscoSansItalic'],
		['CiscoSansLightItalic', 'CiscoSansLightItalic'],
		['CiscoSansBold', 'CiscoSansBold'],
		['CiscoSansThin', 'CiscoSansThin'],
		['CiscoSansOblique', 'CiscoSansOblique'],
		['CiscoSansMedium', 'CiscoSansMedium'],
		['CiscoSansHeavy', 'CiscoSansHeavy']
	];
	const activeEditor = getActiveEditor();
	const value: FontFamilyContext = getContext('fontFamily');
	const style = 'font-family';
	const isEditable = getIsEditable();
	const handleClick = (option: string) => {
		$activeEditor.update(() => {
			const selection = getSelection();
			if (selection !== null) {
				patchStyleText(selection, {
					[style]: option
				});
			}
		});
	};
	const buttonAriaLabel = 'Formatting options for font family';
</script>

<EditorDropdown
	disabled={!$isEditable}
	buttonClassName={'toolbar-item ' + style}
	buttonLabel={$value}
	{buttonAriaLabel}
>
	{#each FONT_FAMILY_OPTIONS as [option, text]}
		<DropDownItem
			class="mx-2 p-2 text-gray-700 dark:text-gray-50 cursor-pointer leading-5 flex content-center shrink-0 justify-between bg-neutral-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 border-none rounded-md max-w-[250px] min-w-100px w-[calc(100%-16px)] {$value ===
			option
				? 'bg-gray-100 dark:bg-gray-700'
				: ''}"
			on:click={() => handleClick(option)}
		>
			<span class="flex leading-5 flex-1 min-w-[150px]">{text}</span>
		</DropDownItem>
	{/each}
</EditorDropdown>
