<script lang="ts">
	import type { ArticleStep } from '$lib/types';
	import { onMount } from 'svelte';
	import { quintIn } from 'svelte/easing';
	import { fly, slide } from 'svelte/transition';
	import { type MarkedOptions, marked } from 'marked';
	import { Info } from 'lucide-svelte';

	export let step: ArticleStep;
	export const index: number = 0;
	export let active: boolean = false;

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

	const { extensions, ...defaults } = marked.getDefaults();

	$: parsedText = marked.parse(step.text, { renderer, ...defaults, gfm: true, breaks: true });

	const copyTextToClipboard = async (text: string) => {
		await navigator.clipboard.writeText(text);
	};

	onMount(() => {
		// Create a mutation observer to watch for DOM changes
		const observer = new MutationObserver(() => {
			const kbds = document.getElementsByClassName('kbd-cdt');
			for (const kbd of kbds) {
				kbd.addEventListener('click', async () => {
					const command = kbd.querySelector('.cCN_CmdName');
					if (command?.textContent) {
						await copyTextToClipboard(command.textContent.trim());
						kbd.classList.add('KBDCDTCOPY');
						setTimeout(() => {
							kbd.classList.remove('KBDCDTCOPY');
						}, 2000);
					}
				});

				kbd.addEventListener('keydown', async (e) => {
					const keyboardEvent = e as KeyboardEvent;
					const isCtrlPressed = keyboardEvent.ctrlKey || keyboardEvent.metaKey;
					if (isCtrlPressed && keyboardEvent.key === 'c') {
						const command = kbd.querySelector('.cCN_CmdName');
						if (command?.textContent) {
							await copyTextToClipboard(command.textContent.trim());
							kbd.classList.add('KBDCDTCOPY');
							setTimeout(() => {
								kbd.classList.remove('KBDCDTCOPY');
							}, 2000);
						}
					}
				});
			}
		});

		// Start observing the DOM for changes
		observer.observe(document.body, { childList: true, subtree: true });

		return () => {
			observer.disconnect(); // Clean up observer when component is destroyed
		};
	});

	$: {
		console.log('active', active);
	}

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
</script>

<div role="contentinfo" class="container py-4 has-[p]:m-0">
	<h4 class="font-bold my-2">Step {step.step_number}</h4>
	{@html parsedText}
	{#if step.src}
		<div class="placeholder">
			<div class="bg-center bg-cover my-6 ml-4 md:ml-3" in:fly={{ y: -15, duration: 750, delay: 250 }}>
				<a target="_blank" href={step.src} class="show-image-alone" title="Related image, diagram or screenshot."
					><img
						alt={step.alt}
						src={step.src}
						class="max-w-full h-auto transition-opacity shadow-lg max-w-[calc(100%-80px)] my-5 {imageLoaded
							? 'block opacity-100'
							: 'hidden opacity-0'}"
						on:load={() => (imageLoaded = true)}
					/></a
				>
			</div>
		</div>
	{/if}
	{#if step.video_src}
		{#if step.video_src.includes('https://www.youtube.com/embed/')}
			<div class="vid-card-container flex flex-col justify-center items-center max-w-full px-4 m-0" in:slide>
				<div
					class="video-card w-full max-w-[800px] h-[400px] bg-white inline-flex flex-col relative top-0 left-0 my-4 p-0 rounded-lg overflow-hidden border border-solid border-gray-300 transition-all duration-500 ease-in-out scroll-snap-align-start self-start mb-8 shadow-lg"
					in:fly={{ delay: 25, duration: 1000, y: 55, easing: quintIn }}
					out:fly={{ duration: 1000, y: -55, easing: quintIn }}
				>
					<iframe
						loading="lazy"
						class="vid-card-iframe w-full h-[clamp(300px,100%,600px)]"
						src={step.video_src}
						title="YouTube video player"
						frameborder="0"
						allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
						allowfullscreen
					/>
				</div>
			</div>
		{:else}
			<video autoplay playsinline muted loop controls class="my-4 ml-4">
				<source src={`https://www.cisco.com${step.video_src}`} type={getMimeType(step.video_src)} />
			</video>
		{/if}
	{/if}
	{#if step.note}
		<div
			class="cdt-note bg-[#0d274d] p-4 text-[#fff] rounded-[5px] shadow-lg border-l-[5px] border-[#64bbe3] max-w-[1100px] text-pretty my-6 mx-4"
			in:fly={{ y: -15, duration: 750, delay: 550 }}
		>
			<div class="p-4 flex items-center space-x-3">
				<div class="flex flex-row items-center flex-none">
					<Info class="mr-2" size="1.5em" color="#64bbe3" />
					<span class="text-[#64bbe3]">Note: </span>
				</div>
				<div class="text-white text-pretty text-left">{@html step.note}</div>
			</div>
		</div>
	{/if}
</div>

<style>
	:global(ul) {
		list-style-type: none;
		margin: 8px 0;
	}

	:global(#eot-doc-wrapper .kbd-cdt) {
		display: block;
		height: auto;
		background-color: #dfdfdf;
		color: #0d274d;
		border-radius: 12px;
		padding: 1.5em;
		margin: 1.5em 0;
		box-shadow: 0 0 16px 0 rgba(43, 85, 146, 0.2);
		max-width: 1100px;
	}

	:global(#eot-doc-wrapper .kbd-cdt p) {
		padding: 0;
		margin: 0;
	}

	:global(#eot-doc-wrapper .kbd-cdt:hover) {
		background-color: #c2c2c2;
		cursor: copy;
	}

	:global(#eot-doc-wrapper .kbd-cdt:hover:after) {
		content: attr(data-label);
		display: grid;
		justify-content: end;
		align-content: flex-start;
		height: 0;
	}
	:global(#eot-doc-wrapper .KBDCDTCOPY::after) {
		display: grid;
		place-items: center;
		color: #ffa000;
		content: ' Copied! ' !important;
	}
</style>
