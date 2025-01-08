<script lang="ts">
	import type { BlockType } from '$lib/types';
	import { type SvelteComponent, afterUpdate, onMount } from 'svelte';
	import { KeywordPlugin } from 'svelte-lexical';
	import { HorizontalRuleNode } from '$lib/components/cisco/components/editor/toolbar/plugins/hr/HorizontalRuleNode';
	import { ImageNode } from '$lib/components/cisco/components/editor/toolbar/plugins/image/ImageNode';
	import { settings } from '$lib/stores';
	import { CAN_USE_DOM, KeywordNode, validateUrl } from '$lib/utils/editor';
	import { createWebsocketProvider } from '$lib/utils/editor/collaboration';
	import { CodeHighlightNode, CodeNode } from '@lexical/code';
	import { $generateHtmlFromNodes as generateHtmlFromNodes } from '@lexical/html';
	import { AutoLinkNode, LinkNode } from '@lexical/link';
	import { ListItemNode, ListNode } from '@lexical/list';
	import { HeadingNode, QuoteNode, $createHeadingNode as createHeadingNode } from '@lexical/rich-text';
	import {
		type CreateEditorArgs,
		type EditorState,
		type LexicalEditor,
		type LexicalNode,
		ParagraphNode,
		TextNode,
		createEditor,
		$createParagraphNode as createParagraphNode,
		$createTextNode as createTextNode,
		$getRoot as getRoot
	} from 'lexical';
	import Composer from './Composer.svelte';
	import ContentEditable from './ContentEditable.svelte';
	import PlaceHolder from './common/Placeholder.svelte';
	import RichTextToolbar from './toolbar/RichTextToolbar.svelte';
	import ActionBar from './toolbar/buttons/ActionBar.svelte';
	import AutoFocus from './toolbar/plugins/AutoFocus.svelte';
	import CheckList from './toolbar/plugins/CheckList.svelte';
	import SharedHistoryPlugin from './toolbar/plugins/History.svelte';
	import List from './toolbar/plugins/List.svelte';
	import RichText from './toolbar/plugins/RichText.svelte';
	import AutoLink from './toolbar/plugins/autolink/AutoLink.svelte';
	import CodeHighlight from './toolbar/plugins/code/CodeHighlight.svelte';
	import CollaborationPlugin from './toolbar/plugins/collaboration/CollaborationPlugin.svelte';
	import ColumnLayoutPlugin from './toolbar/plugins/columns/ColumnLayoutPlugin.svelte';
	import HorizontalRulePlugin from './toolbar/plugins/hr/HorizontalRulePlugin.svelte';
	import CaptionEditorCollaborationPlugin from './toolbar/plugins/image/CaptionEditorCollaborationPlugin.svelte';
	import CaptionEditorHistoryPlugin from './toolbar/plugins/image/CaptionEditorHistoryPlugin.svelte';
	import ImagePlugin from './toolbar/plugins/image/ImagePlugin.svelte';
	import FloatingLinkCapturePlugin from './toolbar/plugins/link/FloatingLinkCapturePlugin.svelte';
	import Link from './toolbar/plugins/link/Link.svelte';
	import { LayoutContainerNode } from './toolbar/plugins/columns/LayoutContainerNode';
	import { LayoutItemNode } from './toolbar/plugins/columns/LayoutItemNode';

	export let config: CreateEditorArgs;
	export let content: string | null = null;
	export let tag: BlockType = 'h1';
	export let section: string | null = null;
	export let articleTitle: string = '';

	let composer: SvelteComponent;
	let editorDiv: HTMLDivElement;

	const shouldBootstrap = window.parent != null && window.parent.frames.right === window;
	const keywordsRegex =
		/(^|$|[^A-Za-zªµºÀ-ÖØ-öø-ˁˆ-ˑˠ-ˤˬˮͰ-ʹͶͷͺ-ͽΆΈ-ΊΌΎ-ΡΣ-ϵϷ-ҁҊ-ԧԱ-Ֆՙա-ևא-תװ-ײؠ-يٮٯٱ-ۓەۥۦۮۯۺ-ۼۿܐܒ-ܯݍ-ޥޱߊ-ߪߴߵߺࠀ-ࠕࠚࠤࠨࡀ-ࡘࢠࢢ-ࢬऄ-हऽॐक़-ॡॱ-ॷॹ-ॿঅ-ঌএঐও-নপ-রলশ-হঽৎড়ঢ়য়-ৡৰৱਅ-ਊਏਐਓ-ਨਪ-ਰਲਲ਼ਵਸ਼ਸਹਖ਼-ੜਫ਼ੲ-ੴઅ-ઍએ-ઑઓ-નપ-રલળવ-હઽૐૠૡଅ-ଌଏଐଓ-ନପ-ରଲଳଵ-ହଽଡ଼ଢ଼ୟ-ୡୱஃஅ-ஊஎ-ஐஒ-கஙசஜஞடணதந-பம-ஹௐఅ-ఌఎ-ఐఒ-నప-ళవ-హఽౘౙౠౡಅ-ಌಎ-ಐಒ-ನಪ-ಳವ-ಹಽೞೠೡೱೲഅ-ഌഎ-ഐഒ-ഺഽൎൠൡൺ-ൿඅ-ඖක-නඳ-රලව-ෆก-ะาำเ-ๆກຂຄງຈຊຍດ-ທນ-ຟມ-ຣລວສຫອ-ະາຳຽເ-ໄໆໜ-ໟༀཀ-ཇཉ-ཬྈ-ྌက-ဪဿၐ-ၕၚ-ၝၡၥၦၮ-ၰၵ-ႁႎႠ-ჅჇჍა-ჺჼ-ቈቊ-ቍቐ-ቖቘቚ-ቝበ-ኈኊ-ኍነ-ኰኲ-ኵኸ-ኾዀዂ-ዅወ-ዖዘ-ጐጒ-ጕጘ-ፚᎀ-ᎏᎠ-Ᏼᐁ-ᙬᙯ-ᙿᚁ-ᚚᚠ-ᛪᜀ-ᜌᜎ-ᜑᜠ-ᜱᝀ-ᝑᝠ-ᝬᝮ-ᝰក-ឳៗៜᠠ-ᡷᢀ-ᢨᢪᢰ-ᣵᤀ-ᤜᥐ-ᥭᥰ-ᥴᦀ-ᦫᧁ-ᧇᨀ-ᨖᨠ-ᩔᪧᬅ-ᬳᭅ-ᭋᮃ-ᮠᮮᮯᮺ-ᯥᰀ-ᰣᱍ-ᱏᱚ-ᱽᳩ-ᳬᳮ-ᳱᳵᳶᴀ-ᶿḀ-ἕἘ-Ἕἠ-ὅὈ-Ὅὐ-ὗὙὛὝὟ-ώᾀ-ᾴᾶ-ᾼιῂ-ῄῆ-ῌῐ-ΐῖ-Ίῠ-Ῥῲ-ῴῶ-ῼⁱⁿₐ-ₜℂℇℊ-ℓℕℙ-ℝℤΩℨK-ℭℯ-ℹℼ-ℿⅅ-ⅉⅎↃↄⰀ-Ⱞⰰ-ⱞⱠ-ⳤⳫ-ⳮⳲⳳⴀ-ⴥⴧⴭⴰ-ⵧⵯⶀ-ⶖⶠ-ⶦⶨ-ⶮⶰ-ⶶⶸ-ⶾⷀ-ⷆⷈ-ⷎⷐ-ⷖⷘ-ⷞⸯ々〆〱-〵〻〼ぁ-ゖゝ-ゟァ-ヺー-ヿㄅ-ㄭㄱ-ㆎㆠ-ㆺㇰ-ㇿ㐀-䶵一-鿌ꀀ-ꒌꓐ-ꓽꔀ-ꘌꘐ-ꘟꘪꘫꙀ-ꙮꙿ-ꚗꚠ-ꛥꜗ-ꜟꜢ-ꞈꞋ-ꞎꞐ-ꞓꞠ-Ɦꟸ-ꠁꠃ-ꠅꠇ-ꠊꠌ-ꠢꡀ-ꡳꢂ-ꢳꣲ-ꣷꣻꤊ-ꤥꤰ-ꥆꥠ-ꥼꦄ-ꦲꧏꨀ-ꨨꩀ-ꩂꩄ-ꩋꩠ-ꩶꩺꪀ-ꪯꪱꪵꪶꪹ-ꪽꫀꫂꫛ-ꫝꫠ-ꫪꫲ-ꫴꬁ-ꬆꬉ-ꬎꬑ-ꬖꬠ-ꬦꬨ-ꬮꯀ-ꯢ가-힣ힰ-ퟆퟋ-ퟻ豈-舘並-龎ﬀ-ﬆﬓ-ﬗיִײַ-ﬨשׁ-זּטּ-לּמּנּסּףּפּצּ-ﮱﯓ-ﴽﵐ-ﶏﶒ-ﷇﷰ-ﷻﹰ-ﹴﹶ-ﻼＡ-Ｚａ-ｚｦ-ﾾￂ-ￇￊ-ￏￒ-ￗￚ-ￜ])(congrats|congratulations|gratuluju|gratuluji|gratulujeme|blahopřeju|blahopřeji|blahopřejeme|Til lykke|Tillykke|Glückwunsch|Gratuliere|felicitaciones|enhorabuena|paljon onnea|onnittelut|Félicitations|gratula|gratulálok|gratulálunk|congratulazioni|complimenti|おめでとう|おめでとうございます|축하해|축하해요|gratulerer|Gefeliciteerd|gratulacje|Parabéns|parabéns|felicitações|felicitări|мои поздравления|поздравляем|поздравляю|gratulujem|blahoželám|ยินดีด้วย|ขอแสดงความยินดี|tebrikler|tebrik ederim|恭喜|祝贺你|恭喜你|恭喜|恭喜|baie geluk|veels geluk|অভিনন্দন|Čestitam|Čestitke|Čestitamo|Συγχαρητήρια|Μπράβο|અભિનંદન|badhai|बधाई|अभिनंदन|Честитам|Свака част|hongera|வாழ்த்துகள்|வாழ்த்துக்கள்|అభినందనలు|അഭിനന്ദനങ്ങൾ|Chúc mừng|מזל טוב|mazel tov|mazal tov)(^|$|[^A-Za-zªµºÀ-ÖØ-öø-ˁˆ-ˑˠ-ˤˬˮͰ-ʹͶͷͺ-ͽΆΈ-ΊΌΎ-ΡΣ-ϵϷ-ҁҊ-ԧԱ-Ֆՙա-ևא-תװ-ײؠ-يٮٯٱ-ۓەۥۦۮۯۺ-ۼۿܐܒ-ܯݍ-ޥޱߊ-ߪߴߵߺࠀ-ࠕࠚࠤࠨࡀ-ࡘࢠࢢ-ࢬऄ-हऽॐक़-ॡॱ-ॷॹ-ॿঅ-ঌএঐও-নপ-রলশ-হঽৎড়ঢ়য়-ৡৰৱਅ-ਊਏਐਓ-ਨਪ-ਰਲਲ਼ਵਸ਼ਸਹਖ਼-ੜਫ਼ੲ-ੴઅ-ઍએ-ઑઓ-નપ-રલળવ-હઽૐૠૡଅ-ଌଏଐଓ-ନପ-ରଲଳଵ-ହଽଡ଼ଢ଼ୟ-ୡୱஃஅ-ஊஎ-ஐஒ-கஙசஜஞடணதந-பம-ஹௐఅ-ఌఎ-ఐఒ-నప-ళవ-హఽౘౙౠౡಅ-ಌಎ-ಐಒ-ನಪ-ಳವ-ಹಽೞೠೡೱೲഅ-ഌഎ-ഐഒ-ഺഽൎൠൡൺ-ൿඅ-ඖක-නඳ-රලව-ෆก-ะาำเ-ๆກຂຄງຈຊຍດ-ທນ-ຟມ-ຣລວສຫອ-ະາຳຽເ-ໄໆໜ-ໟༀཀ-ཇཉ-ཬྈ-ྌက-ဪဿၐ-ၕၚ-ၝၡၥၦၮ-ၰၵ-ႁႎႠ-ჅჇჍა-ჺჼ-ቈቊ-ቍቐ-ቖቘቚ-ቝበ-ኈኊ-ኍነ-ኰኲ-ኵኸ-ኾዀዂ-ዅወ-ዖዘ-ጐጒ-ጕጘ-ፚᎀ-ᎏᎠ-Ᏼᐁ-ᙬᙯ-ᙿᚁ-ᚚᚠ-ᛪᜀ-ᜌᜎ-ᜑᜠ-ᜱᝀ-ᝑᝠ-ᝬᝮ-ᝰក-ឳៗៜᠠ-ᡷᢀ-ᢨᢪᢰ-ᣵᤀ-ᤜᥐ-ᥭᥰ-ᥴᦀ-ᦫᧁ-ᧇᨀ-ᨖᨠ-ᩔᪧᬅ-ᬳᭅ-ᭋᮃ-ᮠᮮᮯᮺ-ᯥᰀ-ᰣᱍ-ᱏᱚ-ᱽᳩ-ᳬᳮ-ᳱᳵᳶᴀ-ᶿḀ-ἕἘ-Ἕἠ-ὅὈ-Ὅὐ-ὗὙὛὝὟ-ώᾀ-ᾴᾶ-ᾼιῂ-ῄῆ-ῌῐ-ΐῖ-Ίῠ-Ῥῲ-ῴῶ-ῼⁱⁿₐ-ₜℂℇℊ-ℓℕℙ-ℝℤΩℨK-ℭℯ-ℹℼ-ℿⅅ-ⅉⅎↃↄⰀ-Ⱞⰰ-ⱞⱠ-ⳤⳫ-ⳮⳲⳳⴀ-ⴥⴧⴭⴰ-ⵧⵯⶀ-ⶖⶠ-ⶦⶨ-ⶮⶰ-ⶶⶸ-ⶾⷀ-ⷆⷈ-ⷎⷐ-ⷖⷘ-ⷞⸯ々〆〱-〵〻〼ぁ-ゖゝ-ゟァ-ヺー-ヿㄅ-ㄭㄱ-ㆎㆠ-ㆺㇰ-ㇿ㐀-䶵一-鿌ꀀ-ꒌꓐ-ꓽꔀ-ꘌꘐ-ꘟꘪꘫꙀ-ꙮꙿ-ꚗꚠ-ꛥꜗ-ꜟꜢ-ꞈꞋ-ꞎꞐ-ꞓꞠ-Ɦꟸ-ꠁꠃ-ꠅꠇ-ꠊꠌ-ꠢꡀ-ꡳꢂ-ꢳꣲ-ꣷꣻꤊ-ꤥꤰ-ꥆꥠ-ꥼꦄ-ꦲꧏꨀ-ꨨꩀ-ꩂꩄ-ꩋꩠ-ꩶꩺꪀ-ꪯꪱꪵꪶꪹ-ꪽꫀꫂꫛ-ꫝꫠ-ꫪꫲ-ꫴꬁ-ꬆꬉ-ꬎꬑ-ꬖꬠ-ꬦꬨ-ꬮꯀ-ꯢ가-힣ힰ-ퟆퟋ-ퟻ豈-舘並-龎ﬀ-ﬆﬓ-ﬗיִײַ-ﬨשׁ-זּטּ-לּמּנּסּףּפּצּ-ﮱﯓ-ﴽﵐ-ﶏﶒ-ﷇﷰ-ﷻﹰ-ﹴﹶ-ﻼＡ-Ｚａ-ｚｦ-ﾾￂ-ￇￊ-ￏￒ-ￗￚ-ￜ])/i;

	const initialConfig: CreateEditorArgs = {
		...config,
		namespace: 'Playground',
		nodes: [
			HeadingNode,
			ListNode,
			ListItemNode,
			QuoteNode,
			HorizontalRuleNode,
			ImageNode,
			CodeNode,
			CodeHighlightNode,
			KeywordNode,
			AutoLinkNode,
			LinkNode,
			LayoutContainerNode,
			LayoutItemNode
		],
		onError: (error: Error) => {
			throw error;
		}
	};

	let placeholder: string | null = 'Enter Rich Text...';
	let mobileViewport: boolean = true;

	onMount(() => {
		const handleResize = () => {
			const nextMobileViewport = CAN_USE_DOM && window.matchMedia('(max-width: 1025px)').matches;

			if (nextMobileViewport !== mobileViewport) {
				mobileViewport = nextMobileViewport;
			}
		};
		handleResize();
		window.addEventListener('resize', handleResize);

		return () => {
			window.removeEventListener('resize', handleResize);
		};
	});

	export function getEditor() {
		return composer.getEditor();
	}

	const downloadHtml = (content: string) => {
		const blob = new Blob([content], { type: 'text/html' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		const filename = `${new Date().toISOString().split('T')[0]}-${articleTitle}${section ? `-` + section : ''}.html`;
		a.download = filename;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	};

	const createArticleHtml = () => {
		const a = `<div id="eot-doc-wrapper">
    
                <h2>Objective</h2><p>The objective of this article is to go over the Auto Surveillance VLAN (ASV) feature in the Catalyst 1200/1300 switches and the steps to configure it.</p>
                
                <h2>Applicable Devices | Software Version</h2>
                
                <ul>
                    <li>Catalyst 1200 | 4.0.0.91 (<a href="https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1200-series-switches/nb-06-cat1200-ser-data-sheet-cte-en.html" data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links">Data Sheet</a>)</li>
                    <li>Catalyst 1300 | 4.0.0.91 (<a href="https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1300-series-switches/nb-06-cat1300-ser-data-sheet-cte-en.html" data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links">Data Sheet</a>)</li>
                </ul>
                
                <h3>Introduction</h3>
                
                <p>Network communication between surveillance devices such as cameras and monitoring equipment should often be given higher priority and it is important that the various devices that comprise the surveillance infrastructure in the organization are reachable for each other. Normally, the network administrator ensures that all surveillance devices are connected to the same VLAN and to configure this VLAN and the interfaces on it to allow for this high priority traffic.</p>
                
                <p>ASV automates aspects of this setup by detecting defined surveillance devices on the network, assigns them to a VLAN, and sets their traffic priority. The surveillance devices are defined by creating a list of OUIs and MAC addresses. Up to 32 sources for surveillance traffic can be defined in any combination of MAC and OUIs.</p>
                
                <h2>Create an ASV VLAN</h2>
                
                <p>ASV can be enabled only on a static VLAN and the VLAN configured as an ASV VLAN cannot be deleted. </p>
                
                <h4>Step 1</h4>
                
                <p>Login to the Catalyst switch and navigate to <strong>VLAN Management &gt; VLAN Settings. </strong></p>
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-1.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-1.png"></a>
                
                <h4>Step 2</h4>
                
                <p>To add a VLAN, click on the <strong>plus</strong> symbol. </p>
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-2.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-2.png"></a>
                
                <h4>Step 3</h4>
                
                <p>Configure the <em>VLAN ID</em> and <em>VLAN Name</em> and click <strong>Apply</strong>. In this example, the VLAN ID is 5 and the VLAN Name is Auto Surveillance. </p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-3.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-3.png"></a>
                
                <h2>Configure ASV Settings </h2>
                
                <h4>Step 1</h4>
                <p>To select the VLAN for ASV, navigate to <strong>VLAN Management &gt; Auto-Surveillance VLAN &gt; ASV General Settings</strong>.  </p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-4.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-4.png"></a>
                
                <h4>Step 2</h4>
                
                <p>From the <em>Auto-Surveillance-VLAN ID</em> drop-down menu, select the VLAN ID for ASV. </p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-5.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-5.png"></a>
                
                <h4>Step 3</h4>
                
                <p>Under the <em>Surveillance Traffic Source Table</em>, click the <strong>plus icon</strong>. </p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-6.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-6.png"></a>
                
                <h4>Step 4</h4>
                
                <p>To add the surveillance traffic source, select <em>Source Type</em> as either <em>OUI Prefix</em> or <em>MAC Address</em>. Enter the <em>Source</em> in the field provided. Optionally, you can add a <em>Description</em> and click <strong>Apply</strong>. </p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-7.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-7.png"></a>
                
                
                <h4>Step 5</h4>
                
                <p>To enable the ASV VLAN on a specific port, navigate to <strong>VLAN Management &gt; Auto-Surveillance VLAN &gt; ASV Interface Settings</strong>.</p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-8.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-8.png"></a>
                
                <h4>Step 6</h4>
                
                <p>Select the interface and click edit. </p><a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-9.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-9.png"></a>
                
                <h4>Step 7</h4>
                
                <p><strong>Enable</strong> the <em>Auto Surveillance VLAN Membership</em> for the interface and click <strong>Apply</strong>. </p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-10.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-10.png"></a>
                
                <h2>Conclusion</h2>
                
                <p>There you go! You have configured ASV on your Catalyst 1200 or 1300 switch. </p>
                
                <p>Check out the following pages for more information on the Catalyst 1200 and 1300 switches. </p>
                
                <ul>
                    <li><a href="https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1200-series-switches/nb-06-cat1200-1300-ser-upgrade-cte-en.html" data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links">Why Upgrade to Cisco Catalyst 1200 or 1300 Series Switches Feature Comparison</a></li>
                    
                    <li><a href="https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1200-series-switches/nb-06-cat1200-1300-ser-aag-cte-en.html" data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links">Cisco Catalyst 1200 and 1300 Series Switches At-a-Glance</a></li>
                
                </ul>
                
                <p>For other configurations and features, refer to the Catalyst series <a href="https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/catalyst-1200-1300/AdminGuide/catalyst-1200-admin-guide.html" data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links">Administration Guide</a>. </p>
            
            </div>`;
	};

	const wrapContent = (content: string) => {
		return `<div id="eot-doc-wrapper">${content}</div>`;
	};

	export let savedSections: any[] = [];

	const exportArticle = () => {
		console.log('Saving article...');
		let editor: LexicalEditor = composer.getEditor();
		let htmlContent = '';
		let editorState = editor.getEditorState();
		console.log('editorState:', editorState);
		editor.update(() => {
			htmlContent = generateHtmlFromNodes(editor);
		});
		console.log(editor._config.namespace);
		console.log(editor._config.theme);
		console.log(JSON.stringify(editor.toJSON()));

		console.log('htmlContent:', htmlContent);
		const parser = new DOMParser();
		const dom = parser.parseFromString(htmlContent, 'text/html');
		const elements = dom.body.getElementsByTagName('*');
		for (const element of elements) {
			const classes = element.classList;
			console.log('classes:', classes);
			element.removeAttribute('data-lexical-text');
			element.removeAttribute('dir');
		}
		let scrubbedHtml = dom.body.innerHTML;
		console.log('scrubbedHtml:', scrubbedHtml);
		const sectionIndex = savedSections.findIndex((s) => s.section === section);
		if (sectionIndex > -1) {
			savedSections[sectionIndex].content = scrubbedHtml;
		} else {
			savedSections.push({ section: section, content: scrubbedHtml });
		}
		console.log('savedSections:', savedSections);
	};
</script>

<Composer {initialConfig} bind:this={composer}>
	<div class="editor-shell my-5 mx-auto rounded-md max-w-[1100px] relative font-normal leading-6">
		<RichTextToolbar />
		<div class="editor-container relative block rounded-br-md rounded-bl-md bg-neutral-100 w-full">
			<div class="editor-scroller min-h-[150px] flex relative overflow-auto resize-y w-full">
				<div class="editor flex-auto relative resize-y outline-none" bind:this={editorDiv}>
					<ContentEditable
						{content}
						{tag}
						className="content-editable border-0 block relative outline-none p-4 min-h-[150px] select-text whitespace-pre-wrap break-words"
					/>
					<PlaceHolder>{placeholder}</PlaceHolder>
				</div>
			</div>
			<AutoFocus />
			<KeywordPlugin {keywordsRegex} />
			<RichText />
			<AutoLink />
			<ColumnLayoutPlugin />
			<!-- <CollaborationPlugin
				providerFactory={createWebsocketProvider}
				shouldBootstrap={!shouldBootstrap}
				id="cisco-workforce-main"
			/> -->
			<SharedHistoryPlugin />
			<List />
			<CheckList />
			<CodeHighlight />
			<HorizontalRulePlugin />
			<ImagePlugin>
				<!-- <CaptionEditorCollaborationPlugin providerFactory={createWebsocketProvider} /> -->
				<CaptionEditorHistoryPlugin />
			</ImagePlugin>
			<Link {validateUrl} />
			{#if !mobileViewport}
				<FloatingLinkCapturePlugin anchorElem={editorDiv} />
			{/if}
			<ActionBar />
		</div>
	</div>
</Composer>
<button on:click={exportArticle}>Save Formatting</button>

<style>
	button {
		margin-top: 1rem;
		padding: 0.5rem 1rem;
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}

	button:hover {
		background-color: #0056b3;
	}
</style>
