<script lang="ts">
	import type { Article, i18nType } from '$lib/types';
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getArticlesForReview } from '$lib/apis/articles';
	import { showSidebar, user } from '$lib/stores';
	import Card from '$lib/components/cisco/components/common/Card.svelte';

	const i18n: i18nType = getContext('i18n');

	let articles: Article[] = [];

	onMount(async () => {
		if ($user && $user.role === 'admin') {
			showSidebar.set(false);
			articles = await getArticlesForReview(localStorage.token);
		} else {
			await goto('/');
		}
	});
</script>

<div class="w-full h-full py-2">
	<div class="text-center font-bold text-lg text-gray-800 dark:text-gray-50">
		{$i18n.t('Articles requiring action')}
	</div>
	<div class="flex flex-wrap gap-4 items-center justify-evenly">
		{#each articles as article, i (i)}
			<Card id={article.id} title={article.title} published={article.published ?? false} category={article.category} />
		{/each}
	</div>
</div>
