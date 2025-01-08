<script lang="ts">
	import type { i18nType } from '$lib/types';
	import { createEventDispatcher, getContext } from 'svelte';
	import { getModels as _getModels } from '$lib/apis';
	import { getArticlesByUser as _getArticlesByUser } from '$lib/apis/articles';
	import { getActiveEditor } from '$lib/utils/editor';
	import Modal from '$lib/components/common/Modal.svelte';
	import Input from '../../common/Input.svelte';
	import { INSERT_IMAGE_COMMAND } from '../plugins/image/ImagePlugin.svelte';

	const i18n: i18nType = getContext('i18n');
	const activeEditor = getActiveEditor();
	const dispatch = createEventDispatcher();

	export let show = false;

	let src: string = '';
	let altText: string = '';
	$: isDisabled = src === '' || src === undefined || src === null;
</script>

<Modal bind:show>
	<div class="text-gray-700 dark:text-gray-100">
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-1">
			<div class=" text-lg font-medium self-center">{$i18n.t('Insert Image')}</div>
			<button
				class="self-center"
				on:click={() => {
					show = false;
				}}
			>
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>

		<div class="py-10 px-4">
			<Input
				label="Image URL"
				placeholder="i.e. https://cisco.com/image.jpg"
				bind:value={src}
				id="lexical-modal-image-url"
			/>
			<Input
				label="Alt Text"
				placeholder="i.e. A beautiful image"
				bind:value={altText}
				id="lexical-modal-image-alttext"
			/>
			<div class="flex justify-end mt-5">
				<button
					data-test-id="image-modal-confirm-btn"
					disabled={isDisabled}
					class="py-2.5 px-4 bg-[#007bff] text-white font-bold rounded-md cursor-pointer hover:bg-[#0056b3]"
					on:click={() => {
						$activeEditor.dispatchCommand(INSERT_IMAGE_COMMAND, { altText, src });
						dispatch('confirm', { editor: $activeEditor });
					}}
				>
					{$i18n.t('Confirm')}
				</button>
			</div>
		</div>
	</div>
</Modal>
