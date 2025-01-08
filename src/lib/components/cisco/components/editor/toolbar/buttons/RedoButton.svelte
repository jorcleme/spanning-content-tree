<script lang="ts">
	import type { i18nType } from '$lib/types';
	import { getContext, onMount } from 'svelte';
	import { getActiveEditor, getEditor, getIsEditable } from '$lib/utils/editor';
	import { IS_APPLE } from '@lexical/utils';
	import { CAN_REDO_COMMAND, COMMAND_PRIORITY_CRITICAL, REDO_COMMAND } from 'lexical';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { Redo } from 'lucide-svelte';

	const i18n: i18nType = getContext('i18n');

	const editor = getEditor();
	const activeEditor = getActiveEditor();
	const isEditable = getIsEditable();
	let canRedo = false;
	onMount(() => {
		return editor.registerCommand(
			CAN_REDO_COMMAND,
			(payload) => {
				canRedo = payload;
				return false;
			},
			COMMAND_PRIORITY_CRITICAL
		);
	});
</script>

<Tooltip content={$i18n.t(IS_APPLE ? 'Redo (⌘Y)' : 'Redo (Ctrl+Y)')}>
	<button
		disabled={!canRedo || !$isEditable}
		on:click={() => {
			$activeEditor.dispatchCommand(REDO_COMMAND, undefined);
		}}
		type="button"
		class="flex items-center justify-center p-2.5 rounded-md text-neutral-500 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 border-none bg-neutral-50 border-lg cursor-pointer align-middle shrink-0"
		aria-label="Redo"
	>
		<Redo class="w-4 h-4" />
	</button>
</Tooltip>
