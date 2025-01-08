<script lang="ts">
	export let label: string;
	export let placeholder = '';
	export let value: string;
	export let id = '';
	export let onChange = void 0;
	export let width = void 0;
</script>

<div class="flex items-center mb-2.5">
	<label class="flex flex-1 text-gray-700" for={id}>{label}</label>
	<input
		type="text"
		class="flex flex-[3_1_0%] border border-gray-200 rounded-md p-2 text-sm text-gray-700 dark:text-gray-50"
		style="width: {width};"
		{placeholder}
		bind:value
		{id}
		on:change={(e) => {
			if (onChange) {
				/* @ts-ignore TS not supported in Svelte Html */
				onChange(e.target.value);
			}
		}}
	/>
</div>
