import type { Writable } from 'svelte/store';
import { writable } from 'svelte/store';
import type { SvelteComponent } from 'svelte';
import { getContext, setContext } from 'svelte';
import type { HistoryState } from '@lexical/history';
import { $isAtNodeEnd as isAtNodeEnd } from '@lexical/selection';
import { $setBlocksType } from '@lexical/selection';
import type { EditorConfig, EditorState, LexicalEditor, NodeKey, RangeSelection } from 'lexical';
import {
	$createParagraphNode as createParagraphNode,
	$getRoot as getRoot,
	$getSelection as getSelection
} from 'lexical';
import { $createNodeSelection, $getNodeByKey, $getSelection, $isNodeSelection, $setSelection } from 'lexical';
import { TextNode } from 'lexical';
import type { SerializedTextNode } from 'lexical';
import type { LexicalNode } from 'lexical';
import { $createParagraphNode, $isRangeSelection } from 'lexical';

export type InitialEditorStateType = null | string | EditorState | ((editor: LexicalEditor) => void);

export const CAN_USE_DOM =
	typeof window !== 'undefined' &&
	typeof window.document !== 'undefined' &&
	typeof window.document.createElement !== 'undefined';

const HISTORY_MERGE_OPTIONS = { tag: 'history-merge' };

export function initializeEditor(editor: LexicalEditor, initialEditorState?: InitialEditorStateType) {
	if (initialEditorState === null) {
		return;
	} else if (initialEditorState === undefined) {
		editor.update(() => {
			const root = getRoot();
			if (root.isEmpty()) {
				const paragraph = createParagraphNode();
				root.append(paragraph);
				const activeElement = CAN_USE_DOM ? document.activeElement : null;
				if (getSelection() !== null || (activeElement !== null && activeElement === editor.getRootElement())) {
					paragraph.select();
				}
			}
		}, HISTORY_MERGE_OPTIONS);
	} else if (initialEditorState !== null) {
		switch (typeof initialEditorState) {
			case 'string': {
				const parsedEditorState = editor.parseEditorState(initialEditorState);
				editor.setEditorState(parsedEditorState, HISTORY_MERGE_OPTIONS);
				break;
			}
			case 'object': {
				editor.setEditorState(initialEditorState, HISTORY_MERGE_OPTIONS);
				break;
			}
			case 'function': {
				editor.update(() => {
					const root = getRoot();
					if (root.isEmpty()) {
						initialEditorState(editor);
					}
				}, HISTORY_MERGE_OPTIONS);
				break;
			}
		}
	}
}

export const getEditor = (): LexicalEditor => {
	return getContext('editor');
};

export const setEditor = (editor: LexicalEditor) => {
	setContext('editor', editor);
};

export const getIsEditable = (): Writable<boolean> => {
	return getContext('isEditable');
};

export const getActiveEditor = (): Writable<LexicalEditor> => {
	return getContext('activeEditor');
};

export const getHistoryStateContext = (): HistoryState => {
	return getContext('historyState');
};
type SvelteComponentTypeRef = {
	componentType: typeof SvelteComponent<any>;
	props?: Record<string, object | string | boolean>;
};

/**
 * Editor plugins and decorator nodes don't fall under the same component hierarchy under the composer. They can't share context.
 * This shared context at editor level allows sharing between editors and decorator nodes.
 */
export const createSharedEditorContext = () => {
	setContext('editorSharedContext', {});
};
export const getSharedEditorContext = (): Record<string, SvelteComponentTypeRef> => {
	return getContext('editorSharedContext');
};

export const setImageHistoryPluginType = (componentTypeRef: SvelteComponentTypeRef) => {
	getSharedEditorContext().ImageHistoryComponentType = componentTypeRef;
};
export const getImageHistoryPluginType = (): SvelteComponentTypeRef => {
	return getSharedEditorContext().ImageHistoryComponentType;
};
/**
 * Save `historyState` in the svelte component context
 */
export const setHistoryStateContext = (historyState: HistoryState) => {
	setContext('historyState', historyState);
};

const VERTICAL_GAP = 10;
const HORIZONTAL_OFFSET = 5;

export const setFloatingAnchorPosition = (
	targetRect: DOMRect | null,
	floatingElem: HTMLElement,
	anchorElem: HTMLElement,
	verticalGap: number = VERTICAL_GAP,
	horizontalOffset: number = HORIZONTAL_OFFSET
) => {
	const scrollerElem = anchorElem.parentElement;
	if (targetRect === null || !scrollerElem) {
		floatingElem.style.opacity = '0';
		floatingElem.style.transform = 'translate(-10000px, -10000px)';
		return;
	}
	const floatingElemRect = floatingElem.getBoundingClientRect();
	const anchorElementRect = anchorElem.getBoundingClientRect();
	const editorScrollerRect = scrollerElem.getBoundingClientRect();
	let top = targetRect.top - verticalGap;
	let left = targetRect.left - horizontalOffset;
	if (top < editorScrollerRect.top) {
		top += floatingElemRect.height + targetRect.height + verticalGap * 2;
	}
	if (left + floatingElemRect.width > editorScrollerRect.right) {
		left = editorScrollerRect.right - floatingElemRect.width - horizontalOffset;
	}
	top -= anchorElementRect.top;
	left -= anchorElementRect.left;
	floatingElem.style.opacity = '1';
	floatingElem.style.transform = `translate(${left}px, ${top}px)`;
};

