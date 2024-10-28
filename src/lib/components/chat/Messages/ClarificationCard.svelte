<script lang="ts">
	import { slide } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import { sanitizeResponseContent } from '$lib/utils';

	export let question = '';
	export let options = [];
	export let onSelect = (options: any) => {};
	export let onSubmit: Function;
	export let visible = false;
	export let selectedOption = '';
	export let notOptions: string[] = [];
	export let inputValue = '';

	export let messages = [];

	export let originalUserPrompt = '';

	let selectedOptions: string[] = [];

	let selectedTab = 'options';

	// let notOptions; // Initialize notOptions as an empty array

	function convertOptionsToString(options: string[]): string {
		return options.length > 0 ? JSON.stringify(options.filter((option) => typeof option === 'string')) : '[]';
	}

	async function handleSubmit() {
		if (!onSubmit) return;
		const selectedOptionsString = convertOptionsToString(selectedOptions);
		const notOptionsString = convertOptionsToString(notOptions);

		console.log(`Selected options: ${selectedOptionsString}`);
		console.log(`Not options: ${notOptionsString}`);
		console.log(`Input value: ${inputValue}`);

		if (selectedOptionsString === '[]' && notOptionsString === '[]' && !inputValue) {
			console.log('No options selected, submitting original user prompt: ', originalUserPrompt);
			await onSubmit([], [], '', originalUserPrompt || '');
		} else {
			await onSubmit(selectedOptionsString, notOptionsString, inputValue, originalUserPrompt || '');
		}
		resetForm();
	}

	function resetForm() {
		visible = false;
		selectedOptions = [];
		notOptions = [];
		inputValue = '';
	}

	function sanitizeContent(content) {
		if (typeof content !== 'string') {
			return '';
		}
		return sanitizeResponseContent(content);
	}
	function isOptionDisabled(option, selectedTab) {
		if (selectedTab === 'options') {
			return notOptions.includes(option.value);
		} else if (selectedTab === 'notOptions') {
			return selectedOptions.includes(option.value);
		}
		return false;
	}
</script>

