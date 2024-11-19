<script lang="ts">
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { activeArticle } from '$lib/stores';
	import { getArticleById } from '$lib/apis/articles';
	import Article from '$lib/components/cisco/components/articles/Article.svelte';
	import GetSupportWidgetContainer from '$lib/components/cisco/components/articles/GetSupportWidgetContainer.svelte';

	const i18n: Writable<i18nType> = getContext('i18n');

	onMount(async () => {
		if (!$activeArticle) {
			activeArticle.set(await getArticleById(localStorage.token, $page.params.id));
			await goto(`/article/${$page.params.id}`);
		}
	});
</script>

<Article>
	<GetSupportWidgetContainer />
</Article>
