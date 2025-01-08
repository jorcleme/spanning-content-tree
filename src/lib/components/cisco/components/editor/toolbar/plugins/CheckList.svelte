<script lang="ts">
	import { onMount } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import {
		INSERT_CHECK_LIST_COMMAND,
		insertList,
		$isListItemNode as isListItemNode,
		$isListNode as isListNode
	} from '@lexical/list';
	import {
		calculateZoomLevel,
		$findMatchingParent as findMatchingParent,
		isHTMLElement,
		mergeRegister
	} from '@lexical/utils';
	import {
		COMMAND_PRIORITY_LOW,
		KEY_ARROW_DOWN_COMMAND,
		KEY_ARROW_LEFT_COMMAND,
		KEY_ARROW_UP_COMMAND,
		KEY_ESCAPE_COMMAND,
		KEY_SPACE_COMMAND,
		type LexicalEditor,
		type LexicalNode,
		$getNearestNodeFromDOMNode as getNearestNodeFromDOMNode,
		$getSelection as getSelection,
		$isElementNode as isElementNode,
		$isRangeSelection as isRangeSelection
	} from 'lexical';

	const editor = getEditor();

	onMount(() => {
		return mergeRegister(
			editor.registerCommand(
				INSERT_CHECK_LIST_COMMAND,
				() => {
					insertList(editor, 'check');
					return true;
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(
				KEY_ARROW_DOWN_COMMAND,
				(event) => {
					return handleArrownUpOrDown(event, editor, false);
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(
				KEY_ARROW_UP_COMMAND,
				(event) => {
					return handleArrownUpOrDown(event, editor, true);
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(
				KEY_ESCAPE_COMMAND,
				(event) => {
					const activeItem = getActiveCheckListItem();
					if (activeItem != null) {
						const rootElement = editor.getRootElement();
						if (rootElement != null) {
							rootElement.focus();
						}
						return true;
					}
					return false;
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(
				KEY_SPACE_COMMAND,
				(event) => {
					const activeItem = getActiveCheckListItem();
					if (activeItem != null && editor.isEditable()) {
						editor.update(() => {
							const listItemNode = getNearestNodeFromDOMNode(activeItem);
							if (isListItemNode(listItemNode)) {
								event.preventDefault();
								listItemNode.toggleChecked();
							}
						});
						return true;
					}
					return false;
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(
				KEY_ARROW_LEFT_COMMAND,
				(event) => {
					return editor.getEditorState().read(() => {
						const selection = getSelection();
						if (isRangeSelection(selection) && selection.isCollapsed()) {
							const { anchor } = selection;
							const isElement = anchor.type === 'element';
							if (isElement || anchor.offset === 0) {
								const anchorNode = anchor.getNode();
								const elementNode = findMatchingParent(anchorNode, (node) => isElementNode(node) && !node.isInline());
								if (isListItemNode(elementNode)) {
									const parent = elementNode.getParent();
									if (
										isListNode(parent) &&
										parent.getListType() === 'check' &&
										(isElement || elementNode.getFirstDescendant() === anchorNode)
									) {
										const domNode = editor.getElementByKey(elementNode.__key);
										if (domNode != null && document.activeElement !== domNode) {
											domNode.focus();
											event.preventDefault();
											return true;
										}
									}
								}
							}
						}
						return false;
					});
				},
				COMMAND_PRIORITY_LOW
			),
			listenPointerDown()
		);
	});
	let listenersCount = 0;
	function listenPointerDown() {
		if (listenersCount++ === 0) {
			document.addEventListener('click', handleClick);
			document.addEventListener('pointerdown', handlePointerDown);
		}
		return () => {
			if (--listenersCount === 0) {
				document.removeEventListener('click', handleClick);
				document.removeEventListener('pointerdown', handlePointerDown);
			}
		};
	}
	function handleCheckItemEvent(event: MouseEvent, callback: (...args: any[]) => void) {
		const target = event.target;
		if (target === null || !isHTMLElement(target)) {
			return;
		}
		const firstChild = target.firstChild;
		if (
			firstChild != null &&
			isHTMLElement(firstChild) &&
			(firstChild.tagName === 'UL' || firstChild.tagName === 'OL')
		) {
			return;
		}
		const parentNode = target.parentNode;
		if (!parentNode || parentNode.__lexicalListType !== 'check') {
			return;
		}
		const rect = target.getBoundingClientRect();
		const pageX = event.pageX / calculateZoomLevel(target);
		if (
			target.dir === 'rtl' ? pageX < rect.right && pageX > rect.right - 20 : pageX > rect.left && pageX < rect.left + 20
		) {
			callback();
		}
	}
	function handleClick(event: MouseEvent) {
		handleCheckItemEvent(event, () => {
			const domNode = event.target as Node & HTMLElement;
			const editor2 = findEditor(domNode);
			if (editor2 != null && editor2.isEditable()) {
				editor2.update(() => {
					if (event.target) {
						const node = getNearestNodeFromDOMNode(domNode);
						if (isListItemNode(node)) {
							domNode.focus();
							node.toggleChecked();
						}
					}
				});
			}
		});
	}
	function handlePointerDown(event: PointerEvent) {
		handleCheckItemEvent(event, () => {
			event.preventDefault();
		});
	}
	function findEditor(target: ParentNode) {
		let node = target as ParentNode | null;
		while (node) {
			if (node.__lexicalEditor) {
				return node.__lexicalEditor;
			}
			node = node.parentNode;
		}
		return null;
	}
	function getActiveCheckListItem() {
		const activeElement = document.activeElement;
		return activeElement != null &&
			activeElement.tagName === 'LI' &&
			activeElement.parentNode != null &&
			activeElement.parentNode.__lexicalListType === 'check'
			? activeElement
			: null;
	}
	function findCheckListItemSibling(node: LexicalNode, backward: boolean) {
		let sibling = backward ? node.getPreviousSibling() : node.getNextSibling();
		let parent = node as LexicalNode | null;
		while (sibling == null && isListItemNode(parent)) {
			parent = parent.getParentOrThrow().getParent();
			if (parent != null) {
				sibling = backward ? parent.getPreviousSibling() : parent.getNextSibling();
			}
		}
		while (isListItemNode(sibling)) {
			const firstChild = backward ? sibling.getLastChild() : sibling.getFirstChild();
			if (!isListNode(firstChild)) {
				return sibling;
			}
			sibling = backward ? firstChild.getLastChild() : firstChild.getFirstChild();
		}
		return null;
	}
	function handleArrownUpOrDown(event: KeyboardEvent, editor2: LexicalEditor, backward: boolean) {
		const activeItem = getActiveCheckListItem();
		if (activeItem != null) {
			editor2.update(() => {
				const listItem = getNearestNodeFromDOMNode(activeItem);
				if (!isListItemNode(listItem)) {
					return;
				}
				const nextListItem = findCheckListItemSibling(listItem, backward);
				if (nextListItem != null) {
					nextListItem.selectStart();
					const dom = editor2.getElementByKey(nextListItem.__key);
					if (dom != null) {
						event.preventDefault();
						setTimeout(() => {
							dom.focus();
						}, 0);
					}
				}
			});
		}
		return false;
	}
</script>