{#if question && visible}
	<div class="clarification-card w-full md:max-w-[850px]" transition:slide={{ duration: 300, easing: cubicOut }}>
		<p>{@html question}</p>
		<div class="tabs mt-4">
			<button id="tab" class:active={selectedTab === 'options'} on:click={() => (selectedTab = 'options')}>
				Options
			</button>
			<button id="tab" class:active={selectedTab === 'notOptions'} on:click={() => (selectedTab = 'notOptions')}>
				Not Options
			</button>
		</div>

		{#if selectedTab === 'options'}
			<div class="options bento-box">
				{#each options as option}
					<button
						class="option-button"
						class:selected={selectedOptions.includes(option.value)}
						class:disabled={isOptionDisabled(option, selectedTab)}
						on:click={() => {
							if (!isOptionDisabled(option, selectedTab)) {
								const index = selectedOptions.indexOf(option.label);
								if (index < 0) {
									selectedOptions = [...selectedOptions, option.label];
								} else {
									selectedOptions = [...selectedOptions.slice(0, index), ...selectedOptions.slice(index + 1)];
								}
								onSelect(selectedOptions);
							}
						}}
					>
						{option.label}
					</button>
				{/each}
			</div>
		{:else if selectedTab === 'notOptions'}
			<div class="not-options bento-box mt-4">
				{#each options as option}
					<button
						class="option-button"
						class:selected={notOptions.includes(option.value)}
						class:disabled={isOptionDisabled(option, selectedTab)}
						on:click={() => {
							if (!isOptionDisabled(option, selectedTab)) {
								const index = notOptions.indexOf(option.label);
								if (index < 0) {
									notOptions = [...notOptions, option.label];
								} else {
									notOptions = [...notOptions.slice(0, index), ...notOptions.slice(index + 1)];
								}
							}
						}}
					>
						{option.label}
					</button>
				{/each}
			</div>
		{/if}
		<div class="context-options mb-4 mt-8 flex text-gray-600 justify-between text-sm">
			<details class="m-4 p-2">
				<summary class="text-gray-500"> Provide text direction </summary>
				<div class="input-field mt-4">
					<input
						type="text"
						bind:value={inputValue}
						placeholder="Enter additional information"
						class="w-full px-4 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>
			</details>
			<!-- <label>
					<input type="checkbox" bind:checked={keepContext} /> Keep previous clarifications
				</label> -->
		</div>
		<div class="flex space-x-2 flex-row justify-end mt-4">
			<button id="cancel-button" on:click={handleSubmit}>Skip</button>
			<button id="submit-button" on:click={handleSubmit}>Submit</button>
		</div>
	</div>
{/if}

<style>
	/* cisco */
	.bento-box {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 1em;
		margin-top: 1em;
	}

	#cancel-button {
		border-radius: 0.375rem;
		background: #f7f7f7;
		color: #333 !important;
		display: flex;

		justify-content: center;
		align-items: center;
		gap: 0.75rem;

		transition: background-color 0.2s ease-out linear;
	}

	#submit-button {
		border-radius: 0.375rem;
		background: #1d69cc;
		color: white !important;
		display: flex;
		padding: 0.3125rem 0.5rem;
		justify-content: center;
		align-items: center;
		gap: 0.75rem;

		transition: background-color 0.2s ease-out linear;
	}

	#submit-button:hover,
	#submit-button:focus {
		border-radius: 0.375rem;
		background: var(--interact-bg-hover, #0d5cbd);
		box-shadow: 0px 0px 0px 4px #3e84e5;

		box-shadow: 0px 0px 0px 2px #cce1ff;
	}

	.clarification-card {
		max-width: 750px;
		position: fixed;
		bottom: 0;
		left: 50%;
		transform: translateX(-50%);
		background-color: #f7f7f7;
		padding: 16px;
		box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.1);
		z-index: 10;
		color: #333;

		border-radius: 16px 16px 0 0;
		/* border: #333 1px solid; */
		border-bottom: 4px solid transparent;
		border-image: linear-gradient(27deg, #3b76ea 10.22%, #00bceb 88.93%, #63fff7 162.86%) 1;
		border-image-slice: 1;
		border-radius: 8px 8px 0 0;
		background: #f7f7f7;
		transition: all 0.3s;
		box-sizing: border-box; /* include padding and border in the element's total width and height */
	}

	.options button {
		position: relative;
		padding: 8px 16px;
		transition: color 0.2s ease-in-out, background-color 0.2s ease-in-out;
		color: var(--base-text-default, #23282e);
		background: white;
		font-size: 0.75rem;
		font-style: normal;
		font-weight: 700;
		line-height: 1.125rem;
		border: none;
		width: max-content;
		border-radius: 6px;
		box-sizing: border-box;
		overflow: hidden;
	}

	.options button::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		border-radius: 8px;
		padding: 2px;
		background: linear-gradient(to bottom right, #3b76ea 0%, #00bceb 51.5625%, #63fff7 100%);
		-webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
		-webkit-mask-composite: xor;
		mask-composite: exclude;
		/* z-index: -1; */
	}

	/* Hover and focus styles */
	.options button:hover::before,
	.options button:focus::before {
		background: linear-gradient(to bottom right, #0d5cbd 0%, #0d5cbd 51.5625%, #0d5cbd 100%);
	}

	.options button:hover,
	.options button:focus {
		color: #0d5cbd;
		background: #cce1ff;
	}

	/* Selected state */
	.options button.selected::before {
		background: linear-gradient(to bottom right, #0d5cbd 0%, #0d5cbd 51.5625%, #0d5cbd 100%);
	}
	.not-options button.selected {
		color: #ff0000;
		background: #ffcccc;
	}

	.options button.selected {
		color: #0d5cbd;
		background: #cce1ff;
	}

	/* Selected state */
	.options button.selected::before {
		background: #cce1ff;
	}

	.clarification-card .options button {
		border-radius: 6px;
	}

	div.clarification-card > div.options > #submit-button-id button {
		border-radius: 6px;
	}

	.clarification-card :focus {
		box-shadow: 0px 0px 0px 2px #cce1ff, 0px 0px 0px 4px #3e84e5;
	}

	.tabs {
		display: flex;
		border-bottom: 2px solid transparent;
		border-image: linear-gradient(to right, #3b76ea, #00bceb, #63fff7) 1;
	}

	#tab {
		padding: 8px 16px;
		font-size: 14px;
		font-weight: 500;
		color: #333;
		background-color: transparent;
		border: none;
		cursor: pointer;
		transition: background-color 0.3s;
		border: transparent;
	}
	#tab::before,
	#cancel-button::before {
		content: none;
		background-color: initial;
		border: initial;
	}

	#tab:hover {
		background-color: #f1f1f1;
	}

	#tab.active {
		color: #333;
		background-color: white;
		font-weight: 800;
	}

	.options button.disabled,
	.not-options button.disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>
