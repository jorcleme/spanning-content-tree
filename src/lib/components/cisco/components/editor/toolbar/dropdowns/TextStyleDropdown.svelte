<script lang="ts">
	import type { BlockTypeContext } from '$lib/types';
	import { getContext } from 'svelte';
	import { blockTypeToBlockName } from '$lib/constants';
	import { getIsEditable } from '$lib/utils/editor';
	import EditorDropdown from './EditorDropdown.svelte';

	const blockType: BlockTypeContext = getContext('blockType');
	const isEditable = getIsEditable();
</script>

<EditorDropdown
	disabled={!$isEditable}
	buttonClassName="toolbar-item block-controls"
	buttonLabel={blockTypeToBlockName[$blockType]}
	buttonAriaLabel="Formatting options for text style"
>
	<slot />
</EditorDropdown>
