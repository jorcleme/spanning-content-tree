<script lang="ts">
	import '@harbor/elements/button';

	type ButtonVariants = 'primary' | 'outline' | 'text';
	type ButtonSentiments = 'neutral' | 'interact' | 'success' | 'danger' | 'info' | 'warning';

	export let text: string = 'Click me';
	export let variant: ButtonVariants = 'primary';
	export let sentiment: ButtonSentiments = 'neutral';
</script>
