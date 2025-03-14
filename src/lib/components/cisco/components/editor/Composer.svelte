<script context="module"></script>

<script lang="ts">
	import { writable } from 'svelte/store';

	import { onMount, setContext } from 'svelte';

	import { createSharedEditorContext, initializeEditor, setEditor, setHistoryStateContext } from '$lib/utils/editor';
	import { createEmptyHistoryState } from '@lexical/history';
	import { createEditor } from 'lexical';
	import type { CreateEditorArgs } from 'lexical';

	export let initialConfig: CreateEditorArgs;

	const { theme, namespace, nodes, onError, editorState: initialEditorState, editable, html } = initialConfig;
	const editor = createEditor({
		editable,
		html,
		namespace,
		nodes,
		onError,
		theme,
		editorState: initialEditorState
	} as CreateEditorArgs);

	initializeEditor(editor, initialEditorState);
	setEditor(editor);

	const isEditable = writable(editable !== void 0 ? editable : true);
	setContext('isEditable', isEditable);

	onMount(() => {
		editor.setEditable($isEditable);

		return editor.registerEditableListener((editable) => {
			$isEditable = editable;
		});
	});

	setHistoryStateContext(createEmptyHistoryState());
	createSharedEditorContext();
	export const getEditor = () => editor;
</script>

<slot />
