<script lang="ts">
	import type { AdvancedModelParams, i18nType } from '$lib/types';

	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	import { getLanguages } from '$lib/i18n';
	import type { ChatParams } from '$lib/stores';
	import { models, settings, theme, user } from '$lib/stores';

	import AdvancedParams from './Advanced/AdvancedParams.svelte';

	const dispatch = createEventDispatcher();

	const i18n: i18nType = getContext('i18n');

	export let saveSettings: Function;

	// General
	let themes = ['dark', 'light', 'oled-dark', 'cisco', 'hbr-mode-dark'];
	let selectedTheme = 'system';

	let languages: Array<{ code: string; title: string }> = [];
	let lang = $i18n.language;
	let notificationEnabled = false;
	let system = '';

	let showAdvanced = false;

	const toggleNotification = async () => {
		const permission = await Notification.requestPermission();

		if (permission === 'granted') {
			notificationEnabled = !notificationEnabled;
			saveSettings({ notificationEnabled: notificationEnabled });
		} else {
			toast.error(
				$i18n.t(
					'Response notifications cannot be activated as the website permissions have been denied. Please visit your browser settings to grant the necessary access.'
				)
			);
		}
	};

	// Advanced
	let requestFormat = '';
	let keepAlive: string | number | null = null;

	let params: AdvancedModelParams = {
		// Advanced
		seed: null,
		temperature: null,
		frequency_penalty: null,
		repeat_last_n: null,
		mirostat: null,
		mirostat_eta: null,
		mirostat_tau: null,
		top_k: null,
		top_p: null,
		stop: null,
		tfs_z: null,
		num_ctx: null,
		num_batch: null,
		num_keep: null,
		max_tokens: null
	};

	const toggleRequestFormat = async () => {
		if (requestFormat === '') {
			requestFormat = 'json';
		} else {
			requestFormat = '';
		}

		saveSettings({ requestFormat: requestFormat !== '' ? requestFormat : undefined });
	};

	onMount(async () => {
		selectedTheme = localStorage.theme ?? 'system';

		languages = await getLanguages();

		notificationEnabled = $settings.notificationEnabled ?? false;
		system = $settings.system ?? '';

		requestFormat = $settings.requestFormat ?? '';
		keepAlive = $settings.keepAlive ?? null;

		params = { ...params, ...$settings.params };
		params.stop = $settings?.params?.stop ? ($settings?.params?.stop ?? []).join(',') : null;
	});

	const applyTheme = (_theme: string) => {
		let themeToApply = _theme === 'oled-dark' ? 'dark' : _theme;

		if (_theme === 'system') {
			themeToApply = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
		}

		if (themeToApply === 'dark' && !_theme.includes('hbr-mode-dark') && !_theme.includes('oled-dark')) {
			document.documentElement.style.setProperty('--color-gray-800', '#333');
			document.documentElement.style.setProperty('--color-gray-850', '#262626');
			document.documentElement.style.setProperty('--color-gray-900', '#171717');
			document.documentElement.style.setProperty('--color-gray-950', '#0d0d0d');
		}

		themes
			.filter((e) => e !== themeToApply)
			.forEach((e) => {
				e.split(' ').forEach((e) => {
					document.documentElement.classList.remove(e);
				});
			});

		themeToApply.split(' ').forEach((e) => {
			document.documentElement.classList.add(e);
		});

		if (_theme === 'hbr-mode-dark') {
			document.documentElement.classList.add('dark');
		}
	};

	const themeChangeHandler = (_theme: string) => {
		theme.set(_theme);
		localStorage.setItem('theme', _theme);
		applyTheme(_theme);
	};

	const onClick = () => {
		saveSettings({
			system: system !== '' ? system : undefined,
			params: {
				seed: (params.seed !== null ? params.seed : undefined) ?? undefined,
				stop: params.stop
					? Array.isArray(params.stop)
						? params.stop
						: params.stop.split(',').filter((e) => e)
					: undefined,
				temperature: params.temperature !== null ? params.temperature : undefined,
				frequency_penalty: params.frequency_penalty !== null ? params.frequency_penalty : undefined,
				repeat_last_n: params.repeat_last_n !== null ? params.repeat_last_n : undefined,
				mirostat: params.mirostat !== null ? params.mirostat : undefined,
				mirostat_eta: params.mirostat_eta !== null ? params.mirostat_eta : undefined,
				mirostat_tau: params.mirostat_tau !== null ? params.mirostat_tau : undefined,
				top_k: params.top_k !== null ? params.top_k : undefined,
				top_p: params.top_p !== null ? params.top_p : undefined,
				tfs_z: params.tfs_z !== null ? params.tfs_z : undefined,
				num_ctx: params.num_ctx !== null ? params.num_ctx : undefined,
				num_batch: params.num_batch !== null ? params.num_batch : undefined,
				num_keep: params.num_keep !== null ? params.num_keep : undefined,
				max_tokens: params.max_tokens !== null ? params.max_tokens : undefined,
				use_mmap: params.use_mmap !== null ? params.use_mmap : undefined,
				use_mlock: params.use_mlock !== null ? params.use_mlock : undefined,
				num_thread: params.num_thread !== null ? params.num_thread : undefined
			},
			keepAlive: keepAlive ? (isNaN(keepAlive as number) ? keepAlive : parseInt(keepAlive as string)) : undefined
		});
		dispatch('save');
	};
</script>

