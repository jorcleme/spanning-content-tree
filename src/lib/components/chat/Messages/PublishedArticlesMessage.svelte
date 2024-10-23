<script lang="ts">
	import type { Message, Article } from '$lib/types';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { getContext, onMount } from 'svelte';
	import { models, settings } from '$lib/stores';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { toast } from 'svelte-sonner';
	import dayjs from 'dayjs';
	import Name from './Name.svelte';
	import ProfileImage from './ProfileImage.svelte';
	import Image from '$lib/components/common/Image.svelte';
	import { createEventDispatcher } from 'svelte';
	import { getArticlesBySeriesId } from '$lib/apis/articles';
	import Card from '$lib/components/cisco/components/common/Card.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n: Writable<i18nType> = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let message: Message;
	export let seriesId = '';
	export let seriesName = '';

	let model = null;
	$: model = $models.find((m) => m.id === message.model);

	let searchQuery = '';
	let articles: Article[] = [];
	let filteredArticles: Article[] = [];
	let loading = false;

	onMount(async () => {
		// Fetch articles from the database
		console.log(seriesId);
		if (seriesId && seriesId !== '') {
			loading = true;
			const res = await getArticlesBySeriesId(localStorage.token, seriesId).catch((err) => {
				console.error(err);
				loading = false;
				return null;
			});
			console.log(res);
			if (res) {
				articles = res;
				filteredArticles = [...articles];
			}
			loading = false;
		}
	});

	function handleSearch() {
		filteredArticles = articles.filter((article) => article.title.toLowerCase().includes(searchQuery.toLowerCase()));
	}

	function handleGenerateNewArticle() {
		dispatch('generate');
	}
</script>

{#key message.id}
	<div class=" flex w-full message-{message.id}" id="message-{message.id}" dir={$settings.chatDirection}>
		<ProfileImage
			src={model?.info?.meta?.profile_image_url ??
				($i18n.language === 'dg-DG' ? `/doge.png` : `${WEBUI_BASE_URL}/static/favicon.png`)}
		/>

		<div class="w-full overflow-hidden pl-1">
			<Name>
				{model?.name ?? message.model}

				{#if message.timestamp}
					<span class=" self-center invisible group-hover:visible text-gray-400 text-xs font-medium uppercase">
						{dayjs(message.timestamp * 1000).format($i18n.t('h:mm a'))}
					</span>
				{/if}
			</Name>
			{#if message.files}
				{#if (message.files ?? []).filter((f) => f.type === 'image').length > 0}
					{#each message.files as file}
						<div>
							{#if file.type === 'image'}
								<Image src={file.url} />
							{/if}
						</div>
					{/each}
				{/if}
			{/if}

			<div class="chat-{message.role} w-full max-w-full">
				<div>
					<div class="w-full">
						<div class="flex flex-col">
							<div class="flex flex-col">
								<h2 class="my-2 text-center">
									{$i18n.t('Current Articles for {{seriesName}}', { seriesName })}
								</h2>
								<input
									class="self-center"
									type="text"
									placeholder="Search articles..."
									bind:value={searchQuery}
									on:input={handleSearch}
								/>
								<div class="flex m-4">
									{#if loading}
										<Spinner />
									{:else}
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
									{/if}
								</div>
								<small
									>Not seeing the article you're looking for? Our writers are publishing new content all the time. In
									the meantime, we can use AI to generate one for you.</small
								>
								<button class="btn self-center px-4 py-2 bg-[#1990fa] text-white" on:click={handleGenerateNewArticle}
									>Generate New Article</button
								>
							</div>
						</div>

						{#if message.error}
							<div
								class="flex mt-2 mb-4 space-x-2 border px-4 py-3 border-red-800 bg-red-800/30 font-medium rounded-lg"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-5 h-5 self-center"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
									/>
								</svg>

								<div class=" self-center">
									{message?.error?.content ?? message.content}
								</div>
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	</div>
{/key}
