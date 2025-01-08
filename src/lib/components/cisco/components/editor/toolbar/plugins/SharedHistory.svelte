<script>
	import { getHistoryStateContext } from '$lib/utils/editor';
	import History from './History.svelte';
</script>

<History externalHistoryState={getHistoryStateContext()} />