<div class="flex flex-col h-full justify-between text-sm">
	<div class="  pr-1.5 overflow-y-scroll max-h-[25rem]">
		<div class="">
			<div class=" mb-1 text-sm font-medium">{$i18n.t('WebUI Settings')}</div>

			<div class="flex w-full justify-between mb-2">
				<div class=" self-center text-xs font-medium">{$i18n.t('Theme')}</div>
				<div class="flex items-center relative">
					<select
						class=" dark:bg-gray-900 w-fit pr-8 rounded py-2 px-2 text-xs bg-transparent outline-none text-right"
						bind:value={selectedTheme}
						placeholder="Select a theme"
						on:change={() => themeChangeHandler(selectedTheme)}
					>
						<option value="system">⚙️ {$i18n.t('System')}</option>
						<option value="dark">🌑 {$i18n.t('Dark')}</option>
						<option value="light">☀️ {$i18n.t('Light')}</option>
						<option value="oled-dark">🖤 {$i18n.t('OLED Dark')}</option>
						<option value="cisco">📱 {$i18n.t('Cisco')}</option>
						<option value="hbr-mode-dark">💣 {$i18n.t('Cisco Dark')}</option>
					</select>
				</div>
			</div>

			<div class="flex w-full justify-between mb-2">
				<div class="self-center text-xs font-medium">{$i18n.t('Language')}</div>
				<div class="flex items-center relative">
					<select
						class="dark:bg-gray-900 w-fit pr-8 rounded py-2 px-2 text-xs bg-transparent outline-none text-right"
						bind:value={lang}
						placeholder="Select a language"
						on:change={(e) => {
							$i18n.changeLanguage(lang);
						}}
					>
						{#each languages as language}
							<option value={language['code']}>{language['title']}</option>
						{/each}
					</select>
				</div>
			</div>
			{#if $i18n.language === 'en-US'}
				<div class="mb-2 text-xs text-gray-400 dark:text-gray-500">
					Couldn't find your language?
					<a
						class=" text-gray-300 font-medium underline"
						href="https://github.com/open-webui/open-webui/blob/main/docs/CONTRIBUTING.md#-translations-and-internationalization"
						target="_blank"
					>
						Help us translate Open WebUI!
					</a>
				</div>
			{/if}

			<div>
				<div class=" py-0.5 flex w-full justify-between">
					<div class=" self-center text-xs font-medium">{$i18n.t('Notifications')}</div>

					<button
						class="p-1 px-3 text-xs flex rounded transition"
						on:click={() => {
							toggleNotification();
						}}
						type="button"
					>
						{#if notificationEnabled === true}
							<span class="ml-2 self-center">{$i18n.t('On')}</span>
						{:else}
							<span class="ml-2 self-center">{$i18n.t('Off')}</span>
						{/if}
					</button>
				</div>
			</div>
		</div>

		<hr class=" dark:border-gray-850 my-3" />

		<div>
			<div class=" my-2.5 text-sm font-medium">{$i18n.t('System Prompt')}</div>
			<textarea
				bind:value={system}
				class="w-full rounded-lg p-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none resize-none"
				rows="4"
			/>
		</div>

		<div class="mt-2 space-y-3 pr-1.5">
			<div class="flex justify-between items-center text-sm">
				<div class="  font-medium">{$i18n.t('Advanced Parameters')}</div>
				<button
					class=" text-xs font-medium text-gray-500"
					type="button"
					on:click={() => {
						showAdvanced = !showAdvanced;
					}}>{showAdvanced ? $i18n.t('Hide') : $i18n.t('Show')}</button
				>
			</div>

			{#if showAdvanced}
				<AdvancedParams admin={$user?.role === 'admin'} bind:params />
				<hr class=" dark:border-gray-850" />

				<div class=" py-1 w-full justify-between">
					<div class="flex w-full justify-between">
						<div class=" self-center text-xs font-medium">{$i18n.t('Keep Alive')}</div>

						<button
							class="p-1 px-3 text-xs flex rounded transition"
							type="button"
							on:click={() => {
								keepAlive = keepAlive === null ? '5m' : null;
							}}
						>
							{#if keepAlive === null}
								<span class="ml-2 self-center"> {$i18n.t('Default')} </span>
							{:else}
								<span class="ml-2 self-center"> {$i18n.t('Custom')} </span>
							{/if}
						</button>
					</div>

					{#if keepAlive !== null}
						<div class="flex mt-1 space-x-2">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none"
								type="text"
								placeholder={$i18n.t("e.g. '30s','10m'. Valid time units are 's', 'm', 'h'.")}
								bind:value={keepAlive}
							/>
						</div>
					{/if}
				</div>

				<div>
					<div class=" py-1 flex w-full justify-between">
						<div class=" self-center text-sm font-medium">{$i18n.t('Request Mode')}</div>

						<button
							class="p-1 px-3 text-xs flex rounded transition"
							on:click={() => {
								toggleRequestFormat();
							}}
						>
							{#if requestFormat === ''}
								<span class="ml-2 self-center"> {$i18n.t('Default')} </span>
							{:else if requestFormat === 'json'}
								<span class="ml-2 self-center"> {$i18n.t('JSON')} </span>
							{/if}
						</button>
					</div>
				</div>
			{/if}
		</div>
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-gray-100 transition rounded-lg"
			on:click={() => onClick()}
		>
			{$i18n.t('Save')}
		</button>
	</div>
</div>
