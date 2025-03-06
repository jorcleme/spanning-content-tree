<script lang="ts">
	import type { BlockType } from '$lib/types';

	import { type SvelteComponent, afterUpdate, createEventDispatcher, getContext, onMount } from 'svelte';
	import { KeywordPlugin } from 'svelte-lexical';

	import { HorizontalRuleNode } from '$lib/components/cisco/components/editor/toolbar/plugins/hr/HorizontalRuleNode';
	import { ImageNode } from '$lib/components/cisco/components/editor/toolbar/plugins/image/ImageNode';
	import { editSectionId, reviewedArticle } from '$lib/stores';
	import { CAN_USE_DOM, KeywordNode, validateUrl } from '$lib/utils/editor';
	import { createWebsocketProvider } from '$lib/utils/editor/collaboration';
	import { CodeHighlightNode, CodeNode } from '@lexical/code';
	import { $generateHtmlFromNodes as generateHtmlFromNodes } from '@lexical/html';
	import { AutoLinkNode, LinkNode } from '@lexical/link';
	import { ListItemNode, ListNode } from '@lexical/list';
	import { HeadingNode, QuoteNode } from '@lexical/rich-text';
	import type { CreateEditorArgs, LexicalEditor } from 'lexical';

	import Article from '../articles/Article.svelte';
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
	export let section: string | null = null;
	export let articleSections: any[] = [];
	export let articleTitle: string = '';

	const dispatch = createEventDispatcher();

	let composer: SvelteComponent<any, any, any>;
	let editorDiv: HTMLDivElement;

	const shouldBootstrap = window.parent != null && window.parent.frames.right === window;
	const keywordsRegex =
		/(^|$|[^A-Za-zªµºÀ-ÖØ-öø-ˁˆ-ˑˠ-ˤˬˮͰ-ʹͶͷͺ-ͽΆΈ-ΊΌΎ-ΡΣ-ϵϷ-ҁҊ-ԧԱ-Ֆՙա-ևא-תװ-ײؠ-يٮٯٱ-ۓەۥۦۮۯۺ-ۼۿܐܒ-ܯݍ-ޥޱߊ-ߪߴߵߺࠀ-ࠕࠚࠤࠨࡀ-ࡘࢠࢢ-ࢬऄ-हऽॐक़-ॡॱ-ॷॹ-ॿঅ-ঌএঐও-নপ-রলশ-হঽৎড়ঢ়য়-ৡৰৱਅ-ਊਏਐਓ-ਨਪ-ਰਲਲ਼ਵਸ਼ਸਹਖ਼-ੜਫ਼ੲ-ੴઅ-ઍએ-ઑઓ-નપ-રલળવ-હઽૐૠૡଅ-ଌଏଐଓ-ନପ-ରଲଳଵ-ହଽଡ଼ଢ଼ୟ-ୡୱஃஅ-ஊஎ-ஐஒ-கஙசஜஞடணதந-பம-ஹௐఅ-ఌఎ-ఐఒ-నప-ళవ-హఽౘౙౠౡಅ-ಌಎ-ಐಒ-ನಪ-ಳವ-ಹಽೞೠೡೱೲഅ-ഌഎ-ഐഒ-ഺഽൎൠൡൺ-ൿඅ-ඖක-නඳ-රලව-ෆก-ะาำเ-ๆກຂຄງຈຊຍດ-ທນ-ຟມ-ຣລວສຫອ-ະາຳຽເ-ໄໆໜ-ໟༀཀ-ཇཉ-ཬྈ-ྌက-ဪဿၐ-ၕၚ-ၝၡၥၦၮ-ၰၵ-ႁႎႠ-ჅჇჍა-ჺჼ-ቈቊ-ቍቐ-ቖቘቚ-ቝበ-ኈኊ-ኍነ-ኰኲ-ኵኸ-ኾዀዂ-ዅወ-ዖዘ-ጐጒ-ጕጘ-ፚᎀ-ᎏᎠ-Ᏼᐁ-ᙬᙯ-ᙿᚁ-ᚚᚠ-ᛪᜀ-ᜌᜎ-ᜑᜠ-ᜱᝀ-ᝑᝠ-ᝬᝮ-ᝰក-ឳៗៜᠠ-ᡷᢀ-ᢨᢪᢰ-ᣵᤀ-ᤜᥐ-ᥭᥰ-ᥴᦀ-ᦫᧁ-ᧇᨀ-ᨖᨠ-ᩔᪧᬅ-ᬳᭅ-ᭋᮃ-ᮠᮮᮯᮺ-ᯥᰀ-ᰣᱍ-ᱏᱚ-ᱽᳩ-ᳬᳮ-ᳱᳵᳶᴀ-ᶿḀ-ἕἘ-Ἕἠ-ὅὈ-Ὅὐ-ὗὙὛὝὟ-ώᾀ-ᾴᾶ-ᾼιῂ-ῄῆ-ῌῐ-ΐῖ-Ίῠ-Ῥῲ-ῴῶ-ῼⁱⁿₐ-ₜℂℇℊ-ℓℕℙ-ℝℤΩℨK-ℭℯ-ℹℼ-ℿⅅ-ⅉⅎↃↄⰀ-Ⱞⰰ-ⱞⱠ-ⳤⳫ-ⳮⳲⳳⴀ-ⴥⴧⴭⴰ-ⵧⵯⶀ-ⶖⶠ-ⶦⶨ-ⶮⶰ-ⶶⶸ-ⶾⷀ-ⷆⷈ-ⷎⷐ-ⷖⷘ-ⷞⸯ々〆〱-〵〻〼ぁ-ゖゝ-ゟァ-ヺー-ヿㄅ-ㄭㄱ-ㆎㆠ-ㆺㇰ-ㇿ㐀-䶵一-鿌ꀀ-ꒌꓐ-ꓽꔀ-ꘌꘐ-ꘟꘪꘫꙀ-ꙮꙿ-ꚗꚠ-ꛥꜗ-ꜟꜢ-ꞈꞋ-ꞎꞐ-ꞓꞠ-Ɦꟸ-ꠁꠃ-ꠅꠇ-ꠊꠌ-ꠢꡀ-ꡳꢂ-ꢳꣲ-ꣷꣻꤊ-ꤥꤰ-ꥆꥠ-ꥼꦄ-ꦲꧏꨀ-ꨨꩀ-ꩂꩄ-ꩋꩠ-ꩶꩺꪀ-ꪯꪱꪵꪶꪹ-ꪽꫀꫂꫛ-ꫝꫠ-ꫪꫲ-ꫴꬁ-ꬆꬉ-ꬎꬑ-ꬖꬠ-ꬦꬨ-ꬮꯀ-ꯢ가-힣ힰ-ퟆퟋ-ퟻ豈-舘並-龎ﬀ-ﬆﬓ-ﬗיִײַ-ﬨשׁ-זּטּ-לּמּנּסּףּפּצּ-ﮱﯓ-ﴽﵐ-ﶏﶒ-ﷇﷰ-ﷻﹰ-ﹴﹶ-ﻼＡ-Ｚａ-ｚｦ-ﾾￂ-ￇￊ-ￏￒ-ￗￚ-ￜ])(congrats|congratulations|gratuluju|gratuluji|gratulujeme|blahopřeju|blahopřeji|blahopřejeme|Til lykke|Tillykke|Glückwunsch|Gratuliere|felicitaciones|enhorabuena|paljon onnea|onnittelut|Félicitations|gratula|gratulálok|gratulálunk|congratulazioni|complimenti|おめでとう|おめでとうございます|축하해|축하해요|gratulerer|Gefeliciteerd|gratulacje|Parabéns|parabéns|felicitações|felicitări|мои поздравления|поздравляем|поздравляю|gratulujem|blahoželám|ยินดีด้วย|ขอแสดงความยินดี|tebrikler|tebrik ederim|恭喜|祝贺你|恭喜你|恭喜|恭喜|baie geluk|veels geluk|অভিনন্দন|Čestitam|Čestitke|Čestitamo|Συγχαρητήρια|Μπράβο|અભિનંદન|badhai|बधाई|अभिनंदन|Честитам|Свака част|hongera|வாழ்த்துகள்|வாழ்த்துக்கள்|అభినందనలు|അഭിനന്ദനങ്ങൾ|Chúc mừng|מזל טוב|mazel tov|mazal tov)(^|$|[^A-Za-zªµºÀ-ÖØ-öø-ˁˆ-ˑˠ-ˤˬˮͰ-ʹͶͷͺ-ͽΆΈ-ΊΌΎ-ΡΣ-ϵϷ-ҁҊ-ԧԱ-Ֆՙա-ևא-תװ-ײؠ-يٮٯٱ-ۓەۥۦۮۯۺ-ۼۿܐܒ-ܯݍ-ޥޱߊ-ߪߴߵߺࠀ-ࠕࠚࠤࠨࡀ-ࡘࢠࢢ-ࢬऄ-हऽॐक़-ॡॱ-ॷॹ-ॿঅ-ঌএঐও-নপ-রলশ-হঽৎড়ঢ়য়-ৡৰৱਅ-ਊਏਐਓ-ਨਪ-ਰਲਲ਼ਵਸ਼ਸਹਖ਼-ੜਫ਼ੲ-ੴઅ-ઍએ-ઑઓ-નપ-રલળવ-હઽૐૠૡଅ-ଌଏଐଓ-ନପ-ରଲଳଵ-ହଽଡ଼ଢ଼ୟ-ୡୱஃஅ-ஊஎ-ஐஒ-கஙசஜஞடணதந-பம-ஹௐఅ-ఌఎ-ఐఒ-నప-ళవ-హఽౘౙౠౡಅ-ಌಎ-ಐಒ-ನಪ-ಳವ-ಹಽೞೠೡೱೲഅ-ഌഎ-ഐഒ-ഺഽൎൠൡൺ-ൿඅ-ඖක-නඳ-රලව-ෆก-ะาำเ-ๆກຂຄງຈຊຍດ-ທນ-ຟມ-ຣລວສຫອ-ະາຳຽເ-ໄໆໜ-ໟༀཀ-ཇཉ-ཬྈ-ྌက-ဪဿၐ-ၕၚ-ၝၡၥၦၮ-ၰၵ-ႁႎႠ-ჅჇჍა-ჺჼ-ቈቊ-ቍቐ-ቖቘቚ-ቝበ-ኈኊ-ኍነ-ኰኲ-ኵኸ-ኾዀዂ-ዅወ-ዖዘ-ጐጒ-ጕጘ-ፚᎀ-ᎏᎠ-Ᏼᐁ-ᙬᙯ-ᙿᚁ-ᚚᚠ-ᛪᜀ-ᜌᜎ-ᜑᜠ-ᜱᝀ-ᝑᝠ-ᝬᝮ-ᝰក-ឳៗៜᠠ-ᡷᢀ-ᢨᢪᢰ-ᣵᤀ-ᤜᥐ-ᥭᥰ-ᥴᦀ-ᦫᧁ-ᧇᨀ-ᨖᨠ-ᩔᪧᬅ-ᬳᭅ-ᭋᮃ-ᮠᮮᮯᮺ-ᯥᰀ-ᰣᱍ-ᱏᱚ-ᱽᳩ-ᳬᳮ-ᳱᳵᳶᴀ-ᶿḀ-ἕἘ-Ἕἠ-ὅὈ-Ὅὐ-ὗὙὛὝὟ-ώᾀ-ᾴᾶ-ᾼιῂ-ῄῆ-ῌῐ-ΐῖ-Ίῠ-Ῥῲ-ῴῶ-ῼⁱⁿₐ-ₜℂℇℊ-ℓℕℙ-ℝℤΩℨK-ℭℯ-ℹℼ-ℿⅅ-ⅉⅎↃↄⰀ-Ⱞⰰ-ⱞⱠ-ⳤⳫ-ⳮⳲⳳⴀ-ⴥⴧⴭⴰ-ⵧⵯⶀ-ⶖⶠ-ⶦⶨ-ⶮⶰ-ⶶⶸ-ⶾⷀ-ⷆⷈ-ⷎⷐ-ⷖⷘ-ⷞⸯ々〆〱-〵〻〼ぁ-ゖゝ-ゟァ-ヺー-ヿㄅ-ㄭㄱ-ㆎㆠ-ㆺㇰ-ㇿ㐀-䶵一-鿌ꀀ-ꒌꓐ-ꓽꔀ-ꘌꘐ-ꘟꘪꘫꙀ-ꙮꙿ-ꚗꚠ-ꛥꜗ-ꜟꜢ-ꞈꞋ-ꞎꞐ-ꞓꞠ-Ɦꟸ-ꠁꠃ-ꠅꠇ-ꠊꠌ-ꠢꡀ-ꡳꢂ-ꢳꣲ-ꣷꣻꤊ-ꤥꤰ-ꥆꥠ-ꥼꦄ-ꦲꧏꨀ-ꨨꩀ-ꩂꩄ-ꩋꩠ-ꩶꩺꪀ-ꪯꪱꪵꪶꪹ-ꪽꫀꫂꫛ-ꫝꫠ-ꫪꫲ-ꫴꬁ-ꬆꬉ-ꬎꬑ-ꬖꬠ-ꬦꬨ-ꬮꯀ-ꯢ가-힣ힰ-ퟆퟋ-ퟻ豈-舘並-龎ﬀ-ﬆﬓ-ﬗיִײַ-ﬨשׁ-זּטּ-לּמּנּסּףּפּצּ-ﮱﯓ-ﴽﵐ-ﶏﶒ-ﷇﷰ-ﷻﹰ-ﹴﹶ-ﻼＡ-Ｚａ-ｚｦ-ﾾￂ-ￇￊ-ￏￒ-ￗￚ-ￜ])/i;

	const initialConfig: CreateEditorArgs = {
		...config,
		namespace: 'Cisco-Editor',
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
	export const getEditor = (): LexicalEditor => composer.getEditor();

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

	const saveArticleSection = () => {
		console.log('Saving article...');
		const editor: LexicalEditor = composer.getEditor();
		let htmlContent = '';
		editor.update(() => {
			htmlContent = generateHtmlFromNodes(editor);
		});
		console.log(editor._config.namespace);

		console.log('htmlContent:', htmlContent);
		const parser = new DOMParser();
		const dom = parser.parseFromString(htmlContent, 'text/html');
		const elements = dom.body.getElementsByTagName('*');
		const textContent = dom.body.textContent?.trim() || '';
		for (const element of elements) {
			element.getAttributeNames().forEach((attr) => {
				if (attr.startsWith('data-lexical-')) {
					element.removeAttribute(attr);
				}
			});
		}

		let scrubbedHtml = dom.body.innerHTML;
		let section = {};
		console.log('scrubbedHtml:', scrubbedHtml);
		if (articleSections.findIndex((s) => s.id === $editSectionId) > -1) {
			if ($editSectionId === 'applicable_devices') {
				const devices = dom.body.getElementsByTagName('li');
				const articleDevices = [];
				for (const device of devices) {
					const articleDevice: Record<string, string | null> = {};
					let text = device.textContent?.trim() || '';
					const datasheet_link =
						device.querySelector('a[href*="https://www.cisco.com/c/en/us/products"]')?.getAttribute('href') || null;
					const software_link =
						device.querySelector('a[href*="https://software.cisco.com/download"]')?.getAttribute('href') || null;

					let [device_name, ...rest] = text.split('|').map((str) => str.trim());
					const nameRegex = /(.*?)(?=\s*\(Data\s*Sheet\))/gi;
					device_name =
						nameRegex.exec(device_name)?.[0] || device_name.replace(/\s*\(DataSheet\)/gi, '') || device_name;
					const software = /\d+\.\d+\.\d+\.\d+/g.exec(rest.join(' '))?.[0] || null;
					articleDevice.device = device_name;
					articleDevice.software = software;
					articleDevice.datasheet_link = datasheet_link;
					articleDevice.software_link = software_link;
					articleDevices.push(articleDevice);
				}
				console.log('articleDevices:', articleDevices);
			}

			articleSections = articleSections.map((s) => {
				if (s.id === $editSectionId) {
					section = { ...s, content: scrubbedHtml, html: scrubbedHtml };
					return section;
				} else {
					return s;
				}
			});
		}

		console.log('updated articleSections:', articleSections);
		dispatch('save', { section });
	};
</script>

<Composer {initialConfig} bind:this={composer}>
	<div class="editor-shell my-5 mx-auto rounded-md max-w-[1100px] relative font-normal leading-6">
		<RichTextToolbar />
		<div class="editor-container relative block rounded-br-md rounded-bl-md bg-gray-100 dark:bg-gray-950 w-full">
			<div class="editor-scroller min-h-[150px] flex relative overflow-auto resize-y w-full">
				<div class="editor flex-auto relative resize-y outline-none" bind:this={editorDiv}>
					<ContentEditable
						{content}
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
<button
	class="py-2.5 px-4 bg-blue-500 text-white font-bold rounded-md cursor-pointer hover:bg-blue-400 shadow-md"
	on:click={saveArticleSection}>Save</button
>
