<script lang="ts">
	import type { i18nType } from '$lib/types';

	import { getContext, onMount } from 'svelte';

	import { page } from '$app/stores';
	import { getFunctions } from '$lib/apis/functions';
	import { WEBUI_NAME, functions, showSidebar } from '$lib/stores';

	import MenuLines from '$lib/components/icons/MenuLines.svelte';

	const i18n: i18nType = getContext('i18n');

	onMount(async () => {
		// functions.set(await getFunctions(localStorage.token));
	});
</script>

<svelte:head>
	<title>
		{$i18n.t('Workspace')} | {$WEBUI_NAME}
	</title>
</svelte:head>

<div class=" flex flex-col w-full min-h-screen max-h-screen {$showSidebar ? 'md:max-w-[calc(100%-260px)]' : ''}">
	<div class=" px-4 pt-3 mt-0.5 mb-1">
		<div class=" flex items-center gap-1">
			<div class="{$showSidebar ? 'md:hidden' : ''} mr-1 self-start flex flex-none items-center">
				<button
					id="sidebar-toggle-button"
					class="cursor-pointer p-1 flex rounded-xl hover:bg-gray-100 dark:hover:bg-gray-850 transition"
					on:click={() => {
						showSidebar.set(!$showSidebar);
					}}
				>
					<div class=" m-auto self-center">
						<MenuLines />
					</div>
				</button>
			</div>
			<div class="flex items-center text-xl font-semibold">{$i18n.t('Workspace')}</div>
		</div>
	</div>

	<div class="px-4 my-1">
		<div
			class="flex scrollbar-none overflow-x-auto w-fit text-center text-sm font-medium rounded-xl bg-transparent/10 dark:bg-gray-800 p-1"
		>
			<a
				class="min-w-fit rounded-lg p-1.5 px-3 {$page.url.pathname.includes('/workspace/models')
					? 'bg-gray-50 dark:bg-gray-850'
					: ''} transition"
				href="/workspace/models">{$i18n.t('Models')}</a
			>

			<a
				class="min-w-fit rounded-lg p-1.5 px-3 {$page.url.pathname.includes('/workspace/prompts')
					? 'bg-gray-50 dark:bg-gray-850'
					: ''} transition"
				href="/workspace/prompts">{$i18n.t('Prompts')}</a
			>

			<a
				class="min-w-fit rounded-lg p-1.5 px-3 {$page.url.pathname.includes('/workspace/documents')
					? 'bg-gray-50 dark:bg-gray-850'
					: ''} transition"
				href="/workspace/documents"
			>
				{$i18n.t('Documents')}
			</a>

			<a
				class="min-w-fit rounded-lg p-1.5 px-3 {$page.url.pathname.includes('/workspace/tools')
					? 'bg-gray-50 dark:bg-gray-850'
					: ''} transition"
				href="/workspace/tools"
			>
				{$i18n.t('Tools')}
			</a>

			<a
				class="min-w-fit rounded-lg p-1.5 px-3 {$page.url.pathname.includes('/workspace/functions')
					? 'bg-gray-50 dark:bg-gray-850'
					: ''} transition"
				href="/workspace/functions"
			>
				{$i18n.t('Functions')}
			</a>
		</div>
	</div>

	<hr class=" my-2 dark:border-gray-850" />

	<div class=" py-1 px-5 flex-1 max-h-full overflow-y-auto">
		<slot />
	</div>
</div>
