<script lang="ts">
	import '@harbor/elements/dropdown';

	export let onDropdown: (e: CustomEvent<{ item: { value: string } }>) => void;
	export let menu: boolean = true;
</script>

<div class="flex">
	<hbr-dropdown on:hbr-select={onDropdown} {menu}>
		<slot />
	</hbr-dropdown>
</div>
