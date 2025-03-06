<script lang="ts">
	import type { i18nType } from '$lib/types';

	import { getContext } from 'svelte';

	import { flyAndScale } from '$lib/utils/transitions';
	import { DropdownMenu } from 'bits-ui';

	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import CommandLine from '$lib/components/icons/CommandLine.svelte';
	import GuideMe from '$lib/components/icons/GuideMe.svelte';

	const i18n: i18nType = getContext('i18n');

	export let openConfigAssistant: () => void;
	export let handleGeneratePromptClick: () => void;
	export let onClose: () => void;
	let show: boolean = false;
</script>

<Dropdown
	bind:show
	on:change={(e) => {
		if (e.detail === false) {
			onClose();
		}
	}}
>
	<Tooltip content={$i18n.t('More')}>
		<slot />
	</Tooltip>

	<div slot="content">
		<DropdownMenu.Content
			class="w-full max-w-[160px] rounded-xl px-1 py-1.5 border border-gray-300/30 dark:border-gray-700/50 z-50 bg-white dark:bg-gray-850 dark:text-white shadow"
			sideOffset={-2}
			side="bottom"
			align="start"
			transition={flyAndScale}
		>
			<DropdownMenu.Item
				class="flex gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
				on:click={() => {
					openConfigAssistant();
				}}
			>
				<CommandLine />
				<div class="flex items-center">{$i18n.t('Config Assistant')}</div>
			</DropdownMenu.Item>

			<DropdownMenu.Item
				class="flex gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
				on:click={() => {
					handleGeneratePromptClick();
				}}
			>
				<GuideMe />

				<div class="flex items-center">{$i18n.t('Guide Me')}</div>
			</DropdownMenu.Item>
		</DropdownMenu.Content>
	</div>
</Dropdown>
