<script lang="ts">
	import type { AdvancedModelParams, ChatFile } from '$lib/types';
	import { onMount } from 'svelte';
	import { slide } from 'svelte/transition';
	import type { ChatParams, Model } from '$lib/stores';
	import Modal from '../common/Modal.svelte';
	import Controls from './Controls/Controls.svelte';

	export let show = false;

	export let models: Model[] = [];

	export const chatId = null;

	export let chatFiles: ChatFile[] = [];
	export let valves = {};
	export let params: AdvancedModelParams = {};

	let largeScreen = false;
	onMount(() => {
		// listen to resize 1024px

		const mediaQuery = window.matchMedia('(min-width: 1024px)');
		const handleMediaQuery = (e: MediaQueryListEvent) => {
			largeScreen = e.matches;
		};

		mediaQuery.addEventListener('change', handleMediaQuery);
		handleMediaQuery({ matches: mediaQuery.matches } as MediaQueryListEvent);
		return () => {
			mediaQuery.removeEventListener('change', handleMediaQuery);
		};
	});
</script>

{#if largeScreen}
	{#if show}
		<div class=" absolute bottom-0 right-0 z-20 h-full pointer-events-none">
			<div class="pr-4 pt-14 pb-8 w-[24rem] h-full" in:slide={{ duration: 200, axis: 'x' }}>
				<div
					class="w-full h-full px-5 py-4 bg-white dark:shadow-lg dark:bg-gray-850 border border-gray-50 dark:border-gray-800 rounded-xl z-50 pointer-events-auto overflow-y-auto scrollbar-hidden"
				>
					<Controls
						on:close={() => {
							show = false;
						}}
						{models}
						bind:chatFiles
						bind:valves
						bind:params
					/>
				</div>
			</div>
		</div>
	{/if}
{:else}
	<Modal bind:show>
		<div class="  px-6 py-4 h-full">
			<Controls
				on:close={() => {
					show = false;
				}}
				{models}
				bind:chatFiles
				bind:valves
				bind:params
			/>
		</div>
	</Modal>
{/if}
