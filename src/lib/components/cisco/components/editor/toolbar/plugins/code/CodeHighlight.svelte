<script lang="ts">
	import { onMount } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import { registerCodeHighlighting } from '@lexical/code';

	const editor = getEditor();

	onMount(() => {
		return registerCodeHighlighting(editor);
	});
</script>
