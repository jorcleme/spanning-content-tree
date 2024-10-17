<script lang="ts">
	import type { Article } from '$lib/types';
	import { onMount } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	import { getArticlesBySeriesId } from '$lib/apis/articles';

	import Card from '../components/common/Card.svelte';
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

<div class="flex flex-col">
	<h2 class="my-2 text-center">Known Article Topics</h2>
	<input
		class="self-center"
		type="text"
		placeholder="Search articles..."
		bind:value={searchQuery}
		on:input={handleSearch}
	/>
	<div class="flex m-4">
		{#key filteredArticles}
			<div
				class="w-full mt-4 snap-x snap-mandatory overflow-x-scroll scroll-ml-2 scroll-smooth grid grid-flow-col gap-2 overscroll-x-contain h-max pb-2.5"
			>
				{#each filteredArticles as article (article.id)}
					<div class="snap-center">
						<Card id={article.id} title={article.title} category={article.category} />
					</div>
				{/each}
			</div>
		{/key}
	</div>
	<button class="btn self-center px-4 py-2 bg-[#1990fa] text-white" on:click={handleGenerateNewArticle}
		>Generate New Article</button
	>
</div>
