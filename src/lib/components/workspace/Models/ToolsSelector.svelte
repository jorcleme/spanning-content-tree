<script lang="ts">
	import type { Tool } from '$lib/types';
	import type { i18nType } from '$lib/types';
	import { getContext, onMount } from 'svelte';
	import Checkbox from '$lib/components/common/Checkbox.svelte';

	type ToolByIdWithSelected = { [key: string]: Tool & { selected: boolean } };

	const i18n: i18nType = getContext('i18n');

	export let tools: Tool[] = [];
	export let selectedToolIds: string[] = [];

	let _tools: ToolByIdWithSelected = {};

	onMount(() => {
		_tools = tools.reduce<ToolByIdWithSelected>((acc, tool) => {
			acc[tool.id] = {
				...tool,
				selected: selectedToolIds.includes(tool.id)
			};

			return acc;
		}, {});
	});
</script>

<div>
	<div class="flex w-full justify-between mb-1">
		<div class=" self-center text-sm font-semibold">{$i18n.t('Tools')}</div>
	</div>

	<div class=" text-xs dark:text-gray-500">
		{$i18n.t('To select toolkits here, add them to the "Tools" workspace first.')}
	</div>

	<div class="flex flex-col">
		{#if tools.length > 0}
			<div class=" flex items-center mt-2 flex-wrap">
				{#each Object.keys(_tools) as tool, toolIdx}
					<div class=" flex items-center gap-2 mr-3">
						<div class="self-center flex items-center">
							<Checkbox
								state={_tools[tool].selected ? 'checked' : 'unchecked'}
								on:change={(e) => {
									_tools[tool].selected = e.detail === 'checked';
									selectedToolIds = Object.keys(_tools).filter((t) => _tools[t].selected);
								}}
							/>
						</div>

						<div class=" py-0.5 text-sm w-full capitalize font-medium">
							{_tools[tool].name}
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
