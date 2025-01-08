<script lang="ts">
	import type { CodeLanguageContext, SelectedElementKeyContext, i18nType } from '$lib/types';
	import { getContext } from 'svelte';
	import { getActiveEditor, getIsEditable } from '$lib/utils/editor';
	import { CODE_LANGUAGE_FRIENDLY_NAME_MAP, getLanguageFriendlyName, $isCodeNode as isCodeNode } from '@lexical/code';
	import { $getNodeByKey as getNodeByKey } from 'lexical';
	import DropdownItem from './DropdownItem.svelte';
	import EditorDropdown from './EditorDropdown.svelte';

	const i18n: i18nType = getContext('i18n');

	const activeEditor = getActiveEditor();
	const isEditable = getIsEditable();
	const selectedElementKey: SelectedElementKeyContext = getContext('selectedElementKey');
	const codeLanguage: CodeLanguageContext = getContext('codeLanguage');

	const getCodeLanguageOptions = () => {
		const options = [];
		for (const [lang, friendlyName] of Object.entries(CODE_LANGUAGE_FRIENDLY_NAME_MAP)) {
			options.push([lang, friendlyName]);
		}
		return options;
	};

	const CODE_LANGUAGE_OPTIONS = getCodeLanguageOptions();

	const onCodeLanguageSelect = (value: string) => {
		$activeEditor.update(() => {
			if ($selectedElementKey !== null) {
				const node = getNodeByKey($selectedElementKey);
				if (isCodeNode(node)) {
					node.setLanguage(value);
				}
			}
		});
	};
</script>

<EditorDropdown
	disabled={!$isEditable}
	buttonClassName="toolbar-item code-language"
	buttonLabel={getLanguageFriendlyName($codeLanguage)}
	buttonAriaLabel="Select language"
>
	{#each CODE_LANGUAGE_OPTIONS as [value, name]}
		<DropdownItem
			class={`item ${value === $codeLanguage ? 'active dropdown-item-active' : ''}`}
			on:click={() => onCodeLanguageSelect(value)}
		>
			<span class="text">{name}</span>
		</DropdownItem>
	{/each}
</EditorDropdown>
