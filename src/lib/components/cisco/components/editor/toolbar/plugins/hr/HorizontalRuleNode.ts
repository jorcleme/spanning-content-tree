import { addClassNamesToElement } from '@lexical/utils';
import { $applyNodeReplacement, DecoratorNode, type LexicalEditor, createCommand } from 'lexical';
import type { EditorConfig, LexicalNode, SerializedLexicalNode } from 'lexical';
import HorizontalRuleComponent from '$lib/components/cisco/components/editor/toolbar/plugins/hr/HorizontalRule.svelte';

export type SerializedHorizontalRuleNode = SerializedLexicalNode;
export const INSERT_HORIZONTAL_RULE_COMMAND = createCommand('INSERT_HORIZONTAL_RULE_COMMAND');
export class HorizontalRuleNode extends DecoratorNode<unknown> {
	static getType() {
		return 'horizontalrule';
	}
	static clone(node: HorizontalRuleNode) {
		return new HorizontalRuleNode(node.__key);
	}
	// eslint-disable-next-line @typescript-eslint/no-unused-vars
	static importJSON(serializedNode: SerializedHorizontalRuleNode) {
		return $createHorizontalRuleNode();
	}
	static importDOM() {
		return {
			hr: () => ({
				conversion: convertHorizontalRuleElement,
				priority: 0 as 0 | 1 | 2 | 3 | 4 | undefined
			})
		};
	}
	/**
	 * It tells `Decorater.svelte` that this component doesn't need rendering during decorator listener call.
	 * `this.decorate` should also return null when skipDecorateRender is true
	 */
	static skipDecorateRender = true;
	exportJSON() {
		return {
			type: 'horizontalrule',
			version: 1
		};
	}
	exportDOM() {
		return { element: document.createElement('hr') };
	}
	createDOM(config: EditorConfig, editor: LexicalEditor) {
		const hr = document.createElement('hr');
		addClassNamesToElement(hr, config.theme.hr);
		new HorizontalRuleComponent({
			target: hr,
			props: {
				nodeKey: this.__key,
				editor,
				self: hr
			}
		});
		return hr;
	}
	getTextContent() {
		return '\n';
	}
	isInline() {
		return false;
	}
	updateDOM() {
		return false;
	}
	/**
	 * @returns should return null if not participating in decorator rendering (skipDecorateRender should also be true)
	 */
	decorate() {
		return null;
	}
}
function convertHorizontalRuleElement() {
	return { node: $createHorizontalRuleNode() };
}
export function $createHorizontalRuleNode() {
	return $applyNodeReplacement(new HorizontalRuleNode());
}
export function $isHorizontalRuleNode(node: LexicalNode | null | undefined): node is HorizontalRuleNode {
	return node instanceof HorizontalRuleNode;
}
