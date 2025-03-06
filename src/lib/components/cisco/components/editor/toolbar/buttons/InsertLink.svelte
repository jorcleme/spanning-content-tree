<script lang="ts">
	import type { IsLinkContext, i18nType } from '$lib/types';

	import { getContext, onMount } from 'svelte';

	import { getActiveEditor, getIsEditable, sanitizeUrl } from '$lib/utils/editor';
	import { TOGGLE_LINK_COMMAND } from '@lexical/link';
	import { IS_APPLE } from '@lexical/utils';
	import { COMMAND_PRIORITY_NORMAL, KEY_MODIFIER_COMMAND } from 'lexical';

	import Tooltip from '$lib/components/common/Tooltip.svelte';

	import { Link } from 'lucide-svelte';

	const activEeditor = getActiveEditor();
	const isEditable = getIsEditable();
	const isLink: IsLinkContext = getContext('isLink');
	const i18n: i18nType = getContext('i18n');

	function insertLink() {
		if (!$isLink) {
			return $activEeditor.dispatchCommand(TOGGLE_LINK_COMMAND, sanitizeUrl('https://'));
		} else {
			return $activEeditor.dispatchCommand(TOGGLE_LINK_COMMAND, null);
		}
	}
	onMount(() => {
		return $activEeditor.registerCommand(
			KEY_MODIFIER_COMMAND,
			(payload) => {
				const event = payload;
				const { code, ctrlKey, metaKey } = event;
				if (code === 'KeyK' && (ctrlKey || metaKey)) {
					event.preventDefault();
					return insertLink();
				}
				return false;
			},
			COMMAND_PRIORITY_NORMAL
		);
	});
</script>

<Tooltip content={$i18n.t(IS_APPLE ? 'Insert link (⌘K)' : 'Insert link (Ctrl+K)')}>
	<button
		disabled={!$isEditable}
		on:click={insertLink}
		class="flex items-center justify-center p-2.5 rounded-md text-gray-500 dark:text-gray-200 dark:bg-gray-850 hover:bg-gray-100 dark:hover:bg-gray-800 border-none bg-gray-50 cursor-pointer align-middle shrink-0 {$isLink
			? 'bg-gray-100 dark:bg-gray-800'
			: ''}"
		aria-label="Insert link"
		type="button"
	>
		<Link class="w-4 h-4" />
	</button>
</Tooltip>
