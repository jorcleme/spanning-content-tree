<script lang="ts">
	import type { Article, Message } from '$lib/types';
	import type { i18nType } from '$lib/types';
	import { getContext, onMount } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { flip } from 'svelte/animate';
	import { quintOut } from 'svelte/easing';
	import { crossfade } from 'svelte/transition';
	import { getArticlesBySeriesId } from '$lib/apis/articles';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { models, settings } from '$lib/stores';
	import dayjs from 'dayjs';
	import Card from '$lib/components/cisco/components/common/Card.svelte';
	import Image from '$lib/components/common/Image.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Name from './Name.svelte';
	import ProfileImage from './ProfileImage.svelte';
	import { InfoIcon } from 'lucide-svelte';

	const i18n: i18nType = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let message: Message;
	export let seriesId = '';
	export let seriesName = '';

	let model = null;
	$: model = $models.find((m) => m.id === message.model);

	let searchQuery = '';
	let articles: Article[] = [];
	let loading = false;
	let showInfo = false;

	const [send, receive] = crossfade({
		duration: (d) => Math.sqrt(d * 200),

		fallback(node, params) {
			const style = getComputedStyle(node);
			const transform = style.transform === 'none' ? '' : style.transform;

			return {
				duration: 600,
				easing: quintOut,
				css: (t) => `
				transform: ${transform} scale(${t});
				opacity: ${t}
			`
			};
		}
	});

	const fetchArticles = async () => {
		loading = true;
		const res = await getArticlesBySeriesId(localStorage.token, seriesId).catch((err) => {
			console.error(err);
			loading = false;
			return null;
		});
		if (res) {
			articles = res.filter((a) => a.published);
		}
		loading = false;
	};

	onMount(async () => {
		// Necessary for loaded chat history, we save the seriesId from the message content
		if (message?.content) {
			const content = JSON.parse(message.content);
			if (content.seriesId && content.seriesId !== '') {
				seriesId = content.seriesId;
			}
		}
	});

	$: if (seriesId && seriesId !== '') {
		fetchArticles();
	}

	const onHandleWheel = (event: WheelEvent & { currentTarget: EventTarget & HTMLDivElement }) => {
		if (event.deltaY !== 0) {
			// If scrolling vertically, prevent default behavior
			event.preventDefault();
			// Adjust horizontal scroll position based on vertical scroll
			event.currentTarget.scrollLeft += event.deltaY * 2;
		}
	};
</script>

{#key seriesId}
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
							<div class="flex flex-col gap-4">
								<h2 class="my-2 text-center">
									{$i18n.t('Current Articles for {{seriesName}}', { seriesName })}
								</h2>
								<input
									class="self-center rounded-md border border-gray-300 dark:border-gray-700 px-2 py-1 w-full sm:max-w-sm mx-auto"
									type="text"
									placeholder={$i18n.t('Search Articles')}
									bind:value={searchQuery}
								/>
								<div class="flex">
									{#if loading}
										<div class="self-center">
											<Spinner />
										</div>
									{:else}
										<div
											on:wheel={onHandleWheel}
											id="articles-container"
											class="w-full mt-4 snap-x snap-mandatory overflow-x-scroll scroll-ml-2 scroll-smooth grid grid-flow-col gap-2 overscroll-x-contain h-max pb-2.5"
										>
											{#each articles.filter((a) => searchQuery === '' || a.title
														.toLowerCase()
														.includes(searchQuery.toLowerCase())) as article (article.id)}
												<div
													class="snap-center"
													in:receive={{ key: article.id }}
													out:send={{ key: article.id }}
													animate:flip={{ duration: 400 }}
												>
													<Card
														id={article.id}
														title={article.title}
														category={article.category}
														url={article.url}
														published={article.published}
													/>
												</div>
											{/each}
										</div>
									{/if}
								</div>
								<small class="my-4 p-2"
									>Not seeing the article you're looking for? Our writers publish new content all the time. In the
									meantime, we can use AI to generate one for you.</small
								>
								<div class="grid grid-cols-4 items-center">
									<button
										class="btn col-start-2 col-span-2 self-center px-4 py-2 bg-[#1990fa] text-white rounded-md shadow-md hover:bg-[#1e88e5]"
										on:click={() => dispatch('generate')}>Generate New Article</button
									>
									<div class="col-start-4 col-span-1 justify-self-end flex space-x-1 mr-1">
										<Tooltip content={$i18n.t('Info')}>
											<button
												class="text-gray-600 dark:text-gray-300 bg-gray-300/20 size-5 flex items-center justify-center text-[0.7rem] rounded-full"
												type="button"
												on:click={() => {
													showInfo = !showInfo;
												}}
											>
												<InfoIcon class="w-5 h-5 translate-y-[0.5px]" />
											</button>
										</Tooltip>
									</div>
								</div>
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

<Modal bind:show={showInfo}>
	<div class="p-4">
		<div class="flex justify-between dark:text-gray-300 px-5 pb-4">
			<div class="text-lg font-medium font-bold self-center">{$i18n.t('Generated Articles')}</div>
			<button
				class="self-center"
				on:click={() => {
					showInfo = false;
				}}
			>
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>
		<div class="flex flex-col space-y-3 text-base">
			<div class="flex items-center">
				<span class="font-bold mr-2">1.</span>
				<p class="font-light">
					Generated articles are created by AI using Cisco Documentation. It can still make mistakes.
				</p>
			</div>
			<div class="flex items-center">
				<span class="font-bold mr-2">2.</span>
				<p class="font-light">Articles must be reviewed by a Cisco team member prior to publishing.</p>
			</div>
			<div class="flex items-center">
				<span class="font-bold mr-2">3.</span>
				<p class="font-light">We can notify you once the article becomes publicly available.</p>
			</div>
			<div class="flex self-center">
				<button
					class="btn flex items-center justify-center px-4 py-2 bg-[#1990fa] text-white rounded-md shadow-md"
					on:click={() => {
						showInfo = false;
						toast.success('We will notify you once the article is available.');
					}}>{$i18n.t('Yes, notify me')}</button
				>
			</div>
		</div>
	</div>
</Modal>
