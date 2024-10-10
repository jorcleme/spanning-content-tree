<script lang="ts">
	export let currentSlide: number;
	export let slideIndex: number;
</script>

<div class="slide" class:active={currentSlide === slideIndex}>
	{#if currentSlide === slideIndex}
		<slot />
	{/if}
</div>

<style>
	.slide {
		display: none;
		transition: transform 0.5s ease-in-out;
	}
	.slide.active {
		display: block;
		transform: translateX(0);
	}
</style>
