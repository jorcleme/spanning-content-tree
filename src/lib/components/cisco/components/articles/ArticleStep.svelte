<script lang="ts">
	import type { ArticleStep } from '$lib/types';
	import { marked, type MarkedOptions } from 'marked';
	import { fly } from 'svelte/transition';
	import { onMount } from 'svelte';

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

	const { extensions, ...defaults } = marked.getDefaults() as MarkedOptions & {
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		extensions: any;
	};

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
</script>

<div role="contentinfo" class="stepContainer">
	<h4>Step {step.step_number}</h4>
	{@html parsedText}
	{#if step.src}
		<div class="placeholder">
			<div class="img-wrapper" in:fly={{ y: -15, duration: 750, delay: 250 }}>
				<a target="_blank" href={step.src} class="show-image-alone" title="Related image, diagram or screenshot."
					><img
						alt={step.alt}
						src={step.src}
						class={imageLoaded ? 'loaded' : 'hidden'}
						on:load={() => (imageLoaded = true)}
					/></a
				>
			</div>
		</div>
	{/if}
	{#if step.note}
		<div class="cdt-note" in:fly={{ y: -15, duration: 750, delay: 550 }}>
			<p>{@html step.note}</p>
		</div>
	{/if}
</div>

<style>
	.hidden {
		display: none;
	}

	img {
		max-width: 100%;
		height: auto;
	}
	.img-wrapper {
		background-size: cover;
		background-position: center;
		margin: 1em 40px;
	}
	.img-wrapper img {
		opacity: 0;
		transition: opacity 0.3s;
	}

	.img-wrapper img.loaded {
		opacity: 1;
	}
	.cdt-note:before {
		color: #64bbe3;
		content: '\1F6C8  Note:';
		font-size: 1rem;
		font-weight: 700;
		line-height: 2em;
	}
	.cdt-note {
		background-color: #0d274d;
		padding: 1.5em;
		color: #fff;
		border-radius: 5px;
		box-shadow: 0 0 16px 0 rgba(43, 85, 146, 0.2);
		border-left: #64bbe3 5px solid;
		max-width: 1100px;
		text-wrap: pretty;
		margin: 1em 0;
	}
	.cdt-note p {
		margin: auto 0;
		color: #fff;
	}
	.stepContainer {
		margin: 1em 0;
		padding: 1em 0;
	}
	.stepContainer p {
		margin: 0;
	}

	.stepContainer h4 {
		margin: 0;
		font-weight: 700;
	}

	:global(ul) {
		list-style-type: none;
	}

	/* :global(ul li::before) {
		content: '\25cf';
		color: #64bbe3;
		font-weight: 900;
		font-size: 1.15em;
		display: inline-block;
		width: 1em;
		text-align: left;
	} */

	.stepContainer img {
		max-width: calc(100% - 80px);
		height: auto;
		margin: 1.5em 40px;
		border-radius: 5px;
		box-shadow: 0 0 16px 0 rgba(43, 85, 146, 0.2);
	}

	:global(#eot-doc-wrapper .kbd-cdt) {
		display: block;
		height: auto;
		background-color: #dfdfdf;
		color: #0d274d;
		border-radius: 12px;
		padding: 1.3em;
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

	@media only screen and (max-width: 768px) {
		.stepContainer img {
			max-width: calc(100% - 40px);
			margin: 1.5em 20px;
		}

		.stepContainer p {
			margin: 0 20px;
		}
	}
</style>
