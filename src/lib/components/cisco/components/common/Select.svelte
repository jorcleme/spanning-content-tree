<script lang="ts">
	import { beforeUpdate, createEventDispatcher, onDestroy, onMount } from 'svelte';
	import { createFloatingActions } from 'svelte-floating-ui';
	import type { ComputeConfig } from 'svelte-floating-ui';
	import { flip, offset, shift } from 'svelte-floating-ui/dom';

	import { getSeriesByName } from '$lib/apis/series';
	import { filterSelect, getSelectItems } from '$lib/utils/index';
	import type { Placement } from '@floating-ui/core/dist/floating-ui.core';

	import ChevronIcon from './ChevronIcon.svelte';
	import ClearIcon from './ClearIcon.svelte';
	import LoadingIcon from './LoadingIcon.svelte';

	const dispatch = createEventDispatcher();

	interface ListItem {
		[key: string]: string;
	}

	let filter = filterSelect;
	let getItems = getSelectItems;

	export let id: string | null = null;
	export let name: string | null = null;
	export let multiple = false;
	export let multiFullItemClearable = false;
	export let disabled = false;
	export let focused = false;
	export let value: any = null;
	export let filterText = '';
	export let placeholder = 'Select an option...';
	export let placeholderAlwaysShow = false;
	export let items: ListItem[];
	export let label: string = 'label';
	export let itemId: string = 'value';
	export let debounceWait = 300;
	export let hideEmptyState = false;
	export let inputAttributes = {};
	export let listOffset = 5;
	export let hoverItemIndex = 0;

	export let groupHeaderSelectable = false;
	let loadOptions: ((...args: any[]) => any) | null = null;

	export let hasError = false;
	export let filterSelectedItems = true;
	export let required = false;
	export let closeListOnChange = true;
	export let clearFilterTextOnBlur = true;

	export let createGroupHeaderItem = (groupValue: any, item: any) => {
		return {
			value: groupValue,
			[label]: groupValue
		};
	};

	let container: HTMLDivElement;
	let input: HTMLInputElement;
	let searchable = true;
	let inputStyles = '';
	let clearable = true;
	let loading = false;
	let listOpen = false;
	let listAutoWidth = true;
	let showChevron = true;
	let activeValue: any;
	let prev_value: any;
	let prev_filterText: string;
	let prev_multiple: boolean;

	let timeout: Timer | number;

	let debounce = (fn: (...args: any[]) => any, wait = 1) => {
		clearTimeout(timeout);
		timeout = setTimeout(fn, wait);
	};

	let itemFilter = (label: string, filterText: string) => `${label}`.toLowerCase().includes(filterText.toLowerCase());
	let groupBy = (group: { [key: string]: string }) => group.category;

	const handleConfirm = async () => {
		console.log('value', value);

		const series = await getSeriesByName(localStorage.token, value.value.trim());
		if (series) {
			dispatch('confirm', { device: series.id, name: series.name });
		}
	};

	const setValue = () => {
		if (typeof value === 'string') {
			let item = (items || []).find((item) => item[itemId] === value);
			value = item || {
				[itemId]: value,
				label: value
			};
		} else if (multiple && Array.isArray(value) && value.length > 0) {
			value = value.map((item) => (typeof item === 'string' ? { value: item, label: item } : item));
		}
	};

	type InputAttrs = {
		autocapitalize: string;
		autocomplete: string;
		autocorrect: string;
		spellcheck: boolean;
		tabindex: number;
		type: string;
		'aria-autocomplete': 'list' | 'none' | 'inline' | 'both' | null | undefined;
		id?: string;
		readonly?: boolean;
	};

	let _inputAttributes: InputAttrs;

	const assignInputAttributes = () => {
		_inputAttributes = Object.assign(
			{},
			{
				autocapitalize: 'none',
				autocomplete: 'off',
				autocorrect: 'off',
				spellcheck: false,
				tabindex: 0,
				type: 'text',
				'aria-autocomplete': 'list' as 'list'
			}
		);

		if (id) {
			_inputAttributes['id'] = id;
		}

		if (!searchable) {
			_inputAttributes['readonly'] = true;
		}
	};

	const convertStringItemsToObjects = (_items: string[]) => {
		return _items.map((item, index) => {
			return {
				index,
				value: item,
				label: `${item}`
			};
		});
	};

	const filterGroupedItems = (_items: ListItem[]) => {
		const groupValues: string[] = [];
		const groups: { [key: string]: any } = {};

		_items.forEach((item) => {
			const groupValue = groupBy(item);

			if (!groupValues.includes(groupValue)) {
				groupValues.push(groupValue);
				groups[groupValue] = [];

				if (groupValue) {
					groups[groupValue].push(
						Object.assign(createGroupHeaderItem(groupValue, item), {
							id: groupValue,
							groupHeader: true,
							selectable: groupHeaderSelectable
						})
					);
				}
			}

			groups[groupValue].push(Object.assign({ groupItem: !!groupValue }, item));
		});

		const sortedGroupedItems: { [key: string]: any }[] = [];

		groupValues.forEach((groupValue) => {
			if (groups[groupValue]) sortedGroupedItems.push(...groups[groupValue]);
		});

		return sortedGroupedItems;
	};

	const dispatchSelectedItem = () => {
		if (multiple) {
			if (JSON.stringify(value) !== JSON.stringify(prev_value)) {
				if (checkValueForDuplicates()) {
					dispatch('input', value);
				}
			}
			return;
		}

		if (!prev_value || JSON.stringify(value[itemId]) !== JSON.stringify(prev_value[itemId])) {
			dispatch('input', value);
		}
	};

	const setupMulti = () => {
		if (value) {
			if (Array.isArray(value)) {
				value = [...value];
			} else {
				value = [value];
			}
		}
	};

	const setupSingle = () => {
		if (value) value = null;
	};

	const checkHoverSelectable = (startingIndex = 0, ignoreGroup: boolean = false) => {
		hoverItemIndex = startingIndex < 0 ? 0 : startingIndex;
		if (!ignoreGroup && filteredItems[hoverItemIndex] && !filteredItems[hoverItemIndex].selectable) {
			setHoverIndex(1);
		}
	};

	const setValueIndexAsHoverIndex = () => {
		const valueIndex = filteredItems.findIndex((i: { [key: string]: string }) => {
			return i[itemId] === value[itemId];
		});

		checkHoverSelectable(valueIndex, true);
	};

	const dispatchHover = (i: number) => {
		dispatch('hoverItem', i);
	};

	const setupFilterText = () => {
		if (!loadOptions && filterText.length === 0) return;

		if (loadOptions) {
			debounce(async function () {
				loading = true;
				let res = await getItems({
					dispatch,
					loadOptions,
					convertStringItemsToObjects,
					filterText
				});

				if (res) {
					loading = res.loading;
					listOpen = listOpen ? res.listOpen : filterText.length > 0 ? true : false;
					focused = listOpen && res.focused;
					items = filterGroupedItems(res.filteredItems);
				} else {
					loading = false;
					focused = true;
					listOpen = true;
				}
			}, debounceWait);
		} else {
			listOpen = true;

			if (multiple) {
				activeValue = undefined;
			}
		}
	};

	const handleFilterEvent = (items: { [key: string]: any }[]) => {
		if (listOpen) dispatch('filter', items);
	};

	const checkValueForDuplicates = () => {
		let noDuplicates = true;
		if (value) {
			const ids: any[] = [];
			const uniqueValues: any[] = [];

			value.forEach((val: any) => {
				if (!ids.includes(val[itemId])) {
					ids.push(val[itemId]);
					uniqueValues.push(val);
				} else {
					noDuplicates = false;
				}
			});

			if (!noDuplicates) value = uniqueValues;
		}
		return noDuplicates;
	};

	const findItem = (selection?: { [key: string]: any }) => {
		let matchTo = selection ? selection[itemId] : value[itemId];
		return items.find((item) => item[itemId] === matchTo);
	};

	const updateValueDisplay = (items?: { [key: string]: any }[]) => {
		if (!items || items.length === 0 || items.some((item) => typeof item !== 'object')) return;
		if (!value || (multiple ? value.some((selection: any) => !selection || !selection[itemId]) : !value[itemId]))
			return;

		if (Array.isArray(value)) {
			value = value.map((selection) => findItem(selection) || selection);
		} else {
			value = findItem() || value;
		}
	};

	const handleMultiItemClear = async (i: number) => {
		const itemToRemove = value[i];

		if (value.length === 1) {
			value = undefined;
		} else {
			value = value.filter((item: any) => {
				return item !== itemToRemove;
			});
		}

		dispatch('clear', itemToRemove);
	};

	const itemSelected = (selection?: { [key: string]: any }) => {
		if (selection) {
			filterText = '';
			const item = Object.assign({}, selection);

			if (item.groupHeader && !item.selectable) return;
			value = multiple ? (value ? value.concat([item]) : [item]) : (value = item);

			setTimeout(() => {
				if (closeListOnChange) closeList();
				activeValue = undefined;
				dispatch('change', value);
				dispatch('select', selection);
			});
		}
	};

	let ariaValues = (values: any) => {
		return `Option ${values}, selected.`;
	};

	let ariaListOpen = (label: string, count: number) => {
		return `You are currently focused on option ${label}. There are ${count} results available.`;
	};

	let ariaFocused = () => {
		return `Select is focused, type to refine list, press down to open the menu.`;
	};

	const handleAriaSelection = (_multiple: boolean) => {
		let selected = undefined;

		if (_multiple && value.length > 0) {
			selected = value.map((v: any) => v[label]).join(', ');
		} else {
			selected = value[label];
		}

		return ariaValues(selected);
	};

	const handleAriaContent = () => {
		if (!filteredItems || filteredItems.length === 0) return '';
		let _item = filteredItems[hoverItemIndex];
		if (listOpen && _item) {
			let count = filteredItems ? filteredItems.length : 0;
			return ariaListOpen(_item[label], count);
		} else {
			return ariaFocused();
		}
	};

	const setHoverIndex = (increment: number) => {
		let selectableFilteredItems = filteredItems.filter(
			(item) => !Object.hasOwn(item, 'selectable') || item.selectable === true
		);

		if (selectableFilteredItems.length === 0) {
			return (hoverItemIndex = 0);
		}

		if (increment > 0 && hoverItemIndex === filteredItems.length - 1) {
			hoverItemIndex = 0;
		} else if (increment < 0 && hoverItemIndex === 0) {
			hoverItemIndex = filteredItems.length - 1;
		} else {
			hoverItemIndex = hoverItemIndex + increment;
		}

		const hover = filteredItems[hoverItemIndex];

		if (hover && hover.selectable === false) {
			if (increment === 1 || increment === -1) setHoverIndex(increment);
			return;
		}
	};

	const isItemActive = (item: { [key: string]: any }, value: { [key: string]: any }, itemId: string) => {
		if (multiple) return;
		return value && value[itemId] === item[itemId];
	};

	const isItemFirst = (index: number) => (index === 0 ? true : false);

	const isItemSelectable = (item: any) => {
		return (item.groupHeader && item.selectable) || item.selectable || !item.hasOwnProperty('selectable');
	};

	const scrollAction = (node: HTMLElement, p0: { scroll: boolean | undefined; listDom: boolean }) => {
		return {
			update(args: any) {
				if (args.scroll) {
					handleListScroll();
					node.scrollIntoView({ behavior: 'auto', block: 'nearest' });
				}
			}
		};
	};

	$: if ((items, value)) setValue();
	$: if (inputAttributes || !searchable) assignInputAttributes();
	$: if (multiple) setupMulti();
	$: if (prev_multiple && !multiple) setupSingle();
	$: if (multiple && value && value.length > 1) checkValueForDuplicates();
	$: if (value) dispatchSelectedItem();
	$: if (!value && multiple && prev_value) dispatch('input', value);
	$: if (!focused && input) closeList();
	$: if (filterText !== prev_filterText) setupFilterText();
	$: if (!multiple && listOpen && value && filteredItems) setValueIndexAsHoverIndex();
	$: dispatchHover(hoverItemIndex);

	$: hasValue = multiple ? value && value.length > 0 : value;
	$: hideSelectedItem = hasValue && filterText.length > 0;
	$: showClear = hasValue && clearable && !disabled && !loading;
	$: placeholderText =
		placeholderAlwaysShow && multiple
			? placeholder
			: multiple && value?.length === 0
			? placeholder
			: value
			? ''
			: placeholder;
	$: ariaSelection = value ? handleAriaSelection(multiple) : '';
	$: ariaContext = handleAriaContent();
	$: updateValueDisplay(items);
	$: if (!multiple && prev_value && !value) dispatch('input', value);
	$: filteredItems = filter({
		filterText,
		items,
		multiple,
		value,
		itemId,
		label,
		filterSelectedItems,
		itemFilter,
		convertStringItemsToObjects,
		filterGroupedItems
	});
	$: if (listOpen && filteredItems && !multiple && !value) checkHoverSelectable();
	$: handleFilterEvent(filteredItems);
	$: if (container) floatingUpdate(_floatingConfig);
	$: listDom = !!list;
	$: listMounted(list, listOpen);
	$: if (listOpen && container && list) setListWidth();
	$: scrollToHoverItem = hoverItemIndex;
	$: if (listOpen && multiple) hoverItemIndex = 0;
	$: if (input && listOpen && !focused) handleFocus();
	$: if (filterText) hoverItemIndex = 0;

	beforeUpdate(async () => {
		prev_value = value;
		prev_filterText = filterText;
		prev_multiple = multiple;
	});

	//////////////////////////
	// Event Handlers
	//////////////////////////

	const handleKeyDown = (e: KeyboardEvent) => {
		if (!focused) return;
		e.stopPropagation();
		switch (e.key) {
			case 'Escape':
				e.preventDefault();
				closeList();
				break;
			case 'Enter':
				e.preventDefault();

				if (listOpen) {
					if (filteredItems.length === 0) break;
					const hoverItem = filteredItems[hoverItemIndex];

					if (value && !multiple && value[itemId] === hoverItem[itemId]) {
						closeList();
						break;
					} else {
						handleSelect(filteredItems[hoverItemIndex]);
					}
				}

				break;
			case 'ArrowDown':
				e.preventDefault();

				if (listOpen) {
					setHoverIndex(1);
				} else {
					listOpen = true;
					activeValue = undefined;
				}

				break;
			case 'ArrowUp':
				e.preventDefault();

				if (listOpen) {
					setHoverIndex(-1);
				} else {
					listOpen = true;
					activeValue = undefined;
				}

				break;
			case 'Tab':
				if (listOpen && focused) {
					if (filteredItems.length === 0 || (value && value[itemId] === filteredItems[hoverItemIndex][itemId]))
						return closeList();

					e.preventDefault();
					handleSelect(filteredItems[hoverItemIndex]);
					closeList();
				}

				break;
			case 'Backspace':
				if (!multiple || filterText.length > 0) return;

				if (multiple && value && value.length > 0) {
					handleMultiItemClear(activeValue !== undefined ? activeValue : value.length - 1);
					if (activeValue === 0 || activeValue === undefined) break;
					activeValue = value.length > activeValue ? activeValue - 1 : undefined;
				}

				break;
			case 'ArrowLeft':
				if (!value || !multiple || filterText.length > 0) return;
				if (activeValue === undefined) {
					activeValue = value.length - 1;
				} else if (value.length > activeValue && activeValue !== 0) {
					activeValue -= 1;
				}
				break;
			case 'ArrowRight':
				if (!value || !multiple || filterText.length > 0 || activeValue === undefined) return;
				if (activeValue === value.length - 1) {
					activeValue = undefined;
				} else if (activeValue < value.length - 1) {
					activeValue += 1;
				}
				break;
		}
	};

	const handleFocus = (e?: FocusEvent & { currentTarget: EventTarget & HTMLInputElement }) => {
		if (focused && input === document?.activeElement) return;
		if (e) dispatch('focus', e);
		input?.focus();
		focused = true;
	};

	const handleBlur = async (e?: FocusEvent & { currentTarget: EventTarget & HTMLInputElement }) => {
		if (isScrolling) return;
		if (listOpen || focused) {
			dispatch('blur', e);
			closeList();
			focused = false;
			activeValue = undefined;
			input?.blur();
		}
	};

	const handleClick = () => {
		if (disabled) return;
		if (filterText.length > 0) return (listOpen = true);
		listOpen = !listOpen;
		dispatch('toggle', { state: listOpen });
	};

	const handleSelect = (item: any) => {
		if (!item || item.selectable === false) return;
		itemSelected(item);
	};

	const handleHover = (i: number) => {
		if (isScrolling) return;
		hoverItemIndex = i;
	};

	const handleItemClick = (args: any) => {
		const { item, i } = args;
		if (item?.selectable === false) return;
		if (value && !multiple && value[itemId] === item[itemId]) return closeList();
		if (isItemSelectable(item)) {
			hoverItemIndex = i;
			handleSelect(item);
		}
	};

	export let handleClear = () => {
		dispatch('clear', value);
		value = undefined;
		closeList();
		handleFocus();
	};

	//////////////////////////
	// Lifecycle
	//////////////////////////

	onMount(() => {
		if (listOpen) focused = true;
		if (focused && input) input.focus();
	});

	onDestroy(() => {
		list?.remove();
	});

	const closeList = () => {
		if (clearFilterTextOnBlur) {
			filterText = '';
		}
		listOpen = false;
	};

	let list: HTMLDivElement;

	let isScrollingTimer: Timer | number;
	const handleListScroll = () => {
		clearTimeout(isScrollingTimer);
		isScrollingTimer = setTimeout(() => {
			isScrolling = false;
		}, 100);
	};

	const handleClickOutside = (event: MouseEvent & { currentTarget: EventTarget & Window }) => {
		if (
			!listOpen &&
			!focused &&
			container &&
			!container.contains(event.target as unknown as Node) &&
			!list?.contains(event.target as unknown as Node)
		) {
			handleBlur();
		}
	};

	let isScrolling = false;
	const activeScroll = scrollAction;
	const hoverScroll = scrollAction;
	let prefloat = true;

	const setListWidth = () => {
		const { width } = container.getBoundingClientRect();
		list.style.width = listAutoWidth ? `${width}px` : 'auto';
	};

	let _floatingConfig: ComputeConfig = {
		strategy: 'absolute',
		placement: 'bottom-start' as Placement,
		middleware: [offset(listOffset), flip(), shift()],
		autoUpdate: false
	};

	const [floatingRef, floatingContent, floatingUpdate] = createFloatingActions(_floatingConfig);

	const listMounted = (list: any, listOpen: boolean) => {
		if (!list || !listOpen) return (prefloat = true);
		setTimeout(() => {
			prefloat = false;
		}, 0);
	};
