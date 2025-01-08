<script lang="ts">
	import { onMount } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import { $canShowPlaceholderCurry as canShowPlaceholderCurry } from '@lexical/text';
	import { mergeRegister } from '@lexical/utils';
	import type { LexicalEditor } from 'lexical';

	export let className = 'placeholder';

	const editor = getEditor();
	let canShowPlaceHolder = true;

	onMount(() => {
		return mergeRegister(
			editor.registerUpdateListener(() => {
				canShowPlaceHolder = canShowPlaceholder(editor);
			}),
			editor.registerEditableListener(() => {
				canShowPlaceHolder = canShowPlaceholder(editor);
			})
		);
	});

	const canShowPlaceholder = (editor: LexicalEditor) => {
		const currentCanShowPlaceholder = editor.getEditorState().read(canShowPlaceholderCurry(editor.isComposing()));
		return currentCanShowPlaceholder;
	};
</script>

{#if canShowPlaceHolder}
	<div
		class="{className} text-base text-gray-100 overflow-hidden absolute text-ellipsis top-2 left-2.5 right-7 lg:left-2"
	>
		<slot />
	</div>
{/if}
