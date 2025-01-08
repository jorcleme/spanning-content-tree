<script lang="ts">
	import type { IsCodeContext, i18nType } from '$lib/types';
	import { getContext } from 'svelte';
	import { AutoLinkNode, LinkNode } from 'svelte-lexical';
	import { getActiveEditor, getIsEditable } from '$lib/utils/editor';
	import { IS_APPLE } from '@lexical/utils';
	import { FORMAT_TEXT_COMMAND } from 'lexical';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { Code } from 'lucide-svelte';

	const isEditable = getIsEditable();
	const activeEditor = getActiveEditor();
	const isCode: IsCodeContext = getContext('isCode');

	const i18n: i18nType = getContext('i18n');
</script>

<Tooltip content={$i18n.t('Insert Code Format')}>
	<button
		disabled={!$isEditable}
		on:click={() => {
			$activeEditor.dispatchCommand(FORMAT_TEXT_COMMAND, 'code');
		}}
		type="button"
		class="flex items-center justify-center p-2.5 rounded-md text-neutral-500 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 border-none border-lg cursor-pointer align-middle shrink-0 {$isCode
			? 'bg-neutral-100 dark:bg-neutral-800'
			: 'bg-neutral-50'}"
		aria-label="Insert Code Format"
	>
		<Code class="w-4 h-4" />
	</button>
</Tooltip>
