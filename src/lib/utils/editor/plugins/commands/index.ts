import type { LexicalEditor } from 'lexical';
import { INSERT_IMAGE_COMMAND } from '$lib/components/cisco/components/editor/toolbar/plugins/image/ImagePlugin.svelte';

const commands = {
	InsertImage: {
		execute: (editor: LexicalEditor, payload: any) => {
			editor.dispatchCommand(INSERT_IMAGE_COMMAND, payload);
		}
	},
	FocusEditor: {
		execute: (editor: LexicalEditor, defaultSelection = undefined) => {
			editor.focus(
				() => {
					// If we try and move selection to the same point with setBaseAndExtent, it won't
					// trigger a re-focus on the element. So in the case this occurs, we'll need to correct it.
					// Normally this is fine, Selection API !== Focus API, but for the intents of the naming
					// of this plugin, which should preserve focus too.
					const activeElement = document.activeElement;
					const rootElement = editor.getRootElement();
					if (rootElement !== null && (activeElement === null || !rootElement.contains(activeElement))) {
						// Note: preventScroll won't work in Webkit.
						rootElement.focus({ preventScroll: true });
					}
				},
				{ defaultSelection }
			);
		}
	}
};
export function getCommands() {
	return commands;
}
