<script lang="ts">
	import AutoLinkStore from './AutoLinkStore.svelte';

	type LinkMatcher = (text: string) => {
		index: number;
		length: number;
		text: string;
		url: string;
	} | null;

	export const createLinkMatcherWithRegExp = (
		regExp: RegExp,
		urlTransformer: (text: string) => string = (text) => text
	): LinkMatcher => {
		return (text) => {
			const match = regExp.exec(text);
			if (match === null) {
				return null;
			}
			return {
				index: match.index,
				length: match[0].length,
				text: match[0],
				url: urlTransformer(match[0])
			};
		};
	};

	const URL_REGEX =
		/((https?:\/\/(www\.)?)|(www\.))[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&//=]*)(?<![-.+():%])/;
	const EMAIL_REGEX =
		/(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))/;
	const MATCHERS = [
		createLinkMatcherWithRegExp(URL_REGEX, (text) => {
			return text.startsWith('http') ? text : `https://${text}`;
		}),
		createLinkMatcherWithRegExp(EMAIL_REGEX, (text) => {
			return `mailto:${text}`;
		})
	];
</script>

<AutoLinkStore matchers={MATCHERS} />
