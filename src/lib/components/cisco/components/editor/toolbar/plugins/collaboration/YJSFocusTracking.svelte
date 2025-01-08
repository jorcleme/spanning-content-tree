<script lang="ts">
	import { onMount } from 'svelte';
	import { mergeRegister } from '@lexical/utils';
	import { type Provider, setLocalStateFocus } from '@lexical/yjs';
	import { BLUR_COMMAND, COMMAND_PRIORITY_EDITOR, FOCUS_COMMAND, type LexicalEditor } from 'lexical';

	export let editor: LexicalEditor;
	export let provider: Provider;
	export let name: string;
	export let color: string;
	export let awarenessData: object | undefined = void 0;

	onMount(() => {
		return mergeRegister(
			editor.registerCommand(
				FOCUS_COMMAND,
				() => {
					setLocalStateFocus(provider, name, color, true, awarenessData || {});
					return false;
				},
				COMMAND_PRIORITY_EDITOR
			),
			editor.registerCommand(
				BLUR_COMMAND,
				() => {
					setLocalStateFocus(provider, name, color, false, awarenessData || {});
					return false;
				},
				COMMAND_PRIORITY_EDITOR
			)
		);
	});
</script>
