<script lang="ts">
	import { onMount } from 'svelte';
	import type { InitialEditorStateType } from '$lib/utils/editor';
	import { mergeRegister } from '@lexical/utils';
	import {
		type Binding,
		CONNECTED_COMMAND,
		type Provider,
		TOGGLE_CONNECT_COMMAND,
		initLocalState,
		syncCursorPositions,
		syncLexicalUpdateToYjs,
		syncYjsChangesToLexical
	} from '@lexical/yjs';
	import {
		COMMAND_PRIORITY_EDITOR,
		type EditorState,
		type LexicalEditor,
		$createParagraphNode as createParagraphNode,
		$getRoot as getRoot,
		$getSelection as getSelection
	} from 'lexical';
	import { type Doc, Transaction, UndoManager, YEvent } from 'yjs';
	import type { YText } from 'yjs/dist/src/internals';

	export let editor: LexicalEditor;
	export let id: string;
	export let provider: Provider;
	export let binding: Binding;
	export let docMap: Map<string, Doc>;
	export let name: string;
	export let color: string;
	export let shouldBootstrap: boolean;
	export let cursorsContainerRef: HTMLElement | null = null;
	export let initialEditorState: InitialEditorStateType | null = null;
	export let awarenessData: object | undefined = void 0;

	let isReloadingDoc = false;
	let doc = docMap.get(id);
	const connect = () => {
		provider.connect();
	};
	const disconnect = () => {
		try {
			provider.disconnect();
		} catch (e) {}
	};
	const setupCollaborationProvider = () => {
		const { root } = binding;
		const { awareness } = provider;
		const onStatus = ({ status }: { status: string }) => {
			editor.dispatchCommand(CONNECTED_COMMAND, status === 'connected');
		};
		const onSync = (isSynced: boolean) => {
			if (shouldBootstrap && isSynced && root.isEmpty() && root._xmlText._length === 0 && isReloadingDoc === false) {
				configureEditor(editor, initialEditorState);
			}
			isReloadingDoc = false;
		};
		const onAwarenessUpdate = () => {
			syncCursorPositions(binding, provider);
		};

		const onYjsTreeChanges = (events: Array<YEvent<YText>>, transaction: Transaction) => {
			const origin = transaction.origin;
			if (origin !== binding) {
				const isFromUndoManger = origin instanceof UndoManager;
				syncYjsChangesToLexical(binding, provider, events, isFromUndoManger);
			}
		};

		initLocalState(provider, name, color, document.activeElement === editor.getRootElement(), awarenessData || {});

		const onProviderDocReload = (ydoc: Doc) => {
			resetEditorWithoutCollab(editor, binding);
			doc = ydoc;
			docMap.set(id, ydoc);
			isReloadingDoc = true;
		};

		provider.on('reload', onProviderDocReload);
		provider.on('status', onStatus);
		provider.on('sync', onSync);
		awareness.on('update', onAwarenessUpdate);

		root.getSharedType().observeDeep(onYjsTreeChanges);

		const removeListener = editor.registerUpdateListener(
			({ prevEditorState, editorState, dirtyLeaves, dirtyElements, normalizedNodes, tags }) => {
				if (tags.has('skip-collab') === false) {
					syncLexicalUpdateToYjs(
						binding,
						provider,
						prevEditorState,
						editorState,
						dirtyElements,
						dirtyLeaves,
						normalizedNodes,
						tags
					);
				}
			}
		);
		connect();
		return () => {
			if (isReloadingDoc === false) {
				disconnect();
			}
			provider.off('sync', onSync);
			provider.off('status', onStatus);
			provider.off('reload', onProviderDocReload);
			awareness.off('update', onAwarenessUpdate);
			root.getSharedType().unobserveDeep(onYjsTreeChanges);
			docMap.delete(id);
			removeListener();
		};
	};
	const setupCursorsPanel = () => {
		const ref = document.createElement('div');
		const target = cursorsContainerRef || document.body;
		target.appendChild(ref);
		binding.cursorsContainer = ref;
		return () => {
			if (ref?.parentNode) {
				ref.parentNode?.removeChild(ref);
			}
		};
	};
	onMount(() => {
		return mergeRegister(
			setupCursorsPanel(),
			setupCollaborationProvider(),
			editor.registerCommand(
				TOGGLE_CONNECT_COMMAND,
				(payload) => {
					if (connect !== void 0 && disconnect !== void 0) {
						const shouldConnect = payload;
						if (shouldConnect) {
							console.log('Collaboration connected!');
							connect();
						} else {
							console.log('Collaboration disconnected!');
							disconnect();
						}
					}
					return true;
				},
				COMMAND_PRIORITY_EDITOR
			)
		);
	});
	const configureEditor = (
		editor2: LexicalEditor,
		initialEditorState2: EditorState | string | InitialEditorStateType
	) => {
		editor2.update(
			() => {
				const root = getRoot();
				if (root.isEmpty()) {
					if (initialEditorState2) {
						switch (typeof initialEditorState2) {
							case 'string': {
								const parsedEditorState = editor2.parseEditorState(initialEditorState2);
								editor2.setEditorState(parsedEditorState, {
									tag: 'history-merge'
								});
								break;
							}
							case 'object': {
								editor2.setEditorState(initialEditorState2, {
									tag: 'history-merge'
								});
								break;
							}
							case 'function': {
								editor2.update(
									() => {
										const root1 = getRoot();
										if (root1.isEmpty()) {
											initialEditorState2(editor2);
										}
									},
									{ tag: 'history-merge' }
								);
								break;
							}
						}
					} else {
						const paragraph = createParagraphNode();
						root.append(paragraph);
						const { activeElement } = document;
						if (getSelection() !== null || (activeElement !== null && activeElement === editor2.getRootElement())) {
							paragraph.select();
						}
					}
				}
			},
			{
				tag: 'history-merge'
			}
		);
	};
	const resetEditorWithoutCollab = (editor2: LexicalEditor, binding2: Binding) => {
		editor2.update(
			() => {
				const root = getRoot();
				root.clear();
				root.select();
			},
			{
				tag: 'skip-collab'
			}
		);
		if (binding2.cursors == null) {
			return;
		}
		const cursors = binding2.cursors;
		if (cursors == null) {
			return;
		}
		const cursorsContainer = binding2.cursorsContainer;
		if (cursorsContainer == null) {
			return;
		}
		const cursorsArr = Array.from(cursors.values());
		for (let i = 0; i < cursorsArr.length; i++) {
			const cursor = cursorsArr[i];
			const selection = cursor.selection;
			if (selection && selection.selections != null) {
				const selections = selection.selections;
				for (let j = 0; j < selections.length; j++) {
					cursorsContainer.removeChild(selections[i]);
				}
			}
		}
	};
</script>
