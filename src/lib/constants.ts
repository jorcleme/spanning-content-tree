import { browser, dev } from '$app/environment';
import { version } from '../../package.json';

const APP_VERSION = import.meta.env.APP_VERSION;
const APP_BUILD_HASH = import.meta.env.APP_BUILD_HASH;
const BUILD_HASH = import.meta.env.BUILD_HASH;

console.log(`${APP_VERSION}`);
console.log(`${APP_BUILD_HASH}`);
console.log(`${BUILD_HASH}`);

export const APP_NAME = 'Spanning Content Tree';

export const WEBUI_HOSTNAME = browser ? (dev ? `${location.hostname}:8080` : ``) : '';
export const WEBUI_BASE_URL = browser ? (dev ? `http://${WEBUI_HOSTNAME}` : ``) : ``;
export const WEBUI_API_BASE_URL = `${WEBUI_BASE_URL}/api/v1`;

export const OLLAMA_API_BASE_URL = `${WEBUI_BASE_URL}/ollama`;
export const OPENAI_API_BASE_URL = `${WEBUI_BASE_URL}/openai`;
export const AUDIO_API_BASE_URL = `${WEBUI_BASE_URL}/audio/api/v1`;
export const IMAGES_API_BASE_URL = `${WEBUI_BASE_URL}/images/api/v1`;
export const RAG_API_BASE_URL = `${WEBUI_BASE_URL}/rag/api/v1`;

export const WEBUI_VERSION = APP_VERSION ?? version;
export const WEBUI_BUILD_HASH = APP_BUILD_HASH;
export const REQUIRED_OLLAMA_VERSION = '0.1.16';

export const SUPPORTED_FILE_TYPE = [
	'application/epub+zip',
	'application/pdf',
	'text/plain',
	'text/csv',
	'text/xml',
	'text/html',
	'text/x-python',
	'text/css',
	'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
	'application/octet-stream',
	'application/x-javascript',
	'text/markdown',
	'audio/mpeg',
	'audio/wav'
];

export const SUPPORTED_FILE_EXTENSIONS = [
	'md',
	'rst',
	'go',
	'py',
	'java',
	'sh',
	'bat',
	'ps1',
	'cmd',
	'js',
	'ts',
	'css',
	'cpp',
	'hpp',
	'h',
	'c',
	'cs',
	'htm',
	'html',
	'sql',
	'log',
	'ini',
	'pl',
	'pm',
	'r',
	'dart',
	'dockerfile',
	'env',
	'php',
	'hs',
	'hsc',
	'lua',
	'nginxconf',
	'conf',
	'm',
	'mm',
	'plsql',
	'perl',
	'rb',
	'rs',
	'db2',
	'scala',
	'bash',
	'swift',
	'vue',
	'svelte',
	'doc',
	'docx',
	'pdf',
	'csv',
	'txt',
	'xls',
	'xlsx',
	'pptx',
	'ppt',
	'msg'
];

// Source: https://kit.svelte.dev/docs/modules#$env-static-public
// This feature, akin to $env/static/private, exclusively incorporates environment variables
// that are prefixed with config.kit.env.publicPrefix (usually set to PUBLIC_).
// Consequently, these variables can be securely exposed to client-side code.

export type Role = 'admin' | 'user' | 'pending';
export type AccessLevel = 1 | 2 | 3 | 4;

export const ROLES = {
	ADMIN: 'admin' as Role,
	USER: 'user' as Role,
	PENDING: 'pending' as Role
};

export const ACCESS_LEVELS = {
	GUEST: 1 as AccessLevel,
	CUSTOMER: 2 as AccessLevel,
	PARTNER: 3 as AccessLevel,
	EMPLOYEE: 4 as AccessLevel
};

export const blockTypeToBlockName = {
	bullet: 'Bulleted List',
	check: 'Check List',
	code: 'Code Block',
	h1: 'Heading 1',
	h2: 'Heading 2',
	h3: 'Heading 3',
	h4: 'Heading 4',
	h5: 'Heading 5',
	h6: 'Heading 6',
	number: 'Numbered List',
	paragraph: 'Normal',
	quote: 'Quote',
	image: 'Image'
};

