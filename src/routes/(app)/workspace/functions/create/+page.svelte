<script lang="ts">
	import type { i18nType } from '$lib/types';
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { getModels } from '$lib/apis';
	import { createNewFunction, getFunctions } from '$lib/apis/functions';
	import { WEBUI_VERSION } from '$lib/constants';
	import type { Func } from '$lib/stores';
	import { functions, models } from '$lib/stores';
	import { compareVersion, extractFrontmatter } from '$lib/utils';
	import FunctionEditor from '$lib/components/workspace/Functions/FunctionEditor.svelte';

	const i18n: i18nType = getContext('i18n');

	let mounted = false;
	let clone = false;
	let func: Func | null = null;

	const saveHandler = async (data: Record<string, any>) => {
		console.log(data);

		const manifest = extractFrontmatter(data.content);
		if (compareVersion(manifest?.required_open_webui_version ?? '0.0.0', WEBUI_VERSION)) {
			console.log('Version is lower than required');
			toast.error(
				$i18n.t('Open WebUI version (v{{OPEN_WEBUI_VERSION}}) is lower than required version (v{{REQUIRED_VERSION}})', {
					OPEN_WEBUI_VERSION: WEBUI_VERSION,
					REQUIRED_VERSION: manifest?.required_open_webui_version ?? '0.0.0'
				})
			);
			return;
		}

		const res = await createNewFunction(localStorage.token, {
			id: data.id,
			name: data.name ?? data.function?.name,
			meta: data.meta ?? data.function?.meta,
			content: data.content ?? data.function?.content
		}).catch((error) => {
			toast.error(error);
			return null;
		});

		if (res) {
			toast.success($i18n.t('Function created successfully'));
			functions.set(await getFunctions(localStorage.token));
			models.set(await getModels(localStorage.token));

			await goto('/workspace/functions');
		}
	};

	onMount(() => {
		window.addEventListener('message', async (event) => {
			if (!['https://openwebui.com', 'https://www.openwebui.com', 'http://localhost:9999'].includes(event.origin))
				return;

			func = JSON.parse(event.data);
			console.log(func);
		});

		if (window.opener ?? false) {
			window.opener.postMessage('loaded', '*');
		}

		if (sessionStorage.function) {
			func = JSON.parse(sessionStorage.function);
			sessionStorage.removeItem('function');

			console.log(func);
			clone = true;
		}

		mounted = true;
	});
</script>

{#if mounted}
	{#key func?.content}
		<FunctionEditor
			id={func?.id ?? ''}
			name={func?.name ?? ''}
			meta={func?.meta ?? { description: '' }}
			content={func?.content ?? ''}
			{clone}
			on:save={(e) => {
				saveHandler(e.detail);
			}}
		/>
	{/key}
{/if}
