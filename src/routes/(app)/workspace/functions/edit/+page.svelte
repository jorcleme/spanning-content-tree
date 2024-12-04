<script lang="ts">
	import type { i18nType } from '$lib/types';
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { getModels } from '$lib/apis';
	import { getFunctionById, getFunctions, updateFunctionById } from '$lib/apis/functions';
	import { WEBUI_VERSION } from '$lib/constants';
	import type { _Function } from '$lib/stores';
	import { functions, models } from '$lib/stores';
	import { compareVersion, extractFrontmatter } from '$lib/utils';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import FunctionEditor from '$lib/components/workspace/Functions/FunctionEditor.svelte';

	const i18n: i18nType = getContext('i18n');

	let func: _Function | null = null;

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

		if (func) {
			const res = await updateFunctionById(localStorage.token, func.id, {
				id: data.id,
				name: data.name,
				meta: data.meta,
				content: data.content
			}).catch((error) => {
				toast.error(error);
				return null;
			});

			if (res) {
				toast.success($i18n.t('Function updated successfully'));
				functions.set(await getFunctions(localStorage.token));
				models.set(await getModels(localStorage.token));
			}
		}
	};

	onMount(async () => {
		console.log('mounted');
		const id = $page.url.searchParams.get('id');

		if (id) {
			func = await getFunctionById(localStorage.token, id).catch((error) => {
				toast.error(error);
				goto('/workspace/functions');
				return null;
			});

			console.log(func);
		}
	});
</script>

{#if func}
	<FunctionEditor
		edit={true}
		id={func.id}
		name={func.name}
		meta={func.meta}
		content={func.content}
		on:save={(e) => {
			saveHandler(e.detail);
		}}
	/>
{:else}
	<div class="flex items-center justify-center h-full">
		<div class=" pb-16">
			<Spinner />
		</div>
	</div>
{/if}
