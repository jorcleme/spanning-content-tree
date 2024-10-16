<script lang="ts">
	import type { Article } from '$lib/types';
	import { onMount } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	import { getArticlesBySeriesId } from '$lib/apis/articles';
	const dispatch = createEventDispatcher();

	export let seriesId = '';
	let searchQuery = '';
	let articles: Article[] = [];
	let filteredArticles: Article[] = [];

	onMount(async () => {
		// Fetch articles from the database
		console.log(seriesId);
		if (seriesId && seriesId !== '') {
			const res = await getArticlesBySeriesId(localStorage.token, seriesId).catch((err) => {
				console.error(err);
				return null;
			});
			console.log(res);
			if (res) {
				articles = res;
				filteredArticles = [...articles];
			}
		}
	});

	function handleSearch() {
		filteredArticles = articles.filter((article) => article.title.toLowerCase().includes(searchQuery.toLowerCase()));
	}

	function handleGenerateNewArticle() {
		dispatch('generateNewArticle');
	}
</script>

<div>
	<h2>Known Article Topics</h2>
	<input type="text" placeholder="Search articles..." bind:value={searchQuery} on:input={handleSearch} />
	{#key filteredArticles}
		<ul>
			{#each filteredArticles as article}
				<li>
					<a target="_blank" href={article.url}>{article.title}</a><span class="ml-2 text-sm"
						>{new Date(article.created_at).toISOString()}</span
					>
				</li>
			{/each}
		</ul>
		<button on:click={handleGenerateNewArticle}>Generate New Article</button>
	{/key}
</div>
