<script context="module"></script>

<script lang="ts">
	import { writable } from 'svelte/store';
	import { onMount, setContext } from 'svelte';
	import { createSharedEditorContext, initializeEditor, setEditor, setHistoryStateContext } from '$lib/utils/editor';
	import { createEmptyHistoryState } from '@lexical/history';
	import { createEditor, $getRoot as getRoot } from 'lexical';
	import type { CreateEditorArgs } from 'lexical';

	// export type InitialEditorStateType = null | string | EditorState | ((editor: LexicalEditor) => void);
	// export type InitialConfigType = Readonly<{
	// 	editor__DEPRECATED?: LexicalEditor | null;
	// 	namespace: string;
	// 	nodes?: ReadonlyArray<Klass<LexicalNode> | LexicalNodeReplacement>;
	// 	onError: (error: Error, editor: LexicalEditor) => void;
	// 	editable?: boolean;
	// 	theme?: EditorThemeClasses;
	// 	editorState?: InitialEditorStateType;
	// 	html?: HTMLConfig;
	// }>;

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

		return editor.registerEditableListener((editable2) => {
			$isEditable = editable2;
		});
	});

	setHistoryStateContext(createEmptyHistoryState());
	createSharedEditorContext();
	export function getEditor() {
		return editor;
	}
</script>

<slot />
