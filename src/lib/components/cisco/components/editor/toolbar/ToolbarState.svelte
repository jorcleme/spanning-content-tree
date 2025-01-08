<script lang="ts">
	import type {
		BgColorContext,
		BlockType,
		BlockTypeContext,
		CodeLanguageContext,
		FontColorContext,
		FontFamilyContext,
		FontSizeContext,
		IsBoldContext,
		IsCodeContext,
		IsImageCaptionContext,
		IsItalicContext,
		IsLinkContext,
		IsRTLContext,
		IsStrikethroughContext,
		IsSubscriptContext,
		IsSuperscriptContext,
		IsUnderlineContext,
		SelectedElementKeyContext
	} from '$lib/types';
	import { getContext, onMount } from 'svelte';
	import { getActiveEditor, getEditor, getSelectedNode } from '$lib/utils/editor';
	import { CODE_LANGUAGE_MAP, $isCodeNode as isCodeNode } from '@lexical/code';
	import { $isLinkNode as isLinkNode } from '@lexical/link';
	import { ListNode, $isListNode as isListNode } from '@lexical/list';
	import { $isHeadingNode as isHeadingNode } from '@lexical/rich-text';
	import {
		$getSelectionStyleValueForProperty as getSelectionStyleValueForProperty,
		$isParentElementRTL as isParentElementRTL
	} from '@lexical/selection';
	import { $isTableSelection as isTableSelection } from '@lexical/table';
	import {
		$findMatchingParent as findMatchingParent,
		$getNearestNodeOfType as getNearestNodeOfType,
		$isEditorIsNestedEditor as isEditorIsNestedEditor,
		mergeRegister
	} from '@lexical/utils';
	import {
		COMMAND_PRIORITY_CRITICAL,
		SELECTION_CHANGE_COMMAND,
		$getSelection as getSelection,
		$isRangeSelection as isRangeSelection,
		$isRootOrShadowRoot as isRootOrShadowRoot
	} from 'lexical';

	const blockTypeMapping = {
		bullet: 'Bulleted List',
		check: 'Check List',
		code: 'Code Block',
		h1: 'Heading 1',
		h2: 'Heading 2',
		h3: 'Heading 3',
		h4: 'Heading 4',
		h5: 'Heading 5',
		h6: 'Heading 6',
		number: 'Numbered List',
		paragraph: 'Normal',
		quote: 'Quote'
	};

	const editor = getEditor();
	const activeEditor = getActiveEditor();
	const isBold: IsBoldContext = getContext('isBold');
	const isItalic: IsItalicContext = getContext('isItalic');
	const isUnderline: IsUnderlineContext = getContext('isUnderline');
	const isStrikethrough: IsStrikethroughContext = getContext('isStrikethrough');
	const isSubscript: IsSubscriptContext = getContext('isSubscript');
	const isSuperscript: IsSuperscriptContext = getContext('isSuperscript');
	const isCode: IsCodeContext = getContext('isCode');
	const blockType: BlockTypeContext = getContext('blockType');
	const selectedElementKey: SelectedElementKeyContext = getContext('selectedElementKey');
	const isRTL: IsRTLContext = getContext('isRTL');
	const codeLanguage: CodeLanguageContext = getContext('codeLanguage');
	const fontSize: FontSizeContext = getContext('fontSize');
	const fontFamily: FontFamilyContext = getContext('fontFamily');
	const fontColor: FontColorContext = getContext('fontColor');
	const bgColor: BgColorContext = getContext('bgColor');
	const isLink: IsLinkContext = getContext('isLink');
	const isImageCaption: IsImageCaptionContext = getContext('isImageCaption');

	const updateToolbar = () => {
		const selection = getSelection();
		if (isRangeSelection(selection)) {
			if ($activeEditor !== editor && isEditorIsNestedEditor($activeEditor)) {
				const rootElement = $activeEditor.getRootElement();
				$isImageCaption = !!rootElement?.parentElement?.classList.contains('image-caption-container');
			} else {
				$isImageCaption = false;
			}
			const anchorNode = selection.anchor.getNode();
			let element =
				anchorNode.getKey() === 'root'
					? anchorNode
					: findMatchingParent(anchorNode, (e) => {
							const parent2 = e.getParent();
							return parent2 !== null && isRootOrShadowRoot(parent2);
					  });
			if (element === null) {
				element = anchorNode.getTopLevelElementOrThrow();
			}
			const elementKey = element.getKey();
			const elementDOM = $activeEditor.getElementByKey(elementKey);
			$isBold = selection.hasFormat('bold');
			$isItalic = selection.hasFormat('italic');
			$isUnderline = selection.hasFormat('underline');
			$isStrikethrough = selection.hasFormat('strikethrough');
			$isSubscript = selection.hasFormat('subscript');
			$isSuperscript = selection.hasFormat('superscript');
			$isCode = selection.hasFormat('code');
			$isRTL = isParentElementRTL(selection);
			const node = getSelectedNode(selection);
			const parent = node.getParent();
			if (isLinkNode(parent) || isLinkNode(node)) {
				$isLink = true;
			} else {
				$isLink = false;
			}
			if (elementDOM !== null) {
				$selectedElementKey = elementKey;
				if (isListNode(element)) {
					const parentList = getNearestNodeOfType(anchorNode, ListNode);
					const type = parentList ? parentList.getListType() : (element.getListType() as BlockType);
					$blockType = type;
				} else {
					const type = isHeadingNode(element) ? element.getTag() : (element.getType() as BlockType);
					if (type in blockTypeMapping) {
						$blockType = type;
					}
					if (isCodeNode(element)) {
						const language = element.getLanguage();
						$codeLanguage = language ? CODE_LANGUAGE_MAP[language] || language : '';
						return;
					}
				}
			}
			$fontColor = getSelectionStyleValueForProperty(selection, 'color', '#333');
			$bgColor = getSelectionStyleValueForProperty(selection, 'background-color', '#fff');
			$fontFamily = getSelectionStyleValueForProperty(selection, 'font-family', 'CiscoSans');
		}
		if (isRangeSelection(selection) || isTableSelection(selection)) {
			$fontSize = getSelectionStyleValueForProperty(selection, 'font-size', '12px');
		}
	};
	onMount(() => {
		return mergeRegister(
			editor.registerUpdateListener(({ editorState }) => {
				editorState.read(() => {
					updateToolbar();
				});
			}),
			editor.registerCommand(
				SELECTION_CHANGE_COMMAND,
				(_payload, editor) => {
					activeEditor.set(editor);
					updateToolbar();
					return false;
				},
				COMMAND_PRIORITY_CRITICAL
			)
		);
	});
</script>
