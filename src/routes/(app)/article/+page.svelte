<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { activeArticle } from '$lib/stores';
	import { getArticleById } from '$lib/apis/articles';
	import Article from '$lib/components/cisco/components/articles/Article.svelte';
	import GetSupportWidgetContainer from '$lib/components/cisco/components/articles/GetSupportWidgetContainer.svelte';
	import { IsSupportingArticle } from '$lib/stores';
	import type { Article as _Article } from '$lib/types';

	let articleId = '019d2492-ec50-46f6-ae64-f06423ca7452';
	onMount(async () => {
		window.history.replaceState({}, '', `/article/${articleId}`);
		activeArticle.set(await getArticleById(localStorage.token, articleId));
		// await goto(`/article/${articleId}`);
	});

	// const a: _Article = {
	// 	id: '56d0fbc3-a03d-47cd-b187-41aeb1da7264',
	// 	title: 'Day Zero Setup of Catalyst 1200 and 1300 Switches Using the CLI',
	// 	document_id: '1690576040004942',
	// 	objective:
	// 		'The objective of this article is to go through the day zero setup of a Catalyst 1200 or 1300 switch using the command line interface (CLI).',
	// 	category: 'Install & Upgrade',
	// 	url: 'http://www.cisco.com/c/en/us/support/docs/smb/switches/Catalyst-switches/kmgmt3582-day-zero-setup-catalyst-1200-1300-switches-using-cli.html',
	// 	applicable_devices: [
	// 		{
	// 			device: 'Catalyst 1200',
	// 			software: '4.0.0.91',
	// 			datasheet_link:
	// 				'https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1200-series-switches/nb-06-cat1200-ser-data-sheet-cte-en.html',
	// 			software_link: null
	// 		},
	// 		{
	// 			device: 'Catalyst 1300',
	// 			software: '4.0.0.91',
	// 			datasheet_link:
	// 				'https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1300-series-switches/nb-06-cat1300-ser-data-sheet-cte-en.html',
	// 			software_link: null
	// 		}
	// 	],
	// 	introduction:
	// 		'Are you looking for an affordable and easy to deploy switch for your small or medium-sized business? The Cisco Catalyst 1200 and 1300 switches fit the bill that also provide advanced switching capabilities, enhanced security, and can be easily managed using the Cisco Business Dashboard or the Cisco Business mobile App. Check out the following pages for more information on the Catalyst 1200 and 1300 switches. <ul> <li> <a href="https:/www.cisco.com/c/en/us/products/collateral/switches/catalyst-1200-series-switches/nb-06-cat1200-1300-ser-upgrade-cte-en.html"> Why Upgrade to Cisco Catalyst 1200 or 1300 Series Switches Feature Comparison </a> </li> <li> <a href="https:/www.cisco.com/c/en/us/products/collateral/switches/catalyst-1200-series-switches/nb-06-cat1200-1300-ser-aag-cte-en.html"> Cisco Catalyst 1200 and 1300 Series Switches At-a-Glance </a> </li> </ul> You can also refer to the following hardware installation guides to get started. <ul> <li> <a href="https:/hig-catalyst-1200.cisco.com/"> Cisco Catalyst 1200 Hardware Installation Guide </a> </li> <li> <a href="https:/hig-catalyst-1300.cisco.com/"> Cisco Catalyst 1300 Hardware Installation Guide </a> </li> </ul> Let’s begin with the day zero setup of a Catalyst 1200 or 1300 switch using the CLI.',
	// 	steps: [
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 1,
	// 			text: 'In this example, a Catalyst 1300 switch is used. Connect to the switch via a console cable.',
	// 			src: 'https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3582-day-zero-setup-catalyst-1200-1300-switches-using-cli-image-1.png',
	// 			alt: 'Related diagram, image, or screenshot',
	// 			note: null,
	// 			emphasized_text: [],
	// 			emphasized_tags: []
	// 		},
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 2,
	// 			text: 'Press Enter twice on the keyboard to complete the console baud-rate auto detection process. This is necessary to identify the speed of console connection and to send data at the proper rate.',
	// 			src: 'https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3582-day-zero-setup-catalyst-1200-1300-switches-using-cli-image-1.png',
	// 			alt: 'Related diagram, image, or screenshot',
	// 			note: null,
	// 			emphasized_text: ['Enter'],
	// 			emphasized_tags: ['strong']
	// 		},
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 3,
	// 			text: 'Enter the default username. As this is a day zero setup, it is cisco .<div class="kbd-cdt" data-label="Click to copy command"> <p> <samp> User Name : </samp> <code class="cCN_CmdName"> <strong> cisco </strong> </code> </p> </div>',
	// 			src: 'https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3582-day-zero-setup-catalyst-1200-1300-switches-using-cli-image-2.png',
	// 			alt: 'Related diagram, image, or screenshot',
	// 			note: 'cisco is all lowercase letters.',
	// 			emphasized_text: [],
	// 			emphasized_tags: []
	// 		},
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 4,
	// 			text: 'Enter the default password which is also cisco .<div class="kbd-cdt" data-label="Click to copy command"> <p> <samp> Password: </samp> <code class="cCN_CmdName"> <strong> cisco </strong> </code> </p> </div>',
	// 			src: 'https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3582-day-zero-setup-catalyst-1200-1300-switches-using-cli-image-2.png',
	// 			alt: 'Related diagram, image, or screenshot',
	// 			note: null,
	// 			emphasized_text: [],
	// 			emphasized_tags: []
	// 		},
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 5,
	// 			text: 'You will be prompted to enter a new username. In this example, it is admin .<div class="kbd-cdt" data-label="Click to copy command"> <p> <samp> Enter new username: </samp> <code class="cCN_CmdName"> <strong> admin </strong> </code> </p> </div>',
	// 			src: 'https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3582-day-zero-setup-catalyst-1200-1300-switches-using-cli-image-2.png',
	// 			alt: 'Related diagram, image, or screenshot',
	// 			note: null,
	// 			emphasized_text: [],
	// 			emphasized_tags: []
	// 		},
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 6,
	// 			text: 'Enter a new password. The password must meet the standard requirements. <ul> <li> The password must be at least eight characters and must contain three of the four following options: uppercase, lowercase, a number, or a special character. </li> <li> A character cannot be repeated more than three times in a row. </li> <li> It cannot have more than two sequential characters or numbers in a row and the characters are case insensitive. </li> <li> You cannot use the username as the password or the reversed or modified form of the username. </li> <li> "Cisco" or variations of the word "Cisco" cannot be used in any part of the password (beginning, middle or end). </li> <li> Well-known usernames and passwords will not be accepted. </li> <li> The word “password" cannot be used as the beginning of your password and it is case insensitive. </li> <li> The word “Catalyst” cannot be any part of the password. </li> <li> Using more than three repeated characters in a row is not allowed. For example, 111 will not be accepted. </li> <li> Using more than two sequential characters in a row like 123 will not be allowed. </li> </ul>',
	// 			src: 'https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3582-day-zero-setup-catalyst-1200-1300-switches-using-cli-image-3.png',
	// 			alt: 'Related diagram, image, or screenshot',
	// 			note: 'If you enter a password that doesn’t comply with the rules like Cisco123, it’ll be rejected along with an explanation of why the password was rejected.',
	// 			emphasized_text: [],
	// 			emphasized_tags: []
	// 		},
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 7,
	// 			text: 'To set an IP address, enter config terminal and in this example, interface VLAN1 will be configured.<div class="kbd-cdt" data-label="Click to copy command"> <p> <samp> switch  </samp> <code class="cCN_CmdName"> <strong> config terminal </strong> </code> </p> </div><div class="kbd-cdt" data-label="Click to copy command"> <p> <samp> switch(config)   </samp> <code class="cCN_CmdName"> <strong> interface Vlan1 </strong> </code> </p> </div>',
	// 			src: null,
	// 			alt: null,
	// 			note: null,
	// 			emphasized_text: [],
	// 			emphasized_tags: []
	// 		},
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 8,
	// 			text: 'Enter the command ip address followed by the IP and the subnet mask. In this example, it’s 172.16.1.11 with a subnet mask of 255.255.255.0.<div class="kbd-cdt" data-label="Click to copy command"> <p> <samp> switch (config-if)   </samp> <code class="cCN_CmdName"> <strong> ip address 172.16.1.111 255.255.255.0 </strong> </code> </p> </div>',
	// 			src: null,
	// 			alt: null,
	// 			note: null,
	// 			emphasized_text: [],
	// 			emphasized_tags: []
	// 		},
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 9,
	// 			text: 'Specify the ip route. In this example, it’s going to be the default gateway of 0.0.0.0 as the destination prefix, with 0.0.0.0 as the network mask followed by the IP address of the network.<div class="kbd-cdt" data-label="Click to copy command"> <p> <samp> switch (config)   </samp> <code class="cCN_CmdName"> <strong> ip route 0.0.0.0 0.0.0.0 172.16.1.60 </strong> </code> </p> </div>',
	// 			src: null,
	// 			alt: null,
	// 			note: null,
	// 			emphasized_text: [],
	// 			emphasized_tags: []
	// 		},
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 10,
	// 			text: 'To enable SSH clients, type ip ssh-client authentication password that allows the use of usernames and password to authenticate via SSH.<div class="kbd-cdt" data-label="Click to copy command"> <p> <samp> switch(config)   </samp> <code class="cCN_CmdName"> <strong> ip ssh-client authentication password </strong> </code> </p> </div>',
	// 			src: null,
	// 			alt: null,
	// 			note: null,
	// 			emphasized_text: [],
	// 			emphasized_tags: []
	// 		},
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 11,
	// 			text: 'Exit the configuration mode to get back to the privileged execution mode.<div class="kbd-cdt" data-label="Click to copy command"> <p> <samp> switch (config)   </samp> <code class="cCN_CmdName"> <strong> exit </strong> </code> </p> </div>',
	// 			src: null,
	// 			alt: null,
	// 			note: null,
	// 			emphasized_text: [],
	// 			emphasized_tags: []
	// 		},
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 12,
	// 			text: 'Enter write memory to save the configuration.<div class="kbd-cdt" data-label="Click to copy command"> <p> <samp> switch  </samp> <code class="cCN_CmdName"> <strong> write memory </strong> </code> </p> </div>',
	// 			src: null,
	// 			alt: null,
	// 			note: null,
	// 			emphasized_text: [],
	// 			emphasized_tags: []
	// 		},
	// 		{
	// 			section: 'Day zero setup',
	// 			step_number: 13,
	// 			text: 'Enter Y to confirm.<div class="kbd-cdt" data-label="Click to copy command"> <p> <samp> Overwrite file [startup-config]. (Y/N) [N] ? </samp> <code class="cCN_CmdName"> <strong> Y </strong> </code> </p> </div>',
	// 			src: null,
	// 			alt: null,
	// 			note: null,
	// 			emphasized_text: [],
	// 			emphasized_tags: []
	// 		}
	// 	],
	// 	created_at: 1727707869,
	// 	updated_at: 1727707869
	// };
</script>

{#if $IsSupportingArticle}
	<Article>
		<GetSupportWidgetContainer />
	</Article>
{/if}
