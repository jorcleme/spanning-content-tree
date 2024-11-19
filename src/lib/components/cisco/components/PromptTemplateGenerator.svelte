<script lang="ts">
	import { writable, get } from 'svelte/store';
	import { slide, fade } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { sanitizeResponseContent } from '$lib/utils';
	import { debounce } from 'lodash';
	// import { createCounter } from '../runeTest.svelte.ts';

	export let showPromptTemplateGenerator: boolean;
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
		Server,
		Network,
		Router,
		Wifi,
		Cloud,
		Users,
		Phone,
		Settings,
		Cpu
	} from 'lucide-svelte';
	import { createEventDispatcher, onMount, tick, onDestroy } from 'svelte';
	import AssistantAnimationHero from '$lib/components/chat/AssistantAnimationHero.svelte';
	export let explanation = '';
	export let showPromptTemplate: boolean;
	export let showPromptIntro: boolean;
	export let isTextareaTruthy: boolean;
	export let fetchAndProcessData: (template: string) => Promise<any>;
	export let generatePrompt: (existingText: string) => Promise<void>;
	let varName;
	export let extractVariablesFromPrompt: (prompt: string) => Record<string, string>;
	import _ from 'lodash';

	const debouncedHandleVariableInput = _.debounce((varName, value) => {
		handleVariableInput(varName, value);
	}, 300);

	export let generatedPrompt = '';
	export let headerText = 'Loading';
	export let originalUserPrompt;
	export let isGeneratingPrompt;
	let lastCaretPosition = { node: null, offset: 0 };

	let editablePrompt = '';
	let editableElement;
	let formattedEditablePrompt = '';
	let updateTimeout;
	let variableUpdateTimeouts = {};
	let observer: MutationObserver;

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

	function extractVariables(text) {
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
	function preserveCaretPosition(element: HTMLElement) {
		const selection = window.getSelection();
		if (selection && selection.rangeCount > 0) {
			const range = selection.getRangeAt(0);
			const startOffset = Math.min(range.startOffset, element.textContent!.length);
			const endOffset = Math.min(range.endOffset, element.textContent!.length);

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
	function handlePromptInput(newContent: string) {
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

	let updateVariableAndPrompt = debounce((varName: string, value: string) => {
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
		dispatch('close');
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
		variablesStore.set('');
		promptStore.set('');
	}

	function handleTemplateClick(event) {
		const clickedVariable = event.target.dataset.variable;
		if (clickedVariable) {
			// Handle variable click if needed
		}
	}

	function renderTemplate(template, variables) {
		return template.replace(/\[\[(.*?)\]\]/g, (match, varName) => {
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
	let selectedCategory = '';
	let deviceOptions = [];
	let deviceContext = '';
	let isOpen = false;

	function handleCategoryClick(category) {
		selectedCategory = category;
		deviceOptions = getDevicesForCategory(category);
		deviceContext = '';
	}

	function handleDeviceSelect(device) {
		deviceContext = device;
		console.log('Device Context:', deviceContext);

		const collectionNames = getCollectionNamesForDevice(device);
		console.log('Collection Names:', collectionNames);

		// You might want to update your stores or perform other actions here
		isOpen = !isOpen;
	}

	function getCollectionNamesForDevice(device) {
		switch (device) {
			case 'Catalyst 1300':
				return {
					admin: 'catalyst_1300_admin_guide',
					cli: 'catalyst_1300_cli_guide'
				};
			case 'Catalyst 1200':
				return {
					admin: 'catalyst_1200_admin_guide',
					cli: 'catalyst_1200_cli_guide'
				};
			case 'CBS220':
				return {
					admin: 'cbs_220_admin_guide',
					cli: 'cbs_220_cli_guide'
				};
			case 'CBS250':
				return {
					admin: 'cbs_250_admin_guide',
					cli: 'cbs_250_cli_guide'
				};
			case 'CBS350':
				return {
					admin: 'cbs_350_admin_guide',
					cli: 'cbs_350_cli_guide'
				};
			case '350':
				return {
					admin: 'cisco_350_admin_guide',
					cli: 'cisco_350_cli_guide'
				};
			case '350X':
				return {
					admin: 'cisco_350x_admin_guide',
					cli: 'cisco_350x_cli_guide'
				};
			case '550X':
				return {
					admin: 'cisco_550x_admin_guide',
					cli: 'cisco_550x_cli_guide'
				};
			case 'RV100':
				return {
					admin: 'rv100_admin_guide',
					cli: 'rv100_cli_guide'
				};
			case 'RV160':
				return {
					admin: 'cisco_rv160_vpn_admin_guide'
				};
			case 'RV260':
				return {
					admin: 'cisco_rv260_vpn_admin_guide'
				};
			case 'RV320':
				return {
					admin: 'rv340_admin_guide',
					cli: 'rv340_cli_guide'
				};
			case 'RV340':
				return {
					admin: 'rv340_admin_guide'
				};
			case 'CBW AC':
				return {
					admin: 'cisco_business_wireless_ac_admin_guide'
				};
			case 'CBW AX':
				return {
					admin: 'cisco_business_wireless_ax_admin_guide'
				};
			case 'WAP100':
				return {
					admin: 'cisco_wap100_admin_guide'
				};
			case 'WAP300':
				return {
					admin: 'cisco_wap300_admin_guide'
				};
			case 'WAP500':
				return {
					admin: 'cisco_wap500_admin_guide'
				};
			default:
				return {};
		}
	}

	function getDevicesForCategory(category) {
		switch (category) {
			case 'Switches':
				return ['Catalyst 1200', 'Catalyst 1300', 'CBS110', 'CBS220', 'CBS250', 'CBS350', '350', '350X', '550X'];
			case 'Routers':
				return ['RV100', 'RV160', 'RV260', 'RV320', 'RV340'];
			case 'Wireless':
				return ['CBW AC', 'CBW AX', 'WAP500', 'WAP300', 'WAP100'];
			case 'Voice':
				return ['CP6800', 'CP7800', 'CP8800', 'SPA300', 'SPA500'];
			case 'Network Management':
				return ['Cisco Business Dashboard', 'Cisco Business Mobile App', 'FindIT Network Manager'];
			default:
				return [];
		}
	}
	function getCategoryIcon(category) {
		switch (category) {
			case 'Switches':
				return Server;
			case 'Routers':
				return Router;
			case 'Wireless':
				return Wifi;
			case 'Voice':
				return Phone;
			case 'Network Management':
				return Settings;
			default:
				return Cpu;
		}
	}

	function resetSelection() {
		selectedCategory = '';
		deviceOptions = [];
		// deviceContext = '';
	}

	function toggleOpen() {
		isOpen = !isOpen;
	}
</script>

<div
	class="relative overflow-hidden"
	transition:slide={{ duration: 300, easing: cubicOut }}
	style="background:whitesmoke;"
>
	<div>
		<div class="flex h-full items-center justify-center">
			{#if showPromptIntro}
				<div class="text-black p-10 max-w-5xl w-full" transition:slide={{ duration: 500, easing: cubicOut }}>
					<div class="flex justify-between items-center mb-1">
						<h2 class="text-3xl font-semibold">Describe your goal</h2>
						<button class="text-gray-400 hover:text-white" on:click={handleClose}>
							<X size={28} />
						</button>
					</div>

					<div class="relative overflow-hidden h-full">
						<div transition:slide={{ duration: 500, easing: cubicOut }}>
							<p class="text-gray-400 text-lg mb-8">
								Choose from a starter prompt below or generate a new one further below.
							</p>
							<div class="my-16 flex flex-row flex-wrap justify-center gap-2">
								{#each ciscoSmbThemes as theme}
									<button
										class="flex items-center px-4 py-2 bg-gray-200 text-black rounded-md h-10"
										on:click={() => handleThemeSelect(theme.text)}
									>
										<div class="flex items-center space-x-2">
											<svelte:component this={theme.icon} size={16} />
											<span>{theme.text}</span>
										</div>
									</button>
								{/each}
							</div>

							<div class="container mx-auto">
								<div class="bg-white shadow-md overflow-hidden" style="border-radius: 16px 16px 0 0 ;">
									<button
										class="w-full flex items-center justify-between p-2 text-sm text-gray-500 font-semibold bg-gray-100 hover:bg-gray-200 transition-colors duration-200"
										on:click={toggleOpen}
									>
										<div class="flex items-center">
											<svelte:component this={Cpu} class="w-4 h-4 mr-2 ml-2 " />
											Device Context {deviceContext}
										</div>
										<svg
											class="w-5 h-5 transition-transform duration-200"
											class:rotate-180={isOpen}
											viewBox="0 0 20 20"
											fill="currentColor"
										>
											<path
												fill-rule="evenodd"
												d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
												clip-rule="evenodd"
											/>
										</svg>
									</button>

									{#if isOpen}
										<div transition:slide={{ duration: 300 }}>
											{#if !selectedCategory}
												<div
													class="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
													transition:slide={{ duration: 200 }}
												>
													{#each ['Switches', 'Routers', 'Wireless', 'Voice', 'Network Management'] as category}
														<button
															class="device-btn flex items-center p-3 border rounded-lg hover:bg-gray-100 transition-colors duration-200"
															class:bg-blue-100={category === selectedCategory}
															on:click={() => handleCategoryClick(category)}
														>
															<svelte:component this={getCategoryIcon(category)} class="w-6 h-6 mr-2" />
															{category}
														</button>
													{/each}
												</div>
											{:else}
												<div class="p-4" transition:slide={{ duration: 200 }}>
													<div class="flex items-center mb-4">
														<button
															class="text-blue-500 hover:text-blue-700 mr-2 flex items-center"
															on:click={resetSelection}
														>
															<svg class="w-4 h-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
																<path
																	fill-rule="evenodd"
																	d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
																	clip-rule="evenodd"
																/>
															</svg>
															Back to categories
														</button>
														<h3 class="text-lg font-semibold">
															Select a {selectedCategory} device:
														</h3>
													</div>
													<div class="grid grid-cols-2 gap-4">
														{#each deviceOptions as device, index}
															<label
																class="flex items-center p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200"
															>
																<input
																	type="radio"
																	name="device"
																	value={device}
																	on:change={() => handleDeviceSelect(device)}
																	class="mr-2"
																/>
																<span>{device}</span>
															</label>
														{/each}
													</div>
												</div>
											{/if}
										</div>
									{/if}
								</div>
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
									<label for={varName} class="block text-sm font-medium text-gray-700 mb-2">
										{varName
											.split('_')
											.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
											.join(' ')}:
									</label>
									<input
										class="p-4 mt-2 w-full bg-white rounded-lg shadow-md border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
								class="ml-4 h-full p-4 bg-gray-200 text-black rounded-lg"
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

		{#if $variablesStore}
			<div class="flex justify-end p-4">
				<button
					class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
					on:click={handleCreateCustomizedPrompt}
				>
					Send
				</button>
			</div>
		{/if}
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
