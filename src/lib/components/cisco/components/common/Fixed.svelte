<script lang="ts">
	import { fade } from 'svelte/transition';
	import { cubicIn } from 'svelte/easing';
	import { createEventDispatcher } from 'svelte';
	import { ExpGradeSelected, isSupportWidgetOpen, activeSupportSection, hideSupportWidgetBtn } from '$lib/stores';

	$: currentSection = $activeSupportSection;

	const dispatch = createEventDispatcher();

	function handleClickThenDispatch() {
		$isSupportWidgetOpen = !$isSupportWidgetOpen;
		console.log($isSupportWidgetOpen);
	}

	const modalityButtons = [
		{
			name: 'Fully Guided',
			svg: `<svg
			width="45"
			height="45"
			style="margin: 0"
			viewBox="0 0 45 45"
			fill="none"
			xmlns="http://www.w3.org/2000/svg"
		>
			<path
				d="M28.544 5.3132C28.4954 5.24783 28.4322 5.19473 28.3594 5.15815C28.2866 5.12158 28.2063 5.10253 28.1248 5.10254H16.8748C16.7652 5.10254 16.6583 5.13706 16.5694 5.20119C16.4805 5.26533 16.414 5.35583 16.3794 5.45987L10.7544 22.3349C10.7282 22.4134 10.721 22.497 10.7335 22.5788C10.746 22.6606 10.7777 22.7383 10.8261 22.8054C10.8745 22.8726 10.9382 22.9273 11.0118 22.965C11.0855 23.0027 11.1671 23.0223 11.2498 23.0223H19.6126L16.3626 39.2725C16.3394 39.3886 16.3563 39.5091 16.4105 39.6143C16.4647 39.7195 16.5531 39.8032 16.6611 39.8516C16.7691 39.9001 16.8904 39.9104 17.005 39.8808C17.1197 39.8513 17.2209 39.7837 17.2921 39.6891L34.1671 17.2921C34.2252 17.215 34.2608 17.1232 34.2699 17.0271C34.279 16.9309 34.2613 16.8341 34.2187 16.7474C34.176 16.6607 34.1102 16.5876 34.0285 16.536C33.9468 16.4845 33.8525 16.4566 33.7559 16.4555L25.4494 16.3605L28.6253 5.77518C28.6486 5.69716 28.6534 5.61477 28.6393 5.53457C28.6252 5.45436 28.5926 5.37856 28.544 5.3132ZM24.2494 16.7247C24.2262 16.8022 24.2213 16.8841 24.2351 16.9638C24.2489 17.0436 24.281 17.1191 24.3289 17.1843C24.3769 17.2495 24.4393 17.3027 24.5113 17.3397C24.5833 17.3766 24.6629 17.3964 24.7438 17.3973L32.7111 17.4885L17.8364 37.2307L20.7621 22.6024C20.7773 22.5266 20.7754 22.4484 20.7567 22.3734C20.738 22.2984 20.7029 22.2285 20.6539 22.1687C20.6049 22.1089 20.5432 22.0608 20.4733 22.0277C20.4035 21.9947 20.3271 21.9775 20.2498 21.9775H11.9747L17.2514 6.14734H27.4228L24.2494 16.7247Z"
				fill="white"
			/>
		</svg>`,
			className: 'modeIconFullyGuided'
		},
		{
			name: 'Lightly Guided',
			svg: `<svg
			width="45"
			height="45"
			style="margin: 0"
			viewBox="0 0 45 45"
			fill="#00549e"
			xmlns="http://www.w3.org/2000/svg"
		>
			<path
				d="M12.375 22.9218H14.1306L14.1515 30.3763C14.1518 30.5016 14.2019 30.6217 14.2906 30.7102C14.3794 30.7987 14.4996 30.8484 14.625 30.8484H31.4675C31.4786 30.8487 31.4889 30.8517 31.5 30.8517C31.9247 30.8512 32.3318 30.6823 32.6321 30.382C32.9324 30.0817 33.1013 29.6746 33.1018 29.2499V22.8976C34.9581 22.7748 36.694 21.9352 37.9425 20.5561C39.1911 19.1769 39.8545 17.3664 39.7926 15.5071C39.7307 13.6477 38.9483 11.8853 37.6107 10.5923C36.2732 9.2993 34.4853 8.57698 32.625 8.578H12.772C12.7227 8.14049 12.5969 7.71504 12.4004 7.32103L14.0966 5.62488L13.5 5.02832L11.9345 6.59388C11.3788 5.9165 10.606 5.45218 9.74706 5.27968C8.88812 5.10718 7.99595 5.23712 7.22189 5.64747C6.44784 6.05781 5.83956 6.72329 5.50025 7.53101C5.16095 8.33873 5.1115 9.23896 5.3603 10.079C5.6091 10.919 6.14082 11.6471 6.86528 12.1398C7.58973 12.6324 8.4623 12.8593 9.33498 12.7819C10.2076 12.7045 11.0267 12.3276 11.6531 11.7152C12.2796 11.1028 12.6749 10.2925 12.772 9.42176H32.625C34.2617 9.42099 35.8349 10.0547 37.0141 11.1897C38.1933 12.3247 38.8866 13.8726 38.9484 15.5081C39.0101 17.1436 38.4355 18.7394 37.3452 19.96C36.2549 21.1807 34.7339 21.9312 33.1018 22.0538V14.6249C33.1018 14.5623 33.0895 14.5002 33.0656 14.4424C33.0416 14.3845 33.0065 14.3319 32.9622 14.2877C32.9179 14.2434 32.8654 14.2082 32.8075 14.1843C32.7496 14.1603 32.6876 14.148 32.625 14.1481H15.9181C15.8555 14.148 15.7934 14.1603 15.7356 14.1843C15.6777 14.2082 15.6251 14.2434 15.5809 14.2877C15.5366 14.3319 15.5015 14.3845 15.4775 14.4424C15.4536 14.5002 15.4412 14.5623 15.4413 14.6249V16.3662L14.5882 16.3643H14.5871C14.5248 16.3642 14.463 16.3765 14.4055 16.4004C14.3479 16.4242 14.2956 16.4592 14.2516 16.5033C14.2076 16.5475 14.1728 16.5999 14.1491 16.6575C14.1254 16.7151 14.1133 16.7769 14.1136 16.8392L14.1283 22.078H12.375C10.4729 22.078 8.64871 22.8336 7.30372 24.1786C5.95873 25.5236 5.20313 27.3478 5.20312 29.2499C5.20313 31.152 5.95873 32.9762 7.30372 34.3212C8.64871 35.6662 10.4729 36.4218 12.375 36.4218H32.228C32.3358 37.3862 32.8088 38.2727 33.5498 38.8993C34.2909 39.5258 35.2437 39.8449 36.2126 39.7909C37.1815 39.7369 38.093 39.3139 38.7598 38.6089C39.4267 37.9039 39.7982 36.9703 39.7982 35.9999C39.7982 35.0295 39.4267 34.0959 38.7598 33.3908C38.093 32.6858 37.1815 32.2629 36.2126 32.2089C35.2437 32.1549 34.2909 32.4739 33.5498 33.1005C32.8088 33.7271 32.3358 34.6136 32.228 35.578H12.375C10.6967 35.578 9.08709 34.9113 7.90034 33.7245C6.71359 32.5378 6.04688 30.9282 6.04688 29.2499C6.04688 27.5716 6.71359 25.962 7.90034 24.7752C9.08709 23.5885 10.6967 22.9218 12.375 22.9218ZM9 11.953C8.49727 11.9559 8.00213 11.8304 7.56147 11.5884C7.12081 11.3464 6.74923 10.9959 6.48192 10.5701C6.21461 10.1443 6.06043 9.65733 6.03397 9.15529C6.00752 8.65325 6.10966 8.15277 6.33074 7.70124C6.55181 7.24972 6.8845 6.86211 7.29728 6.57513C7.71006 6.28815 8.18927 6.1113 8.68951 6.06133C9.18976 6.01136 9.69449 6.08992 10.1559 6.28958C10.6173 6.48923 11.0201 6.80337 11.3261 7.20224L9 9.52832L7.875 8.40332L7.27844 8.99988L8.70172 10.4232C8.74089 10.4623 8.78739 10.4934 8.83856 10.5146C8.88974 10.5358 8.9446 10.5468 9 10.5468C9.0554 10.5468 9.11026 10.5358 9.16144 10.5146C9.21262 10.4934 9.25911 10.4623 9.29828 10.4232L11.7561 7.96538C11.8839 8.29543 11.9506 8.64596 11.9531 8.99988C11.9522 9.78282 11.6408 10.5334 11.0872 11.0871C10.5336 11.6407 9.78294 11.9521 9 11.953ZM16.3949 15.1017H32.1482V29.2499C32.1482 29.4218 32.0799 29.5867 31.9583 29.7082C31.8368 29.8298 31.6719 29.8981 31.5 29.8981C31.3281 29.8981 31.1632 29.8298 31.0417 29.7082C30.9201 29.5867 30.8518 29.4218 30.8518 29.2499V28.1249H30.8485V16.8749C30.8485 16.7495 30.7987 16.6293 30.7102 16.5405C30.6216 16.4517 30.5015 16.4017 30.3761 16.4014L16.3949 16.3685V15.1017ZM29.9015 17.3473V28.1249H29.8982V29.2499C29.8988 29.4746 29.947 29.6967 30.0398 29.9014H15.0974L15.0617 17.3124L29.9015 17.3473ZM36 33.0468C36.5841 33.0468 37.155 33.22 37.6407 33.5444C38.1263 33.8689 38.5048 34.3302 38.7283 34.8698C38.9518 35.4094 39.0103 36.0032 38.8964 36.576C38.7824 37.1489 38.5012 37.6751 38.0882 38.0881C37.6752 38.5011 37.149 38.7823 36.5761 38.8963C36.0033 39.0102 35.4095 38.9517 34.8699 38.7282C34.3303 38.5047 33.8691 38.1262 33.5446 37.6406C33.2201 37.1549 33.0469 36.584 33.0469 35.9999C33.0478 35.2169 33.3592 34.4663 33.9128 33.9127C34.4664 33.3591 35.2171 33.0477 36 33.0468Z"
				fill="#00549e"
			/>
			<path d="M28.125 19.7729H16.875V20.7266H28.125V19.7729Z" fill="white" />
			<path d="M28.125 23.1479H16.875V24.1016H28.125V23.1479Z" fill="white" />
			<path d="M24.75 26.5229H16.875V27.4766H24.75V26.5229Z" fill="white" />
		</svg>`,
			className: 'modeIconLightlyGuided'
		}
	];

	function handleClick() {
		console.log('Modality Btn Clicked!');
		$ExpGradeSelected = $ExpGradeSelected === 'Fully Guided' ? 'Lightly Guided' : 'Fully Guided';
		console.log($ExpGradeSelected);
	}
