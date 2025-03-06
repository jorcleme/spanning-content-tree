<script lang="ts">
	import type { i18nType } from '$lib/types';

	import { getContext, onMount } from 'svelte';

	import { page } from '$app/stores';
	import { getArticleById } from '$lib/apis/articles';
	import { activeArticle, showSidebar } from '$lib/stores';

	import ArticleReview from '$lib/components/cisco/components/editor/common/ArticleReview.svelte';

	const i18n: i18nType = getContext('i18n');

	let loaded = false;
	let articleId: string = '';
	$: articleId = $page.params.id;

	onMount(async () => {
		if ($showSidebar) {
			showSidebar.set(false);
		}
		const article = await getArticleById(localStorage.token, articleId);
		if (article) {
			activeArticle.set(article);
		}

		loaded = true;
		return Promise.resolve();
	});

	const getMimeType = (src: string) => {
		const ext = src.split('.').pop()?.toLowerCase().trim();
		switch (ext) {
			case 'mp4':
				return 'video/mp4';
			case 'webm':
				return 'video/webm';
			case 'ogg':
				return 'video/ogg';
			default:
				return 'video/mp4';
		}
	};

	let savedSections: any[] = [];

	const onKeydown = (e: KeyboardEvent) => {
		e.key === 'Enter' && console.log(savedSections);
	};
</script>

{#if loaded}
	<main id="editor-page" class="p-4 min-h-screen">
		<ArticleReview>
			<button
				class="shadow-md transition px-4 py-2 rounded-md bg-blue-950 text-gray-50 dark:bg-blue-100 dark:text-gray-850 hover:bg-blue-850 dark:hover:bg-blue-200"
				tabindex="0"
				on:click={() => console.log(savedSections)}
				on:keydown={onKeydown}
			>
				Export Article HTML
			</button>
		</ArticleReview>
	</main>
{/if}

<style>
	main {
		margin: 0 auto;
		padding: 1rem;
	}
</style>
