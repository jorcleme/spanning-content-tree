import { addClassNamesToElement } from '@lexical/utils';
import type { DOMConversionMap, EditorConfig, LexicalNode, NodeKey, SerializedElementNode } from 'lexical';
import { ElementNode } from 'lexical';
import { createCommand } from 'lexical';

export type SerializedLayoutItemNode = SerializedElementNode;

export const INSERT_LAYOUT_COMMAND = createCommand<string>('INSERT_LAYOUT_COMMAND');
export const UPDATE_LAYOUT_COMMAND = createCommand<{
	template: string;
	nodeKey: NodeKey;
}>();
export class LayoutItemNode extends ElementNode {
	static getType() {
		return 'layout-item';
	}
	static clone(node: LayoutItemNode) {
		return new LayoutItemNode(node.__key);
	}
	createDOM(config: EditorConfig) {
		const dom = document.createElement('div');
		if (typeof config.theme.layoutItem === 'string') {
			addClassNamesToElement(dom, config.theme.layoutItem);
		}
		return dom;
	}
	updateDOM() {
		return false;
	}
	static importDOM(): DOMConversionMap | null {
		return {};
	}
	static importJSON() {
		return $createLayoutItemNode();
	}
	isShadowRoot() {
		return true;
	}
	exportJSON() {
		return {
			...super.exportJSON(),
			type: 'layout-item',
			version: 1
		};
	}
}
export function $createLayoutItemNode() {
	return new LayoutItemNode();
}
export function $isLayoutItemNode(node: LexicalNode | null | undefined): node is LayoutItemNode {
	return node instanceof LayoutItemNode;
}
