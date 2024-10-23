<script lang="ts">
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import type { Model } from '$lib/stores';
	import {
		models,
		settings,
		config,
		showSidebar,
		activeSupportSection,
		isSupportStepDetailsOpen,
		activeSupportStep,
		mostRecentStep,
		mountedArticleSteps,
		mountedArticlePreambleObjective,
		mountedArticlePreambleDevices,
		ExpGradeSelected,
		activeArticleId,
		activeArticle,
		hideSupportWidgetBtn
	} from '$lib/stores';
	import { page } from '$app/stores';
	import { onMount, getContext } from 'svelte';
	import { slide, fly } from 'svelte/transition';
	import { quintIn } from 'svelte/easing';
	import { titleizeWords } from '$lib/utils';
	import { getArticleById, getArticleByDocumentId } from '$lib/apis/articles';
	import DetailsGetSupportStep from './DetailsGetSupport.svelte';
	import ArticleStep from './ArticleStep.svelte';
	import Navbar from '$lib/components/layout/Navbar.svelte';
	import Controls from '$lib/components/chat/Controls/Controls.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import ChatControls from '$lib/components/chat/ChatControls.svelte';
	import lightlyGuidedImage from '$lib/assets/assing-port-to-vlan-dall-e-2.png';
	import fullyGuidedImage from '$lib/assets/assing-port-to-vlan-dall-e.png';

	const i18n: Writable<i18nType> = getContext('i18n');

	let observer: IntersectionObserver;
	let articleId: string;
	let hasRelatedVideo = false;
	let expandedSteps = new Set<number>();
	let stepElements: HTMLDivElement[] = [];
	let objectiveElement: HTMLDivElement;
	let relatedVideo: object | null = null;
	let expanded = false;
	let isSticky = false;
	let showModelSelector = true;
	let showControls = false;
	let selectedModels = [''];
	let atSelectedModel: Model | undefined;
	let selectedModelIds = [];
	let largeScreen = false;

	$: selectedModelIds = atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;
	$: console.log('selectedModels', selectedModels);
	$: getSupportDivs = [] as HTMLDivElement[];
	$: backgroundImage = $ExpGradeSelected === 'Fully Guided' ? fullyGuidedImage : lightlyGuidedImage;
	$: activeStep = -1;

	const handleIntersection = (entries: IntersectionObserverEntry[]) => {
		entries.forEach((entry) => {
			if (entry.isIntersecting) {
				const section = entry.target.getAttribute('data-section');
				const step = entry.target.getAttribute('data-step');
				if (section) {
					activeSupportSection.set(section);
					console.log('activeSupportSection', $activeSupportSection);
				}
				if (step) {
					mostRecentStep.set(parseInt(step));
					console.log('mostRecentStep', $mostRecentStep);
				}
			}
		});
	};

	const getClosestSupportDiv = () => {
		const divs = Array.from(getSupportDivs) as Array<HTMLDivElement>;
		divs.unshift(objectiveElement);
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

	onMount(() => {
		window.addEventListener('scroll', getClosestSupportDiv);

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

		(async () => {
			if ($page.url.searchParams.has('id')) {
				activeArticle.set(await getArticleById(localStorage.token, $page.url.searchParams.get('id')!));
			} else if ($page.url.searchParams.has('document_id')) {
				activeArticle.set(await getArticleByDocumentId(localStorage.token, $page.url.searchParams.get('document_id')!));
			} else if ($page.params.id) {
				activeArticle.set(await getArticleById(localStorage.token, $page.params.id));
			}
		})();
		// document.body.addEventListener('scroll', getClosestSupportDiv, { capture: true });
		return () => {
			// document.body.removeEventListener('scroll', getClosestSupportDiv);
			window.removeEventListener('scroll', getClosestSupportDiv);
			mediaQuery.removeEventListener('change', handleMediaQuery);
		};
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

	function handleOpen(event: CustomEvent<{ index: number }>) {
		isSupportStepDetailsOpen.set(true);
		console.log('handleOpen', event);
		console.log('mostRecentStep', $mostRecentStep);
		expandedSteps.add(event.detail.index);
		console.log('expandedSteps', expandedSteps);
	}
	function handleClose(event: CustomEvent<{ index: number }>) {
		console.log('handleClose', event);
		expandedSteps.delete(event.detail.index);
		console.log('expandedSteps', expandedSteps);
		// $isSupportStepDetailsOpen = false;
		mostRecentStep.set(-1);
	}

	$: isStepActive = expandedSteps.has(activeStep);

	$: title = $activeArticle?.title ?? 'Article';

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
</script>

<div
	class="h-screen max-h-[100dvh] {$showSidebar ? 'md:max-w-[calc(100%-260px)]' : ''} w-full max-w-full flex flex-col"
>
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

	<Navbar
		{title}
		bind:selectedModels
		bind:showModelSelector
		bind:showControls
		shareEnabled={false}
		chat={{}}
		initNewChat={() => {}}
	/>
	{#if $activeArticle}
		<div id="eot-doc-wrapper" style="position: relative;" class="w-full text-gray-800 {$showSidebar ? 'my-3' : 'my-8'}">
			<div class="flex flex-col mx-auto {$showSidebar ? 'w-[calc(100%-16px)]' : 'w-[calc(100%-50px)]'}">
				<div class="article-Hero rounded-xl">
					<div class="frostedGlass">
						<!-- <img id="heroImage" src={backgroundImage} alt="hero dynamic experience background" /> -->

						<div class="band" />

						<h1 class="text-3xl text-left" style="line-height: 1.075em;">{$activeArticle.title}</h1>
						<h2 class="articleHeadersExp">Objective</h2>
						<div data-section="Objective" bind:this={objectiveElement}>
							<p>{$activeArticle.objective}</p>
						</div>

						{#if $activeArticle.applicable_devices && $activeArticle.applicable_devices.length > 0}
							<h2 class="articleHeadersExp">Applicable Devices | Software Version</h2>
							<ul>
								{#each $activeArticle.applicable_devices as device}
									{#if device.device && device.software && device.datasheet_link && device.software_link}
										<li>
											{device.device}
											<a href={device.datasheet_link}> (Datasheet) </a>
											| {device.software}
											<a href={device.software_link}> (Download Latest) </a>
										</li>
									{:else if device.device && device.software && device.datasheet_link}
										<li>
											{device.device}
											<a href={device.datasheet_link}> (Datasheet) </a>
											| {device.software}
										</li>
									{:else if device.device && device.software && device.software_link}
										<li>
											{device.device} | {device.software}
											<a href={device.software_link}> (Download Latest) </a>
										</li>
									{:else if device.device && device.software}
										<li>
											{device.device}{#if device.software}
												| {device.software}{/if}
										</li>
									{:else}
										<li>{device.device}</li>
									{/if}
								{/each}
							</ul>
						{/if}
						{#if $activeArticle.introduction}
							<h2 class="articleHeadersExp">Introduction</h2>
							<p>{@html $activeArticle.introduction}</p>
						{/if}
					</div>
				</div>
				<div class="cdt-best-practice">
					<p>
						Backup your configuration prior to upgrading the firmware. You can do this by navigating to <b
							>Administration &gt; File Management &gt; File Operations</b
						> in the menu. Download a copy of the running configuration to your PC. It is not recommended to do a firmware
						upgrade of your device remotely.
					</p>
				</div>
				<div class="container-est-completion" id="test">
					<div class="nested-1">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 80 80"
							class="s-qHuZzP0FnHPs"
							style="width: 50px;display:inline-block;"
							><path
								d="M58,39.25H46.70581a6.74732,6.74732,0,0,0-13.41162,0H22a12.75,12.75,0,0,0,0,25.5H57.29419a6.75,6.75,0,1,0,0-1.5H22a11.25,11.25,0,0,1,0-22.5H33.29419a6.74732,6.74732,0,0,0,13.41162,0H58a12.75,12.75,0,0,0,0-25.5H22.70581a6.687,6.687,0,0,0-.66064-2.23462L25.06055,10,24,8.93945l-2.78308,2.78308A6.74807,6.74807,0,1,0,22.70581,16.75H58a11.25,11.25,0,0,1,0,22.5Zm6,19.5A5.25,5.25,0,1,1,58.75,64,5.25605,5.25605,0,0,1,64,58.75ZM40,45.25A5.25,5.25,0,1,1,45.25,40,5.25605,5.25605,0,0,1,40,45.25Zm-24-24a5.25009,5.25009,0,1,1,4.13525-8.44586L16,16.93945l-2-2L12.93945,16l2.53028,2.53027a.74971.74971,0,0,0,1.06054,0l4.36939-4.36944A5.19508,5.19508,0,0,1,21.25,16,5.25605,5.25605,0,0,1,16,21.25Z"
								class="s-qHuZzP0FnHPs"
							/></svg
						>
						<p class="estcomText">{$i18n.t('Estimated Completion')}:</p>
						<span>14 Min.</span>
					</div>
				</div>
				{#if expanded && hasRelatedVideo}
					<div class="vid-card-container" in:slide>
						<div
							class="video-card"
							in:fly={{ delay: 25, duration: 1000, y: 55, easing: quintIn }}
							out:fly={{ duration: 1000, y: -55, easing: quintIn }}
						>
							<iframe
								loading="lazy"
								class="vid-card-iframe"
								src={relatedVideo?.URL}
								title="YouTube video player"
								frameborder="0"
								allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
								allowfullscreen
							/>
							<div class="video-text-content">
								<h3 class="video-card-title">{$activeArticle.title}</h3>
								<p id="video-card-description">{$activeArticle.objective}</p>
							</div>
						</div>
					</div>
					<!-- <GetSupportDetailsFooter index={$mostRecentStep} /> -->
				{/if}
				{#each $activeArticle.steps as step, index}
					<div class="stepContainer" bind:this={stepElements[index]}>
						{#if step.step_number === 1}
							<h4 class="section-title text-2xl">{step.section}</h4>
						{/if}
						<ArticleStep {index} {step} bind:active={isStepActive} />

						<div
							class="getSupportStep"
							data-section={step.section}
							data-step={index}
							bind:this={getSupportDivs[index]}
							class:hidden={$ExpGradeSelected === 'Lightly Guided'}
						>
							<DetailsGetSupportStep
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
				{/each}
				<slot />
			</div>
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
								hideSupportWidgetBtn.set(false);
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
						hideSupportWidgetBtn.set(false);
					}}
					models={chatControlModels}
				/>
			</div>
		</Modal>
	{/if}
</div>

<style>
	#eot-doc-wrapper a[href] {
		color: #2b5592;
		-webkit-text-decoration-color: #64bbe3;
		text-decoration-color: #64bbe3;
		font-family: 'CiscoSansThin';
		font-weight: 700;
	}
	.hidden {
		visibility: hidden;
		margin: 0;
		padding: 0;
		height: 0;
	}
	#eot-doc-wrapper {
		color: #58585b;
	}
	.frostedGlass {
		background: rgba(255, 255, 255, 0.5);
		backdrop-filter: blur(10px);
		border-radius: 16px;
		padding: 1em;
		z-index: -1;
		transition: all 0.1s ease;
	}

	.article-Hero {
		/* border: linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%), linear-gradient(90deg, #a1c4fd 0%, #c2e9fb 100%),
			linear-gradient(10deg, #a1c4fd 0%, #c2e9fb 100%); */
		transition: all 0.3s ease-in-out;
		background-size: cover;
		mix-blend-mode: darken;
		margin: 1em;
		border-radius: 20px;
	}

	#eot-doc-wrapper h1,
	#eot-doc-wrapper h2 {
		font-weight: 700;
	}

	#eot-doc-wrapper h1 {
		/* text-align: center; */
		text-wrap: balance;
		font-family: 'CiscoSansTT';
		margin: 2em 0;
		font-weight: 700;
		color: #58585b;
		line-height: 1.25em;
	}

	#eot-doc-wrapper h2 {
		font-family: 'CiscoSansTT';
		margin: 1em 0;
		/* color: #2b5592; */
		font-weight: 800;
		font-size: 1.5rem;
	}

	.container-est-completion {
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: 100%;
		flex-wrap: wrap;
		margin: 10px 0;
	}

	.nested-1 {
		display: flex;
		align-items: center;
		justify-content: center;
		/* margin: 1em; */
	}

	.nested-1 svg,
	.nested-1 p {
		margin-right: 10px;
	}

	:link {
		text-decoration: none;
	}

	ul {
		list-style-type: none;
	}

	ul li::before {
		content: '\25cf';
		color: #9b9b9b;
		font-weight: 100;
		font-size: 1em;
		display: inline-block;
		width: 0.25em;
		height: 0.25em;
		text-align: left;

		padding-right: 1.5rem;
	}

	.section-title {
		font-weight: 700;
		/* font-size: 1.5rem; */
		margin: 20px 0 16px 0;
		color: #132d4e;
	}

	#eot-doc-wrapper .cdt-best-practice {
		background-color: #0d274d;
		padding: 1.5em;
		color: #fff;
		margin: 1.5em 40px;
		border-radius: 5px;
		-webkit-box-shadow: 0 0 16px 0 rgba(43, 85, 146, 0.2);
		box-shadow: 0 0 16px 0 rgba(43, 85, 146, 0.2);
		border-left: #6cc04a 5px solid;
		font-size: 14px;
	}

	#eot-doc-wrapper .cdt-best-practice:before {
		color: #6cc04a;
		content: '\272A  Best Practice:';
		font-size: 14px;
		font-weight: 700;
		line-height: 2em;
		-webkit-transition: all 0.3s ease;
		-o-transition: all 0.3s ease;
		transition: all 0.3s ease;
	}

	@media only screen and (max-width: 768px) {
		.estcomText {
			display: none;
		}
	}
</style>
