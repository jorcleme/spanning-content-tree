<script lang="ts">
	import { onMount } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import {
		$findMatchingParent as findMatchingParent,
		$insertNodeToNearestRoot as insertNodeToNearestRoot,
		mergeRegister
	} from '@lexical/utils';
	import {
		COMMAND_PRIORITY_EDITOR,
		COMMAND_PRIORITY_LOW,
		KEY_ARROW_DOWN_COMMAND,
		KEY_ARROW_LEFT_COMMAND,
		KEY_ARROW_RIGHT_COMMAND,
		KEY_ARROW_UP_COMMAND,
		$createParagraphNode as createParagraphNode,
		$getNodeByKey as getNodeByKey,
		$getSelection as getSelection,
		$isRangeSelection as isRangeSelection
	} from 'lexical';
	import {
		LayoutContainerNode,
		$createLayoutContainerNode as createLayoutContainerNode,
		$isLayoutContainerNode as isLayoutContainerNode
	} from './LayoutContainerNode';
	import {
		INSERT_LAYOUT_COMMAND,
		LayoutItemNode,
		UPDATE_LAYOUT_COMMAND,
		$createLayoutItemNode as createLayoutItemNode,
		$isLayoutItemNode as isLayoutItemNode
	} from './LayoutItemNode';

	const editor = getEditor();
	onMount(() => {
		if (!editor.hasNodes([LayoutContainerNode, LayoutItemNode])) {
			throw new Error('LayoutPlugin: LayoutContainerNode, or LayoutItemNode not registered on editor');
		}
		const $onEscape = (before: boolean) => {
			const selection = getSelection();
			if (isRangeSelection(selection) && selection.isCollapsed() && selection.anchor.offset === 0) {
				const container = findMatchingParent(selection.anchor.getNode(), isLayoutContainerNode);
				if (container && isLayoutContainerNode(container)) {
					const parent = container.getParent();
					const child = parent && (before ? parent.getFirstChild() : parent?.getLastChild());
					const descendant = before
						? container.getFirstDescendant()?.getKey()
						: container.getLastDescendant()?.getKey();
					if (parent !== null && child === container && selection.anchor.key === descendant) {
						if (before) {
							container.insertBefore(createParagraphNode());
						} else {
							container.insertAfter(createParagraphNode());
						}
					}
				}
			}
			return false;
		};
		return mergeRegister(
			// When layout is the last child pressing down/right arrow will insert paragraph
			// below it to allow adding more content. It's similar what $insertBlockNode
			// (mainly for decorators), except it'll always be possible to continue adding
			// new content even if trailing paragraph is accidentally deleted
			editor.registerCommand(KEY_ARROW_DOWN_COMMAND, () => $onEscape(false), COMMAND_PRIORITY_LOW),
			editor.registerCommand(KEY_ARROW_RIGHT_COMMAND, () => $onEscape(false), COMMAND_PRIORITY_LOW),
			// When layout is the first child pressing up/left arrow will insert paragraph
			// above it to allow adding more content. It's similar what $insertBlockNode
			// (mainly for decorators), except it'll always be possible to continue adding
			// new content even if leading paragraph is accidentally deleted
			editor.registerCommand(KEY_ARROW_UP_COMMAND, () => $onEscape(true), COMMAND_PRIORITY_LOW),
			editor.registerCommand(KEY_ARROW_LEFT_COMMAND, () => $onEscape(true), COMMAND_PRIORITY_LOW),
			editor.registerCommand(
				INSERT_LAYOUT_COMMAND,
				(template) => {
					editor.update(() => {
						const container = createLayoutContainerNode(template);
						const itemsCount = getItemsCountFromTemplate(template);
						for (let i = 0; i < itemsCount; i++) {
							container.append(createLayoutItemNode().append(createParagraphNode()));
						}
						insertNodeToNearestRoot(container);
						container.selectStart();
					});
					return true;
				},
				COMMAND_PRIORITY_EDITOR
			),
			editor.registerCommand(
				UPDATE_LAYOUT_COMMAND,
				({ template, nodeKey }) => {
					editor.update(() => {
						const container = getNodeByKey(nodeKey);
						if (!isLayoutContainerNode(container)) {
							return;
						}
						const itemsCount = getItemsCountFromTemplate(template);
						const prevItemsCount = getItemsCountFromTemplate(container.getTemplateColumns());
						if (itemsCount > prevItemsCount) {
							for (let i = prevItemsCount; i < itemsCount; i++) {
								container.append(createLayoutItemNode().append(createParagraphNode()));
							}
						} else if (itemsCount < prevItemsCount) {
							for (let i = prevItemsCount - 1; i >= itemsCount; i--) {
								const layoutItem = container.getChildAtIndex(i);
								if (isLayoutItemNode(layoutItem)) {
									layoutItem.remove();
								}
							}
						}
						container.setTemplateColumns(template);
					});
					return true;
				},
				COMMAND_PRIORITY_EDITOR
			),
			// Structure enforcing transformers for each node type. In case nesting structure is not
			// "Container > Item" it'll unwrap nodes and convert it back
			// to regular content.
			editor.registerNodeTransform(LayoutItemNode, (node) => {
				const parent = node.getParent();
				if (!isLayoutContainerNode(parent)) {
					const children = node.getChildren();
					for (const child of children) {
						node.insertBefore(child);
					}
					node.remove();
				}
			}),
			editor.registerNodeTransform(LayoutContainerNode, (node) => {
				const children = node.getChildren();
				if (!children.every(isLayoutItemNode)) {
					for (const child of children) {
						node.insertBefore(child);
					}
					node.remove();
				}
			})
		);
	});
	function getItemsCountFromTemplate(template: string) {
		return template.trim().split(/\s+/).length;
	}
</script>
