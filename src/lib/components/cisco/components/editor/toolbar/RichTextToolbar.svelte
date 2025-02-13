<script lang="ts">
	import { getCommands } from '$lib/utils/editor/plugins/commands';
	import type { HeadingTagType } from '@lexical/rich-text';
	import { type LexicalEditor, $getRoot as getRoot, $getSelection as getSelection } from 'lexical';
	import Divider from '../common/Divider.svelte';
	import Toolbar from './Toolbar.svelte';
	import BoldButton from './buttons/BoldButton.svelte';
	import InsertCodeButton from './buttons/InsertCodeButton.svelte';
	import InsertLink from './buttons/InsertLink.svelte';
	import ItalicButton from './buttons/ItalicButton.svelte';
	import RedoButton from './buttons/RedoButton.svelte';
	import RegenerateAi from './buttons/RegenerateAI.svelte';
	import StrikethroughButton from './buttons/StrikethroughButton.svelte';
	import UnderlineButton from './buttons/UnderlineButton.svelte';
	import UndoButton from './buttons/UndoButton.svelte';
	import CodeLanguageDropdown from './dropdowns/CodeLanguageDropdown.svelte';
	import FontFamilyDropdown from './dropdowns/FontFamilyDropdown.svelte';
	import FontSizeDropdown from './dropdowns/FontSizeDropdown.svelte';
	import InsertDropdown from './dropdowns/InsertDropdown.svelte';
	import TextStyleDropdown from './dropdowns/TextStyleDropdown.svelte';
	import BulletListItem from './dropdowns/items/BulletListItem.svelte';
	import CheckListItem from './dropdowns/items/CheckListItem.svelte';
	import CodeBlockItem from './dropdowns/items/CodeBlockItem.svelte';
	import HeadingItem from './dropdowns/items/HeadingItem.svelte';
	import NumberListItem from './dropdowns/items/NumberListItem.svelte';
	import InsertColumnsModal from './modals/InsertColumnsModal.svelte';
	import InsertImageModal from './modals/InsertImageModal.svelte';
	import { ChevronDown, Plus } from 'lucide-svelte';

	let show;
	let showImageModal = false;
	let showColumnModal = false;

	const onInsertColumnClick = () => {
		showColumnModal = true;
	};

	const onInsertImageClick = () => {
		showImageModal = true;
	};

	const onConfirm = (event: CustomEvent<{ editor: LexicalEditor }>) => {
		getCommands().FocusEditor.execute(event.detail.editor);
		showImageModal = false;
	};

	const HEADING_ITEMS: Array<HeadingTagType> = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
</script>

<Toolbar let:editor let:activeEditor let:blockType>
	<UndoButton />
	<RedoButton />
	<Divider />
	{#if activeEditor === editor}
		<TextStyleDropdown>
			{#each HEADING_ITEMS as HEADING, i (i)}
				<HeadingItem headingSize={HEADING} />
			{/each}
			<BulletListItem />
			<NumberListItem />
			<CheckListItem />
			<CodeBlockItem />
		</TextStyleDropdown>
		<Divider />
	{/if}
	{#if blockType === 'code'}
		<CodeLanguageDropdown />
	{:else}
		<FontFamilyDropdown />
		<FontSizeDropdown />
		<Divider />
		<BoldButton />
		<ItalicButton />
		<UnderlineButton />
		<StrikethroughButton />
		<InsertCodeButton />
		<InsertLink />
		<Divider />
		<RegenerateAi {editor} params={{}} />
		<Divider />
		<InsertDropdown {onInsertImageClick} {onInsertColumnClick}>
			<button
				class="flex items-center mr-1 justify-between bg-neutral-50 rounded-md p-2.5 text-neutral-500 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 border-none cursor-pointer align-middle shrink-0"
				on:click={() => (show = true)}
			>
				<span><Plus class="w-4 h-4 text-neutral-500 mr-2" /></span>
				<span>Insert</span>
				<span><ChevronDown class="w-4 h-4 text-neutral-500 ml-2" /></span>
			</button>
		</InsertDropdown>
		<Divider />
		<!-- modals -->
		<InsertImageModal bind:show={showImageModal} on:confirm={onConfirm} />
		<InsertColumnsModal bind:show={showColumnModal} />
	{/if}
</Toolbar>
