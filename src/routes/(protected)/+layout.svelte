<script lang="ts">
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { getContext } from 'svelte';
	const i18n: Writable<i18nType> = getContext('i18n');
</script>

<div class="protected relative">
	<slot />
</div>
