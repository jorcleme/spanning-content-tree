<script lang="ts">
	import type { Writable } from 'svelte/store';
	import { onMount } from 'svelte';
	import { getSelectedNode, sanitizeUrl, setFloatingAnchorPosition } from '$lib/utils/editor';
	import {
		TOGGLE_LINK_COMMAND,
		$createLinkNode as createLinkNode,
		$isAutoLinkNode as isAutoLinkNode,
		$isLinkNode as isLinkNode
	} from '@lexical/link';
	import { $findMatchingParent as findMatchingParent, mergeRegister } from '@lexical/utils';
	import type { BaseSelection, LexicalEditor } from 'lexical';
	import {
		COMMAND_PRIORITY_HIGH,
		COMMAND_PRIORITY_LOW,
		KEY_ESCAPE_COMMAND,
		SELECTION_CHANGE_COMMAND,
		$getSelection as getSelection,
		$isRangeSelection as isRangeSelection
	} from 'lexical';
	import { CircleCheck, CircleX, Pencil, Trash } from 'lucide-svelte';

	export let editor: LexicalEditor;
	export let isLink: Writable<boolean>;
	export let anchorElem: HTMLElement;
	export let isEditMode: Writable<boolean>;

	let editorRef: HTMLDivElement;
	let inputRef: HTMLInputElement;
	let linkUrl = '';
	let editedLinkUrl = '';

	let lastSelection: BaseSelection | null = null;

	$: if ($isEditMode && inputRef) {
		inputRef.focus();
	}
	$: if (anchorElem && editorRef) {
		anchorElem.appendChild(editorRef);
	}
	onMount(() => {
		const scrollerElem = anchorElem.parentElement;
		const update = () => {
			editor.getEditorState().read(() => {
				updateLinkEditor();
			});
		};
		window.addEventListener('resize', update);
		if (scrollerElem) {
			scrollerElem.addEventListener('scroll', update);
		}
		return mergeRegister(
			() => {
				window.removeEventListener('resize', update);
				if (scrollerElem) {
					scrollerElem.removeEventListener('scroll', update);
				}
			},
			editor.registerUpdateListener(({ editorState }) => {
				editorState.read(() => {
					updateLinkEditor();
				});
			}),
			editor.registerCommand(
				SELECTION_CHANGE_COMMAND,
				() => {
					updateLinkEditor();
					return true;
				},
				COMMAND_PRIORITY_LOW
			),
			editor.registerCommand(
				KEY_ESCAPE_COMMAND,
				() => {
					if ($isLink) {
						$isLink = false;
						return true;
					}
					return false;
				},
				COMMAND_PRIORITY_HIGH
			)
		);
	});
	function updateLinkEditor() {
		const selection = getSelection();
		if (isRangeSelection(selection)) {
			const node = getSelectedNode(selection);
			const linkParent = findMatchingParent(node, isLinkNode);
			if (isLinkNode(linkParent)) {
				linkUrl = linkParent.getURL();
			} else if (isLinkNode(node)) {
				linkUrl = node.getURL();
			} else {
				linkUrl = '';
			}
		}
		if ($isEditMode) {
			editedLinkUrl = linkUrl;
		}
		const editorElem = editorRef;
		const nativeSelection = window.getSelection();
		const activeElement = document.activeElement;
		if (editorElem === null) {
			return;
		}
		const rootElement = editor.getRootElement();
		if (
			selection !== null &&
			nativeSelection !== null &&
			rootElement !== null &&
			rootElement.contains(nativeSelection.anchorNode) &&
			editor.isEditable()
		) {
			const domRect = nativeSelection.focusNode?.parentElement?.getBoundingClientRect();
			if (domRect) {
				domRect.y += 40;
				setFloatingAnchorPosition(domRect, editorElem, anchorElem);
			}
			lastSelection = selection;
		} else if (!activeElement || activeElement.className !== 'link-input') {
			if (rootElement !== null) {
				setFloatingAnchorPosition(null, editorElem, anchorElem);
			}
			lastSelection = null;
			$isEditMode = false;
			linkUrl = '';
		}
		return true;
	}
	function monitorInputInteraction(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			event.preventDefault();
			handleLinkSubmission();
		} else if (event.key === 'Escape') {
			event.preventDefault();
			$isEditMode = false;
		}
	}
	function handleLinkSubmission() {
		if (lastSelection !== null) {
			if (linkUrl !== '') {
				editor.dispatchCommand(TOGGLE_LINK_COMMAND, sanitizeUrl(editedLinkUrl));
				editor.update(() => {
					const selection = getSelection();
					if (isRangeSelection(selection)) {
						const parent = getSelectedNode(selection).getParent();
						if (isAutoLinkNode(parent)) {
							const linkNode = createLinkNode(parent.getURL(), {
								rel: parent.__rel,
								target: parent.__target,
								title: parent.__title
							});
							parent.replace(linkNode, true);
						}
					}
				});
			}
			$isEditMode = false;
		}
	}
</script>

<!-- svelte-ignore a11y-interactive-supports-focus -->

<div
	bind:this={editorRef}
	class="link-editor flex items-center absolute top-0 left-0 z-10 max-w-[400px] w-full opacity-0 bg-white shadow-md rounded-b-8 transition-opacity duration-500 will-change-transform"
>
	{#if $isLink}
		{#if $isEditMode}
			<input
				bind:this={inputRef}
				class="link-input block w-[calc(100%-75px)] box-border m-3 p-2 rounded-lg bg-gray-100 text-gray-800 border-none outline-none relative"
				bind:value={editedLinkUrl}
				on:keydown={(event) => {
					monitorInputInteraction(event);
				}}
			/>
			<div>
				<button
					on:click={() => {
						$isEditMode = false;
					}}
					on:mousedown|preventDefault><CircleX class="w-5 h-5" /></button
				>

				<!-- svelte-ignore a11y-click-events-have-key-events -->
				<button on:click={handleLinkSubmission} on:mousedown|preventDefault>
					<CircleCheck class="w-5 h-5" />
				</button>
			</div>
		{:else}
			<div
				class="link-view block w-[calc(100%-24px)] my-2 mx-3 py-2 px-3 rounded-lg bg-gray-100 text-gray-800 border-none outline-none relative"
			>
				<a
					class="block break-words w-[calc(100%-33px)]"
					href={sanitizeUrl(linkUrl)}
					target="_blank"
					rel="noopener noreferrer"
				>
					{linkUrl}
				</a>
				<button
					type="button"
					class="w-[35px] absolute right-[30px] top-0 bottom-0 align-[-0.25em] cursor-pointer"
					on:mousedown|preventDefault
					on:click={() => {
						editedLinkUrl = linkUrl;
						$isEditMode = true;
					}}
				>
					<Pencil class="w-5 h-5" />
				</button>
				<button
					type="button"
					class="w-[35px] absolute right-0 top-0 bottom-0 align-[-0.25em] cursor-pointer"
					on:mousedown|preventDefault
					on:click={() => {
						editor.dispatchCommand(TOGGLE_LINK_COMMAND, null);
					}}
				>
					<Trash class="w-5 h-5" />
				</button>
			</div>
		{/if}
	{/if}
</div>
