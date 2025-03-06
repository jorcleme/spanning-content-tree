<script lang="ts">
	import { CAN_USE_DOM } from '$lib/utils/editor';

	import DropdownItems from './DropdownItems.svelte';
	import { ChevronDown, Columns, Type } from 'lucide-svelte';

	export let disabled = false;
	export let buttonAriaLabel: string = '';
	export let buttonClassName: string;
	export let buttonLabel: string = '';
	export let buttonIconClassName: string = '';
	export let stopCloseOnClickSelf = false;
	export let title: string = '';

	let dropDownRef: HTMLDivElement;
	let buttonRef: HTMLButtonElement;
	let showDropDown = false;

	function handleClose() {
		showDropDown = false;
		if (buttonRef) {
			buttonRef.focus();
		}
	}
	$: if (showDropDown && buttonRef && dropDownRef) {
		const { top, left } = buttonRef.getBoundingClientRect();
		dropDownRef.style.top = `${top + 42}px`;
		dropDownRef.style.left = `${Math.min(left, window.innerWidth - dropDownRef.offsetWidth - 20)}px`;
	}
	const handle = (event: MouseEvent) => {
		const target = event.target as Node;
		if (stopCloseOnClickSelf && target) {
			if (dropDownRef && dropDownRef.contains(target)) return;
		}
		if (!buttonRef.contains(target)) {
			showDropDown = false;
		}
	};
	$: if (showDropDown) {
		document.addEventListener('click', handle);
	} else if (CAN_USE_DOM) {
		document.removeEventListener('click', handle);
	}
</script>

<button
	type="button"
	{disabled}
	aria-label={buttonAriaLabel || buttonLabel}
	class="{buttonClassName} flex items-center justify-between text-sm bg-gray-50 rounded-md p-2 text-gray-500 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 dark:bg-gray-850 border-none cursor-pointer align-middle shrink-0"
	on:click={() => (showDropDown = !showDropDown)}
	bind:this={buttonRef}
	{title}
>
	{#if buttonIconClassName === 'columns'}
		<Columns class="w-4 h-4 text-gray-500" />
	{:else}
		<Type class="w-4 h-4 text-gray-500" />
	{/if}

	{#if buttonLabel}
		<span
			class="flex align-middle leading-5 text-sm text-gray-700 dark:text-gray-50 text-ellipsis overflow-hidden h-[20px] text-left px-3"
			>{buttonLabel}</span
		>
	{/if}

	<ChevronDown class="w-4 h-4 text-gray-500" />
</button>

{#if showDropDown}
	<DropdownItems bind:dropDownRef onClose={handleClose}>
		<slot />
	</DropdownItems>
{/if}
