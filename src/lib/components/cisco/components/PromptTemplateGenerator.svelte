<script lang="ts">
	import { writable, get } from 'svelte/store';
	import { slide, fade, fly } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { sanitizeResponseContent } from '$lib/utils';
	import _ from 'lodash';
	import Slide from './common/Slide.svelte';
	import DeviceSelection from '../gen/CiscoDeviceSelector.svelte';
	import ArticleTopics from '../gen/ArticleTopics.svelte';
	import GenerateNewArticle from '../gen/GenerateNewArticle.svelte';
	import { explanationStore, promptStore, variablesStore } from '$lib/stores';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import {
		X,
		BookOpen,
		PenTool,
		Calculator,
		Globe,
		Microscope,
		Info,
		Volume2,
		Network,
		Router,
		Wifi,
		Cloud,
		Users
	} from 'lucide-svelte';
	import { createEventDispatcher, onMount, tick, onDestroy } from 'svelte';
	import AssistantAnimationHero from '$lib/components/cisco/components/layout/AssistantAnimationHero.svelte';

	export let showPromptTemplateGenerator: boolean;
	export let explanation = '';
	export let showPromptTemplate: boolean;
	export let showPromptIntro: boolean;
	export let isTextareaTruthy: boolean;
	export let fetchAndProcessData: (template: string) => Promise<any>;
	export let generatePrompt: (existingText: string) => Promise<void>;

	let varName;
	export let extractVariablesFromPrompt: (prompt: string) => Record<string, string>;

	const debouncedHandleVariableInput = _.debounce((varName, value) => {
		handleVariableInput(varName, value);
	}, 300);

	export let generatedPrompt = '';
	export let headerText = 'Loading';
	export let originalUserPrompt;
	export let isGeneratingPrompt: boolean;

	let currentSlide = writable(0);

	const slides: { component: any; props: Record<string, any> }[] = [
		{
			component: DeviceSelection,
			props: { onConfirm: handleDeviceConfirm }
		},
		{
			component: ArticleTopics,
			props: { onGenerateNewArticle: handleGenerateNewArticle }
		},
		{
			component: GenerateNewArticle,
			props: { onSubmit: handleArticleSubmit }
		}
	];

	function handleDeviceConfirm(event: CustomEvent<{ device: string; name: string }>) {
		// Move to the next slide
		currentSlide.set(1);
		const { device, name } = event.detail;
		console.log('Device selected:', device, name);
		seriesId = device;
		variablesStore.update((vars) => ({ ...vars, device: name }));
	}

	function handleGenerateNewArticle() {
		// Move to the generate new article slide
		currentSlide.set(2);
	}

	function handleArticleSubmit(event) {
		// Handle article submission
		console.log('Article submitted:', event.detail.input);
	}
	let lastCaretPosition = { node: null, offset: 0 };

	let editablePrompt = '';
	let editableElement;
	let formattedEditablePrompt = '';
	let updateTimeout;
	let variableUpdateTimeouts = {};
	let observer: MutationObserver;
	let seriesId = '';
	$: seriesId;

	const dispatch = createEventDispatcher();

	let infoExplanation = '';
	if (!$variablesStore) {
		variablesStore.set({});
	}

	$: transformedPromptTemplate = $promptStore.replace(/\[\[(.*?)\]\]/g, (match, varName) => {
		const value = $variablesStore ? $variablesStore[varName.trim()] : undefined;
		// Replace the placeholder with the current variable value, or keep the placeholder if empty
		return value ? value : match;
	});

	$: {
		infoExplanation = `You can add variables by enclosing words in double square brackets, e.g. [[variable_name]]
<br><br><h3>Why this prompt?</h3><br>
<p>${$explanationStore}</p>`;
	}
	$: formattedPrompt = generatedPrompt.replace(/\[\[(.*?)\]\]/g, (match, p1) => {
		const value = $variablesStore[p1.trim()];
		return value ? `${match}: <span class="variable">${value}</span>` : match;
	});
	$: {
		console.log('variablesStore', $variablesStore);
	}
	// $: {
	// 	if ($promptStore) {
	// 		editablePrompt = $promptStore;
	// 		updateFormattedPrompt($promptStore);
	// 	}
	// 	if (isTextareaTruthy) {
	// 		showPromptTemplate = true;
	// 		showPromptIntro = false;
	// 	} else {
	// 		showPromptTemplate = false;
	// 		showPromptIntro = false;
	// 	}
	// }

	$: {
		if ($promptStore) {
			editablePrompt = $promptStore;
			updateFormattedPrompt($promptStore);
			updateVariables($promptStore);
		}
	}
	onMount(() => {
		initializePromptAndVariables();
		setupMutationObserver();
	});

	onDestroy(() => {
		if (observer) {
			observer.disconnect();
		}
	});

	function initializePromptAndVariables() {
		updateFormattedPrompt($promptStore);
	}
	function handleSubmit() {
		dispatch('submit', {
			customizedPrompt: generatedPrompt,
			promptTemplate: generatedPrompt,
			explanation
		});
	}

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

	function extractVariables(text: string) {
		const regex = /\[\[(.*?)\]\]/g;
		const matches = [...text.matchAll(regex)];
		return [...new Set(matches.map((match) => match[1].trim()))];
	}

	function updateFormattedPrompt(template) {
		formattedEditablePrompt = template.replace(/\[\[(.*?)\]\]/g, (match, p1) => {
			const varName = p1.trim();
			return `<span class="variable" data-variable="${varName}">${match}</span>`;
		});
	}

	function updateVariables(template) {
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
	}
	let debounceUpdatePromptInput = _.debounce((content) => {
		handlePromptInput(content);
	}, 300);
	function preserveCaretPosition(element) {
		const selection = window.getSelection();
		if (selection && selection.rangeCount > 0) {
			const range = selection.getRangeAt(0);
			const startOffset = Math.min(range.startOffset, element.textContent.length);
			const endOffset = Math.min(range.endOffset, element.textContent.length);

			setTimeout(() => {
				try {
					const newRange = document.createRange();
					if (element.childNodes[0]) {
						newRange.setStart(element.childNodes[0], startOffset);
						newRange.setEnd(element.childNodes[0], endOffset);
						selection.removeAllRanges();
						selection.addRange(newRange);
					}
				} catch (error) {
					console.error('Error setting caret position:', error);
				}
			}, 0);
		}
	}

	// Usage when updating the editable area
	function handlePromptInput(newContent) {
		const element = editableElement; // The element where content is edited
		updateTimeout = setTimeout(() => {
			const currentContent = $promptStore;
			if (newContent !== currentContent) {
				promptStore.set(newContent);
				updateVariables(newContent);
				updateFormattedPrompt(newContent);
			}
		}, 200);
		preserveCaretPosition(element);
	}

	function handleGeneratePromptClick() {
		isGeneratingPrompt = true;
		showPromptIntro = false;
		generatePrompt(editablePrompt).then(() => {
			isGeneratingPrompt = false;
			showPromptIntro = false;
			showPromptTemplate = true;
			updateVariables($promptStore);
		});
	}

	let updateVariableAndPrompt = _.debounce((varName: string, value: string) => {
		variablesStore.update((store) => ({
			...store,
			[varName]: value
		}));

		promptStore.update((template) => {
			return template.replace(new RegExp(`\\[\\[${varName}\\]\\]`, 'g'), `[[${varName}]]`);
		});

		updateFormattedPrompt($promptStore);
		dispatch('update', { prompt: $promptStore, variables: $variablesStore });
	}, 2000);

	function handleVariableInput(varName, value) {
		variablesStore.update((vars) => ({ ...vars, [varName]: value }));
		// Svelte reactivity will take care of updating the UI using transformedPromptTemplate
	}

	function handleClose() {
		dispatch('close', { state: false });
	}

	function handleCreateCustomizedPrompt() {
		const customizedPrompt = renderTemplate($promptStore, $variablesStore);
		const promptTemplate = $promptStore;
		showPromptTemplate = false;
		showPromptTemplateGenerator = false;

		dispatch('submit', {
			customizedPrompt,
			promptTemplate,
			explanation: $explanationStore
		});
	}

	function handleTemplateClick(event) {
		const clickedVariable = event.target.dataset.variable;
		if (clickedVariable) {
			// Handle variable click if needed
		}
	}

	function renderTemplate(template: string, variables: { [key: string]: string }) {
		return template.replace(/\[\[(.*?)\]\]/g, (match, varName: string) => {
			const varValue = variables[varName.trim()];
			return varValue ? `[${varName.trim()}: ${varValue}]` : match;
		});
	}

	function validateVariableName(name) {
		return /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name);
	}

	function addVariable(name) {
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
			return vars;
		});
		const currentPrompt = $promptStore;
		const updatedPrompt = `${currentPrompt} [[${name}]]`;
		promptStore.set(updatedPrompt);
		updateFormattedPrompt(updatedPrompt);
		return true;
	}

	const ciscoSmbThemes = [
		{
			icon: Network,
			text: 'Network Infrastructure Support',
			template:
				'Provide a comprehensive article that guides [[smb_customer_type]] on how to implement [[subject]] solutions. The article should cover the following key aspects: [[key_aspects]]. There may optionally be a signifier for [[article_or_video]].'
		},
		{
			icon: Router,
			text: 'Routing and Switching Support',
			template:
				'Create a detailed video tutorial that demonstrates the steps for [[smb_customer_type]] to upgrade their [[subject]] infrastructure. The video should include: [[key_aspects]]. There may optionally be a signifier for [[article_or_video]].'
		},
		{
			icon: Wifi,
			text: 'Wireless Solutions Support',
			template:
				'Develop a support guide to help [[smb_customer_type]] deploy [[subject]] solutions across their facilities. The guide should address: [[key_aspects]]. There may optionally be a signifier for [[article_or_video]].'
		},
		{
			icon: Cloud,
			text: 'Cloud Computing Support',
			template:
				'Outline a step-by-step migration guide for [[smb_customer_type]] to transition to [[subject]] solutions. The guide should cover: [[key_aspects]]. There may optionally be a signifier for [[article_or_video]].'
		},
		{
			icon: Users,
			text: 'Collaboration Tools Support',
			template:
				'Provide a recommendations list for [[smb_customer_type]] to implement [[subject]] solutions to enhance collaboration. The recommendations should include: [[key_aspects]]. There may optionally be a signifier for [[article_or_video]].'
		}
	];
	export let updateTemplate: (newTemplate: string) => void;

	// Select the theme
	function handleThemeSelect(theme: string) {
		showPromptIntro = false;
		showPromptTemplate = true;
		isGeneratingPrompt = false;
		const selectedThemeObj = ciscoSmbThemes.find((t) => t.text === theme);
		if (selectedThemeObj) {
			variablesStore.update((vars) => ({ ...vars, subject: theme }));
			const template = selectedThemeObj.template;
			promptStore.set(template);
			editablePrompt = template;
			updateVariables(template);
			updateFormattedPrompt(template);
		}
	}
