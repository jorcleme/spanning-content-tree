<script lang="ts">
	import type { Article, BlockType } from '$lib/types';
	import { afterUpdate, onMount } from 'svelte';
	import { quintIn } from 'svelte/easing';
	import { fly, slide } from 'svelte/transition';
	import { page } from '$app/stores';
	import { getArticleById } from '$lib/apis/articles';
	import { activeArticle, showSidebar } from '$lib/stores';
	import { t } from 'i18next';
	import { type MarkedOptions, marked } from 'marked';
	import Editor from '$lib/components/cisco/components/editor/Editor.svelte';
	import { Info } from 'lucide-svelte';

	$: if ($showSidebar) showSidebar.set(false);

	const renderer = new marked.Renderer();

	let imageLoaded: boolean = false;

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
	let articleObjective = '';
	let articleIntro = '';
	let articleApplicableDevices: Article['applicable_devices'] = [];
	let articleSteps: Article['steps'] = [];

	// Editor theme (class names) for styling
	const theme = {
		ltr: 'ltr',
		rtl: 'rtl',
		paragraph: 'editor-paragraph',
		layoutContainer: 'editor-layoutContainer',
		layoutItem: 'editor-layoutItem',
		quote: 'editor-quote',
		heading: {
			h1: 'editor-heading-h1',
			h2: 'editor-heading-h2',
			h3: 'editor-heading-h3',
			h4: 'editor-heading-h4',
			h5: 'editor-heading-h5',
			h6: 'editor-heading-h6'
		},
		list: {
			checklist: 'editor-checklist',
			listitem: 'editor-listItem',
			listitemChecked: 'editor-listItemChecked',
			listitemUnchecked: 'editor-listItemUnchecked',
			nested: {
				listitem: 'editor-nestedListItem'
			},
			olDepth: ['editor-ol1', 'editor-ol2', 'editor-ol3', 'editor-ol4', 'editor-ol5'],
			ul: 'editor-ul'
		},

		hashtag: 'editor-hashtag',
		image: 'editor-image',
		link: 'editor-link',
		text: {
			bold: 'editor-textBold',
			code: 'editor-textCode',
			italic: 'editor-textItalic',
			strikethrough: 'editor-textStrikethrough',
			subscript: 'editor-textSubscript',
			superscript: 'editor-textSuperscript',
			underline: 'editor-textUnderline',
			underlineStrikethrough: 'editor-textUnderlineStrikethrough'
		},
		code: 'editor-code',
		codeHighlight: {
			atrule: 'editor-tokenAttr',
			attr: 'editor-tokenAttr',
			boolean: 'editor-tokenProperty',
			builtin: 'editor-tokenSelector',
			cdata: 'editor-tokenComment',
			char: 'editor-tokenSelector',
			class: 'editor-tokenFunction',
			'class-name': 'editor-tokenFunction',
			comment: 'editor-tokenComment',
			constant: 'editor-tokenProperty',
			deleted: 'editor-tokenProperty',
			doctype: 'editor-tokenComment',
			entity: 'editor-tokenOperator',
			function: 'editor-tokenFunction',
			important: 'editor-tokenVariable',
			inserted: 'editor-tokenSelector',
			keyword: 'editor-tokenAttr',
			namespace: 'editor-tokenVariable',
			number: 'editor-tokenProperty',
			operator: 'editor-tokenOperator',
			prolog: 'editor-tokenComment',
			property: 'editor-tokenProperty',
			punctuation: 'editor-tokenPunctuation',
			regex: 'editor-tokenVariable',
			selector: 'editor-tokenSelector',
			string: 'editor-tokenSelector',
			symbol: 'editor-tokenProperty',
			tag: 'editor-tokenProperty',
			url: 'editor-tokenOperator',
			variable: 'editor-tokenVariable'
		},
		autocomplete: 'editor-autocomplete',
		blockCursor: 'editor-blockCursor',
		characterLimit: 'editor-characterLimit',
		embedBlock: {
			base: 'editor-embedBlock',
			focus: 'editor-embedBlockFocus'
		},
		hr: 'editor-hr',
		indent: 'editor-indent',
		inlineImage: 'inline-editor-image',
		mark: 'editor-mark',
		markOverlap: 'editor-markOverlap',
		table: 'editor-table',
		tableCell: 'editor-tableCell',
		tableCellActionButton: 'editor-tableCellActionButton',
		tableCellActionButtonContainer: 'editor-tableCellActionButtonContainer',
		tableCellEditing: 'editor-tableCellEditing',
		tableCellHeader: 'editor-tableCellHeader',
		tableCellPrimarySelected: 'editor-tableCellPrimarySelected',
		tableCellResizer: 'editor-tableCellResizer',
		tableCellSelected: 'editor-tableCellSelected',
		tableCellSortedIndicator: 'editor-tableCellSortedIndicator',
		tableResizeRuler: 'editor-tableCellResizeRuler',
		tableSelected: 'editor-tableSelected',
		tableSelection: 'editor-tableSelection'
	};
	type Section = { id: number; title: keyof Article; content: string; tag: BlockType };
	type Device = Article['applicable_devices'][number];
	let articleSections: Section[] = [];

	const createListItemsHTML = (items: string[]) => {
		return items.map((item) => `<li class='editor-listItem'>${item}</li>`).join('');
	};

	onMount(async () => {
		const article = await getArticleById(localStorage.token, articleId);
		if (article) {
			activeArticle.set(article);
			articleTitle = article.title;
			articleObjective = article.objective;
			articleIntro = article.introduction;
			articleApplicableDevices = article.applicable_devices;
			articleSteps = article.steps;
		}

		if ($activeArticle) {
			articleSections = Object.entries($activeArticle)
				.flatMap(([key, value], i) => {
					console.log('key:', key);
					console.log('value:', value);
					if (key === 'title') {
						return { id: i + 1, title: key, content: value, tag: 'h1' as BlockType };
					} else if (key === 'objective' || key === 'introduction') {
						if (key === 'objective') {
							return { id: i + 1, title: key, content: value.trim(), tag: 'paragraph' as BlockType };
						} else if (key === 'introduction') {
							return { id: i + 1, title: key, content: parseStepText(value.trim()), tag: 'paragraph' as BlockType };
						}
					} else if (key === 'steps') {
						return value.map((step: Article['steps'][number]) => ({
							id: i + 1,
							title: `${step.section} | Step ${step.step_number}`,
							content: parseStepText(step.text.trim()),
							tag: 'paragraph' as BlockType
						}));
					} else if (key === 'applicable_devices') {
						const listStrings: string[] = value.map((device: Device) => {
							if (device.software && device.datasheet_link && device.software_link)
								return `<span>${device.device} | ${device.software} <a target="_blank" href='${device.datasheet_link}'>(DataSheet)</a></span>`;
							else if (device.software && device.datasheet_link)
								return `<span>${device.device} | ${device.software} <a target="_blank" href='${device.datasheet_link}'>(DataSheet)</a></span>`;
							else if (device.software && device.software_link)
								return `<span>${device.device} | ${device.software} <a target="_blank" href='${device.software_link}'>(Software)</a></span>`;
							else if (device.software) return `<span>${device.device} | ${device.software}</span>`;
							else if (device.datasheet_link)
								return `<span>${device.device} | <a target="_blank" href='${device.datasheet_link}>(DataSheet)</a></span>`;
							else if (device.software_link)
								return `<span>${device.device} | <a target="_blank" href='${device.software_link}>(Software)</a></span>`;
							else return device.device;
						});
						return { id: i + 1, title: key, content: createListItemsHTML(listStrings), tag: 'bullet' as BlockType };
					}
				})
				.filter((section) => section !== undefined);
			console.log('articleSections:', articleSections);
		}
		loaded = true;
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
</script>

{#if loaded}
	<main class="p-4 min-h-screen">
		<h1 class="text-2xl font-bold mb-6">Edit Article Sections</h1>
		{#each articleSections as section, i (i)}
			<div class="mb-8 p-2 bg-white shadow rounded max-w-[1100px]">
				<h2 class="text-xl font-semibold mb-4">{formatTitle(section.title)}</h2>
				<Editor
					config={{
						namespace: `cisco-admin-editor-${section.title}`,
						onError: (error) => console.error(error),
						theme,
						editable: true
					}}
					content={section.content}
					tag={section.tag}
					section={section.title}
					{articleTitle}
					bind:savedSections
				/>
			</div>
		{/each}
		<button
			class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-400"
			on:click={() => console.log(savedSections)}
		>
			Export Article HTML
		</button>
	</main>
{/if}

<style>
	main {
		margin: 0 auto;
		padding: 1rem;
	}
</style>