export const EDITOR_THEME = {
	ltr: 'ltr',
	rtl: 'rtl',
	paragraph: 'editor-paragraph',
	layoutContainer: 'editor-layoutContainer',
	layoutItem: 'editor-layoutItem',
	quote: 'editor-quote',
	heading: {
		h1: 'editor-heading-h1',
		h2: 'editor-heading-h2',
		h3: 'editor-heading-h3',
		h4: 'editor-heading-h4',
		h5: 'editor-heading-h5',
		h6: 'editor-heading-h6'
	},
	list: {
		checklist: 'editor-checklist',
		listitem: 'editor-listItem',
		listitemChecked: 'editor-listItemChecked',
		listitemUnchecked: 'editor-listItemUnchecked',
		nested: {
			listitem: 'editor-nestedListItem'
		},
		olDepth: ['editor-ol1', 'editor-ol2', 'editor-ol3', 'editor-ol4', 'editor-ol5'],
		ul: 'editor-ul'
	},

	hashtag: 'editor-hashtag',
	image: 'editor-image',
	link: 'editor-link',
	text: {
		bold: 'editor-textBold',
		code: 'editor-textCode',
		italic: 'editor-textItalic',
		strikethrough: 'editor-textStrikethrough',
		subscript: 'editor-textSubscript',
		superscript: 'editor-textSuperscript',
		underline: 'editor-textUnderline',
		underlineStrikethrough: 'editor-textUnderlineStrikethrough'
	},
	code: 'editor-code',
	codeHighlight: {
		atrule: 'editor-tokenAttr',
		attr: 'editor-tokenAttr',
		boolean: 'editor-tokenProperty',
		builtin: 'editor-tokenSelector',
		cdata: 'editor-tokenComment',
		char: 'editor-tokenSelector',
		class: 'editor-tokenFunction',
		'class-name': 'editor-tokenFunction',
		comment: 'editor-tokenComment',
		constant: 'editor-tokenProperty',
		deleted: 'editor-tokenProperty',
		doctype: 'editor-tokenComment',
		entity: 'editor-tokenOperator',
		function: 'editor-tokenFunction',
		important: 'editor-tokenVariable',
		inserted: 'editor-tokenSelector',
		keyword: 'editor-tokenAttr',
		namespace: 'editor-tokenVariable',
		number: 'editor-tokenProperty',
		operator: 'editor-tokenOperator',
		prolog: 'editor-tokenComment',
		property: 'editor-tokenProperty',
		punctuation: 'editor-tokenPunctuation',
		regex: 'editor-tokenVariable',
		selector: 'editor-tokenSelector',
		string: 'editor-tokenSelector',
		symbol: 'editor-tokenProperty',
		tag: 'editor-tokenProperty',
		url: 'editor-tokenOperator',
		variable: 'editor-tokenVariable'
	},
	autocomplete: 'editor-autocomplete',
	blockCursor: 'editor-blockCursor',
	characterLimit: 'editor-characterLimit',
	embedBlock: {
		base: 'editor-embedBlock',
		focus: 'editor-embedBlockFocus'
	},
	hr: 'editor-hr',
	indent: 'editor-indent',
	inlineImage: 'inline-editor-image',
	mark: 'editor-mark',
	markOverlap: 'editor-markOverlap',
	table: 'editor-table',
	tableCell: 'editor-tableCell',
	tableCellActionButton: 'editor-tableCellActionButton',
	tableCellActionButtonContainer: 'editor-tableCellActionButtonContainer',
	tableCellEditing: 'editor-tableCellEditing',
	tableCellHeader: 'editor-tableCellHeader',
	tableCellPrimarySelected: 'editor-tableCellPrimarySelected',
	tableCellResizer: 'editor-tableCellResizer',
	tableCellSelected: 'editor-tableCellSelected',
	tableCellSortedIndicator: 'editor-tableCellSortedIndicator',
	tableResizeRuler: 'editor-tableCellResizeRuler',
	tableSelected: 'editor-tableSelected',
	tableSelection: 'editor-tableSelection'
};
