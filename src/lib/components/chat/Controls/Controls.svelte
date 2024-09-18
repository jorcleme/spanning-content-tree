<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import { type i18n as i18nType } from 'i18next';
	import type { Model, ChatParams } from '$lib/stores';
	import type { ChatFile } from '$lib/types';
	// @ts-ignore
	import { interpolateLab } from 'd3-interpolate';

	const dispatch = createEventDispatcher();
	const i18n: Writable<i18nType> = getContext('i18n');

	import XMark from '$lib/components/icons/XMark.svelte';
	import AdvancedParams from '../Settings/Advanced/AdvancedParams.svelte';
	import Valves from '$lib/components/common/Valves.svelte';
	import FileItem from '$lib/components/common/FileItem.svelte';
	import { tweened } from 'svelte/motion';

	export let models: Model[] = [];

	export let chatFiles: ChatFile[] = [];
	export let valves = {};
	export let params: ChatParams = {
		system: null,
		seed: null,
		stop: null,
		temperature: null,
		max_tokens: null,
		mirostat: null,
		mirostat_eta: null,
		mirostat_tau: null,
		use_mlock: null,
		use_mmap: null,
		num_batch: null,
		num_ctx: null,
		num_keep: null,
		num_thread: null,
		repeat_last_n: null,
		tfs_z: null,
		top_k: null,
		top_p: null,
		template: null,
		frequency_penalty: null,
		proficiency: 0
	};

	let proficiency = 0;
	const labels = ['Beginner', 'Intermediate', 'Advanced'];
	// const colors = ['bg-green-500', 'bg-yellow-500', 'bg-red-500'];
	// let color = 'rgb(25, 144, 250)';
	const colors = ['rgb(25, 144, 250)', 'rgb(15, 90, 210)', 'rgb(9, 70, 200)'];
	const color = tweened(colors[0], {
		duration: 800,
		interpolate: interpolateLab
	});

	function getProficiencyColor(proficiency: number) {
		return colors[proficiency];
	}

	const handleProficiencyChange = async (
		e: Event & { currentTarget: EventTarget & HTMLInputElement }
	) => {
		const value = Number((e.target as HTMLInputElement).value);
		params.proficiency = value;
		await color.set(colors[value]);
	};

	// {getProficiencyColor(
	// 					proficiency
	// 				)}
</script>

<div class=" dark:text-white">
	<div class=" flex justify-between dark:text-gray-100 mb-2">
		<div class=" text-lg font-medium self-center font-primary">{$i18n.t('Chat Controls')}</div>
		<button
			class="self-center"
			on:click={() => {
				dispatch('close');
			}}
		>
			<XMark className="size-4" />
		</button>
	</div>

	<div class=" dark:text-gray-200 text-sm font-primary">
		{#if chatFiles.length > 0}
			<div>
				<div class="mb-1.5 font-medium">{$i18n.t('Files')}</div>

				<div class="flex flex-col gap-1">
					{#each chatFiles as file, fileIdx}
						<FileItem
							className="w-full"
							url={`${file?.url}`}
							name={file.name}
							type={file.type}
							dismissible={true}
							on:dismiss={() => {
								// Remove the file from the chatFiles array

								chatFiles.splice(fileIdx, 1);
								chatFiles = chatFiles;
							}}
						/>
					{/each}
				</div>
			</div>

			<hr class="my-2 border-gray-100 dark:border-gray-800" />
		{/if}

		{#if models.length === 1 && models[0]?.pipe?.valves_spec}
			<div>
				<div class=" font-medium">{$i18n.t('Valves')}</div>

				<div>
					<Valves valvesSpec={models[0]?.pipe?.valves_spec} bind:valves />
				</div>
			</div>

			<hr class="my-2 border-gray-100 dark:border-gray-800" />
		{/if}
		<div class="mb-4">
			<label for="proficiency-slider" class="block text-md font-medium dark:text-gray-200 mb-2">
				Network Proficiency Level
			</label>
			<div class="flex items-center space-x-4 justify-evenly">
				<span class="text-sm dark:text-gray-300">Beginner</span>
				<input
					id="proficiency-slider"
					type="range"
					min="0"
					max="2"
					step="1"
					bind:value={proficiency}
					class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 max-w-fit"
					style:background-color={$color}
					on:change={handleProficiencyChange}
				/>
				<span class="text-sm dark:text-gray-300">Advanced</span>
			</div>
			<div class="text-center mt-2 text-sm font-medium dark:text-gray-400" id="proficiency-label">
				{labels[proficiency]}
			</div>
		</div>

		<div>
			<div class="mb-1.5 font-medium">{$i18n.t('System Prompt')}</div>

			<div>
				<textarea
					bind:value={params.system}
					class="w-full rounded-lg px-4 py-3 text-sm dark:text-gray-300 dark:bg-gray-850 border border-gray-100 dark:border-gray-800 outline-none resize-none"
					rows="3"
					placeholder={$i18n.t('Enter system prompt')}
				/>
			</div>
		</div>

		<hr class="my-2 border-gray-100 dark:border-gray-800" />

		<div>
			<div class="mb-1.5 font-medium">{$i18n.t('Advanced Params')}</div>

			<div>
				<AdvancedParams bind:params />
			</div>
		</div>
	</div>
</div>
