<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { flyAndScale } from '$lib/utils/transitions';
	import { DropdownMenu } from 'bits-ui';

	export let show = false;
	export let typeahead = false;
	const dispatch = createEventDispatcher();
</script>

<DropdownMenu.Root
	bind:open={show}
	closeFocus={false}
	onOpenChange={(state) => {
		dispatch('change', state);
	}}
	{typeahead}
>
	<DropdownMenu.Trigger>
		<slot />
	</DropdownMenu.Trigger>

	<slot name="content">
		<DropdownMenu.Content
			class="w-full max-w-[130px] rounded-lg px-1 py-1.5 border border-gray-700 z-50 bg-gray-850 text-white"
			sideOffset={8}
			side="bottom"
			align="start"
			transition={flyAndScale}
		>
			<DropdownMenu.Item class="flex items-center px-3 py-2 text-sm  font-medium">
				<div class="flex items-center">Profile</div>
			</DropdownMenu.Item>

			<DropdownMenu.Item class="flex items-center px-3 py-2 text-sm  font-medium">
				<div class="flex items-center">Profile</div>
			</DropdownMenu.Item>

			<DropdownMenu.Item class="flex items-center px-3 py-2 text-sm  font-medium">
				<div class="flex items-center">Profile</div>
			</DropdownMenu.Item>
		</DropdownMenu.Content>
	</slot>
</DropdownMenu.Root>
