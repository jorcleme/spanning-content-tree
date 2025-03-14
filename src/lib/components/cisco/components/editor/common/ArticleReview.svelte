<script lang="ts">
	import type { Article, BlockType, ReviewedArticle, i18nType } from '$lib/types';

	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { flip } from 'svelte/animate';
	import { cubicOut, quintOut } from 'svelte/easing';
	import { crossfade, fly, slide } from 'svelte/transition';

	import { addNewArticle } from '$lib/apis/articles';
	import { getSeriesByName } from '$lib/apis/series';
	import { updateUserSavedArticles } from '$lib/apis/users';
	import { EDITOR_THEME } from '$lib/constants';
	import type { Model } from '$lib/stores';
	import {
		ExpGradeSelected,
		activeArticle,
		activeSupportSection,
		activeSupportStep,
		config,
		editSectionId,
		hideSupportWidgetBtn,
		isSupportStepDetailsOpen,
		models,
		mostRecentStep,
		mountedArticleSteps,
		reviewedArticle,
		settings,
		showSidebar,
		user
	} from '$lib/stores';
	import { titleizeWords } from '$lib/utils';
	import { type MarkedOptions, marked } from 'marked';

	import Controls from '$lib/components/chat/Controls/Controls.svelte';
	import ArticleStep from '$lib/components/cisco/components/articles/ArticleStep.svelte';
	import DetailsGetSupport from '$lib/components/cisco/components/articles/DetailsGetSupport.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	import Editor from '../Editor.svelte';
	import SectionSelector from './SectionSelector.svelte';

	const i18n = getContext<i18nType>('i18n');
	const dispatch = createEventDispatcher();

	const renderer = new marked.Renderer();
	renderer.codespan = (code) => {
		return `<code>${code.replaceAll('&amp;', '&')}</code>`;
	};
	const origLinkRenderer = renderer.link;
	renderer.link = (href, title, text) => {
		const html = origLinkRenderer.call(renderer, href, title, text);
		return html.replace(/^<a /, '<a target="_blank" rel="nofollow" ');
	};
	const { extensions, ...defaults } = marked.getDefaults() as MarkedOptions;

	let lang = $i18n.language;
	let expandedSteps = new Set<number>();
	let stepElements: HTMLDivElement[] = [];
	let objectiveElement: HTMLDivElement;
	let showControls = false;
	let selectedModels = [''];
	let atSelectedModel: Model | undefined;
	let selectedModelIds = [];
	let largeScreen = false;

	$: selectedModelIds = atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;
	$: console.log('selectedModels', selectedModels);
	$: getSupportDivs = [] as HTMLDivElement[];
	$: activeStep = -1;
	$: isAdmin = ($user?.role ?? false) === 'admin';

	$: parseStepText = function (text: string) {
		return marked.parse(text, { renderer, ...defaults, gfm: true, breaks: true });
	};

	const getClosestSupportDiv = () => {
		let divs = Array.from(getSupportDivs) as Array<HTMLDivElement>;
		divs.unshift(objectiveElement);
		divs = divs;
		let { closestSection, currentStep } = divs.reduce<{
			closestDistance: number;
			closestSection: string | null;
			currentStep: string | null;
		}>(
			(acc, div) => {
				const rect = div.getBoundingClientRect();
				const divCenter = rect.top + rect.height / 2;
				const screenCenter = window.innerHeight / 2;
				const distance = Math.abs(screenCenter - divCenter);
				return distance < acc.closestDistance
					? {
							closestDistance: distance,
							closestSection: div.getAttribute('data-section'),
							currentStep: div.getAttribute('data-step')
					  }
					: acc;
			},
			{ closestDistance: Infinity, closestSection: null, currentStep: null }
		);
		if (closestSection) {
			activeSupportSection.set(closestSection);
		}
		if (currentStep) {
			mostRecentStep.set(parseInt(currentStep));
		}
	};

	type Section = {
		id: string;
		title: string;
		content: string;
		tag: BlockType;
		type: 'heading' | 'step';
		html?: string;
	};
	type Device = Article['applicable_devices'][number];
	let articleSections: Section[] = [];
	let articleTitle = '';

	const createListItemsHTML = (items: string[]) => {
		return items.map((item) => `<li class='editor-listItem'>${item}</li>`).join('\n');
	};

	const createUnorderedListHTML = (items: string[]) => {
		return `<ul class='editor-list'>${createListItemsHTML(items)}</ul>`;
	};

	const formatSection = (): Section[] => {
		return Object.entries($activeArticle ?? {})
			.flatMap(([k, v]) => {
				if (k === 'title') {
					return {
						id: k,
						title: formatTitle(k),
						content: `<h1 class="editor-heading-h1" dir="ltr">${v.trim()}</h1>`,
						tag: 'h1' as BlockType,
						type: 'heading',
						text: v.trim()
					};
				} else if (k === 'objective') {
					return {
						id: k,
						title: formatTitle(k),
						content: `<p class="editor-paragraph" dir="ltr">${v.trim()}</p>`, // Updated to wrap objective in a paragraph tag
						tag: 'paragraph' as BlockType,
						type: 'heading',
						text: v.trim()
					};
				} else if (k === 'introduction') {
					return {
						id: k,
						title: formatTitle(k),
						content: parseStepText(v.trim()),
						tag: 'paragraph' as BlockType,
						type: 'heading',
						text: v.trim()
					};
				} else if (k === 'steps') {
					const steps = v.map((step: Article['steps'][number], stepIndex: number) => {
						return {
							id: `${stepIndex}`,
							title: `${step.section} | Step ${step.step_number}`,
							content: parseStepText(step.text.trim()),
							tag: 'paragraph' as BlockType,
							type: 'step',
							text: step.text.trim()
						};
					});

					$reviewedArticle!.steps = steps;
					return steps;
				} else if (k === 'applicable_devices') {
					const listStrings: string[] = v.map((device: Device) => {
						if (device.software && device.datasheet_link && device.software_link) {
							return `<span>${device.device} <a target="_blank" href='${device.datasheet_link}'>(DataSheet)</a> | ${device.software} <a target="_blank" href='${device.software_link}'>(Download Latest)</a></span>`;
						} else if (device.software && device.datasheet_link) {
							return `<span>${device.device} <a target="_blank" href='${device.datasheet_link}'>(DataSheet)</a> | ${device.software}</span>`;
						} else if (device.software && device.software_link) {
							return `<span>${device.device} | ${device.software} <a target="_blank" href='${device.software_link}'>(Download Latest)</a></span>`;
						} else if (device.software) return `<span>${device.device} | ${device.software}</span>`;
						else if (device.datasheet_link) {
							return `<span>${device.device} <a target="_blank" href='${device.datasheet_link}'>(DataSheet)</a></span>`;
						} else if (device.software_link) {
							return `<span>${device.device} | <a target="_blank" href='${device.software_link}'>(Download Latest)</a></span>`;
						} else {
							return device.device;
						}
					});
					const ul = createUnorderedListHTML(listStrings);
					if ($reviewedArticle) {
						$reviewedArticle.applicable_devices = ul;
					}

					return {
						id: k,
						title: formatTitle(k),
						content: ul,
						tag: 'bullet' as BlockType,
						type: 'heading'
					};
				}
			})
			.filter((s) => s !== undefined);
	};
	let title: string = '';
	onMount(async () => {
		window.addEventListener('scroll', getClosestSupportDiv);

		title = titleElement?.textContent?.trim() ?? '';

		if ($activeArticle) {
			reviewedArticle.set({
				id: $activeArticle.id,
				title: $activeArticle.title,
				objective: $activeArticle.objective,
				introduction: $activeArticle.introduction,
				applicable_devices: '',
				best_practices: [],
				steps: [],
				url: $activeArticle.url,
				published: $activeArticle.published,
				document_id: $activeArticle.document_id,
				revision_history: [],
				category: $activeArticle.category,
				created_at: $activeArticle.created_at,
				updated_at: $activeArticle.updated_at
			});
			articleSections = formatSection();
			articleTitle = $activeArticle.title;
			console.log('articleSections:', articleSections);
		}

		const mediaQuery = window.matchMedia('(min-width: 1024px)');
		const handleMediaQuery = (e: MediaQueryListEvent) => {
			largeScreen = e.matches;
		};

		mediaQuery.addEventListener('change', handleMediaQuery);
		handleMediaQuery({ matches: mediaQuery.matches } as MediaQueryListEvent);

		if ($settings.models) {
			selectedModels = $settings.models;
		} else if ($config?.default_models) {
			selectedModels = $config.default_models.split(',');
		} else {
			selectedModels = [''];
		}

		selectedModels = selectedModels.map((modelId) => ($models.map((m) => m.id).includes(modelId) ? modelId : ''));

		return new Promise((resolve, reject) => {
			window.removeEventListener('scroll', getClosestSupportDiv);
			mediaQuery.removeEventListener('change', handleMediaQuery);
			resolve(void 0);
		});
	});

	$: {
		console.log('mostRecentStep', $mostRecentStep);
	}

	$: {
		let step = $mountedArticleSteps.at($mostRecentStep);
		if (step) {
			activeSupportStep.set(step.step_number);
		}
	}

	const stepSupportDetailsOpen = (e: CustomEvent<{ index: number }>) => {
		const { index } = e.detail;
		activeStep = index;
		if (!expandedSteps.has(index)) {
			expandedSteps.add(index);
		} else {
			expandedSteps.delete(index);
			activeStep = -1;
		}
	};

	const stepSupportDetailsClose = (e: CustomEvent<{ index: number }>) => {
		const { index } = e.detail;
		expandedSteps.delete(index);
		activeStep = -1;
	};

	$: isStepActive = expandedSteps.has(activeStep);
	$: title = $activeArticle?.title ?? 'Cisco Technical Document';
	$: chatControlModels = selectedModelIds.reduce((a, e, i, arr) => {
		const model = $models.find((m) => m.id === e);
		if (model) {
			return [...a, model];
		}
		return a;
	}, [] as Model[]);

	const concatSupportString = (title: string, stepNum: number) => {
		return `${title} | Step ${stepNum}`;
	};

	const formatTitle = (title: string) => {
		return title.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
	};

	$: activeSectionTitle = articleSections.find((s) => s.id === $editSectionId)?.title ?? '';
	$: activeSectionContent =
		articleSections.find((s) => s.id === $editSectionId)?.content ??
		articleSections.find((s) => parseInt(s.id) === parseInt($editSectionId))?.content ??
		'';

	const onSave = (e: CustomEvent<{ section: Section }>) => {
		console.log('save event fired');
		const { section } = e.detail;
		if ($reviewedArticle && section.type === 'heading') {
			if (section.id === 'title') {
				$reviewedArticle.title = section.content;
			} else if (section.id === 'objective') {
				$reviewedArticle.objective = section.content;
			} else if (section.id === 'introduction') {
				$reviewedArticle.introduction = section.content;
			} else if (section.id === 'applicable_devices') {
				$reviewedArticle.applicable_devices = section.content;
			}
		}
		$editSectionId = '';
	};

	const onEdit = (e: CustomEvent<{ id: string }>) => {
		const { id } = e.detail;
		console.log('id:', id);
		let div: HTMLElement | null;
		if (id === 'title') {
			div = document.getElementById('title-editor');
			div?.scrollIntoView({ behavior: 'smooth' });
			// if (div) div.scrollTop = 0;
		}
		if (id === 'objective') {
			// changed 'Objective' to 'objective'
			div = document.getElementById('objective-editor');
			div?.scrollIntoView({ behavior: 'smooth' });
			// if (div) div.scrollTop = 0;
		}
		if (id === 'applicable_devices') {
			// changed 'Applicable Devices' to 'applicable devices'
			div = document.getElementById('applicable-devices-editor');
			div?.scrollIntoView({ behavior: 'smooth' });
			// if (div) div.scrollTop = 0;
		}
		if (id === 'introduction') {
			// changed 'Introduction' to 'introduction'
			div = document.getElementById('introduction-editor');
			div?.scrollIntoView({ behavior: 'smooth' });
			// if (div) div.scrollTop = 0;
		}
	};

	let titleElement: HTMLDivElement | null = null;

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

	$: published = $activeArticle?.published ?? false;
