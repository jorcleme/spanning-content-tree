<script lang="ts">
	import type { i18nType } from '$lib/types';

	import { getContext, onMount } from 'svelte';

	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { WEBUI_NAME, showSidebar, user } from '$lib/stores';

	import MenuLines from '$lib/components/icons/MenuLines.svelte';

	const i18n: i18nType = getContext('i18n');

	let loaded: boolean = false;

	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
		}
		loaded = true;
	});

	$: console.log($page.url.pathname);
	$: console.log($page.route.id);

	$: editorPage = $page.url.pathname.includes('/admin/editor');
</script>

<svelte:head>
	<title>
		{$i18n.t('Admin Panel')} | {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
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
				<div class="flex items-center text-xl font-semibold">{$i18n.t('Admin Panel')}</div>
				{#if editorPage}
					<div class="flex items-center text-sm font-thin ml-2">&gt;</div>
					<div class="flex items-center text-sm font-medium ml-2">
						{$i18n.t('Editor')}
					</div>
				{/if}
			</div>
		</div>

		<div class="px-4 my-1">
			<div
				class="flex scrollbar-none overflow-x-auto w-fit text-center text-sm font-medium rounded-xl bg-transparent/10 dark:bg-gray-800 p-1"
			>
				<a
					class="min-w-fit rounded-lg p-1.5 px-3 {['/admin', '/admin/'].includes($page.url.pathname)
						? 'bg-gray-50 dark:bg-gray-850'
						: ''} transition"
					href="/admin">{$i18n.t('Dashboard')}</a
				>

				<a
					class="min-w-fit rounded-lg p-1.5 px-3 {$page.url.pathname.includes('/admin/settings')
						? 'bg-gray-50 dark:bg-gray-850'
						: ''} transition"
					href="/admin/settings">{$i18n.t('Settings')}</a
				>
				<a
					class="min-w-fit rounded-lg p-1.5 px-3 {$page.url.pathname.includes('/admin/editor')
						? 'bg-gray-50 dark:bg-gray-850'
						: ''} transition"
					href="/admin/editor">{$i18n.t('Editor')}</a
				>
			</div>
		</div>

		<hr class=" my-2 dark:border-gray-850" />

		<div class="py-1 px-5 flex-1 max-h-full overflow-y-auto">
			<slot />
		</div>
	</div>
{/if}
