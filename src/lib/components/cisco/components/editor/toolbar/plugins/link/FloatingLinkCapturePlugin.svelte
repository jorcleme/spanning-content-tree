<script lang="ts">
	import { writable } from 'svelte/store';
	import { onMount } from 'svelte';
	import { getEditor, getSelectedNode } from '$lib/utils/editor';
	import { TOGGLE_LINK_COMMAND, $isAutoLinkNode as isAutoLinkNode, $isLinkNode as isLinkNode } from '@lexical/link';
	import { $findMatchingParent as findMatchingParent, mergeRegister } from '@lexical/utils';
	import {
		CLICK_COMMAND,
		COMMAND_PRIORITY_CRITICAL,
		COMMAND_PRIORITY_LOW,
		SELECTION_CHANGE_COMMAND,
		$getSelection as getSelection,
		$isLineBreakNode as isLineBreakNode,
		$isRangeSelection as isRangeSelection
	} from 'lexical';
	import FLoatingLinkCapture from './FloatingLinkCapture.svelte';

	const editor = getEditor();

	export let anchorElem = document.body;

	let activeEditor = editor;

	const isLink = writable(false);
	let isEditMode = writable(false);

	function updateToolbar() {
		const selection = getSelection();
		if (isRangeSelection(selection)) {
			const focusNode = getSelectedNode(selection);
			const focusLinkNode = findMatchingParent(focusNode, isLinkNode);
			const focusAutoLinkNode = findMatchingParent(focusNode, isAutoLinkNode);
			if (!(focusLinkNode || focusAutoLinkNode)) {
				$isLink = false;
				return;
			}
			const badNode = selection
				.getNodes()
				.filter((node) => !isLineBreakNode(node))
				.find((node) => {
					const linkNode = findMatchingParent(node, isLinkNode);
					const autoLinkNode = findMatchingParent(node, isAutoLinkNode);
					return (
						(focusLinkNode && !focusLinkNode.is(linkNode)) ||
						(linkNode && !linkNode.is(focusLinkNode)) ||
						(focusAutoLinkNode && !focusAutoLinkNode.is(autoLinkNode)) ||
						(autoLinkNode && (!autoLinkNode.is(focusAutoLinkNode) || autoLinkNode.getIsUnlinked()))
					);
				});
			if (!badNode) {
				$isLink = true;
			} else {
				$isLink = false;
			}
		}
	}
	onMount(() => {
		return mergeRegister(
			editor.registerUpdateListener(({ editorState }) => {
				editorState.read(() => {
					updateToolbar();
				});
			}),
			editor.registerCommand(
				SELECTION_CHANGE_COMMAND,
				(_payload, newEditor) => {
					updateToolbar();
					activeEditor = newEditor;
					return false;
				},
				COMMAND_PRIORITY_CRITICAL
			),
			editor.registerCommand(
				CLICK_COMMAND,
				(payload) => {
					const selection = getSelection();
					if (isRangeSelection(selection)) {
						const node = getSelectedNode(selection);
						const linkNode = findMatchingParent(node, isLinkNode);
						if (isLinkNode(linkNode) && (payload.metaKey || payload.ctrlKey)) {
							window.open(linkNode.getURL(), '_blank');
							return true;
						}
					}
					return false;
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(
				TOGGLE_LINK_COMMAND,
				(payload) => {
					if (payload === 'https://') {
						$isEditMode = true;
					}
					return false;
				},
				COMMAND_PRIORITY_CRITICAL
			)
		);
	});
</script>

<FLoatingLinkCapture editor={activeEditor} {isLink} {anchorElem} {isEditMode} />
