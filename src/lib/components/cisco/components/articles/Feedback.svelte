<script lang="ts">
	import type { i18nType } from '$lib/types';
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { fade } from 'svelte/transition';
	import { enhance } from '$app/forms';
	import type { _CiscoArticleMessage } from '$lib/stores/index';
	import { activeSupportSection, activeSupportStep } from '$lib/stores/index';

	const i18n: i18nType = getContext('i18n');

	const dispatch = createEventDispatcher();

	export let messageId: string | null = null;
	export let show = false;
	export let message: _CiscoArticleMessage;

	export let btnText = "I don't understand this step";

	type Reason = { id: string; label: string; value: string };

	let LIKE_REASONS: Reason[] = [];
	let DISLIKE_REASONS: Reason[] = [];

	let reasons: Reason[] = [];
	let selectedReasons: string[] = [];
	let selectedReason: string | null = null;
	let comment = '';

	const loadReasons = () => {
		LIKE_REASONS = [
			$i18n.t('Accurate information'),
			$i18n.t('Followed instructions perfectly'),
			$i18n.t('Showcased creativity'),
			$i18n.t('Positive attitude'),
			$i18n.t('Attention to detail'),
			$i18n.t('Thorough explanation'),
			'Helped me solve my own issue',
			$i18n.t('Other')
		].map((reason, i) => ({ id: `like-reason-${i}`, label: reason, value: reason }));

		DISLIKE_REASONS = [
			$i18n.t("Don't like the style"),
			$i18n.t('Not factually correct'),
			$i18n.t("Didn't fully follow instructions"),
			$i18n.t("Refused when it shouldn't have"),
			$i18n.t('Being lazy'),
			$i18n.t('Other')
		].map((reason, i) => ({ id: `dislike-reason-${i}`, label: reason, value: reason }));
	};

	onMount(() => {
		selectedReasons = message?.annotation?.reasons ?? [];
		comment = message?.annotation?.comment ?? '';
		loadReasons();
	});

	const submitHandler = () => {
		console.log('submitHandler');
		if (!message.annotation) {
			message.annotation = {};
		}
		message.annotation.reasons = selectedReasons;
		message.annotation.comment = comment;

		dispatch('submit');

		toast.success($i18n.t('Thanks for your feedback!'));
		show = false;
	};

	$: if (message?.annotation?.rating === 1) {
		reasons = LIKE_REASONS;
	} else if (message?.annotation?.rating === -1) {
		reasons = DISLIKE_REASONS;
	}
</script>

{#if show}
	<div class="my-2.5 rounded-xl px-4 py-3 border dark:border-gray-850" id="message-feedback-{messageId}">
		<div class="flex justify-between items-center">
			<div class="flex flex-col flex-wrap text-base gap-2">
				<h2 class="font-medium">Please provide additional information</h2>
				<span class="mt-1 font-['CiscoSansThin']"
					>{`Step ${$activeSupportStep} `}<strong>&gt;</strong><span>{` ${btnText}`}</span></span
				>
			</div>

			<button
				on:click={() => {
					show = false;
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="size-4"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		{#if reasons.length > 0}
			<div class="flex flex-wrap gap-2 text-sm mt-2.5">
				{#each reasons as reason}
					<label
						class="px-3.5 py-1 rounded-lg transition border dark:border-gray-850 hover:bg-gray-100 dark:hover:bg-gray-850 cursor-pointer {selectedReasons.includes(
							reason.value
						)
							? 'bg-[#2b5592] text-neutral-50'
							: ''}"
						for={reason.id}
					>
						{reason.label}
						<input
							bind:group={selectedReasons}
							name={reason.id}
							type="checkbox"
							id={reason.id}
							value={reason.value}
							style="display: none;"
						/>
					</label>
				{/each}
			</div>
		{/if}

		<div class="mt-2">
			<textarea
				bind:value={comment}
				class="w-full text-sm px-1 py-2 bg-transparent outline-none resize-none border border-[#ccc] rounded-xl"
				placeholder={$i18n.t('Feel free to add specific details')}
				rows="2"
			/>
		</div>

		<div class="mt-2 flex justify-end">
			<button
				class=" bg-emerald-700 text-white text-sm font-medium rounded-lg px-3.5 py-1.5"
				on:click={() => {
					submitHandler();
				}}
			>
				{$i18n.t('Submit')}
			</button>
		</div>
	</div>
{/if}

<style>
	textarea {
		border: 1px solid #ccc;
	}
</style>
