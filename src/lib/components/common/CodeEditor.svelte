<script lang="ts">
	import type { i18nType } from '$lib/types';
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { formatPythonCode } from '$lib/apis/utils';
	import { acceptCompletion } from '@codemirror/autocomplete';
	import { indentWithTab } from '@codemirror/commands';
	import { python } from '@codemirror/lang-python';
	import { indentUnit } from '@codemirror/language';
	import { Compartment, EditorState } from '@codemirror/state';
	import { oneDark } from '@codemirror/theme-one-dark';
	import { keymap, placeholder } from '@codemirror/view';
	import { EditorView, basicSetup } from 'codemirror';

	const dispatch = createEventDispatcher();
	const i18n: i18nType = getContext('i18n');

	export let boilerplate = '';
	export let value = '';

	let codeEditor: EditorView;

	let isDarkMode = false;
	let editorTheme = new Compartment();

	export const formatPythonCodeHandler = async () => {
		if (codeEditor) {
			const res = await formatPythonCode(value).catch((error) => {
				toast.error(error);
				return null;
			});

			if (res && res.code) {
				const formattedCode = res.code;
				codeEditor.dispatch({
					changes: [{ from: 0, to: codeEditor.state.doc.length, insert: formattedCode }]
				});

				toast.success($i18n.t('Code formatted successfully'));
				return true;
			}
			return false;
		}
		return false;
	};

	let extensions = [
		basicSetup,
		keymap.of([{ key: 'Tab', run: acceptCompletion }, indentWithTab]),
		python(),
		indentUnit.of('    '),
		placeholder('Enter your code here...'),
		EditorView.updateListener.of((e) => {
			if (e.docChanged) {
				value = e.state.doc.toString();
			}
		}),
		editorTheme.of([])
	];

	onMount(() => {
		console.log(value);
		if (value === '') {
			value = boilerplate;
		}

		// Check if html class has dark mode
		isDarkMode = document.documentElement.classList.contains('dark');

		// python code editor, highlight python code
		codeEditor = new EditorView({
			state: EditorState.create({
				doc: value,
				extensions: extensions
			}),
			parent: document.getElementById('code-textarea') as Element
		});

		if (isDarkMode) {
			codeEditor.dispatch({
				effects: editorTheme.reconfigure(oneDark)
			});
		}

		// listen to html class changes this should fire only when dark mode is toggled
		const observer = new MutationObserver((mutations) => {
			mutations.forEach((mutation) => {
				if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
					const _isDarkMode = document.documentElement.classList.contains('dark');

					if (_isDarkMode !== isDarkMode) {
						isDarkMode = _isDarkMode;
						if (_isDarkMode) {
							codeEditor.dispatch({
								effects: editorTheme.reconfigure(oneDark)
							});
						} else {
							codeEditor.dispatch({
								effects: editorTheme.reconfigure([])
							});
						}
					}
				}
			});
		});

		observer.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ['class']
		});

		const keydownHandler = async (e: KeyboardEvent) => {
			if ((e.ctrlKey || e.metaKey) && e.key === 's') {
				e.preventDefault();
				dispatch('save');
			}

			// Format code when Ctrl + Shift + F is pressed
			if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'f') {
				e.preventDefault();
				await formatPythonCodeHandler();
			}
		};

		document.addEventListener('keydown', keydownHandler);

		return () => {
			observer.disconnect();
			document.removeEventListener('keydown', keydownHandler);
		};
	});
</script>

<div id="code-textarea" class="h-full w-full" />
