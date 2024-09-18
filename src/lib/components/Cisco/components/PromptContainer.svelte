<script lang="ts">
	import PromptSelection from '$lib/components/Cisco/components/PromptSelection.svelte';
	import PromptTemplateEditor from '$lib/components/Cisco/components/PromptTemplateEditor.svelte';
	import AssistantAnimationHero from '$lib/components/Cisco/components/layout/AssistantAnimationHero.svelte';
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { promptStore, variablesStore, explanationStore } from '$lib/stores';
	import { fade } from 'svelte/transition';

	export let showPromptTemplate: boolean;
	export let showPromptIntro: boolean;
	export let isGeneratingPrompt: boolean;

	export let observer: MutationObserver | null = null;
	export let generatePrompt: (prompt: string) => Promise<void>;

	let editablePrompt = '';
	let formattedEditablePrompt = '';
	let editableElement: HTMLElement;

	$: showPromptTemplateGenerator = showPromptTemplate;

	$: if ($promptStore) {
		editablePrompt = $promptStore;
		updateFormattedPrompt($promptStore);
		updateVariables($promptStore);
	}

	const dispatch = createEventDispatcher();

	const initializePromptAndVariables = () => {
		updateFormattedPrompt($promptStore);
	};

	const extractVariables = (text: string) => {
		const regex = /\[\[(.*?)\]\]/g;
		const matches = [...text.matchAll(regex)];
		return [...new Set(matches.map((match) => match[1].trim()))];
	};

	const updateVariables = (template: string) => {
		const extractedVars = extractVariables(template);
		console.log('extractedVars:', extractedVars);

		variablesStore.update((currentVars) => {
			// Preserve existing values while adding new variables with default empty string
			const updatedVars = { ...currentVars };
			extractedVars.forEach((varName) => {
				if (!(varName in updatedVars)) {
					updatedVars[varName] = ''; // Initialize new variables only
				}
			});
			return updatedVars;
		});

		console.log('variablesStore:', $variablesStore);
		dispatch('update', { prompt: template, variables: $variablesStore });
	};

	const handleGeneratePromptClick = async () => {
		isGeneratingPrompt = true;
		showPromptIntro = false;

		try {
			await generatePrompt(editablePrompt);
			updateVariables($promptStore);
		} catch (error) {
			console.error('Error generating prompt:', error);
		} finally {
			isGeneratingPrompt = false;
			showPromptTemplate = true;
		}
	};

	function setupMutationObserver() {
		if (editableElement) {
			observer = new MutationObserver((mutations) => {
				mutations.forEach((mutation) => {
					if (mutation.type === 'childList' || mutation.type === 'characterData') {
						const newContent = editableElement.innerText;
						handlePromptInput(newContent);
					}
				});
			});

			observer.observe(editableElement, {
				childList: true,
				characterData: true,
				subtree: true
			});
		}
	}

	const handleClose = () => {
		dispatch('close');
	};

	const updateFormattedPrompt = (template: string) => {
		formattedEditablePrompt = template.replace(/\[\[(.*?)\]\]/g, (match, p1) => {
			const varName = p1.trim();
			return `<span class="variable" data-variable="${varName}">${match}</span>`;
		});
	};

	const renderTemplate = (template: string, variables: { [key: string]: string }) => {
		return template.replace(/\[\[(.*?)\]\]/g, (match, varName: string) => {
			const varValue = variables[varName.trim()];
			return varValue ? `[${varName.trim()}: ${varValue}]` : match;
		});
	};

	const handleCreateCustomizedPrompt = () => {
		const customPrompt = renderTemplate($promptStore, $variablesStore);
		const promptTemplate = $promptStore;
		showPromptTemplate = false;
		showPromptTemplateGenerator = false;

		dispatch('submit', {
			customPrompt,
			promptTemplate,
			explanation: $explanationStore
		});
	};

	onMount(() => {
		console.log('PromptContainer mounted');
		initializePromptAndVariables();
		// setupMutationObserver();
	});

	onDestroy(() => {
		if (observer) {
			observer.disconnect();
		}
	});
</script>

<div class="relative overflow-x-scroll h-full p-4 bg-whitesmoke">
	<div class="flex h-full">
		{#if showPromptIntro}
			<PromptSelection
				{showPromptIntro}
				bind:editablePrompt
				{handleClose}
				{handleGeneratePromptClick}
				{updateVariables}
			/>
		{/if}

		{#if isGeneratingPrompt}
			<div
				class="flex items-center justify-center p-10 w-full"
				transition:fade={{ delay: 500, duration: 500 }}
			>
				<AssistantAnimationHero />
			</div>
		{:else if showPromptTemplate}
			<PromptTemplateEditor {updateFormattedPrompt} />
		{/if}
	</div>

	<div class="flex justify-end mt-8 p-8">
		<button
			class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
			on:click={handleCreateCustomizedPrompt}
		>
			Send
		</button>
	</div>
</div>
