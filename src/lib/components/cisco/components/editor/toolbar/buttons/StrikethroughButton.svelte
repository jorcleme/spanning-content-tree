<script lang="ts">
	import type { IsStrikethroughContext, i18nType } from '$lib/types';
	import { getContext } from 'svelte';
	import { getActiveEditor, getIsEditable } from '$lib/utils/editor';
	import { FORMAT_TEXT_COMMAND } from 'lexical';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { Strikethrough } from 'lucide-svelte';

	const i18n: i18nType = getContext('i18n');

	const activeEditor = getActiveEditor();
	const isEditable = getIsEditable();
	const isStrikethrough: IsStrikethroughContext = getContext('isStrikethrough');
</script>

<Tooltip content={$i18n.t('Strikethrough')}>
	<button
		disabled={!$isEditable}
		on:click={() => {
			$activeEditor.dispatchCommand(FORMAT_TEXT_COMMAND, 'strikethrough');
		}}
		class="flex items-center justify-center p-2.5 rounded-md text-neutral-500 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 border-none border-lg cursor-pointer align-middle shrink-0 {$isStrikethrough
			? 'bg-neutral-100 dark:bg-neutral-800'
			: 'bg-neutral-50'}"
		title="Strikethrough"
		type="button"
		aria-label="Format text with a strikethrough"
	>
		<Strikethrough class="w-4 h-4" />
	</button>
</Tooltip>
