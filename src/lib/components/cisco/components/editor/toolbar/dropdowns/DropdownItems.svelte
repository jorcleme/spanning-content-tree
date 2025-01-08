<script lang="ts">
	import { onMount } from 'svelte';
	import { setRegisterItemFunc } from '$lib/utils/editor';

	export let onClose: () => void;
	export let dropDownRef: HTMLDivElement;
	let items: any[] = [];
	let highlightedItem: any = null;
	function registerItem(itemRef: any) {
		items.push(itemRef);
		items = items;
	}
	setRegisterItemFunc(registerItem);
	function handleKeyDown(event: KeyboardEvent) {
		if (!items) return;
		const key = event.key;
		if (['Escape', 'ArrowUp', 'ArrowDown', 'Tab'].includes(key)) {
			event.preventDefault();
		}
		if (key === 'Escape' || key === 'Tab') {
			onClose();
		} else if (key === 'ArrowUp') {
			if (highlightedItem === null) {
				highlightedItem = items[0];
			} else {
				const index = items.indexOf(highlightedItem) - 1;
				highlightedItem = items[index === -1 ? items.length - 1 : index];
			}
		} else if (key === 'ArrowDown') {
			if (highlightedItem === null) {
				highlightedItem = items[0];
			} else {
				const index = items.indexOf(highlightedItem) + 1;
				highlightedItem = items[index >= items.length ? 0 : index];
			}
		}
	}
	onMount(() => {
		if (!highlightedItem) {
			highlightedItem = items[0];
		}
	});
	$: if (highlightedItem) {
		highlightedItem.focus();
	}
</script>

<!-- svelte-ignore a11y-no-static-element-interactions -->
<div
	class="dropdown block fixed shadow-md rounded-md min-h-[40px] bg-neutral-100 z-20"
	bind:this={dropDownRef}
	on:keydown={handleKeyDown}
>
	<slot />
</div>
