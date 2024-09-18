<script lang="ts">
	import { fade } from 'svelte/transition';
	import { promptStore, variablesStore, explanationStore } from '$lib/stores';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { Info } from 'lucide-svelte';

	export const formattedEditablePrompt: string = '';
	export let updateFormattedPrompt: (template: string) => void;

	// const updateFormattedPrompt = (template: string) => {
	// 	formattedEditablePrompt = template.replace(/\[\[(.*?)\]\]/g, (match, p1) => {
	// 		const varName = p1.trim();
	// 		return `<span class="variable" data-variable="${varName}">${match}</span>`;
	// 	});
	// };

	$: transformedPromptTemplate = $promptStore.replace(/\[\[(.*?)\]\]/g, (match, varName) => {
		const value = $variablesStore ? $variablesStore[varName.trim()] : undefined;
		// Replace the placeholder with the current variable value, or keep the placeholder if empty
		return value ? value : match;
	});

	const handleVariableInput = (varName: string, value: string) => {
		variablesStore.update((vars) => ({ ...vars, [varName]: value }));
	};

	const validateVariableName = (name: string) => {
		return /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name);
	};

	const addVariable = (name: string) => {
		if (name === '') {
			alert('Variable name cannot be empty.');
			return false;
		}
		if (!validateVariableName(name)) {
			alert('Invalid variable name. Use only letters, numbers, and underscores.');
			return false;
		}
		if ($variablesStore.hasOwnProperty(name)) {
			alert('Variable already exists.');
			return false;
		}
		variablesStore.update((vars) => {
			vars[name] = '';
			return {
				...vars,
				[name]: ''
			};
		});
		console.log($variablesStore);
		const currentPrompt = $promptStore;
		promptStore.set(`${currentPrompt} [[${name}]]`);
		updateFormattedPrompt($promptStore);
		return true;
	};

	const handleAddVariableClick = () => {
		const newVariable = document.querySelector('#newVariable') as HTMLInputElement;
		const newVarName = newVariable.value;
		if (addVariable(newVarName)) {
			// Clear the input field
			newVariable.value = '';
		}
	};
</script>

<div class="flex w-full p-4 overflow-y-auto" transition:fade={{ delay: 500, duration: 500 }}>
	<div class="w-1/2 pr-8">
		<h3 class="text-2xl font-semibold mb-6">Prompt Variables</h3>
		<div class="space-y-6 mb-8 p-4">
			{#each Object.entries($variablesStore) as [varName, value]}
				<div class="variable-input">
					<label for={varName}>{varName}:</label>
					<input
						class="p-4 mt-4 bg-white rounded-lg shadow-md"
						type="text"
						id={varName}
						bind:value={$variablesStore[varName]}
						on:input={(e) => handleVariableInput(varName, e.currentTarget.value)}
					/>
				</div>
			{/each}
		</div>
		<div>
			<input
				type="text"
				id="newVariable"
				placeholder="New variable name"
				class="p-4 mt-4 bg-white rounded-lg shadow-md"
			/>
			<button class="btn btn-tertiary" on:click={() => handleAddVariableClick()}
				>Add Variable</button
			>
		</div>
	</div>
	<div class="w-1/2 pl-8 border-l border-gray-300">
		<h3 class="flex flex-row text-2xl font-semibold mb-6">
			Prompt Template
			<Tooltip content={$explanationStore} placement="bottom">
				<span class="ml-2 text-gray-500 cursor-help">
					<Info size={20} />
				</span>
			</Tooltip>
		</h3>
		<div class="relative">
			<p>{@html transformedPromptTemplate}</p>
		</div>
	</div>
</div>
