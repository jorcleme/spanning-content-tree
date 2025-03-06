<script lang="ts">
	import type { BlockTypeContext } from '$lib/types';

	import { writable } from 'svelte/store';

	import { setContext } from 'svelte';

	import { getEditor } from '$lib/utils/editor';

	import StateStoreRichTextUpdator from './ToolbarState.svelte';

	const editor = getEditor();
	const activeEditor = writable(editor);

	setContext('activeEditor', activeEditor);
	setContext('isBold', writable(false));
	setContext('isItalic', writable(false));
	setContext('isUnderline', writable(false));
	setContext('isStrikethrough', writable(false));
	setContext('isSubscript', writable(false));
	setContext('isSuperscript', writable(false));
	setContext('isCode', writable(false));
	const blockType: BlockTypeContext = writable('paragraph');
	setContext('blockType', blockType);
	setContext('selectedElementKey', writable(null));
	setContext('fontSize', writable('15px'));
	setContext('fontFamily', writable('Arial'));
	setContext('fontColor', writable('#000'));
	setContext('bgColor', writable('#fff'));
	setContext('isRTL', writable(false));
	setContext('codeLanguage', writable(''));
	setContext('isLink', writable(false));
	setContext('isImageCaption', writable(false));
</script>

<StateStoreRichTextUpdator />
<div
	class="toolbar flex items-center border-b border-gray-300 dark:border-gray-700/50 mb-1 bg-gray-50 dark:bg-gray-850 dark:text-gray-50 p-2 rounded-t-lg sticky top-0 z-10 align-middle overflow-x-scroll overflow-y-hidden h-[36px]"
>
	<slot {editor} activeEditor={$activeEditor} blockType={$blockType} />
</div>
