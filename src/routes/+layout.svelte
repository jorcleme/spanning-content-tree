<script>
	// // Styles
	// import '@harbor/elements/styles.css';
	// Magnetic Design System styles
	import '@harbor/elements/dist/harbor-elements/styles/themes/magnetic.css';
	import '@harbor/elements/dist/harbor-elements/styles/tokens/magnetic.css';
	import '@harbor/elements/styles/themes/magnetic.dark.css';
	import '@harbor/elements/styles/tokens/magnetic.dark.css';
	// for brand colors (blue 🟦 instead of green)
	import '@harbor/elements/styles/themes/magnetic-brand-alt.css';
	import { io } from 'socket.io-client';
	import { spring } from 'svelte/motion';

	let loadingProgress = spring(0, {
		stiffness: 0.05
	});

	import { onMount, tick, setContext } from 'svelte';
	import { config, user, theme, WEBUI_NAME, mobile, socket, activeUserCount, USAGE_POOL } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { Toaster, toast } from 'svelte-sonner';

	import { getBackendConfig } from '$lib/apis';
	import { getSessionUser } from '$lib/apis/auths';

	import '../tailwind.css';
	import '../app.css';

	import 'tippy.js/dist/tippy.css';

	import { WEBUI_BASE_URL, WEBUI_HOSTNAME } from '$lib/constants';
	// @ts-ignore
	import i18n, { initI18n, getLanguages } from '$lib/i18n';
	import { bestMatchingLanguage } from '$lib/utils';

	setContext('i18n', i18n);

	let loaded = false;
	const BREAKPOINT = 768;

	/**
	 * @type {WakeLockSentinel | null}
	 */
	let wakeLock = null;

	// @ts-ignore
	onMount(async () => {
		theme.set(localStorage.theme);

		if ($theme === 'hbr-mode-dark') {
			document.documentElement.classList.add('cisco', 'dark');
		}

		mobile.set(window.innerWidth < BREAKPOINT);
		const onResize = () => {
			if (window.innerWidth < BREAKPOINT) {
				mobile.set(true);
			} else {
				mobile.set(false);
			}
		};

		window.addEventListener('resize', onResize);

		const setWakeLock = async () => {
			try {
				wakeLock = await navigator.wakeLock.request('screen');
			} catch (err) {
				// The Wake Lock request has failed - usually system related, such as battery.
				console.log(err);
			}

			if (wakeLock) {
				// Add a listener to release the wake lock when the page is unloaded
				wakeLock.addEventListener('release', () => {
					// the wake lock has been released
					console.log('Wake Lock released');
				});
			}
		};

		if ('wakeLock' in navigator) {
			await setWakeLock();

			document.addEventListener('visibilitychange', async () => {
				// Re-request the wake lock if the document becomes visible
				if (wakeLock !== null && document.visibilityState === 'visible') {
					await setWakeLock();
				}
			});
		}

		let backendConfig = null;
		try {
			backendConfig = await getBackendConfig();
			console.log('Backend config:', backendConfig);
		} catch (error) {
			console.error('Error loading backend config:', error);
		}
		// Initialize i18n even if we didn't get a backend config,
		// so `/error` can show something that's not `undefined`.

		initI18n(backendConfig?.default_locale);
		if (!localStorage.locale) {
			const languages = await getLanguages();
			const browserLanguages = navigator.languages
				? navigator.languages
				: // @ts-ignore
				  [navigator.language || navigator.userLanguage];
			const lang = backendConfig.default_locale
				? backendConfig.default_locale
				: // @ts-ignore
				  bestMatchingLanguage(languages, browserLanguages, 'en-US');
			$i18n.changeLanguage(lang);
		}

		if (backendConfig) {
			// Save Backend Status to Store
			config.set(backendConfig);
			WEBUI_NAME.set(backendConfig.name);

			if ($config) {
				const _socket = io(`${WEBUI_BASE_URL}`, {
					path: '/ws/socket.io',
					auth: { token: localStorage.token }
				});

				_socket.on('connect', () => {
					console.log('connected');
				});

				socket.set(_socket);

				_socket.on('user-count', (data) => {
					console.log('user-count', data);
					activeUserCount.set(data.count);
				});

				_socket.on('usage', (data) => {
					console.log('usage', data);
					USAGE_POOL.set(data['models']);
				});

				if (localStorage.token) {
					// Get Session User Info
					const sessionUser = await getSessionUser(localStorage.token).catch((error) => {
						toast.error(error);
						return null;
					});

					if (sessionUser) {
						// Save Session User to Store
						user.set(sessionUser);
					} else {
						// Redirect Invalid Session User to /auth Page
						localStorage.removeItem('token');
						await goto('/auth');
					}
				} else {
					// Don't redirect if we're already on the auth page
					// Needed because we pass in tokens from OAuth logins via URL fragments
					if ($page.url.pathname !== '/auth') {
						await goto('/auth');
					}
				}
			}
		} else {
			// Redirect to /error when Backend Not Detected
			await goto(`/error`);
		}

		await tick();

		if (document.documentElement.classList.contains('her') && document.getElementById('progress-bar')) {
			loadingProgress.subscribe((value) => {
				const progressBar = document.getElementById('progress-bar');

				if (progressBar) {
					progressBar.style.width = `${value}%`;
				}
			});

			await loadingProgress.set(100);

			document.getElementById('splash-screen')?.remove();

			const audio = new Audio(`/audio/greeting.mp3`);
			const playAudio = () => {
				audio.play();
				document.removeEventListener('click', playAudio);
			};

			document.addEventListener('click', playAudio);

			loaded = true;
		} else {
			document.getElementById('splash-screen')?.remove();
			loaded = true;
		}

		return () => {
			window.removeEventListener('resize', onResize);
		};
	});
</script>

<svelte:head>
	<title>{$WEBUI_NAME}</title>
	<link crossorigin="anonymous" rel="icon" href="{WEBUI_BASE_URL}/static/favicon.png" />
</svelte:head>

{#if loaded}
	<slot />
{/if}

<Toaster richColors position="top-center" />