</script>

{#if !$hideSupportWidgetBtn}
	<div id="buttonContainer">
		<div>
			<button class="button support text-base" id="getSupportBtn" on:click={handleClickThenDispatch}
				><span id="stepNumberBreadcrumb">?</span> Get Support {currentSection}</button
			>
		</div>
		{#each modalityButtons as btn}
			<div>
				{#if btn.name === $ExpGradeSelected}
					<button class="button text-base rounded-md cursor-pointer" id="toggleBtn" on:click={handleClick}>
						<div
							class:hide={$ExpGradeSelected !== btn.name}
							class={btn.className}
							in:fade={{ duration: 1000, easing: cubicIn }}
						>
							{@html btn.svg}
							<span>{btn.name}</span>
						</div>
					</button>
				{/if}
			</div>
		{/each}
	</div>
{/if}

<style>
	#buttonContainer {
		position: fixed;
		right: 0;
		bottom: 0;
		display: grid;
		grid-template-columns: 1fr;
		z-index: 1000;
		min-width: 400px;
		margin: 0.5em;
		justify-items: end;
		transition: width 0.3s ease-in-out;
	}

	.button {
		background: #00549e;
		color: whitesmoke;
		text-decoration: none;
		transition: all 0.3s ease-in-out;
	}

	.button:hover {
		background-color: rgba(155, 215, 255, 0.5);
		color: #00549e;
		border-radius: 12px;
	}
	#toggleBtn {
		width: fit-content;
		align-items: end;
		border: #00549e 1px solid;
		margin: 1em 0 0 0;
	}

	.modeIconFullyGuided,
	.modeIconLightlyGuided {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		gap: 1em;
		padding: 0 0.5em;
	}

	.button.support {
		background: whitesmoke;
		color: #888;
		border: 1px solid #888;
		border-radius: 12px;
		text-decoration: none;
		transition: all 0.3s ease-in-out;
		padding: 0.5rem 1rem;
		cursor: pointer;
	}

	#stepNumberBreadcrumb {
		display: inline-block;
		text-align: center;
		line-height: 1.75em;
		font-weight: bold;
		font-size: 1.25em;
		width: 1.75em;
		height: 1.75em;
		color: #888;
		border-radius: 25px;
		/* aspect-ratio: 1/1; */
		margin-right: 0.5em;
		transition: all 0.3s ease-in-out;
	}

	.button.support:hover,
	.button.support:hover > span {
		background: #d0e0f8;
		color: #00549e !important;
		border: #d0e0f8 1px solid !important;
		border-radius: 12px;
	}
</style>
