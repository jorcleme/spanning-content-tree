<script lang="ts">
	import type { IsUnderlineContext, i18nType } from '$lib/types';

	import { getContext } from 'svelte';

	import { getActiveEditor, getIsEditable } from '$lib/utils/editor';
	import { IS_APPLE } from '@lexical/utils';
	import { FORMAT_TEXT_COMMAND } from 'lexical';

	import Tooltip from '$lib/components/common/Tooltip.svelte';

	import { Underline } from 'lucide-svelte';

	const activeEditor = getActiveEditor();
	const isEditable = getIsEditable();
	const isUnderline: IsUnderlineContext = getContext('isUnderline');

	const i18n: i18nType = getContext('i18n');
</script>

<Tooltip content={$i18n.t(IS_APPLE ? 'Underline (⌘U)' : 'Underline (Ctrl+U)')}>
	<button
		disabled={!$isEditable}
		on:click={() => {
			$activeEditor.dispatchCommand(FORMAT_TEXT_COMMAND, 'underline');
		}}
		type="button"
		class="flex items-center justify-center p-2.5 rounded-md text-gray-500 dark:text-gray-200 dark:bg-gray-850 hover:bg-gray-100 dark:hover:bg-gray-800 border-none bg-gray-50 cursor-pointer align-middle shrink-0 {$isUnderline
			? 'bg-gray-100 dark:bg-gray-800'
			: ''}"
		aria-label={`Format text to underlined. Shortcut: ${IS_APPLE ? '⌘U' : 'Ctrl+U'}`}
	>
		<Underline class="w-4 h-4" />
	</button>
</Tooltip>
