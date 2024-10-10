<script lang="ts">
	import { slide } from 'svelte/transition';
	import { cubicIn } from 'svelte/easing';
	import Fixed from '../common/Fixed.svelte';
	import DetailsGetSupportWidget from './DetailsGetSupportWidget.svelte';
	import { isSupportWidgetOpen } from '$lib/stores/index';

	let dialog;

	function handleCloseDialog(event: CustomEvent<{ open: boolean }>) {
		$isSupportWidgetOpen = event.detail.open;
		console.log($isSupportWidgetOpen);
	}
</script>

<Fixed />
<div>
	<dialog id="getSupportWidgetContainer" open={$isSupportWidgetOpen}>
		<div id="backgroundDecoration">
			<div id="getSupportWidgetContent" in:slide={{ duration: 1000, delay: 200, easing: cubicIn, axis: 'y' }}>
				{#if $isSupportWidgetOpen}
					<DetailsGetSupportWidget open={!!$isSupportWidgetOpen} on:closeDialog={handleCloseDialog} />
				{/if}
			</div>
		</div>
	</dialog>
</div>

<style>
	#getSupportWidgetContainer {
		position: fixed;
		z-index: 9999; /* or fixed, if needed */
		background: inherit;
	}

	#getSupportWidgetContent {
		background: white;
		padding: 1em 0 0 0;
		max-width: 750px;
		animation: slideInFromright 0.5s ease-out forwards;
		position: fixed;
		right: 8px;
		bottom: 155px;
		z-index: 9999;
		background: transparent;
		border: none;
	}
</style>
