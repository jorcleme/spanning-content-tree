<script lang="ts">
	import { setImageHistoryPluginType } from '$lib/utils/editor';
	import type { Provider } from '@lexical/yjs';
	import type { Doc } from 'yjs';
	import CollaborationPlugin from '../collaboration/CollaborationPlugin.svelte';

	export let providerFactory: (id: string, yjsDocMap: Map<string, Doc>) => Provider;

	setImageHistoryPluginType({
		componentType: CollaborationPlugin,
		props: {
			providerFactory,
			shouldBootstrap: true
		}
	});
</script>
