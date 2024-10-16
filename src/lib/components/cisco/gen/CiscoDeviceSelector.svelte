<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { getSeriesByName } from '$lib/apis/series';

	const dispatch = createEventDispatcher();

	let selectedDevice = '';

	const devices = {
		Switches: [
			{ label: 'Catalyst 1200', value: 'Cisco Catalyst 1200 Series Switches' },
			{ label: 'Catalyst 1300', value: 'Cisco Catalyst 1300 Series Switches' },
			{ label: 'CBS110 Series', value: 'Cisco Business 110 Series Unmanaged Switches' },
			{ label: 'CBS220 Series', value: 'Cisco Business 220 Series Smart Switches' },
			{ label: 'CBS250 Series', value: 'Cisco Business 250 Series Smart Switches' },
			{ label: 'CBS350 Series', value: 'Cisco Business 350 Series Managed Switches' },
			{ label: '350 Series', value: 'Cisco 350 Series Managed Switches' },
			{ label: '350X Series', value: 'Cisco 350X Series Stackable Managed Switches' },
			{ label: '550X Series', value: 'Cisco 550X Series Stackable Managed Switches' }
		],
		Routers: [
			{ label: 'RV100 Series', value: 'RV100 Product Family' },
			{ label: 'RV320 Series', value: 'RV320 Product Family' },
			{ label: 'RV340 Series', value: 'RV340 Product Family' },
			{ label: 'RV160 VPN Series', value: 'RV160 VPN Router' },
			{ label: 'RV260 VPN Series', value: 'RV260 VPN Router' }
		],
		Wireless: [
			{ label: 'CBW-AC', value: 'Cisco Business Wireless AC' },
			{ label: 'CBW-AX', value: 'Cisco Business Wireless AX' }
		]
		// Add more categories and devices as needed
	};

	const handleConfirm = async () => {
		const series = await getSeriesByName(localStorage.token, selectedDevice);
		if (series) {
			dispatch('confirm', { device: series.id, name: series.name });
		}
	};
</script>

<div class="flex flex-col space-y-2">
	<h2 class="text-slate-800 text-center">Select your device</h2>
	<select
		class="border-current inline-flex cursor-pointer select-none appearance-none select select-primary min-w-80 max-w-xs"
		bind:value={selectedDevice}
	>
		{#each Object.entries(devices) as [category, deviceList]}
			<optgroup label={category}>
				{#each deviceList as device}
					<option value={device.value}>{device.label}</option>
				{/each}
			</optgroup>
		{/each}
	</select>
	<button on:click={async () => await handleConfirm()}>Confirm</button>
</div>
