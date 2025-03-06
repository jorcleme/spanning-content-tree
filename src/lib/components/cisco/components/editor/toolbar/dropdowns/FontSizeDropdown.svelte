<script lang="ts">
	import type { FontSizeContext, i18nType } from '$lib/types';

	import { getContext } from 'svelte';

	import { getEditor, getIsEditable } from '$lib/utils/editor';
	import { $patchStyleText as patchStyleText } from '@lexical/selection';
	import { $getSelection as getSelection, $isRangeSelection as isRangeSelection } from 'lexical';

	import Tooltip from '$lib/components/common/Tooltip.svelte';

	import DropdownItem from './DropdownItem.svelte';
	import EditorDropdown from './EditorDropdown.svelte';

	const i18n: i18nType = getContext('i18n');

	const FONT_SIZE_OPTIONS = [
		['10px', '10px'],
		['11px', '11px'],
		['12px', '12px'],
		['13px', '13px'],
		['14px', '14px'],
		['15px', '15px'],
		['16px', '16px'],
		['17px', '17px'],
		['18px', '18px'],
		['19px', '19px'],
		['20px', '20px'],
		['24px', '24px'],
		['26px', '26px'],
		['28px', '28px'],
		['30px', '30px'],
		['32px', '32px'],
		['34px', '34px'],
		['36px', '36px'],
		['38px', '38px'],
		['40px', '40px'],
		['42px', '42px'],
		['44px', '44px'],
		['46px', '46px'],
		['48px', '48px'],
		['50px', '50px'],
		['52px', '52px'],
		['54px', '54px'],
		['56px', '56px'],
		['64px', '64px'],
		['72px', '72px'],
		['80px', '80px'],
		['96px', '96px'],
		['112px', '112px'],
		['128px', '128px'],
		['144px', '144px']
	];
	const editor = getEditor();
	const value: FontSizeContext = getContext('fontSize');
	const style = 'font-size';
	const isEditable = getIsEditable();

	const handleClick = (option: string) => {
		editor.update(() => {
			const selection = getSelection();
			if (isRangeSelection(selection)) {
				patchStyleText(selection, {
					[style]: option
				});
			}
		});
	};

	const buttonAriaLabel = 'Formatting options for font size';
</script>

<Tooltip content={$i18n.t('Font Size')}>
	<EditorDropdown
		disabled={!$isEditable}
		buttonClassName={'toolbar-item ' + style}
		buttonLabel={$value}
		{buttonAriaLabel}
	>
		{#each FONT_SIZE_OPTIONS as [option, text]}
			<DropdownItem
				class="mx-2 p-2 text-gray-700 dark:text-gray-50 cursor-pointer leading-5 flex content-center shrink-0 justify-between bg-neutral-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 border-none rounded-md max-w-[250px] min-w-100px w-[calc(100%-16px)] {$value ===
				option
					? 'bg-gray-100 dark:bg-gray-700'
					: ''}"
				on:click={() => handleClick(option)}
			>
				<span class="flex leading-5 flex-1 min-w-[150px]">{text}</span>
			</DropdownItem>
		{/each}
	</EditorDropdown>
</Tooltip>
