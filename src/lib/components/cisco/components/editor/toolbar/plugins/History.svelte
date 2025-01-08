<script lang="ts">
	import { onMount } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import { createEmptyHistoryState, registerHistory } from '@lexical/history';

	const editor = getEditor();
	export let externalHistoryState = createEmptyHistoryState();
	export let delay = 1e3;
	onMount(() => registerHistory(editor, externalHistoryState, delay));
</script>
