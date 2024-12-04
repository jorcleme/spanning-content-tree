declare module 'turndown' {
	interface TurndownOptions {
		headingStyle?: 'setext' | 'atx';
		hr?: string;
		bulletListMarker?: string;
		codeBlockStyle?: 'indented' | 'fenced';
		fence?: string;
		emDelimiter?: string;
		strongDelimiter?: string;
		linkStyle?: 'inlined' | 'referenced';
		linkReferenceStyle?: 'full' | 'collapsed' | 'shortcut';
		blankReplacement?: (content: string, node: HTMLElement) => string;
		keepReplacement?: (content: string, node: HTMLElement) => string;
		defaultReplacement?: (content: string, node: HTMLElement) => string;
	}

	interface Rule {
		filter: string | string[] | ((node: HTMLElement) => boolean);
		replacement: (content: string, node: HTMLElement, options: TurndownOptions) => string;
	}

	class TurndownService {
		constructor(options?: TurndownOptions);
		turndown(input: string | HTMLElement): string;
		use(plugin: (service: TurndownService) => void): void;
		addRule(key: string, rule: Rule): void;
		keep(filter: string | string[] | ((node: HTMLElement) => boolean)): void;
		remove(filter: string | string[] | ((node: HTMLElement) => boolean)): void;
		escape(string: string): string;
	}

	export default TurndownService;
}
