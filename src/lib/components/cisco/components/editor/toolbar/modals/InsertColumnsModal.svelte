<script lang="ts">
	import type { i18nType } from '$lib/types';
	import { getContext, tick } from 'svelte';
	import { getActiveEditor, getEditor } from '$lib/utils/editor';
	import { getCommands } from '$lib/utils/editor/plugins/commands';
	import { dispatch } from 'd3';
	import Modal from '$lib/components/common/Modal.svelte';
	import DropDownItem from '../dropdowns/DropdownItem.svelte';
	import DropDown from '../dropdowns/EditorDropdown.svelte';
	import { INSERT_LAYOUT_COMMAND } from '../plugins/columns/LayoutItemNode';

	const editor = getEditor();
	const activeEditor = getActiveEditor();
	const i18n: i18nType = getContext('i18n');

	export let show = false;
	export function open() {
		show = true;
	}
	async function close() {
		show = false;
		await tick();
		getCommands().FocusEditor.execute(editor);
	}
	const LAYOUTS = [
		{ label: '2 columns (equal width)', value: '1fr 1fr' },
		{ label: '2 columns (25% - 75%)', value: '1fr 3fr' },
		{ label: '3 columns (equal width)', value: '1fr 1fr 1fr' },
		{ label: '3 columns (25% - 50% - 25%)', value: '1fr 2fr 1fr' },
		{ label: '4 columns (equal width)', value: '1fr 1fr 1fr 1fr' }
	];
	let currentLabel = LAYOUTS[0].label;
	let currentValue = LAYOUTS[0].value;

	const handleClick = (label: string, value: string) => {
		currentLabel = label;
		currentValue = value;
	};
</script>

<Modal bind:show>
	<div class="text-gray-700 dark:text-gray-100">
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-1">
			<div class=" text-lg font-medium self-center">{$i18n.t('Insert Column Layout')}</div>
			<button
				class="self-center"
				title="Close"
				on:click={() => {
					show = false;
					dispatch('close');
				}}
			>
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>
		<div class="py-10 px-4">
			<DropDown
				buttonClassName="toolbar-item spaced"
				buttonLabel={currentLabel}
				buttonAriaLabel="Insert specialized editor node"
				buttonIconClassName="columns"
			>
				{#each LAYOUTS as layout}
					<DropDownItem
						class={`item ${currentLabel === layout.label ? 'active dropdown-item-active' : ''}`}
						on:click={() => {
							handleClick(layout.label, layout.value);
						}}
					>
						<span class="text">{layout.label}</span>
					</DropDownItem>
				{/each}
			</DropDown>

			<div class="flex justify-end mt-5">
				<button
					data-test-id="image-modal-file-upload-btn"
					class="py-2.5 px-4 bg-[#007bff] text-white font-bold rounded-md cursor-pointer hover:bg-[#0056b3]"
					on:click={() => {
						$activeEditor.dispatchCommand(INSERT_LAYOUT_COMMAND, currentValue);
						close();
					}}
				>
					Insert
				</button>
			</div>
		</div>
	</div>
</Modal>