const SUPPORTED_URL_PROTOCOLS = new Set(['http:', 'https:', 'mailto:', 'sms:', 'tel:']);

export const sanitizeUrl = (url: string) => {
	try {
		const parsedUrl = new URL(url);
		// eslint-disable-next-line no-script-url
		if (!SUPPORTED_URL_PROTOCOLS.has(parsedUrl.protocol)) {
			return 'about:blank';
		}
	} catch {
		return url;
	}
	return url;
};

const urlRegExp = new RegExp(
	/((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=+$,\w]+@)?[A-Za-z0-9.-]+|(?:www.|[-;:&=+$,\w]+@)[A-Za-z0-9.-]+)((?:\/[+~%/.\w-_]*)?\??(?:[-+=&;%@.\w_]*)#?(?:[\w]*))?)/
);
export const validateUrl = (url: string) => {
	// TODO Fix UI for link insertion; it should never default to an invalid URL such as https://.
	// Maybe show a dialog where they user can type the URL before inserting it.
	return url === 'https://' || urlRegExp.test(url);
};

export const getSelectedNode = (selection: RangeSelection) => {
	const anchor = selection.anchor;
	const focus = selection.focus;
	const anchorNode = selection.anchor.getNode();
	const focusNode = selection.focus.getNode();
	if (anchorNode === focusNode) {
		return anchorNode;
	}
	const isBackward = selection.isBackward();
	if (isBackward) {
		return isAtNodeEnd(focus) ? anchorNode : focusNode;
	} else {
		return isAtNodeEnd(anchor) ? focusNode : anchorNode;
	}
};

export function isNodeSelected(editor: LexicalEditor, key: NodeKey) {
	return editor.getEditorState().read(() => {
		const node = $getNodeByKey(key);
		if (node === null) {
			return false;
		}
		return node.isSelected();
	});
}
/**
 * Clear editor selection
 */
export function clearSelection(editor: LexicalEditor) {
	editor.update(() => {
		const selection = $getSelection();
		if ($isNodeSelection(selection)) {
			selection.clear();
		}
	});
}
/**
 * Stores `isSelected` state for a SvelteComponent node.
 * Rather than updating the component state directly, it updates the editor node selection and receives updates from the editor.
 */
export function createNodeSelectionStore(editor: LexicalEditor, nodeKey: NodeKey) {
	const { subscribe, set /*, update*/ } = writable(false);
	editor.registerUpdateListener(() => {
		set(isNodeSelected(editor, nodeKey));
	});
	return {
		subscribe,
		set: (selected: boolean) => {
			editor.update(() => {
				let selection = $getSelection();
				if (!$isNodeSelection(selection)) {
					selection = $createNodeSelection();
					$setSelection(selection);
				}
				if ($isNodeSelection(selection)) {
					if (selected) {
						selection.add(nodeKey);
					} else {
						selection.delete(nodeKey);
					}
				}
			});
		}
	};
}

export class KeywordNode extends TextNode {
	static getType() {
		return 'keyword';
	}
	static clone(node: KeywordNode) {
		return new KeywordNode(node.__text, node.__key);
	}
	static importJSON(serializedNode: SerializedTextNode) {
		const node = $createKeywordNode(serializedNode.text);
		node.setFormat(serializedNode.format);
		node.setDetail(serializedNode.detail);
		node.setMode(serializedNode.mode);
		node.setStyle(serializedNode.style);
		return node;
	}
	exportJSON() {
		return {
			...super.exportJSON(),
			type: 'keyword',
			version: 1
		};
	}
	createDOM(config: EditorConfig) {
		const dom = super.createDOM(config);
		dom.style.cursor = 'default';
		dom.className = 'keyword';
		return dom;
	}
	canInsertTextBefore() {
		return false;
	}
	canInsertTextAfter() {
		return false;
	}
	isTextEntity() {
		return true;
	}
}
export function $createKeywordNode(keyword: string) {
	return new KeywordNode(keyword);
}
export function $isKeywordNode(node: LexicalNode | null | undefined) {
	return node instanceof KeywordNode;
}

type RegisterItemTypeFunc = (ref: HTMLButtonElement) => void;

const registerItemSymbol = Symbol();
export function getRegisterItemFunc(): RegisterItemTypeFunc {
	return getContext(registerItemSymbol);
}
export function setRegisterItemFunc(registerItem: RegisterItemTypeFunc) {
	setContext(registerItemSymbol, registerItem);
}

export function formatParagraph(editor: LexicalEditor) {
	editor.update(() => {
		const selection = $getSelection();
		if ($isRangeSelection(selection)) {
			$setBlocksType(selection, () => $createParagraphNode());
		}
	});
}
