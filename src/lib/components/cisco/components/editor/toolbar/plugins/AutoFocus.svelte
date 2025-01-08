<script>
	import { onMount } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import { getCommands } from '$lib/utils/editor/plugins/commands';

	const editor = getEditor();
	onMount(() => {
		getCommands().FocusEditor.execute(editor);
	});
</script>
