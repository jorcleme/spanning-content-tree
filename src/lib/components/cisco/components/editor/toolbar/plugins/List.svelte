<script lang="ts">
	import { onMount } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import {
		INSERT_ORDERED_LIST_COMMAND,
		INSERT_UNORDERED_LIST_COMMAND,
		REMOVE_LIST_COMMAND,
		$handleListInsertParagraph as handleListInsertParagraph,
		insertList,
		removeList
	} from '@lexical/list';
	import { mergeRegister } from '@lexical/utils';
	import { COMMAND_PRIORITY_LOW, INSERT_PARAGRAPH_COMMAND } from 'lexical';

	const editor = getEditor();

	onMount(() => {
		return mergeRegister(
			editor.registerCommand(
				INSERT_ORDERED_LIST_COMMAND,
				() => {
					insertList(editor, 'number');
					return true;
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(
				INSERT_UNORDERED_LIST_COMMAND,
				() => {
					insertList(editor, 'bullet');
					return true;
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(
				REMOVE_LIST_COMMAND,
				() => {
					removeList(editor);
					return true;
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(
				INSERT_PARAGRAPH_COMMAND,
				() => {
					const hasHandledInsertParagraph = handleListInsertParagraph();
					if (hasHandledInsertParagraph) {
						return true;
					}
					return false;
				},
				COMMAND_PRIORITY_LOW
			)
		);
	});
</script>
