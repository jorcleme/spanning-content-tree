<script lang="ts">
	import type { Message } from '$lib/types';
	import type { i18nType } from '$lib/types';
	import { getContext, onMount } from 'svelte';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { config, models, settings } from '$lib/stores';
	import dayjs from 'dayjs';
	import Select from '$lib/components/cisco/components/common/Select.svelte';
	import Image from '$lib/components/common/Image.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Name from './Name.svelte';
	import ProfileImage from './ProfileImage.svelte';
	import { RouterIcon } from 'lucide-svelte';

	const i18n: i18nType = getContext('i18n');

	export let message: Message;
	export let siblings;
	export let isLastMessage = true;
	export let handleDeviceConfirm: (e: CustomEvent) => void;

	let value: string | null = null;

	onMount(() => {
		if (message?.content) {
			const content = JSON.parse(message.content);
			if (content.value && content.value !== '') {
				value = content.value;
			}
		} else {
			value = null;
		}
	});

	interface Device {
		[key: string]: string;
	}
	const devices: Device[] = [
		{ label: 'Cisco Catalyst 1200 Series', value: 'Cisco Catalyst 1200 Series Switches', category: 'Switches' },
		{ label: 'Cisco Catalyst 1300 Series', value: 'Cisco Catalyst 1300 Series Switches', category: 'Switches' },
		{ label: 'CBS110 Series', value: 'Cisco Business 110 Series Unmanaged Switches', category: 'Switches' },
		{ label: 'CBS220 Series', value: 'Cisco Business 220 Series Smart Switches', category: 'Switches' },
		{ label: 'CBS250 Series', value: 'Cisco Business 250 Series Smart Switches', category: 'Switches' },
		{ label: 'CBS350 Series', value: 'Cisco Business 350 Series Managed Switches', category: 'Switches' },
		{ label: 'Cisco 350 Series', value: 'Cisco 350 Series Managed Switches', category: 'Switches' },
		{
			label: 'Cisco 350X Stackable Series',
			value: 'Cisco 350X Series Stackable Managed Switches',
			category: 'Switches'
		},
		{
			label: 'Cisco 550X Stackable Series',
			value: 'Cisco 550X Series Stackable Managed Switches',
			category: 'Switches'
		},
		{ label: 'RV100 Series', value: 'RV100 Product Family', category: 'Routers' },
		{ label: 'RV320 Series', value: 'RV320 Product Family', category: 'Routers' },
		{ label: 'RV340 Series', value: 'RV340 Product Family', category: 'Routers' },
		{ label: 'Cisco RV160 VPN Series', value: 'RV160 VPN Router', category: 'Routers' },
		{ label: 'Cisco RV260 VPN Series', value: 'RV260 VPN Router', category: 'Routers' },
		{ label: 'CBW-AC', value: 'Cisco Business Wireless AC', category: 'Wireless' },
		{ label: 'CBW-AX', value: 'Cisco Business Wireless AX', category: 'Wireless' }
	];

	let model = null;
	$: model = $models.find((m) => m.id === message.model);

	let listOpen = false;

	const onToggleSelect = (e: CustomEvent<{ state: boolean }>) => {
		listOpen = e.detail.state;
	};
</script>

{#key message.id}
	<div class=" flex w-full message-{message.id}" id="message-{message.id}" dir={$settings.chatDirection}>
		<ProfileImage
			src={model?.info?.meta?.profile_image_url ??
				($i18n.language === 'dg-DG' ? `/doge.png` : `${WEBUI_BASE_URL}/static/favicon.png`)}
		/>

		<div class="w-full overflow-hidden pl-1">
			<Name>
				{model?.name ?? message.model}

				{#if message.timestamp}
					<span class=" self-center invisible group-hover:visible text-gray-400 text-xs font-medium uppercase">
						{dayjs(message.timestamp * 1000).format($i18n.t('h:mm a'))}
					</span>
				{/if}
			</Name>
			{#if message.files}
				{#if (message.files ?? []).filter((f) => f.type === 'image').length > 0}
					{#each message.files as file}
						<div>
							{#if file.type === 'image'}
								<Image src={file.url} />
							{/if}
						</div>
					{/each}
				{/if}
			{/if}

			<div class="prose chat-{message.role} w-full max-w-full dark:prose-invert {listOpen ? 'min-h-[14rem]' : ''}">
				<div>
					<div class="w-full">
						<div class="flex flex-col w-full sm:max-w-sm mx-auto">
							<Select
								bind:value
								items={devices}
								placeholder="Choose your device..."
								on:confirm={handleDeviceConfirm}
								on:toggle={onToggleSelect}
							>
								<div slot="prepend"><RouterIcon class="w-4 h-4 mr-2.5" /></div>
							</Select>
						</div>

						{#if message.error}
							<div
								class="flex mt-2 mb-4 space-x-2 border px-4 py-3 border-red-800 bg-red-800/30 font-medium rounded-lg"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-5 h-5 self-center"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
									/>
								</svg>

								<div class=" self-center">
									{message?.error?.content ?? message.content}
								</div>
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	</div>
{/key}
