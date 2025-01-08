<script lang="ts">
	import type { i18nType } from '$lib/types';
	import { getContext } from 'svelte';
	import { INSERT_HORIZONTAL_RULE_COMMAND } from '$lib/components/cisco/components/editor/toolbar/plugins/hr/HorizontalRuleNode';
	import { getActiveEditor, getEditor, getIsEditable } from '$lib/utils/editor';
	import { flyAndScale } from '$lib/utils/transitions';
	import { DropdownMenu } from 'bits-ui';
	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	const i18n: i18nType = getContext('i18n');

	export let onInsertImageClick: () => void;
	export let onInsertColumnClick: () => void;

	const OPTIONS = [
		['Horizontal Rule', 'hr'],
		['Image', 'image'],
		['Column', 'column']
	];

	const activeEditor = getActiveEditor();
	const isEditable = getIsEditable();

	let show: boolean = false;
	let showImageModal = false;
	let showColumnModal = false;
</script>

<Dropdown
	bind:show
	on:change={(e) => {
		if (e.detail === false) {
			show = false;
		}
	}}
>
	<Tooltip content={$i18n.t('Insert')}>
		<slot />
	</Tooltip>

	<div slot="content">
		<DropdownMenu.Content
			class="w-full max-w-[160px] rounded-xl px-1 py-1.5 border border-gray-300/30 dark:border-gray-700/50 z-50 bg-white dark:bg-gray-850 dark:text-white shadow"
			sideOffset={-4}
			side="bottom"
			align="start"
			transition={flyAndScale}
		>
			{#each OPTIONS as [option, text], i (i)}
				<DropdownMenu.Item
					class="flex gap-2 items-center px-3 py-2 text-sm  font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
					on:click={() => {
						if (text === 'hr') {
							$activeEditor.dispatchCommand(INSERT_HORIZONTAL_RULE_COMMAND, undefined);
						} else if (text === 'image') {
							showImageModal = true;
							onInsertImageClick();
						} else if (text === 'column') {
							showColumnModal = true;
							onInsertColumnClick();
						}
					}}
					disabled={!$isEditable}
				>
					<div class="flex items-center">
						<div>{$i18n.t('{{option}}', { option })}</div>
					</div>
				</DropdownMenu.Item>
			{/each}
		</DropdownMenu.Content>
	</div>
</Dropdown>
