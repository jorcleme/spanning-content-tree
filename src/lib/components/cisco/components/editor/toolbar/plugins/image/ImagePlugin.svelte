<script context="module" lang="ts">
	export const INSERT_IMAGE_COMMAND = createCommand();
	const getDOMSelection = (targetWindow: typeof globalThis | null | undefined) =>
		CAN_USE_DOM ? (targetWindow || window).getSelection() : null;
</script>

<script lang="ts">
	import { onMount } from 'svelte';
	import { CAN_USE_DOM, getEditor } from '$lib/utils/editor';
	import { mergeRegister, $wrapNodeInElement as wrapNodeInElement } from '@lexical/utils';
	import {
		COMMAND_PRIORITY_EDITOR,
		COMMAND_PRIORITY_HIGH,
		COMMAND_PRIORITY_LOW,
		DRAGOVER_COMMAND,
		DRAGSTART_COMMAND,
		DROP_COMMAND,
		type LexicalEditor,
		createCommand,
		$createParagraphNode as createParagraphNode,
		$createRangeSelection as createRangeSelection,
		$getSelection as getSelection,
		$insertNodes as insertNodes,
		$isNodeSelection as isNodeSelection,
		$isRootOrShadowRoot as isRootOrShadowRoot,
		$setSelection as setSelection
	} from 'lexical';
	import type { ImagePayload } from './ImageNode.js';
	import { ImageNode, $createImageNode as createImageNode, $isImageNode as isImageNode } from './ImageNode.js';

	const editor = getEditor();
	const TRANSPARENT_IMAGE = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
	let img: HTMLImageElement;
	export let captionsEnabled = true;
	onMount(() => {
		if (!editor.hasNodes([ImageNode])) {
			throw new Error('ImagesPlugin: ImageNode not registered on editor');
		}
		img = document.createElement('img');
		img.src = TRANSPARENT_IMAGE;
		return mergeRegister(
			editor.registerCommand(
				INSERT_IMAGE_COMMAND,
				(payload: ImagePayload) => {
					payload.captionsEnabled = captionsEnabled;
					const imageNode = createImageNode(payload);
					insertNodes([imageNode]);
					if (isRootOrShadowRoot(imageNode.getParentOrThrow())) {
						wrapNodeInElement(imageNode, createParagraphNode).selectEnd();
					}
					return true;
				},
				COMMAND_PRIORITY_EDITOR
			),
			editor.registerCommand(
				DRAGSTART_COMMAND,
				(event) => {
					return onDragStart(event);
				},
				COMMAND_PRIORITY_HIGH
			),
			editor.registerCommand(
				DRAGOVER_COMMAND,
				(event) => {
					return onDragover(event);
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(
				DROP_COMMAND,
				(event) => {
					return onDrop(event, editor);
				},
				COMMAND_PRIORITY_HIGH
			)
		);
	});
	function onDragStart(event: DragEvent) {
		const node = getImageNodeInSelection();
		if (!node) {
			return false;
		}
		const dataTransfer = event.dataTransfer;
		if (!dataTransfer) {
			return false;
		}
		dataTransfer.setData('text/plain', '_');
		dataTransfer.setDragImage(img, 0, 0);
		dataTransfer.setData(
			'application/x-lexical-drag',
			JSON.stringify({
				data: {
					altText: node.__altText,
					caption: node.__caption,
					height: node.__height,
					key: node.getKey(),
					maxWidth: node.__maxWidth,
					showCaption: node.__showCaption,
					src: node.__src,
					width: node.__width
				},
				type: 'image'
			})
		);
		return true;
	}
	function onDragover(event: DragEvent) {
		const node = getImageNodeInSelection();
		if (!node) {
			return false;
		}
		if (!canDropImage(event)) {
			event.preventDefault();
		}
		return true;
	}
	function onDrop(event: DragEvent, editor2: LexicalEditor) {
		const node = getImageNodeInSelection();
		if (!node) {
			return false;
		}
		const data = getDragImageData(event);
		if (!data) {
			return false;
		}
		event.preventDefault();
		if (canDropImage(event)) {
			const range = getDragSelection(event);
			node.remove();
			const rangeSelection = createRangeSelection();
			if (range !== null && range !== void 0) {
				rangeSelection.applyDOMRange(range);
			}
			setSelection(rangeSelection);
			editor2.dispatchCommand(INSERT_IMAGE_COMMAND, data);
		}
		return true;
	}
	function getImageNodeInSelection() {
		const selection = getSelection();
		if (!isNodeSelection(selection)) {
			return null;
		}
		const nodes = selection.getNodes();
		const node = nodes[0];
		return isImageNode(node) ? node : null;
	}
	function getDragImageData(event: DragEvent) {
		const dragData = event.dataTransfer?.getData('application/x-lexical-drag');
		if (!dragData) {
			return null;
		}
		const { type, data } = JSON.parse(dragData);
		if (type !== 'image') {
			return null;
		}
		return data;
	}
	function canDropImage(event: DragEvent) {
		const target = event.target;
		return !!(
			target &&
			target instanceof HTMLElement &&
			!target.closest('code, span.editor-image') &&
			target.parentElement &&
			target.parentElement.closest('div.content-editable')
		);
	}

	const getEventTarget = (event: Event): Element | Document | null => {
		const target = event.target;
		if (!target) return null;
		if ((target as Node).nodeType === Node.DOCUMENT_NODE) {
			return target as Document;
		}
		return target as Element;
	};

	function getDragSelection(event: DragEvent) {
		let range;
		const target = getEventTarget(event);
		const targetWindow =
			target == null
				? null
				: target.nodeType === Node.DOCUMENT_NODE
				? (target as Document).defaultView
				: target.ownerDocument?.defaultView;
		const domSelection = getDOMSelection(targetWindow);
		if (document.caretRangeFromPoint) {
			range = document.caretRangeFromPoint(event.clientX, event.clientY);
		} else if (event.rangeParent && domSelection !== null) {
			domSelection.collapse(event.rangeParent, event.rangeOffset || 0);
			range = domSelection.getRangeAt(0);
		} else {
			throw Error(`Cannot get the selection when dragging`);
		}
		return range;
	}
</script>

<!--for ImageComponent history plugin -->
<slot />
