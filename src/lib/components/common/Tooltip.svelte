<script lang="ts">
	import { onDestroy } from 'svelte';
	import { marked } from 'marked';
	import type { Instance, SingleTarget } from 'tippy.js';

	import tippy from 'tippy.js';
	import { roundArrow } from 'tippy.js';

	import type { Placement } from 'tippy.js';

	export let placement: Placement = 'top';
	export let content = `I'm a tooltip!`;
	export let touch = true;
	export let className = 'flex';
	export let theme = '';

	let tooltipElement: SingleTarget;
	let tooltipInstance: Instance;

	$: if (tooltipElement && content) {
		if (tooltipInstance) {
			tooltipInstance.setContent(content);
		} else {
			tooltipInstance = tippy(tooltipElement, {
				content: content,
				placement: placement,
				allowHTML: true,
				touch: touch,
				...(theme !== '' ? { theme } : { theme: 'dark' }),
				arrow: false,
				offset: [0, 4]
			});
		}
	} else if (tooltipInstance && content === '') {
		if (tooltipInstance) {
			tooltipInstance.destroy();
		}
	}

	onDestroy(() => {
		if (tooltipInstance) {
			tooltipInstance.destroy();
		}
	});
</script>

<div bind:this={tooltipElement} aria-label={content} class={className}>
	<slot />
</div>
