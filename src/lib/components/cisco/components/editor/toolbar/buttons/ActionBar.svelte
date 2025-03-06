<script lang="ts">
	import type { i18nType } from '$lib/types';

	import { getContext } from 'svelte';

	import { getEditor, getIsEditable } from '$lib/utils/editor';
	import { exportFile, importFile } from '@lexical/file';

	import Tooltip from '$lib/components/common/Tooltip.svelte';

	import { Forward, Import, Lock, Unlock } from 'lucide-svelte';

	const i18n: i18nType = getContext('i18n');
	const editor = getEditor();
	const isEditable = getIsEditable();
</script>

<div class="actions flex w-full justify-end pb-2">
	<Tooltip content={$i18n.t('Import')}>
		<button class="mr-4" on:click={() => importFile(editor)} aria-label="Import editor state from JSON">
			<Import class="w-5 h-5" />
		</button>
	</Tooltip>
	<Tooltip content={$i18n.t('Export')}>
		<button
			class="action-button export mr-4"
			on:click={() =>
				exportFile(editor, {
					fileName: `Cisco_Editor_${new Date().toISOString()}`,
					source: 'Cisco Editor'
				})}
			aria-label="Export editor state to JSON"
		>
			<Forward class="w-5 h-5" />
		</button>
	</Tooltip>
	<Tooltip content={$i18n.t('{{mode}}', { mode: !$isEditable ? 'Unlock' : 'Lock' })}>
		<button
			class={`action-button ${!$isEditable ? 'unlock' : 'lock'} mr-4`}
			on:click={() => {
				editor.setEditable(!editor.isEditable());
			}}
			aria-label={`${!$isEditable ? 'Unlock' : 'Lock'} read-only mode`}
		>
			{#if !$isEditable}
				<Unlock class="w-5 h-5" />
			{:else}
				<Lock class="w-5 h-5" />
			{/if}
		</button>
	</Tooltip>
</div>
