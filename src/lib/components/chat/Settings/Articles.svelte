<script lang="ts">
	import type { Article, i18nType } from '$lib/types';
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { getArticlesByUser as _getArticlesByUser, getManyArticlesByIds } from '$lib/apis/articles';
	import { getUserSavedArticles as _getUserSavedArticles, deleteOneUserSavedArticle } from '$lib/apis/users';
	import { user } from '$lib/stores';
	import Card from '$lib/components/cisco/components/common/Card.svelte';
	import { XIcon } from 'lucide-svelte';

	const i18n: i18nType = getContext('i18n');
	const dispatch = createEventDispatcher();

	let userArticles: Article[] = [];
	let savedArticles: Article[] = [];

	const getArticlesByUser = async () => {
		if (!$user) {
			return [] as Article[];
		}
		return await _getArticlesByUser(localStorage.token, $user?.id);
	};

	const getUserSavedArticles = async () => {
		const articleIds = await _getUserSavedArticles(localStorage.token);
		return await getManyArticlesByIds(articleIds);
	};

	const onRemoveSavedArticle = async (articleId: string) => {
		console.log('Remove saved article with id: ', articleId);
		savedArticles = savedArticles.filter((article) => article.id !== articleId);
		await deleteOneUserSavedArticle(localStorage.token, articleId);
		dispatch('save');
		return true;
	};

	const onClick = () => {
		if ($user) {
			getArticlesByUser().then((res) => {
				userArticles = res;
			});

			getUserSavedArticles().then((res) => {
				savedArticles = res;
			});

			dispatch('save');
		}
	};

	onMount(async () => {
		if ($user) {
			userArticles = await getArticlesByUser();
			savedArticles = await getUserSavedArticles();
		}
	});
</script>

<div class="flex flex-col h-full justify-between text-sm">
	<div class="pr-1.5 overflow-y-scroll max-h-[25rem]">
		<div class="mb-4">
			{#if userArticles.length === 0}
				<div class="text-gray-500 py-2">{$i18n.t('No generated articles')}</div>
			{:else}
				<div class=" mb-2 text-sm font-medium">{$i18n.t('Generated Articles')}</div>
				<div class="flex flex-wrap justify-between gap-3">
					{#each userArticles as article, i (article.id)}
						<Card
							id={article.id}
							title={article.title}
							category={article.category}
							published={i === 1 ? true : false}
						/>
					{/each}
				</div>
			{/if}
			<div class="flex justify-start text-gray-300 text-sm font-bold py-2">Generated Count: {userArticles.length}</div>
		</div>

		<hr class=" dark:border-gray-850 my-3" />

		<div>
			{#if savedArticles.length === 0}
				<div class="text-gray-500 py-2">{$i18n.t('No saved articles')}</div>
			{:else}
				<div class="my-3 text-sm font-medium">{$i18n.t('Saved Articles')}</div>
				<div class="flex flex-wrap justify-between gap-3">
					{#each savedArticles as article (article.id)}
						<div class="relative">
							<div class="absolute top-2 right-2 rounded-full bg-gray-100 hover:bg-gray-50 z-10">
								<button
									class="p-2 text-gray-500"
									title="Remove"
									on:click={async () => await onRemoveSavedArticle(article.id)}
								>
									<XIcon class="w-4 h-4" />
								</button>
							</div>
							<Card id={article.id} title={article.title} category={article.category} published={article.published} />
						</div>
					{/each}
				</div>
			{/if}
			<div class="flex justify-start text-gray-300 text-sm font-bold py-2">Saved Count: {savedArticles.length}</div>
		</div>
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="  px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-gray-100 transition rounded-lg"
			on:click={() => onClick()}
		>
			{$i18n.t('Save')}
		</button>
	</div>
</div>
