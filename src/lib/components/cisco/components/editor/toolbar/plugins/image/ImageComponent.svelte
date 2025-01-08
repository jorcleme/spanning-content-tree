<script context="module">
	const imageCache = new Set();
	export const RIGHT_CLICK_IMAGE_COMMAND = createCommand('RIGHT_CLICK_IMAGE_COMMAND');
</script>

<script lang="ts">
	import { onMount } from 'svelte';
	import { getImageHistoryPluginType } from '$lib/utils/editor';
	import { KeywordNode, clearSelection, createNodeSelectionStore } from '$lib/utils/editor';
	import { HashtagNode } from '@lexical/hashtag';
	import { LinkNode } from '@lexical/link';
	import { mergeRegister } from '@lexical/utils';
	import {
		type BaseSelection,
		CLICK_COMMAND,
		COMMAND_PRIORITY_LOW,
		DRAGSTART_COMMAND,
		KEY_BACKSPACE_COMMAND,
		KEY_DELETE_COMMAND,
		KEY_ENTER_COMMAND,
		KEY_ESCAPE_COMMAND,
		type LexicalEditor,
		LineBreakNode,
		ParagraphNode,
		RootNode,
		SELECTION_CHANGE_COMMAND,
		TextNode,
		createCommand,
		$getNodeByKey as getNodeByKey,
		$getSelection as getSelection,
		$isNodeSelection as isNodeSelection,
		$isRangeSelection as isRangeSelection
	} from 'lexical';
	import ContentEditable from '$lib/components/cisco/components/editor/ContentEditable.svelte';
	import ImageResizer from '$lib/components/cisco/components/editor/common/ImageResizer.svelte';
	import PlaceHolder from '$lib/components/cisco/components/editor/common/Placeholder.svelte';
	import ImageBroken from '$lib/components/icons/ImageBroken.svelte';
	import Nested from '../../../Nested.svelte';
	import AutoFocus from '../AutoFocus.svelte';
	import RichText from '../RichText.svelte';
	import { $isImageNode as isImageNode } from './ImageNode';
	import './ImageNodeStyles.css';

	export let src: string;
	export let altText: string;
	export let nodeKey: string;
	export let width: number | 'inherit';
	export let height: number | 'inherit';
	export let maxWidth: number | null = null;
	export let resizable: boolean = true;
	export let showCaption: boolean = false;
	export let caption: LexicalEditor;
	export let captionsEnabled: boolean = false;
	export let editor: LexicalEditor;

	$: heightCss = height === 'inherit' ? 'inherit' : height + 'px';
	$: widthCss = width === 'inherit' ? 'inherit' : width + 'px';

	let selection: BaseSelection | null = null;
	let imageRef: HTMLImageElement;
	let buttonRef: HTMLButtonElement;
	let isSelected = createNodeSelectionStore(editor, nodeKey);
	let isResizing = false;
	let activeEditorRef: LexicalEditor;

	$: draggable = $isSelected && isNodeSelection(selection) && !isResizing;
	$: isFocused = $isSelected || isResizing;

	let promise = new Promise((resolve, reject) => {
		if (imageCache.has(src)) {
			resolve(null);
		} else {
			const img = new Image();
			img.src = src;
			img.onload = () => {
				imageCache.add(src);
				resolve(null);
			};
			img.onerror = () => {
				reject(null);
			};
		}
	});
	const onDelete = (payload: any) => {
		if ($isSelected && isNodeSelection(getSelection())) {
			const event = payload;
			event.preventDefault();
			const node = getNodeByKey(nodeKey);
			if (isImageNode(node)) {
				node.remove();
				return true;
			}
		}
		return false;
	};
	const onEnter = (event: Event) => {
		const latestSelection = getSelection();
		const buttonElem = buttonRef;
		if ($isSelected && isNodeSelection(latestSelection) && latestSelection.getNodes().length === 1) {
			if (showCaption) {
				selection = null;
				event.preventDefault();
				caption.focus(
					() => {
						console.log('caption focused');
					},
					{ defaultSelection: 'rootStart' }
				);
				return true;
			} else if (buttonElem !== null && buttonElem !== document.activeElement) {
				event.preventDefault();
				buttonElem.focus();
				return true;
			}
		}
		return false;
	};
	const onEscape = (event: Event) => {
		if (activeEditorRef === caption || buttonRef === event.target) {
			selection = null;
			editor.update(() => {
				$isSelected = true;
				const parentRootElement = editor.getRootElement();
				if (parentRootElement !== null) {
					parentRootElement.focus();
				}
			});
			return true;
		}
		return false;
	};

	const onClick = (payload: MouseEvent) => {
		const event = payload;
		if (isResizing) {
			return true;
		}
		if (event.target === imageRef) {
			if (event.shiftKey) {
				$isSelected = !$isSelected;
			} else {
				clearSelection(editor);
				$isSelected = true;
			}
			return true;
		}
		return false;
	};

	const onRightClick = (event: any) => {
		editor.getEditorState().read(() => {
			const latestSelection = getSelection();
			const domElement = event.target;
			if (
				domElement &&
				domElement.tagName === 'IMG' &&
				isRangeSelection(latestSelection) &&
				latestSelection.getNodes().length === 1
			) {
				editor.dispatchCommand(RIGHT_CLICK_IMAGE_COMMAND, event);
			}
		});
	};

	onMount(() => {
		let isMounted = true;
		const rootElement = editor.getRootElement();
		const unregister = mergeRegister(
			editor.registerUpdateListener(({ editorState }) => {
				if (isMounted) {
					selection = editorState.read(() => getSelection());
				}
			}),
			editor.registerCommand(
				SELECTION_CHANGE_COMMAND,
				(_, activeEditor) => {
					activeEditorRef = activeEditor;
					return false;
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(CLICK_COMMAND, onClick, COMMAND_PRIORITY_LOW),
			editor.registerCommand(RIGHT_CLICK_IMAGE_COMMAND, onClick, COMMAND_PRIORITY_LOW),
			editor.registerCommand(
				DRAGSTART_COMMAND,
				(event) => {
					if (event.target === imageRef) {
						event.preventDefault();
						return true;
					}
					return false;
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(KEY_DELETE_COMMAND, onDelete, COMMAND_PRIORITY_LOW),
			editor.registerCommand(KEY_BACKSPACE_COMMAND, onDelete, COMMAND_PRIORITY_LOW),
			editor.registerCommand(KEY_ENTER_COMMAND, onEnter, COMMAND_PRIORITY_LOW),
			editor.registerCommand(KEY_ESCAPE_COMMAND, onEscape, COMMAND_PRIORITY_LOW)
		);
		rootElement?.addEventListener('contextmenu', onRightClick);
		return () => {
			isMounted = false;
			unregister();
			rootElement?.removeEventListener('contextmenu', onRightClick);
		};
	});

	const setShowCaption = () => {
		editor.update(() => {
			const node = getNodeByKey(nodeKey);
			if (isImageNode(node)) {
				node.setShowCaption(true);
			}
		});
	};

	const onResizeEnd = (nextWidth: number | 'inherit', nextHeight: number | 'inherit') => {
		setTimeout(() => {
			isResizing = false;
		}, 200);
		editor.update(() => {
			const node = getNodeByKey(nodeKey);
			if (isImageNode(node)) {
				node.setWidthAndHeight(nextWidth, nextHeight);
			}
		});
	};

	const onResizeStart = () => {
		isResizing = true;
	};

	const historyPlugin = getImageHistoryPluginType();
</script>

<div {draggable}>
	{#await promise}
		<p>...loading image</p>
	{:then _}
		<img
			class:focused={isFocused}
			class:draggable={isFocused && isNodeSelection(selection)}
			{src}
			alt={altText}
			bind:this={imageRef}
			style="height:{heightCss};max-width:{maxWidth}px;width:{widthCss};"
			draggable="false"
		/>
	{:catch _}
		<ImageBroken />
	{/await}
</div>
{#if showCaption}
	<div class="image-caption-container">
		<Nested
			initialEditor={caption}
			parentEditor={editor}
			initialNodes={[RootNode, TextNode, LineBreakNode, ParagraphNode, LinkNode, HashtagNode, KeywordNode]}
		>
			<AutoFocus />

			<svelte:component this={historyPlugin.componentType} {...historyPlugin.props} />

			<RichText />
			<ContentEditable className="ImageNode__contentEditable" />
			<PlaceHolder className="ImageNode__placeholder">Enter image caption...</PlaceHolder>
		</Nested>
	</div>
{/if}
{#if resizable && isNodeSelection(selection) && isFocused}
	<ImageResizer
		{showCaption}
		{setShowCaption}
		{editor}
		{buttonRef}
		{imageRef}
		{maxWidth}
		{onResizeStart}
		{onResizeEnd}
		{captionsEnabled}
	/>
{/if}
