<script lang="ts">
	import type { BlockType, i18nType } from '$lib/types';

	import { createEventDispatcher, getContext } from 'svelte';

	import { editSectionId } from '$lib/stores';
	import '@harbor/elements/button';
	import '@harbor/elements/dropdown';
	import { deviceGenericDevice } from '@harbor/elements/icons';
	import '@harbor/elements/menu';
	import '@harbor/elements/menu-item';
	import '@harbor/elements/option';

	export let sections: { id: string; title: string; content: string; tag: BlockType }[] = [];

	const i18n: i18nType = getContext('i18n');
	const dispatch = createEventDispatcher();

	const handleSelect = (e: CustomEvent<{ item: { value: string } }>) => {
		console.log(e.detail.item.value);
		editSectionId.set(e.detail.item.value.trim());
		dispatch('edit', { id: e.detail.item.value.trim() });
	};
</script>

<div class="flex">
	<hbr-dropdown on:hbr-select={handleSelect}>
		<hbr-icon size="6" sentiment="interact" asset={deviceGenericDevice} slot="prefix" />
		<hbr-button slot="trigger" variant="outline" caret>{$i18n.t('Edit')}</hbr-button>
		<hbr-menu>
			{#each sections as { id, title }, i (i)}
				<hbr-menu-item value={id}>{$i18n.t(`${title.charAt(0).toUpperCase()}` + `${title.slice(1)}`)}</hbr-menu-item>
			{/each}
		</hbr-menu>
	</hbr-dropdown>
</div>

<style>
	div[slot='trigger'] {
		display: flex;
		align-items: center;
	}
</style>
