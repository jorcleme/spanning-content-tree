<script lang="ts">
	import { onMount } from 'svelte';
	import { clearSelection, createNodeSelectionStore } from '$lib/utils/editor/plugins';
	import { addClassNamesToElement, mergeRegister, removeClassNamesFromElement } from '@lexical/utils';
	import type { LexicalEditor, NodeKey } from 'lexical';
	import {
		CLICK_COMMAND,
		COMMAND_PRIORITY_LOW,
		KEY_BACKSPACE_COMMAND,
		KEY_DELETE_COMMAND,
		$getNodeByKey as getNodeByKey,
		$getSelection as getSelection,
		$isNodeSelection as isNodeSelection
	} from 'lexical';
	import { $isHorizontalRuleNode as isHorizontalRuleNode } from './HorizontalRuleNode';

	export let editor: LexicalEditor;
	export let nodeKey: NodeKey;
	export let self: HTMLElement;

	let isSelected = createNodeSelectionStore(editor, nodeKey);

	const isSelectedClassName = 'selected';

	$: if ($isSelected) {
		addClassNamesToElement(self, isSelectedClassName);
	} else {
		removeClassNamesFromElement(self, isSelectedClassName);
	}

	const onDelete = (event: CustomEvent<any>) => {
		if ($isSelected && isNodeSelection(getSelection())) {
			event.preventDefault();
			const node = getNodeByKey(nodeKey);
			if (isHorizontalRuleNode(node)) {
				node.remove();
				return true;
			}
		}
		return false;
	};

	onMount(() => {
		return mergeRegister(
			editor.registerCommand(
				CLICK_COMMAND,
				(event) => {
					if (event.target === self) {
						if (!event.shiftKey) {
							clearSelection(editor);
						}
						$isSelected = !$isSelected;
						return true;
					}
					return false;
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(KEY_DELETE_COMMAND, onDelete, COMMAND_PRIORITY_LOW),
			editor.registerCommand(KEY_BACKSPACE_COMMAND, onDelete, COMMAND_PRIORITY_LOW)
		);
	});
</script>
