<script lang="ts">
	export let _classes: string | null = null;
</script>

<div class="{_classes ? _classes : ''} self-center font-semibold mb-0.5 line-clamp-1 contents">
	<slot />
</div>
