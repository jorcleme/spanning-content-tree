<script lang="ts">
	import { onMount } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import { createBinding } from '@lexical/yjs';
	import YJSCollaboration from './YJSCollaboration.svelte';
	import YJSFocusTracking from './YJSFocusTracking.svelte';
	import YJSHistory from './YJSHistory.svelte';
	import { useCollaborationContext } from './CollaborationContext.js';

	const editor = getEditor();

	export let id = editor.getKey();
	export let providerFactory;
	export let shouldBootstrap;
	export let username = void 0;
	export let cursorColor = void 0;
	export let cursorsContainerRef = null;
	export let initialEditorState = null;
	export let excludedProperties = void 0;
	export let awarenessData = void 0;

	const collabContext = useCollaborationContext(username, cursorColor);
	const { yjsDocMap, name, color } = collabContext;
	const provider = providerFactory(id, yjsDocMap);
	const doc = yjsDocMap.get(id);
	const binding = createBinding(editor, provider, id, doc, yjsDocMap, excludedProperties);

	collabContext.clientID = binding.clientID;
	collabContext.isCollabActive = true;

	onMount(() => {
		return () => {
			if (editor._parentEditor == null) {
				collabContext.isCollabActive = false;
			}
		};
	});
</script>

<YJSCollaboration
	{editor}
	{id}
	{provider}
	{binding}
	docMap={yjsDocMap}
	{name}
	{color}
	{shouldBootstrap}
	{cursorsContainerRef}
	{initialEditorState}
	{awarenessData}
/>

<YJSHistory {editor} {binding} />
<YJSFocusTracking {editor} {provider} {name} {color} {awarenessData} />