</script>

<div class="relative overflow-x-scroll h-full p-4" style="background:whitesmoke;">
	<div>
		<div class="flex flex-col h-full">
			{#if showPromptIntro}
				<div class="slide flex justify-center items-center" transition:fly={{ x: 200, duration: 500 }}>
					{#if $currentSlide === 0}
						<Slide currentSlide={0} slideIndex={0}>
							<DeviceSelection on:confirm={handleDeviceConfirm} />
						</Slide>
					{:else if $currentSlide === 1}
						<Slide currentSlide={1} slideIndex={1}>
							<ArticleTopics {seriesId} on:generateNewArticle={handleGenerateNewArticle} />
						</Slide>
					{:else if $currentSlide === 2}
						<Slide currentSlide={2} slideIndex={2}>
							<GenerateNewArticle on:submit={handleArticleSubmit} />
						</Slide>
					{/if}
				</div>
				<div class="text-black p-10 max-w-5xl w-full" transition:slide={{ duration: 500, easing: cubicOut }}>
					<div class="flex justify-between items-center mb-8">
						<h2 class="text-3xl font-semibold">Describe your learning goal</h2>
						<button class="text-gray-400 hover:text-white" on:click={handleClose}>
							<X size={28} />
						</button>
					</div>

					<div class="relative overflow-scroll h-full">
						<div transition:slide={{ duration: 500, easing: cubicOut }}>
							<p class="text-gray-400 text-lg mb-8">
								Choose from a starter prompt below or generate a new one further below.
							</p>
							<div class="space-y-2 my-16 flex flex-row flex-wrap">
								{#each ciscoSmbThemes as theme}
									<button
										class="flex items-center justify-between w-full bg-gray-600 hover:bg-gray-700 text-white py-2 px-3 rounded text-left transition-colors duration-200 text-sm mx-4"
										on:click={() => handleThemeSelect(theme.text)}
									>
										<div class="flex items-center space-x-2">
											<svelte:component this={theme.icon} size={16} />
											<span style="width:max-content">{theme.text}</span>
										</div>
									</button>
								{/each}
							</div>
							<textarea
								bind:value={editablePrompt}
								rows="5"
								class="w-full bg-gray-50 p-2 border rounded btn btn-secondary"
							/>
							<button
								class="px-4 py-2 bg-blue-500 text-white text-semibold rounded hover:bg-blue-600"
								on:click={handleGeneratePromptClick}
							>
								Generate Prompt from your directions
							</button>
						</div>
					</div>
				</div>
			{/if}

			{#if isGeneratingPrompt}
				<div class="flex items-center justify-center p-10 w-full" transition:fade={{ delay: 500, duration: 500 }}>
					<AssistantAnimationHero />
				</div>
			{:else if showPromptTemplate}
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
										on:input={(e) => handleVariableInput(varName, e.target.value)}
									/>
								</div>
							{/each}
						</div>
						<div>
							<input
								type="text"
								id="newVariable"
								placeholder="New variable name"
								class="p-4 mt-4 bg-white rounded-lg shadow-md overflow-hidden"
							/>
							<button
								class="btn btn-tertiary"
								on:click={() => {
									const newVarName = document.getElementById('newVariable').value;
									if (addVariable(newVarName)) {
										document.getElementById('newVariable').value = '';
									}
								}}>Add Variable</button
							>
						</div>
					</div>
					<div class="w-1/2 pl-8 border-l border-gray-300">
						<h3 class="flex flex-row text-2xl font-semibold mb-6">
							Prompt Template
							<Tooltip content={infoExplanation} placement="bottom">
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
</div>

<style>
	@keyframes colorPulse {
		0%,
		100% {
			color: #3b82f6;
		}
		50% {
			color: #ef4444;
		}
	}

	.editing-variable {
		animation: colorPulse 1s ease-in-out;
	}

	.variable {
		color: #3b82f6;
		font-weight: bold;
		background-color: #e5e7eb;
		padding: 2px 4px;
		border-radius: 4px;
	}

	[contenteditable='true'] {
		outline: none;
	}

	[contenteditable='true']:focus {
		background-color: #f0f4f8;
	}

	:global(.tooltip) {
		--tooltip-background-color: #333;
		--tooltip-color: white;
		--tooltip-padding: 0.5rem;
		--tooltip-font-size: 0.875rem;
		max-width: 250px;
	}
	.TemplateGeneratorContainer {
		background-color: #f7f7f7;
	}
	@media (min-width: 1024px) {
		.TemplateGeneratorContainer {
			height: 680px;
			min-width: 1023px;
		}
	}
	@media (min-width: 768px) and (max-width: 1023px) {
		.TemplateGeneratorContainer {
			min-height: 45dvh;
			min-width: 1023px;
		}
	}
	@media (max-width: 767px) {
		.TemplateGeneratorContainer {
			height: 100%;
			min-width: 100%;
		}
	}

	.variable {
		color: blue;
		font-weight: bold;
	}

	.prompt-template-container {
		background-color: #f0f0f0;
		padding: 20px;
		border-radius: 8px;
		max-width: 800px;
		margin: 0 auto;
	}

	.prompt-preview {
		background-color: white;
		padding: 10px;
		border-radius: 4px;
		margin-bottom: 20px;
	}

	.variables-container {
		display: grid;
		gap: 10px;
	}

	.variable-input {
		display: flex;
		flex-direction: column;
	}

	.variable {
		color: blue;
		font-weight: bold;
	}

	.explanation {
		margin-top: 20px;
	}

	.button-container {
		margin-top: 20px;
		display: flex;
		justify-content: space-between;
	}
</style>
