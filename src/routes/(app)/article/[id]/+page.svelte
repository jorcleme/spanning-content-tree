<script lang="ts">
	import type { i18nType } from '$lib/types';
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { getArticleById } from '$lib/apis/articles';
	import { activeArticle } from '$lib/stores';
	import Article from '$lib/components/cisco/components/articles/Article.svelte';
	import GetSupportWidgetContainer from '$lib/components/cisco/components/articles/GetSupportWidgetContainer.svelte';

	const i18n: i18nType = getContext('i18n');

	onMount(async () => {
		if (!$activeArticle) {
			activeArticle.set(await getArticleById(localStorage.token, $page.params.id));
			await goto(`/article/${$page.params.id}`);
		}
	});
</script>

<Article on:save={() => toast.success($i18n.t('Article saved successfully'))}>
	<GetSupportWidgetContainer />
</Article>
