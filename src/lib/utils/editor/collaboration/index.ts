import type { Provider } from 'svelte-lexical';
import { WebsocketProvider } from 'y-websocket';
import { Doc } from 'yjs';

export const createWebsocketProvider = (id: string, yjsDocMap: Map<string, Doc>): Provider => {
	const url = new URL(window.location.href);
	const params = new URLSearchParams(url.search);
	const WEBSOCKET_ENDPOINT = params.get('collabEndpoint') || 'ws://localhost:1234';
	const WEBSOCKET_SLUG = 'cisco-admin-editor';
	const WEBSOCKET_ID = params.get('collabId') || '0';

	let doc = yjsDocMap.get(id);

	if (doc === undefined) {
		doc = new Doc();
		yjsDocMap.set(id, doc);
	} else {
		doc.load();
	}

	return new WebsocketProvider(WEBSOCKET_ENDPOINT, WEBSOCKET_SLUG + '/' + WEBSOCKET_ID + '/' + id, doc, {
		connect: false
	}) as unknown as Provider;
};