</script>

<svelte:window on:click={handleClickOutside} on:keydown={handleKeyDown} />

<div
	class="svelte-select min-w-80 bg-gray-50 text-gray-850 dark:bg-gray-850 dark:text-gray-100 border border-gray-300 dark:border-gray-700 rounded-md hover:border-gray-400 dark:hover:border-gray-600 focus:border-blue-500 dark:focus:border-blue-400"
	class:multi={multiple}
	class:disabled
	class:focused
	class:list-open={listOpen}
	class:show-chevron={showChevron}
	class:error={hasError}
	on:pointerup|preventDefault={handleClick}
	bind:this={container}
	use:floatingRef
	role="none"
>
	{#if listOpen}
		<div
			use:floatingContent
			bind:this={list}
			class="svelte-select-list bg-gray-50 text-gray-850"
			class:prefloat
			on:scroll={handleListScroll}
			on:pointerup|preventDefault|stopPropagation
			on:mousedown|preventDefault|stopPropagation
			role="none"
		>
			{#if $$slots['list-prepend']}<slot name="list-prepend" />{/if}
			{#if $$slots.list}<slot name="list" {filteredItems} />
			{:else if filteredItems.length > 0}
				{#each filteredItems as item, i}
					<div
						on:mouseover={() => handleHover(i)}
						on:focus={() => handleHover(i)}
						on:click|stopPropagation={() => handleItemClick({ item, i })}
						on:keydown|preventDefault|stopPropagation
						class="list-item"
						tabindex="-1"
						role="none"
					>
						<div
							use:activeScroll={{ scroll: isItemActive(item, value, itemId), listDom }}
							use:hoverScroll={{ scroll: scrollToHoverItem === i, listDom }}
							class="item"
							class:list-group-title={item.groupHeader}
							class:active={isItemActive(item, value, itemId)}
							class:first={isItemFirst(i)}
							class:hover={hoverItemIndex === i}
							class:group-item={item.groupItem}
							class:not-selectable={item?.selectable === false}
						>
							<slot name="item" {item} index={i}>
								{item?.[label]}
							</slot>
						</div>
					</div>
				{/each}
			{:else if !hideEmptyState}
				<slot name="empty">
					<div class="empty">No options</div>
				</slot>
			{/if}
			{#if $$slots['list-append']}<slot name="list-append" />{/if}
		</div>
	{/if}

	<span aria-live="polite" aria-atomic="false" aria-relevant="additions text" class="a11y-text">
		{#if focused}
			<span id="aria-selection">{ariaSelection}</span>
			<span id="aria-context">
				{ariaContext}
			</span>
		{/if}
	</span>

	<div class="prepend">
		<slot name="prepend" />
	</div>

	<div class="value-container">
		{#if hasValue}
			{#if multiple}
				{#each value as item, i}
					<div
						class="multi-item"
						class:active={activeValue === i}
						class:disabled
						on:click|preventDefault={() => (multiFullItemClearable ? handleMultiItemClear(i) : {})}
						on:keydown|preventDefault|stopPropagation
						role="none"
					>
						<span class="multi-item-text">
							<slot name="selection" selection={item} index={i}>
								{item[label]}
							</slot>
						</span>

						{#if !disabled && !multiFullItemClearable && ClearIcon}
							<div class="multi-item-clear" on:pointerup|preventDefault|stopPropagation={() => handleMultiItemClear(i)}>
								<slot name="multi-clear-icon">
									<ClearIcon />
								</slot>
							</div>
						{/if}
					</div>
				{/each}
			{:else}
				<div class="selected-item" class:hide-selected-item={hideSelectedItem}>
					<slot name="selection" selection={value}>
						{value[label]}
					</slot>
				</div>
			{/if}
		{/if}

		<input
			on:keydown={handleKeyDown}
			on:blur={handleBlur}
			on:focus={handleFocus}
			readOnly={!searchable}
			{..._inputAttributes}
			bind:this={input}
			bind:value={filterText}
			placeholder={placeholderText}
			style={inputStyles}
			{disabled}
			class="bg-gray-50 dark:bg-gray-850 dark:text-gray-100"
		/>
	</div>

	<div class="indicators">
		{#if loading}
			<div class="icon loading" aria-hidden="true">
				<slot name="loading-icon">
					<LoadingIcon />
				</slot>
			</div>
		{/if}

		{#if showClear}
			<button type="button" class="icon clear-select" on:click={handleClear}>
				<slot name="clear-icon">
					<ClearIcon />
				</slot>
			</button>
		{/if}

		<div class="icon chevron" aria-hidden="true">
			<slot name="chevron-icon" {listOpen}>
				<ChevronIcon />
			</slot>
		</div>
	</div>

	<slot name="input-hidden" {value}>
		<input {name} type="hidden" value={value ? JSON.stringify(value) : null} />
	</slot>

	{#if required && (!value || value.length === 0)}
		<slot name="required" {value}>
			<select class="required" required tabindex="-1" aria-hidden="true" />
		</slot>
	{/if}
</div>
<button
	class="btn self-center m-4 px-4 py-2 bg-blue-850 text-gray-50 dark:bg-gray-850 dark:hover:bg-gray-800 rounded-md"
	on:click={async () => await handleConfirm()}>Confirm</button
>

<style>
	.svelte-select {
		--borderRadius: var(--border-radius);
		--clearSelectColor: var(--clear-select-color);
		--clearSelectWidth: var(--clear-select-width);
		--disabledBackground: var(--disabled-background);
		--disabledBorderColor: var(--disabled-border-color);
		--disabledColor: var(--disabled-color);
		--disabledPlaceholderColor: var(--disabled-placeholder-color);
		--disabledPlaceholderOpacity: var(--disabled-placeholder-opacity);
		--errorBackground: var(--error-background);
		--errorBorder: var(--error-border);
		--groupItemPaddingLeft: var(--group-item-padding-left);
		--groupTitleColor: var(--group-title-color);
		--groupTitleFontSize: var(--group-title-font-size);
		--groupTitleFontWeight: var(--group-title-font-weight);
		--groupTitlePadding: var(--group-title-padding);
		--groupTitleTextTransform: var(--group-title-text-transform);
		--groupTitleBorderColor: var(--group-title-border-color);
		--groupTitleBorderWidth: var(--group-title-border-width);
		--groupTitleBorderStyle: var(--group-title-border-style);
		--indicatorColor: var(--chevron-color);
		--indicatorHeight: var(--chevron-height);
		--indicatorWidth: var(--chevron-width);
		--inputColor: var(--input-color);
		--inputLeft: var(--input-left);
		--inputLetterSpacing: var(--input-letter-spacing);
		--inputMargin: var(--input-margin);
		--inputPadding: var(--input-padding);
		--itemActiveBackground: var(--item-active-background);
		--itemColor: var(--item-color);
		--itemFirstBorderRadius: var(--item-first-border-radius);
		--itemHoverBG: var(--item-hover-bg);
		--itemHoverColor: var(--item-hover-color);
		--itemIsActiveBG: var(--item-is-active-bg);
		--itemIsActiveColor: var(--item-is-active-color);
		--itemIsNotSelectableColor: var(--item-is-not-selectable-color);
		--itemPadding: var(--item-padding);
		--listBackground: var(--list-background);
		--listBorder: var(--list-border);
		--listBorderRadius: var(--list-border-radius);
		--listEmptyColor: var(--list-empty-color);
		--listEmptyPadding: var(--list-empty-padding);
		--listEmptyTextAlign: var(--list-empty-text-align);
		--listMaxHeight: var(--list-max-height);
		--listPosition: var(--list-position);
		--listShadow: var(--list-shadow);
		--listZIndex: var(--list-z-index);
		--multiItemBG: var(--multi-item-bg);
		--multiItemBorderRadius: var(--multi-item-border-radius);
		--multiItemDisabledHoverBg: var(--multi-item-disabled-hover-bg);
		--multiItemDisabledHoverColor: var(--multi-item-disabled-hover-color);
		--multiItemHeight: var(--multi-item-height);
		--multiItemMargin: var(--multi-item-margin);
		--multiItemPadding: var(--multi-item-padding);
		--multiSelectInputMargin: var(--multi-select-input-margin);
		--multiSelectInputPadding: var(--multi-select-input-padding);
		--multiSelectPadding: var(--multi-select-padding);
		--placeholderColor: var(--placeholder-color);
		--placeholderOpacity: var(--placeholder-opacity);
		--selectedItemPadding: var(--selected-item-padding);
		--spinnerColor: var(--spinner-color);
		--spinnerHeight: var(--spinner-height);
		--spinnerWidth: var(--spinner-width);

		--internal-padding: 0 0 0 16px;

		border: var(--border, 1px solid #d8dbdf);
		border-radius: var(--border-radius, 6px);
		min-height: var(--height, 42px);
		position: relative;
		display: flex;
		align-items: stretch;
		padding: var(--padding, var(--internal-padding));
		background: var(--background, #f7f7f7);
		margin: var(--margin, 0);
		width: var(--width, 100%);
		font-size: var(--font-size, 16px);
		max-height: var(--max-height);
	}

	.value-container {
		display: flex;
		flex: 1 1 0%;
		flex-wrap: wrap;
		align-items: center;
		gap: 5px 10px;
		padding: 0;
		position: relative;
		overflow: hidden;
		align-self: stretch;
	}

	.prepend,
	.indicators {
		display: flex;
		flex-shrink: 0;
		align-items: center;
		color: var(--text-gray-700, #464c54);
	}

	.indicators {
		position: var(--indicators-position);
		top: var(--indicators-top);
		right: var(--indicators-right);
		bottom: var(--indicators-bottom);
	}

	input {
		position: absolute;
		cursor: default;
		border: none;
		color: var(--input-color, var(--item-color));
		padding: var(--input-padding, 0);
		letter-spacing: var(--input-letter-spacing, inherit);
		margin: var(--input-margin, 0);
		min-width: 10px;
		top: 0;
		right: 0;
		bottom: 0;
		left: 0;
		background: transparent;
		font-size: var(--font-size, 16px);
	}

	:not(.multi) > .value-container > input {
		width: 100%;
		height: 100%;
	}

	input::placeholder {
		color: var(--placeholder-color, #7e868f);
		opacity: var(--placeholder-opacity, 1);
	}

	input:focus {
		outline: none;
	}

	.svelte-select.focused {
		border: var(--border-focused, 1px solid #0d5cbd);
		border-radius: var(--border-radius-focused, var(--border-radius, 6px));
	}

	.disabled {
		background: var(--disabled-background, #f0f1f2);
		border-color: var(--disabled-border-color, #f0f1f2);
		color: var(--disabled-color, #c1c6cc);
	}

	.disabled input::placeholder {
		color: var(--disabled-placeholder-color, #c1c6cc);
		opacity: var(--disabled-placeholder-opacity, 1);
	}

	.selected-item {
		position: relative;
		overflow: var(--selected-item-overflow, hidden);
		padding: var(--selected-item-padding, 0 20px 0 0);
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--selected-item-color, #23282e);
		font-size: var(--font-size, 16px);
	}

	.multi .selected-item {
		position: absolute;
		line-height: var(--height, 42px);
		height: var(--height, 42px);
	}

	.selected-item:focus {
		outline: none;
	}

	.hide-selected-item {
		opacity: 0;
	}

	.icon {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.clear-select {
		all: unset;
		display: flex;
		align-items: center;
		justify-content: center;
		width: var(--clear-select-width, 40px);
		height: var(--clear-select-height, 100%);
		color: var(--clear-select-color, var(--icons-color));
		margin: var(--clear-select-margin, 0);
		pointer-events: all;
		flex-shrink: 0;
	}

	.clear-select:focus {
		outline: var(--clear-select-focus-outline, 1px solid #0d5cbd);
	}

	.loading {
		width: var(--loading-width, 40px);
		height: var(--loading-height);
		color: var(--loading-color, var(--icons-color));
		margin: var(--loading--margin, 0);
		flex-shrink: 0;
	}

	.chevron {
		width: var(--chevron-width, 40px);
		height: var(--chevron-height, 40px);
		background: var(--chevron-background, transparent);
		pointer-events: var(--chevron-pointer-events, none);
		color: var(--chevron-color, var(--icons-color));
		border: var(--chevron-border, 0 0 0 1px solid #7e868f);
		flex-shrink: 0;
	}

	.multi {
		padding: var(--multi-select-padding, var(--internal-padding));
	}

	.multi input {
		padding: var(--multi-select-input-padding, 0);
		position: relative;
		margin: var(--multi-select-input-margin, 5px 0);
		flex: 1 1 40px;
	}

	.svelte-select.error {
		border: var(--error-border, 1px solid #d93843);
		background: var(--error-background, #f7f7f7);
	}

	.a11y-text {
		z-index: 9999;
		border: 0px;
		clip: rect(1px, 1px, 1px, 1px);
		height: 1px;
		width: 1px;
		position: absolute;
		overflow: hidden;
		padding: 0px;
		white-space: nowrap;
	}

	.multi-item {
		background: var(--multi-item-bg, #e1e4e8);
		margin: var(--multi-item-margin, 0);
		outline: var(--multi-item-outline, 1px solid #d0d4d9);
		border-radius: var(--multi-item-border-radius, 4px);
		height: var(--multi-item-height, 25px);
		line-height: var(--multi-item-height, 25px);
		display: flex;
		cursor: default;
		padding: var(--multi-item-padding, 0 5px);
		overflow: hidden;
		gap: var(--multi-item-gap, 4px);
		outline-offset: -1px;
		max-width: var(--multi-max-width, none);
		color: var(--multi-item-color, var(--item-color));
	}

	.multi-item.disabled:hover {
		background: var(--multi-item-disabled-hover-bg, #e1e4e8);
		color: var(--multi-item-disabled-hover-color, #c1c6cc);
	}

	.multi-item-text {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.multi-item-clear {
		display: flex;
		align-items: center;
		justify-content: center;
		--clear-icon-color: var(--multi-item-clear-icon-color, #0f1214);
	}

	.multi-item.active {
		outline: var(--multi-item-active-outline, 1px solid #0d5cbd);
	}

	.svelte-select-list {
		box-shadow: var(--list-shadow, 0 2px 3px 0 rgba(44, 62, 80, 0.24));
		border-radius: var(--list-border-radius, 4px);
		max-height: var(--list-max-height, 252px);
		overflow-y: auto;
		background: var(--list-background, #f7f7f7);
		position: var(--list-position, absolute);
		z-index: var(--list-z-index, 9999);
		border: var(--list-border);
	}

	.prefloat {
		opacity: 0;
		pointer-events: none;
	}

	.list-group-title {
		color: var(--group-title-color, #464c54);
		cursor: default;
		font-size: var(--group-title-font-size, 16px);
		font-weight: var(--group-title-font-weight, 600);
		height: var(--height, 42px);
		line-height: var(--height, 42px);
		padding: var(--group-title-padding, 0 20px);
		text-overflow: ellipsis;
		overflow-x: hidden;
		white-space: nowrap;
		text-transform: var(--group-title-text-transform, uppercase);
		border-width: var(--group-title-border-width, medium);
		border-style: var(--group-title-border-style, none);
		border-color: var(--group-title-border-color, color);
	}

	.empty {
		text-align: var(--list-empty-text-align, center);
		padding: var(--list-empty-padding, 20px 0);
		color: var(--list-empty-color, #464c54);
	}

	.item {
		cursor: default;
		height: var(--item-height, var(--height, 42px));
		line-height: var(--item-line-height, var(--height, 42px));
		padding: var(--item-padding, 0 20px);
		color: var(--item-color, inherit);
		text-overflow: ellipsis;
		overflow: hidden;
		white-space: nowrap;
		transition: var(--item-transition, all 0.2s);
		align-items: center;
		width: 100%;
	}

	.item.group-item {
		padding-left: var(--group-item-padding-left, 40px);
	}

	.item:active {
		background: var(--item-active-background, #bad6ff);
	}

	.item.active {
		background: var(--item-is-active-bg, #0d5cbd);
		color: var(--item-is-active-color, #f7f7f7);
	}

	.item.first {
		border-radius: var(--item-first-border-radius, 4px 4px 0 0);
	}

	.item.hover:not(.active) {
		background: var(--item-hover-bg, #e1e4e8);
		color: var(--item-hover-color, inherit);
	}

	.item.not-selectable,
	.item.hover.item.not-selectable,
	.item.active.item.not-selectable,
	.item.not-selectable:active {
		color: var(--item-is-not-selectable-color, #999);
		background: transparent;
	}

	.required {
		opacity: 0;
		z-index: -1;
		position: absolute;
		top: 0;
		left: 0;
		bottom: 0;
		right: 0;
	}
</style>
