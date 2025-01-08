<script lang="ts">
	import { onMount } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import { registerRichText } from '@lexical/rich-text';
	import Decorator from '../../Decorator.svelte';

	const editor = getEditor();
	onMount(() => registerRichText(editor));
</script>

<Decorator />
