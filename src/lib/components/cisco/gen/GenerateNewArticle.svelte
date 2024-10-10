<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	let userInput = '';

	function handleSubmit() {
		dispatch('submit', { input: userInput });
	}
</script>

<div>
	<h2>Generate a New Article</h2>
	<textarea bind:value={userInput} placeholder="Describe the configuration you are looking for..." />
	<button on:click={handleSubmit}>Submit</button>
</div>
