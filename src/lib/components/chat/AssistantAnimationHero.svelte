<script lang="ts">
	import { cubicInOut } from 'svelte/easing';
	import { tweened } from 'svelte/motion';
	import { scale } from 'svelte/transition';
	import { onMount } from 'svelte';

	let lensRotation = tweened(0, {
		duration: 2000,
		easing: cubicInOut
	});
	let isLoading = true;

	onMount(() => {
		const loopAnimation = () => {
			lensRotation.set(360, { duration: 2500 }).then(() => {
				lensRotation.set(0, { duration: 0 });
				loopAnimation();
			});
		};

		loopAnimation();
	});
</script>

<div class="my-2 flex justify-end">
	<div class="self-center overflow-visible">
		<svg
			width="200"
			height="200"
			viewBox="0 0 200 200"
			fill="none"
			xmlns="http://www.w3.org/2000/svg"
			style="overflow: visible;"
		>
			{#if isLoading}
				<path
					d="M146.88 112.5C172.768 112.5 193.755 91.5134 193.755 65.625C193.755 39.7366 172.768 18.75 146.88 18.75C120.992 18.75 100.005 39.7367 100.005 65.625C100.005 91.5133 120.992 112.5 146.88 112.5Z"
					fill="url(#paint0_linear_143_1711)"
					id="greenHighlight"
					class="lens"
					style="transform-origin: center; transform: rotate({$lensRotation}deg);"
					in:scale={{ delay: 0, duration: 500, easing: cubicInOut, start: 0.5 }}
				/>
				<path
					fill-rule="evenodd"
					clip-rule="evenodd"
					d="M100.005 52.6417C73.829 52.6417 52.6092 73.8555 52.6092 100.024C52.6092 126.192 73.829 147.406 100.005 147.406C126.181 147.406 147.401 126.192 147.401 100.024C147.401 73.8555 126.181 52.6417 100.005 52.6417ZM18.755 100.024C18.755 55.1637 55.1319 18.7973 100.005 18.7973C144.878 18.7973 181.255 55.1637 181.255 100.024C181.255 144.884 144.878 181.251 100.005 181.251C55.1319 181.251 18.755 144.884 18.755 100.024Z"
					fill="url(#paint1_linear_143_1711)"
					id="bigCircle"
				/>
				<path
					fill-rule="evenodd"
					clip-rule="evenodd"
					d="M181.212 97.532C172.656 106.711 160.457 112.451 146.918 112.451C146.527 112.451 146.137 112.446 145.748 112.437C146.827 108.466 147.404 104.288 147.404 99.975C147.404 74.4205 127.173 53.591 101.854 52.6277C105.577 39.6475 114.757 28.9742 126.751 23.2491C157.75 34.0471 180.195 63.1 181.212 97.532Z"
					fill="url(#paint2_linear_143_1711)"
					id="lensTrack"
					class="lens"
					style="transform-origin: center; transform: rotate({$lensRotation}deg);"
					in:scale={{ delay: 250, duration: 500, easing: cubicInOut, start: 0.5 }}
				/>
				<path
					d="M146.856 112.5C172.744 112.5 193.731 91.5134 193.731 65.625C193.731 39.7366 172.744 18.75 146.856 18.75C120.967 18.75 99.9806 39.7367 99.9806 65.625C99.9806 91.5133 120.967 112.5 146.856 112.5Z"
					fill="url(#paint3_radial_143_1711)"
					id="lens"
					class="lens"
					style="transform-origin: center; transform: rotate({$lensRotation}deg);"
					in:scale={{ delay: 500, duration: 500, easing: cubicInOut, start: 0.5 }}
				/>
			{/if}
			<style>
				.lens {
					transform-origin: center;
					transform: rotate($lensRotation);
				}
			</style>
			<defs>
				<linearGradient
					id="paint0_linear_143_1711"
					x1="101.864"
					y1="18.75"
					x2="178.624"
					y2="95.5095"
					gradientUnits="userSpaceOnUse"
				>
					<stop stop-color="#0087EA" />
					<stop offset="1" stop-color="#63FFF7" />
				</linearGradient>
				<linearGradient
					id="paint1_linear_143_1711"
					x1="181.255"
					y1="18.7973"
					x2="18.8017"
					y2="181.297"
					gradientUnits="userSpaceOnUse"
				>
					<stop stop-color="#0051AF" />
					<stop offset="0.666238" stop-color="#0087EA" />
					<stop offset="1" stop-color="#00BCEB" />
				</linearGradient>
				<linearGradient
					id="paint2_linear_143_1711"
					x1="130.914"
					y1="49.9375"
					x2="174.369"
					y2="100.198"
					gradientUnits="userSpaceOnUse"
				>
					<stop stop-color="#74BF4B" stop-opacity="0" />
					<stop offset="1" stop-color="#74BF4B" />
				</linearGradient>
				<radialGradient
					id="paint3_radial_143_1711"
					cx="0"
					cy="0"
					r="1"
					gradientUnits="userSpaceOnUse"
					gradientTransform="translate(193.731 112.5) rotate(-135) scale(132.583 132.527)"
				>
					<stop stop-color="#00BCEB" stop-opacity="0" />
					<stop offset="0.666962" stop-color="#00BCEB" stop-opacity="0" />
					<stop offset="1" stop-color="#00BCEB" />
				</radialGradient>
			</defs>
		</svg>
	</div>
</div>
