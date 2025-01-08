<script lang="ts">
	import { onMount } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import {
		AutoLinkNode,
		TOGGLE_LINK_COMMAND,
		$createAutoLinkNode as createAutoLinkNode,
		$isAutoLinkNode as isAutoLinkNode,
		$isLinkNode as isLinkNode
	} from '@lexical/link';
	import type { AutoLinkAttributes } from '@lexical/link';
	import { mergeRegister } from '@lexical/utils';
	import {
		COMMAND_PRIORITY_LOW,
		type LexicalNode,
		TextNode,
		$createTextNode as createTextNode,
		$getSelection as getSelection,
		$isElementNode as isElementNode,
		$isLineBreakNode as isLineBreakNode,
		$isNodeSelection as isNodeSelection,
		$isRangeSelection as isRangeSelection,
		$isTextNode as isTextNode
	} from 'lexical';

	type Matchers = Array<
		(
			text: string
		) => { attributes?: AutoLinkAttributes; index: number; length: number; text: string; url: string } | null
	>;

	function findFirstMatch(text: string, matchers2: Matchers) {
		for (let i = 0; i < matchers2.length; i++) {
			const match = matchers2[i](text);
			if (match) {
				return match;
			}
		}
		return null;
	}
	const PUNCTUATION_OR_SPACE = /[.,;\s]/;
	const isSeparator = (char: string) => PUNCTUATION_OR_SPACE.test(char);
	const endsWithSeparator = (textContent: string) => isSeparator(textContent[textContent.length - 1]);
	const startsWithSeparator = (textContent: string) => isSeparator(textContent[0]);
	const startsWithFullStop = (textContent: string) => /^\.[a-zA-Z0-9]{1,}/.test(textContent);
	const isPreviousNodeValid = (node: any) => {
		let previousNode = node.getPreviousSibling();
		if (isElementNode(previousNode)) {
			previousNode = previousNode.getLastDescendant();
		}
		return (
			previousNode === null ||
			isLineBreakNode(previousNode) ||
			(isTextNode(previousNode) && endsWithSeparator(previousNode.getTextContent()))
		);
	};
	const isNextNodeValid = (node: any) => {
		let nextNode = node.getNextSibling();
		if (isElementNode(nextNode)) {
			nextNode = nextNode.getFirstDescendant();
		}
		return (
			nextNode === null ||
			isLineBreakNode(nextNode) ||
			(isTextNode(nextNode) && startsWithSeparator(nextNode.getTextContent()))
		);
	};
	const isContentAroundIsValid = (matchStart: number, matchEnd: number, text: string, nodes: any[]) => {
		const contentBeforeIsValid = matchStart > 0 ? isSeparator(text[matchStart - 1]) : isPreviousNodeValid(nodes[0]);
		if (!contentBeforeIsValid) {
			return false;
		}
		const contentAfterIsValid =
			matchEnd < text.length ? isSeparator(text[matchEnd]) : isNextNodeValid(nodes[nodes.length - 1]);
		return contentAfterIsValid;
	};
	const extractMatchingNodes = (
		nodes: LexicalNode[],
		startIndex: number,
		endIndex: number
	): [number, LexicalNode[], LexicalNode[], LexicalNode[]] => {
		const unmodifiedBeforeNodes = [];
		const matchingNodes = [];
		const unmodifiedAfterNodes = [];
		let matchingOffset = 0;
		let currentOffset = 0;
		const currentNodes = [...nodes];
		while (currentNodes.length > 0) {
			const currentNode = currentNodes[0];
			const currentNodeText = currentNode.getTextContent();
			const currentNodeLength = currentNodeText.length;
			const currentNodeStart = currentOffset;
			const currentNodeEnd = currentOffset + currentNodeLength;
			if (currentNodeEnd <= startIndex) {
				unmodifiedBeforeNodes.push(currentNode);
				matchingOffset += currentNodeLength;
			} else if (currentNodeStart >= endIndex) {
				unmodifiedAfterNodes.push(currentNode);
			} else {
				matchingNodes.push(currentNode);
			}
			currentOffset += currentNodeLength;
			currentNodes.shift();
		}
		return [matchingOffset, unmodifiedBeforeNodes, matchingNodes, unmodifiedAfterNodes];
	};

	function createAutoLinkNodeLocal(nodes: any[], startIndex: number, endIndex: number, match: any) {
		const linkNode = createAutoLinkNode(match.url, match.attributes);
		if (nodes.length === 1) {
			let remainingTextNode = nodes[0];
			let linkTextNode;
			if (startIndex === 0) {
				[linkTextNode, remainingTextNode] = remainingTextNode.splitText(endIndex);
			} else {
				[, linkTextNode, remainingTextNode] = remainingTextNode.splitText(startIndex, endIndex);
			}
			const textNode = createTextNode(match.text);
			textNode.setFormat(linkTextNode.getFormat());
			textNode.setDetail(linkTextNode.getDetail());
			textNode.setStyle(linkTextNode.getStyle());
			linkNode.append(textNode);
			linkTextNode.replace(linkNode);
			return remainingTextNode;
		} else if (nodes.length > 1) {
			const firstTextNode = nodes[0];
			let offset = firstTextNode.getTextContent().length;
			let firstLinkTextNode;
			if (startIndex === 0) {
				firstLinkTextNode = firstTextNode;
			} else {
				[, firstLinkTextNode] = firstTextNode.splitText(startIndex);
			}
			const linkNodes = [];
			let remainingTextNode;
			for (let i = 1; i < nodes.length; i++) {
				const currentNode = nodes[i];
				const currentNodeText = currentNode.getTextContent();
				const currentNodeLength = currentNodeText.length;
				const currentNodeStart = offset;
				const currentNodeEnd = offset + currentNodeLength;
				if (currentNodeStart < endIndex) {
					if (currentNodeEnd <= endIndex) {
						linkNodes.push(currentNode);
					} else {
						const [linkTextNode, endNode] = currentNode.splitText(endIndex - currentNodeStart);
						linkNodes.push(linkTextNode);
						remainingTextNode = endNode;
					}
				}
				offset += currentNodeLength;
			}
			const selection = getSelection();
			const selectedTextNode = selection ? selection.getNodes().find(isTextNode) : void 0;
			const textNode = createTextNode(firstLinkTextNode.getTextContent());
			textNode.setFormat(firstLinkTextNode.getFormat());
			textNode.setDetail(firstLinkTextNode.getDetail());
			textNode.setStyle(firstLinkTextNode.getStyle());
			linkNode.append(textNode, ...linkNodes);
			if (selectedTextNode && selectedTextNode === firstLinkTextNode) {
				if (isRangeSelection(selection)) {
					textNode.select(selection.anchor.offset, selection.focus.offset);
				} else if (isNodeSelection(selection)) {
					textNode.select(0, textNode.getTextContent().length);
				}
			}
			firstLinkTextNode.replace(linkNode);
			return remainingTextNode;
		}
		return void 0;
	}
	function handleLinkCreation(nodes: any[], matchers2: Matchers, onChange2: (...args: any[]) => void) {
		let currentNodes = [...nodes];
		const initialText = currentNodes.map((node) => node.getTextContent()).join('');
		let text = initialText;
		let match;
		let invalidMatchEnd = 0;
		while ((match = findFirstMatch(text, matchers2)) && match !== null) {
			const matchStart = match.index;
			const matchLength = match.length;
			const matchEnd = matchStart + matchLength;
			const isValid = isContentAroundIsValid(
				invalidMatchEnd + matchStart,
				invalidMatchEnd + matchEnd,
				initialText,
				currentNodes
			);
			if (isValid) {
				const [matchingOffset, , matchingNodes, unmodifiedAfterNodes] = extractMatchingNodes(
					currentNodes,
					invalidMatchEnd + matchStart,
					invalidMatchEnd + matchEnd
				);
				const actualMatchStart = invalidMatchEnd + matchStart - matchingOffset;
				const actualMatchEnd = invalidMatchEnd + matchEnd - matchingOffset;
				const remainingTextNode = createAutoLinkNodeLocal(matchingNodes, actualMatchStart, actualMatchEnd, match);
				currentNodes = remainingTextNode ? [remainingTextNode, ...unmodifiedAfterNodes] : unmodifiedAfterNodes;
				onChange2(match.url, null);
				invalidMatchEnd = 0;
			} else {
				invalidMatchEnd += matchEnd;
			}
			text = text.substring(matchEnd);
		}
	}
	function handleLinkEdit(linkNode: AutoLinkNode, matchers2: Matchers, onChange2: (...args: any[]) => void) {
		const children = linkNode.getChildren();
		const childrenLength = children.length;
		for (let i = 0; i < childrenLength; i++) {
			const child = children[i];
			if (!isTextNode(child) || !child.isSimpleText()) {
				replaceWithChildren(linkNode);
				onChange2(null, linkNode.getURL());
				return;
			}
		}
		const text = linkNode.getTextContent();
		const match = findFirstMatch(text, matchers2);
		if (match === null || match.text !== text) {
			replaceWithChildren(linkNode);
			onChange2(null, linkNode.getURL());
			return;
		}
		if (!isPreviousNodeValid(linkNode) || !isNextNodeValid(linkNode)) {
			replaceWithChildren(linkNode);
			onChange2(null, linkNode.getURL());
			return;
		}
		const url = linkNode.getURL();
		if (url !== match.url) {
			linkNode.setURL(match.url);
			onChange2(match.url, url);
		}
		if (match.attributes) {
			const rel = linkNode.getRel();
			if (rel !== match.attributes.rel) {
				linkNode.setRel(match.attributes.rel || null);
				onChange2(match.attributes.rel || null, rel);
			}
			const target = linkNode.getTarget();
			if (target !== match.attributes.target) {
				linkNode.setTarget(match.attributes.target || null);
				onChange2(match.attributes.target || null, target);
			}
		}
	}
	function handleBadNeighbors(textNode: TextNode, matchers2: Matchers, onChange2: (...args: any[]) => void) {
		const previousSibling = textNode.getPreviousSibling();
		const nextSibling = textNode.getNextSibling();
		const text = textNode.getTextContent();
		if (
			isAutoLinkNode(previousSibling) &&
			!previousSibling.getIsUnlinked() &&
			(!startsWithSeparator(text) || startsWithFullStop(text))
		) {
			previousSibling.append(textNode);
			handleLinkEdit(previousSibling, matchers2, onChange2);
			onChange2(null, previousSibling.getURL());
		}
		if (isAutoLinkNode(nextSibling) && !nextSibling.getIsUnlinked() && !endsWithSeparator(text)) {
			replaceWithChildren(nextSibling);
			handleLinkEdit(nextSibling, matchers2, onChange2);
			onChange2(null, nextSibling.getURL());
		}
	}
	function replaceWithChildren(node: AutoLinkNode) {
		const children = node.getChildren();
		const childrenLength = children.length;
		for (let j = childrenLength - 1; j >= 0; j--) {
			node.insertAfter(children[j]);
		}
		node.remove();
		return children.map((child) => child.getLatest());
	}
	function getTextNodesToMatch(textNode: TextNode) {
		const textNodesToMatch = [textNode];
		let nextSibling = textNode.getNextSibling();
		while (nextSibling !== null && isTextNode(nextSibling) && nextSibling.isSimpleText()) {
			textNodesToMatch.push(nextSibling);
			if (/[\s]/.test(nextSibling.getTextContent())) {
				break;
			}
			nextSibling = nextSibling.getNextSibling();
		}
		return textNodesToMatch;
	}
	const editor = getEditor();

	export let matchers: Array<
		(text: string) => {
			attributes?: AutoLinkAttributes;
			index: number;
			length: number;
			text: string;
			url: string;
		} | null
	>;
	export let onChange: ((url: string | null, prevUrl: string | null) => void) | undefined = void 0;
	onMount(() => {
		if (!editor.hasNodes([AutoLinkNode])) {
			throw new Error('AutoLinkPlugin: AutoLinkNode not registered on editor');
		}
		const onChangeWrapped = (url: string | null = null, prevUrl: string | null = null) => {
			if (onChange) {
				onChange(url, prevUrl);
			}
		};
		return mergeRegister(
			editor.registerNodeTransform(TextNode, (textNode) => {
				const parent = textNode.getParentOrThrow();
				const previous = textNode.getPreviousSibling();
				if (isAutoLinkNode(parent) && !parent.getIsUnlinked()) {
					handleLinkEdit(parent, matchers, onChangeWrapped);
				} else if (!isLinkNode(parent)) {
					if (
						textNode.isSimpleText() &&
						(startsWithSeparator(textNode.getTextContent()) || !isAutoLinkNode(previous))
					) {
						const textNodesToMatch = getTextNodesToMatch(textNode);
						handleLinkCreation(textNodesToMatch, matchers, onChangeWrapped);
					}
					handleBadNeighbors(textNode, matchers, onChangeWrapped);
				}
			}),
			editor.registerCommand(
				TOGGLE_LINK_COMMAND,
				(payload) => {
					const selection = getSelection();
					if (payload !== null || !isRangeSelection(selection)) {
						return false;
					}
					const nodes = selection.extract();
					nodes.forEach((node) => {
						const parent = node.getParent();
						if (isAutoLinkNode(parent)) {
							parent.setIsUnlinked(!parent.getIsUnlinked());
							parent.markDirty();
							return true;
						}
					});
					return false;
				},
				COMMAND_PRIORITY_LOW
			)
		);
	});
</script>
