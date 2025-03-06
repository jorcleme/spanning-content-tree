<script lang="ts">
	import type { i18nType } from '$lib/types';

	import { getContext, onMount } from 'svelte';

	import { getActiveEditor, getEditor, getIsEditable } from '$lib/utils/editor';
	import { IS_APPLE } from '@lexical/utils';
	import { CAN_UNDO_COMMAND, COMMAND_PRIORITY_CRITICAL, UNDO_COMMAND } from 'lexical';

	import Tooltip from '$lib/components/common/Tooltip.svelte';

	import { Undo } from 'lucide-svelte';

	const i18n: i18nType = getContext('i18n');

	const editor = getEditor();
	const activeEditor = getActiveEditor();
	const isEditable = getIsEditable();
	let canUndo = false;
	onMount(() => {
		return editor.registerCommand(
			CAN_UNDO_COMMAND,
			(payload) => {
				canUndo = payload;
				return false;
			},
			COMMAND_PRIORITY_CRITICAL
		);
	});
</script>

<Tooltip content={$i18n.t(IS_APPLE ? 'Undo (⌘Z)' : 'Undo (Ctrl+Z)')}>
	<button
		disabled={!canUndo || !$isEditable}
		on:click={() => {
			$activeEditor.dispatchCommand(UNDO_COMMAND, undefined);
		}}
		type="button"
		class="flex items-center justify-center p-2.5 rounded-md text-gray-500 dark:text-gray-200 dark:bg-gray-850 hover:bg-gray-100 dark:hover:bg-gray-800 border-none bg-gray-50 cursor-pointer align-middle shrink-0"
		aria-label="Undo"
	>
		<Undo class="w-4 h-4" />
	</button>
</Tooltip>
