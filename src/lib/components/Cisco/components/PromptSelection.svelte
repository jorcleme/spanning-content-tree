<script lang="ts">
	import { writable } from 'svelte/store';
	import { createEventDispatcher, onMount } from 'svelte';
	import { slide } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import { X, Network, Router, Wifi, Cloud, Users } from 'lucide-svelte';
	import { promptStore, variablesStore } from '$lib/stores';

	export let showPromptIntro: boolean;
	export let editablePrompt: string;
	export let handleClose: () => void;
	export let handleGeneratePromptClick: () => void;
	export let updateVariables: (template: string) => void;

	onMount(() => {
		console.log('PromptSelection mounted');
	});

	const dispatch = createEventDispatcher();
	let formattedEditablePrompt = '';

	const CISCO_SMB_JOURNEYS = [
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

	const handleJourneySelect = (journey: string) => {
		showPromptIntro = false;
		const selectedJourney = CISCO_SMB_JOURNEYS.find((j) => j.text === journey);
		if (selectedJourney) {
			variablesStore.update((v) => ({ ...v, subject: journey }));
			editablePrompt = selectedJourney.template;
			promptStore.set(selectedJourney.template);
			updateVariables(selectedJourney.template);
			updateFormattedPrompt(selectedJourney.template);
		}
	};
	function updateFormattedPrompt(template: string) {
		formattedEditablePrompt = template.replace(/\[\[(.*?)\]\]/g, (match, p1) => {
			const varName = p1.trim();
			return `<span class="variable" data-variable="${varName}">${match}</span>`;
		});
	}

	function extractVariables(text: string) {
		const regex = /\[\[(.*?)\]\]/g;
		const matches = [...text.matchAll(regex)];
		return [...new Set(matches.map((match) => match[1].trim()))];
	}
</script>

{#if showPromptIntro}
	<div
		class="text-black p-10 max-w-5xl w-full"
		transition:slide={{ duration: 500, easing: cubicOut }}
	>
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
					{#each CISCO_SMB_JOURNEYS as journey}
						<button
							class="flex items-center justify-between w-full bg-gray-600 hover:bg-gray-700 text-white py-2 px-3 rounded text-left transition-colors duration-200 text-sm mx-4"
							on:click={() => handleJourneySelect(journey.text)}
						>
							<div class="flex items-center space-x-2">
								<svelte:component this={journey.icon} size={16} />
								<span style="width:max-content">{journey.text}</span>
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
