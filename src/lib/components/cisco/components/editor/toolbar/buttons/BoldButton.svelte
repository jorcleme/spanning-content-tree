<script lang="ts">
	import type { IsBoldContext, i18nType } from '$lib/types';
	import { getContext } from 'svelte';
	import { getActiveEditor, getIsEditable } from '$lib/utils/editor';
	import { IS_APPLE } from '@lexical/utils';
	import { FORMAT_TEXT_COMMAND } from 'lexical';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { Bold } from 'lucide-svelte';

	const activeEditor = getActiveEditor();
	const isEditable = getIsEditable();
	const isBold: IsBoldContext = getContext('isBold');

	const i18n: i18nType = getContext('i18n');
</script>

<Tooltip content={$i18n.t(IS_APPLE ? 'Bold (⌘B)' : 'Bold (Ctrl+B)')}>
	<button
		disabled={!$isEditable}
		on:click={() => {
			$activeEditor.dispatchCommand(FORMAT_TEXT_COMMAND, 'bold');
		}}
		type="button"
		class="flex items-center justify-center p-2.5 rounded-md text-neutral-500 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 border-none border-lg cursor-pointer align-middle shrink-0 {$isBold
			? 'bg-neutral-100 dark:bg-neutral-800'
			: 'bg-neutral-50'}"
		aria-label={`Format text as bold. Shortcut: ${IS_APPLE ? '⌘B' : 'Ctrl+B'}`}
	>
		<Bold class="w-4 h-4" />
	</button>
</Tooltip>
