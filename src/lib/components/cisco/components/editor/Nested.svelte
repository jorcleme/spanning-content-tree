<script lang="ts">
	import { onMount, setContext } from 'svelte';
	import type { EditorThemeClasses, Klass, LexicalEditor, LexicalNode } from 'lexical';

	export let initialEditor: LexicalEditor;
	export let parentEditor: LexicalEditor;
	export let initialTheme: EditorThemeClasses | null = null;
	export let initialNodes: ReadonlyArray<Klass<LexicalNode>> | null = null;
	function getTransformSetFromKlass(klass: any) {
		const transform = klass.transform();
		return transform !== null ? new Set([transform]) : new Set();
	}
	setContext('editor', initialEditor);
	const composerTheme = initialTheme || parentEditor._config.theme;
	if (composerTheme) {
		initialEditor._config.theme = composerTheme;
	}
	initialEditor._parentEditor = parentEditor;
	if (initialNodes) {
		for (const klass of initialNodes) {
			const type = klass.getType();
			const registeredKlass = initialEditor._nodes.get(klass.getType());
			initialEditor._nodes.set(type, {
				exportDOM: registeredKlass ? registeredKlass.exportDOM : void 0,
				klass,
				replace: null,
				replaceWithKlass: null,
				transforms: new Set()
			});
		}
	} else {
		const parentNodes = (initialEditor._nodes = new Map(parentEditor._nodes));
		for (const [type, entry] of parentNodes) {
			initialEditor._nodes.set(type, {
				exportDOM: entry.exportDOM,
				klass: entry.klass,
				replace: entry.replace,
				replaceWithKlass: entry.replaceWithKlass,
				transforms: getTransformSetFromKlass(entry.klass)
			});
		}
	}

	initialEditor._config.namespace = parentEditor._config.namespace;
	initialEditor._editable = parentEditor._editable;
	onMount(() => {
		return parentEditor.registerEditableListener((editable) => {
			initialEditor.setEditable(editable);
		});
	});
</script>

<slot />
