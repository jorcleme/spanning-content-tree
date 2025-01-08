<script lang="ts">
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	export let content: string = '';
	export let onClick: () => void;
</script>

<Tooltip {content}>
	<button
		on:click={onClick}
		class="flex mr-1 rounded-md text-gray-700 dark:bg-gray-800 dark:text-gray-50 hover:bg-neutral-200 dark:hover:bg-gray-700 border-none bg-neutral-50 border-lg p-3 cursor-pointer align-middle items-center shrink-0"
	>
		<slot />
	</button>
</Tooltip>