</script>

<div class="h-screen max-h-[100dvh] w-full max-w-full flex flex-col">
	{#if $settings?.backgroundImageUrl ?? null}
		<div
			class="absolute {$showSidebar
				? 'md:max-w-[calc(100%-260px)] md:translate-x-[260px]'
				: ''} top-0 left-0 w-full h-full bg-cover bg-center bg-no-repeat"
			style="background-image: url({$settings.backgroundImageUrl})  "
		/>

		<div
			class="absolute top-0 left-0 w-full h-full bg-gradient-to-t from-white to-white/85 dark:from-gray-900 dark:to-[#171717]/90 z-0"
		/>
	{/if}

	{#if $reviewedArticle && $activeArticle}
		<div id="editor-eot-doc-wrapper" class="w-full dark:bg-gray-900 text-gray-850 dark:text-gray-50 pb-8 p-4">
			<div class="flex flex-col mx-auto {$showSidebar ? 'w-[calc(100%-16px)]' : 'w-[calc(100%-50px)]'} text-prose">
				<div class="flex flex justify-between items-center">
					<div class="hbr-css__layout-row-sm">
						<div
							class="px-2.5 py-1 text-xs font-medium {published
								? 'bg-green-500 hover:bg-green-400'
								: 'bg-yellow-600 hover:bg-yellow-500'} transition rounded-full"
						>
							{published ? 'Published' : 'Draft'}
						</div>
					</div>
					<SectionSelector sections={articleSections} on:edit={onEdit} />
				</div>
				<div class="rounded-xl">
					{#if $editSectionId === 'title' && articleSections.find((s) => s.id === 'title')}
						<div
							id="title-editor"
							class="my-8 p-2 bg-white dark:bg-gray-800 text-gray-850 dark:text-gray-50 shadow rounded max-w-[1100px]"
						>
							<h1 class="text-xl font-semibold mb-4">{formatTitle(activeSectionTitle)}</h1>
							<Editor
								config={{
									namespace: `cisco-admin-editor-title`,
									onError: (error) => console.error(error),
									theme: EDITOR_THEME,
									editable: true
								}}
								content={activeSectionContent}
								section={activeSectionTitle}
								articleTitle={title}
								bind:articleSections
								on:save={onSave}
							/>
						</div>
					{:else}
						<div bind:this={titleElement} id="title" class="w-full relative cursor-pointer" role="contentinfo">
							<h1 class="text-3xl text-left font-bold my-4 text-pretty">
								{@html marked.parse($reviewedArticle.title, { ...defaults, gfm: true, renderer })}
							</h1>
						</div>
					{/if}

					<div
						class="control-bar p-4 bg-gray-200 text-gray-800 dark:bg-gray-800 dark:text-gray-50 rounded-md shadow-md"
					>
						<div class="flex items-center">
							<div class="flex flex-col justify-start">
								<p class="text-md font-bold">{$i18n.t('Document Id')}:</p>
								<p class="text-sm">{$reviewedArticle.document_id}</p>
							</div>
						</div>
					</div>
					{#if $editSectionId === 'objective' && articleSections.find((s) => s.id === 'objective')}
						<div
							id="objective-editor"
							class="my-8 p-2 bg-white dark:bg-gray-800 text-gray-850 dark:text-gray-50 shadow rounded max-w-[1100px]"
						>
							<h2 class="text-xl font-semibold mb-4 text-gray-850 dark:text-gray-50">{activeSectionTitle}</h2>
							<Editor
								config={{
									namespace: `cisco-admin-editor-objective`,
									onError: (error) => console.error(error),
									theme: EDITOR_THEME,
									editable: true
								}}
								content={activeSectionContent}
								section={activeSectionTitle}
								articleTitle={title}
								bind:articleSections
								on:save={onSave}
							/>
						</div>
					{:else}
						<h2 class="text-2xl my-5 font-bold text-blue-950 dark:text-blue-100">Objective</h2>
						<div id="objective" data-section="Objective" bind:this={objectiveElement}>
							{@html marked.parse($reviewedArticle.objective, { ...defaults, gfm: true, renderer })}
						</div>
					{/if}

					{#if $editSectionId === 'applicable_devices' && articleSections.find((s) => s.id === 'applicable_devices')}
						<div
							id="applicable-devices-editor"
							class="my-8 p-2 bg-white dark:bg-gray-800 text-gray-850 dark:text-gray-50 shadow rounded max-w-[1100px]"
						>
							<h2 class="text-xl font-semibold mb-4">{activeSectionTitle}</h2>
							<Editor
								config={{
									namespace: `cisco-admin-editor-applicable-devices`,
									onError: (error) => console.error(error),
									theme: EDITOR_THEME,
									editable: true
								}}
								content={activeSectionContent}
								section={activeSectionTitle}
								articleTitle={title}
								bind:articleSections
								on:save={onSave}
							/>
						</div>
					{:else if $reviewedArticle.applicable_devices}
						<div id="applicable-devices">
							<h2 class="text-2xl my-5 font-bold text-blue-950 dark:text-blue-100">
								Applicable Devices | Software Version
							</h2>
							{@html parseStepText($reviewedArticle.applicable_devices)}
						</div>
					{/if}
					{#if $editSectionId === 'introduction' && articleSections.find((s) => s.id === 'introduction')}
						<div
							id="introduction-editor"
							class="my-8 p-2 bg-white dark:bg-gray-800 text-gray-850 dark:text-gray-50 shadow rounded max-w-[1100px]"
						>
							<h2 class="text-xl font-semibold mb-4">{activeSectionTitle}</h2>
							<Editor
								config={{
									namespace: `cisco-admin-editor-introduction`,
									onError: (error) => console.error(error),
									theme: EDITOR_THEME,
									editable: true
								}}
								content={activeSectionContent}
								section={activeSectionTitle}
								articleTitle={title}
								bind:articleSections
								on:save={onSave}
							/>
						</div>
					{:else if $reviewedArticle.introduction}
						<div id="introduction">
							<h2 class="text-2xl my-5 font-bold text-blue-950 dark:text-blue-100">Introduction</h2>
							{@html marked.parse($reviewedArticle.introduction, {
								...defaults,
								gfm: true,
								breaks: true,
								renderer
							})}
						</div>
					{/if}
				</div>
				{#if $activeArticle.best_practices && $activeArticle.best_practices.length > 0}
					{#each $activeArticle.best_practices as bestPractice, i (i)}
						<div
							class="cdt-best-practice text-base bg-[#0d274d] p-2.5 text-[#fff] m-8 rounded-[5px] shadow-[0_0_16px_0_rgba(43, 85, 146, 0.2) border-l-[5px] border-[#6cc04a]"
						>
							<p>{bestPractice}</p>
						</div>
					{/each}
				{/if}
				<div class="w-full">
					{#each $activeArticle.steps as step, index (index)}
						{#if step.step_number === 1}
							<h4 class="text-xl font-bold my-4 text-blue-950 dark:text-blue-100">{step.section}</h4>
						{/if}
						{#if index === parseInt($editSectionId) && articleSections.find((s) => parseInt(s.id) === parseInt($editSectionId))}
							<div class="my-8" in:receive={{ key: index }} out:send={{ key: index }}>
								<div
									id="step-editor-{$editSectionId}"
									class="my-8 p-2 bg-white dark:bg-gray-800 text-gray-850 dark:text-gray-50 shadow rounded max-w-[1100px]"
								>
									<h2 class="text-xl font-semibold mb-4">{activeSectionTitle}</h2>
									<Editor
										config={{
											namespace: `cisco-admin-editor-section-${$editSectionId}`,
											onError: (error) => console.error(error),
											theme: EDITOR_THEME,
											editable: true
										}}
										content={activeSectionContent}
										section={activeSectionTitle}
										articleTitle={title}
										bind:articleSections
										on:save={onSave}
									/>
								</div>
							</div>
						{:else}
							<div class="my-8" bind:this={stepElements[index]}>
								<ArticleStep {index} {step} bind:active={isStepActive} />
								<div
									class="getSupportStep p-4 border border-gray-400 transition-all duration-250 ease-in bg-gray-50 text-gray-850 dark:bg-gray-850 dark:text-gray-50 max-w-[1100px] rounded-md"
									data-section={step.section}
									data-step={index}
									bind:this={getSupportDivs[index]}
									class:hidden={$ExpGradeSelected === 'Lightly Guided'}
								>
									<DetailsGetSupport
										{selectedModels}
										open={expandedSteps.has(index)}
										{index}
										currentStepStr={concatSupportString(titleizeWords(step.section), step.step_number)}
										{step}
										on:openStepSupport={stepSupportDetailsOpen}
										on:closeStepSupport={stepSupportDetailsClose}
									/>
								</div>
							</div>
						{/if}
					{/each}
				</div>
				<slot />
			</div>
			{#if $activeArticle.revision_history && $activeArticle.revision_history.length > 0}
				<div class="m-4">
					<table class="table-auto border-collapse border-spacing-2 border-2 border-gray-600">
						<caption class="caption-top mb-2 font-bold text-lg">{$i18n.t('Revision History')}</caption>
						<thead>
							<tr>
								{#each [$i18n.t('Revision'), $i18n.t('Publish Date'), $i18n.t('Comments')] as header}
									<th class="bg-blue-950 text-gray-50 font-['CiscoSansLight'] font-bold p-2 border-2 border-slate-700"
										>{header}</th
									>
								{/each}
							</tr>
						</thead>
						<tbody>
							{#each $activeArticle.revision_history ?? [] as history, i (i)}
								<tr>
									<td class="border-2 border-gray-600 p-2">{history.revision}</td>
									<td class="border-2 border-gray-600 p-2">{new Date(history.publish_date).toLocaleDateString(lang)}</td
									>
									<td class="border-2 border-gray-600 p-2">{history.comments}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	{/if}
	{#if largeScreen}
		{#if showControls}
			<div class=" absolute bottom-0 right-0 z-20 h-full pointer-events-none">
				<div class="pr-4 pt-14 pb-8 w-[24rem] h-full" in:slide={{ duration: 200, axis: 'x' }}>
					<div
						class="w-full h-full px-5 py-4 bg-white dark:shadow-lg dark:bg-gray-850 border border-gray-50 dark:border-gray-800 rounded-xl z-50 pointer-events-auto overflow-y-auto scrollbar-hidden"
					>
						<Controls
							on:close={() => {
								showControls = false;
							}}
							models={chatControlModels}
						/>
					</div>
				</div>
			</div>
		{/if}
	{:else}
		<Modal bind:show={showControls}>
			<div class="px-6 py-4 h-full">
				<Controls
					on:close={() => {
						showControls = false;
					}}
					models={chatControlModels}
				/>
			</div>
		</Modal>
	{/if}
</div>

<style>
	.hidden {
		visibility: hidden;
		margin: 0;
		padding: 0;
		height: 0;
	}

	:global(#editor-eot-doc-wrapper ul:not(.rounded-counter) > li::before) {
		content: '●';
		color: #9b9b9b;
		font-weight: 100;
		font-size: 1em;
		display: inline-block;
		height: 0.25em;
		text-align: left;
		padding-right: 0.5rem;
	}

	:global(#editor-eot-doc-wrapper ul:not(.rounded-counter) > li) {
		margin: 6px;
	}

	:global(#editor-eot-doc-wrapper ul > li > a) {
		color: #0051af;
		font-size: 1rem;
		font-family: 'CiscoSansThin';
		font-weight: 700;
	}

	#editor-eot-doc-wrapper .cdt-best-practice:before {
		color: #6cc04a;
		content: '\272A  Best Practice:';
		font-size: 14px;
		font-weight: 700;
		line-height: 2em;
		-webkit-transition: all 0.3s ease;
		-o-transition: all 0.3s ease;
		transition: all 0.3s ease;
	}
</style>
