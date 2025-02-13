<script lang="ts">
	import type { BlockType, BlockTypeContext } from '$lib/types';
	import { getContext, onMount } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import { $generateNodesFromDOM as generateNodesFromDOM } from '@lexical/html';
	import { $getRoot as getRoot } from 'lexical';

	export let ariaActiveDescendantID: string | undefined = void 0;
	export let ariaAutoComplete: 'list' | 'none' | 'inline' | 'both' | null = null;
	export let ariaControls: string | undefined = void 0;
	export let ariaDescribedBy: string | undefined = void 0;
	export let ariaExpanded: boolean | null = null;
	export let ariaLabel: string | undefined = void 0;
	export let ariaLabelledBy: string | undefined = void 0;
	export let ariaMultiline: boolean | null = null;
	export let ariaOwns: string | undefined = void 0;
	export let ariaRequired: boolean | null = null;
	export let autoCapitalize: string | undefined = void 0;
	export let className = 'content-editable';
	export let id: string = 'contenteditable';
	export let role: string = 'textbox';
	export let spellCheck: boolean = true;
	export let style: string | null = null;
	export let tabIndex: number = 0;
	export let testid: string = 'testid';
	export let content: string | null = null;

	let isEditable = false;
	const editor = getEditor();
	let ref: HTMLDivElement;

	const blockType: BlockTypeContext = getContext('blockType');

	$: isListType = $blockType === 'bullet' || $blockType === 'number' || $blockType === 'check';
	$: console.log('Current block type:', isListType);

	const getHTML = (tagType: BlockType) => {
		if (tagType === 'h1') {
			return `<h1 class="editor-heading-h1" dir="ltr">${content}</h1>`;
		} else if (tagType === 'h2') {
			return `<h2 class="editor-heading-h2" dir="ltr">${content}</h2>`;
		} else if (tagType === 'h3') {
			return `<h3 class="editor-heading-h3" dir="ltr">${content}</h3>`;
		} else if (tagType === 'h4') {
			return `<h4 class="editor-heading-h4" dir="ltr">${content}</h4>`;
		} else if (tagType === 'h5') {
			return `<h5 class="editor-heading-h5" dir="ltr">${content}</h5>`;
		} else if (tagType === 'h6') {
			return `<h6 class="editor-heading-h6" dir="ltr">${content}</h6>`;
		} else if (tagType === 'bullet') {
			return `<ul class="editor-list" dir="ltr">${content}</ul>`;
		} else if (tagType === 'paragraph') {
			return `<p class="editor-paragraph" dir="ltr">${content}</p>`;
		} else if (tagType === 'quote') {
			return `<blockquote class="editor-quote" dir="ltr">${content}</blockquote>`;
		} else {
			return `<p class="editor-paragraph" dir="ltr">${content}</p>`;
		}
	};

	onMount(() => {
		console.log('content: ', content);
		if (ref && ref.ownerDocument && ref.ownerDocument.defaultView) {
			editor.setRootElement(ref);
			if (content) {
				editor.update(() => {
					const html = content;
					const parser = new DOMParser();
					const dom = parser.parseFromString(html, 'text/html');
					console.log(dom.body);
					for (const child of dom.body.children) {
						if ((child.children.length === 0 && child.textContent === '') || child.textContent === null) {
							child.remove();
						}
					}
					console.log(`After removing empty nodes: ${dom.body}`);
					const nodes = generateNodesFromDOM(editor, dom);
					const root = getRoot();
					root.clear();
					root.append(...nodes);
				});
			}
		} else {
			editor.setRootElement(null);
		}
		isEditable = editor.isEditable();
		return editor.registerEditableListener((updated) => {
			isEditable = updated;
		});
	});
</script>

<!-- svelte-ignore a11y-no-noninteractive-tabindex -->
<div
	aria-activedescendant={!isEditable ? undefined : ariaActiveDescendantID}
	aria-autocomplete={!isEditable ? 'none' : ariaAutoComplete}
	aria-controls={!isEditable ? undefined : ariaControls}
	aria-describedby={ariaDescribedBy}
	aria-expanded={!isEditable ? undefined : role === 'combobox' ? !!ariaExpanded : undefined}
	aria-label={ariaLabel}
	aria-labelledby={ariaLabelledBy}
	aria-multiline={ariaMultiline}
	aria-owns={!isEditable ? null : ariaOwns}
	aria-readonly={!isEditable ? true : undefined}
	aria-required={ariaRequired}
	autocapitalize={autoCapitalize}
	class="{className} border-none text-base relative outline-none lg:p-2 p-4 min-h-[150px] w-full"
	contentEditable={isEditable}
	data-testid={testid}
	{id}
	bind:this={ref}
	{role}
	spellcheck={spellCheck}
	{style}
	tabindex={tabIndex}
/>
