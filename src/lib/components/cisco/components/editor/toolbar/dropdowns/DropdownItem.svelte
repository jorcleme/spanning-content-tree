<script lang="ts">
	import { onMount } from 'svelte';
	import { getRegisterItemFunc } from '$lib/utils/editor';

	let className;

	export { className as class };
	export let title = void 0;
	export let ariaLabel = void 0;

	let ref: HTMLButtonElement;
	const registerItem = getRegisterItemFunc();

	if (registerItem === null) {
		throw new Error('DropDownItem must be used within a DropDown');
	}

	onMount(() => {
		registerItem(ref);
	});
</script>

<button class="{className} flex items-center" on:click bind:this={ref} {title} type="button" aria-label={ariaLabel}>
	<slot />
</button>
