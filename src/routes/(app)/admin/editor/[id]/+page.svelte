<script lang="ts">
	import type { Article, BlockType, i18nType } from '$lib/types';

	import { afterUpdate, getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	import { page } from '$app/stores';
	import { getArticleById } from '$lib/apis/articles';
	import { EDITOR_THEME } from '$lib/constants';
	import { activeArticle, reviewedArticle, showSidebar } from '$lib/stores';
	import '@harbor/elements/button';
	import '@harbor/elements/tag';
	import { type MarkedOptions, marked } from 'marked';

	import Editor from '$lib/components/cisco/components/editor/Editor.svelte';
	import ArticleReview from '$lib/components/cisco/components/editor/common/ArticleReview.svelte';

	const i18n: i18nType = getContext('i18n');

	const renderer = new marked.Renderer();

	renderer.list = (body, ordered) => {
		const type = ordered ? 'ol' : 'ul';
		return `<${type} class='space-y-2 cisco-list'>${body}</${type}>`;
	};

	renderer.listitem = (text) => {
		return `<li class="ml-2 cisco-list-item">${text}</li>`;
	};

	// For code blocks with simple backticks
	renderer.codespan = (code) => {
		return `<code>${code.replaceAll('&amp;', '&')}</code>`;
	};

	// Open all links in a new tab/window (from https://github.com/markedjs/marked/issues/655#issuecomment-383226346)
	const origLinkRenderer = renderer.link;
	renderer.link = (href, title, text) => {
		const html = origLinkRenderer.call(renderer, href, title, text);
		return html.replace(/^<a /, '<a target="_blank" rel="nofollow" ');
	};

	const { extensions, ...defaults } = marked.getDefaults() as MarkedOptions & {
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		extensions: any;
	};

	$: parseStepText = function (text: string) {
		return marked.parse(text, { renderer, ...defaults, gfm: true, breaks: true });
	};

	let loaded = false;
	let articleId: string = '';
	$: articleId = $page.params.id;

	let articleTitle = '';

	// Editor theme (class names) for styling

	type Section = { id: number; title: keyof Article; content: string; tag: BlockType };
	type Device = Article['applicable_devices'][number];
	let articleSections: Section[] = [];

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

	const formatTitle = (title: string) => {
		return title.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
	};

	let savedSections: any[] = [];

	const onKeydown = (e: KeyboardEvent) => {
		e.key === 'Enter' && console.log(savedSections);
	};
</script>

{#if loaded}
	<main id="editor-page" class="p-4 min-h-screen">
		<ArticleReview>
			<hbr-button role="button" tabindex="-1" on:click={() => console.log(savedSections)} on:keydown={onKeydown}>
				Export Article HTML
			</hbr-button>
		</ArticleReview>
	</main>
{/if}

<style>
	main {
		margin: 0 auto;
		padding: 1rem;
	}
</style>
