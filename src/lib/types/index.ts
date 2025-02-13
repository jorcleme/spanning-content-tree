import type { Writable } from 'svelte/store';
import type { FileUpload } from '$lib/apis/files';
import type { i18n } from 'i18next';
import type { LexicalEditor } from 'lexical';

export type BlockType =
	| 'bullet'
	| 'check'
	| 'code'
	| 'h1'
	| 'h2'
	| 'h3'
	| 'h4'
	| 'h5'
	| 'h6'
	| 'number'
	| 'paragraph'
	| 'quote'
	| 'image';

export type i18nType = Writable<i18n>;
export type LexicalEditorType = LexicalEditor;

export type ActiveEditorContext = Writable<LexicalEditor>;
export type IsBoldContext = Writable<boolean>;
export type IsItalicContext = Writable<boolean>;
export type IsUnderlineContext = Writable<boolean>;
export type IsStrikethroughContext = Writable<boolean>;
export type IsSubscriptContext = Writable<boolean>;
export type IsSuperscriptContext = Writable<boolean>;
export type IsCodeContext = Writable<boolean>;
export type BlockTypeContext = Writable<BlockType>;
export type SelectedElementKeyContext = Writable<string | null>;
export type FontSizeContext = Writable<string>;
export type FontFamilyContext = Writable<string>;
export type FontColorContext = Writable<string>;
export type BgColorContext = Writable<string>;
export type IsRTLContext = Writable<boolean>;
export type CodeLanguageContext = Writable<string>;
export type IsLinkContext = Writable<boolean>;
export type IsImageCaptionContext = Writable<boolean>;

// Shared Utility
export type Nullable<T> = T | null;
export type Or<T, U> = T | U;

interface BaseEntity {
	id: string;
}

interface TimestampEntity {
	created_at: number; // epoch time in seconds
	updated_at: number; // epoch time in seconds
}

interface UserEntity {
	user_id: string;
}

interface MessageInfo {
	total_duration?: number;
	load_duration?: number;
	prompt_eval_count?: number;
	prompt_eval_duration?: number;
	eval_count?: number;
	eval_duration?: number;
	sample_count?: number;
	sample_duration?: number;
	openai?: boolean;
	ollama?: boolean;
	prompt_tokens?: number;
	completion_tokens?: number;
	total_tokens?: number;
}

interface MessageStatusHistory {
	done?: boolean;
	error?: boolean;
	action?: string;
	description?: string;
	query?: any;
	urls?: string[];
}

interface MessageAnnotation {
	rating?: number;
	reason?: string;
	comment?: string;
}

export interface BaseMessage {
	role: string;
	content: string;
}

export interface Message extends BaseEntity, BaseMessage {
	parentId: string | null;
	childrenIds?: string[];
	timestamp?: number; // epoch time in seconds
	models?: string[];
	model?: string;
	modelName?: string;
	userContext?: any;
	lastSentence?: string;
	done?: boolean;
	context?: any;
	type?: string;
	info?: MessageInfo;
	statusHistory?: MessageStatusHistory[];
	files?: ClientFile[];
	citations?: any[];
	error?: any;
	images?: any;
	raContent?: string;
	originalContent?: string;
	status?: MessageStatusHistory;
	annotation?: MessageAnnotation;
}

export interface EditedMessage extends Message {}

export interface ClientFile {
	collection_name?: string;
	error?: string;
	file?: FileUpload;
	id?: string;
	name?: string;
	status?: boolean | string;
	type?: string;
	url?: string;
	urls?: string[];
}
export interface ChatFile extends Pick<ClientFile, 'name' | 'url' | 'type'> {}

export interface MessageHistory {
	messages: {
		[id: string]: Message;
	};
	currentId: Nullable<string>;
	state?: any;
}

export interface Chat extends BaseEntity, TimestampEntity {
	title: string;
	models: string[];
	params: Record<string, any>;
	messages: Message[];
	history: MessageHistory;
	tags: string[];
	timestamp: number; // epoch time in seconds
	files: ClientFile[];
	mapping?: Record<string, any>;
	article?: string; // article id
}

interface TagByUser extends BaseEntity, UserEntity {
	name: string;
	data?: string | null;
}

export interface ChatTag extends BaseEntity, UserEntity {
	name: string;
	data?: any;
}

export interface ChatResponse {
	id: string;
	user_id: string;
	title: string;
	chat: Chat;
	share_id?: Nullable<string>;
	archived: boolean;
	time_range: string;
	updated_at: number; // epoch time in seconds
	created_at: number; // epoch time in seconds
}

export interface ChatSummary extends Pick<ChatResponse, 'id' | 'title' | 'created_at' | 'updated_at'> {}

export interface ChatSummaryWithTimeRange extends ChatSummary, Pick<ChatResponse, 'time_range'> {}

export type ChatListResponse = ChatResponse[];
export type ChatTagListResponse = Array<ChatTag>;
export type TagsByUserResponse = Array<TagByUser>;

export interface UserMemoryQuery {
	ids?: string[][]; // array of array of strings
	distances?: number[][]; // array of array of numbers
	metadatas: Array<Array<{ created_at: number }>>;
	embeddings?: number[][] | null;
	documents: string[][];
	uris?: any;
	data?: any;
	included?: string[];
}

export interface Memory extends BaseEntity, UserEntity, TimestampEntity {
	content: string;
}

interface ArticleDevice {
	device?: string;
	software?: string;
	datasheet_link?: string;
	software_link?: string | null;
}

interface ArticleRevisionHistory {
	revision: number; // e.g. 1.0, 1.1, 1.2, etc.
	publish_date: string; // e.g. 2021-01-01
	comments: string;
}

interface ArticleAnnotation {
	rating?: number;
	reasons?: string[];
	comment?: string;
}

interface ArticleQNAPair {
	id: string;
	question: string;
	answer: string | null;
	sources?: Record<string, any>[];
	original_answer?: string;
	rating?: number;
	annotation?: ArticleAnnotation;
	model?: string;
}

export interface ArticleStep {
	section: string;
	step_number: number;
	text: string;
	src: string | null;
	alt: string | null;
	video_src?: string | null;
	note: string | null;
	emphasized_text: string[];
	emphasized_tags: string[];
	qna_pairs?: Array<ArticleQNAPair>;
}

export interface Article {
	id: string;
	title: string;
	document_id: string;
	series?: string;
	series_ids?: string[];
	objective: string;
	category: string;
	url: string;
	best_practices?: string[];
	applicable_devices: ArticleDevice[];
	introduction: string;
	steps: ArticleStep[];
	revision_history: ArticleRevisionHistory[];
	published: boolean;
	user_id?: string | null;
	sources?: Record<string, string>[] | null;
	created_at: number;
	updated_at: number;
}

export interface ReviewedArticle {
	id: string;
	title: string;
	document_id: string;
	objective: string;
	category: string;
	url: string;
	best_practices?: string[];
	applicable_devices: string;
	introduction: string;
	steps: string[];
	revision_history: string[];
	published: boolean;
	user_id?: string | null;
	sources?: Record<string, string>[] | null;
	created_at: number;
	updated_at: number;
	date_reviewed?: number;
	reviewed_by?: string;
	reviewed_by_id?: string;
}

export interface Series {
	id: string;
	name: string;
	admin_guide_urls: string[];
	datasheet_urls: string[];
	cli_guide_urls: string[];
	software_url: string | null;
	created_at: number;
	updated_at: number;
}

interface ToolManifest {
	id: string;
	title: string;
	description: string;
	author: string;
	version: string;
	license: string;
	author_url?: string;
	funding_url?: string;
	GitHub?: string;
	Notes?: string;
}

interface ToolMeta {
	description: string;
	manifest: ToolManifest;
}

export interface Tool extends BaseEntity, UserEntity, TimestampEntity {
	name: string;
	content: string;
	specs: {
		name: string;
		description: string;
		parameters: {
			type: string;
			properties: Record<string, string>;
			required: string[];
		};
	}[];
	meta: ToolMeta;
}

export interface Valve {
	[key: string]: any;
}

export type Collection = {
	name: string;
	type?: string;
	title?: string;
	filename?: string;
	collection_names?: (string | undefined)[];
	timestamp?: number;
} & Partial<Document> &
	Partial<UserEntity>;

type PromptSuggestion = {
	content: string;
	title?: [string, string];
};

interface ModelMetaCapabilities {
	vision?: boolean;
	[capability: string]: any;
}
interface ModelMeta {
	description?: string | null;
	capabilities?: ModelMetaCapabilities;
	knowledge?: Collection[];
	tags?: any[];
	hidden?: boolean;
	position?: number;
	suggestion_prompts?: PromptSuggestion[] | null;
	toolIds?: string[];
	profile_image_url?: string;
	filterIds?: string[];
	user?: {
		name: string;
		community?: boolean;
		username: string;
	};
	task?:
		| 'text-generation'
		| 'feature-extraction'
		| 'sentence-similarity'
		| 'fill-mask'
		| 'question-answering'
		| 'summarization'
		| 'table-question-answering'
		| 'text-classification'
		| 'sentiment-analysis'
		| 'translation'
		| 'ner'
		| 'token-classification'
		| 'zero-shot-classification'
		| 'depth-estimation'
		| 'image-classification'
		| 'image-segmentation'
		| 'image-to-image'
		| 'mask-generation'
		| 'object-detection'
		| 'image-feature-extraction'
		| 'audio-classification'
		| 'automatic-speech-recognition'
		| 'text-to-speech'
		| 'text-to-audio'
		| 'document-question-answering'
		| 'image-to-text'
		| 'text-to-image'
		| 'visual-question-answering'
		| 'zero-shot-audio-classification'
		| 'zero-shot-image-classification'
		| 'zero-shot-object-detection';
	dtype?:
		| 'auto'
		| 'fp32'
		| 'fp16'
		| 'q8'
		| 'int8'
		| 'uint8'
		| 'q4'
		| 'bnb4'
		| 'q4f16'
		| Record<string, 'auto' | 'fp32' | 'fp16' | 'q8' | 'int8' | 'uint8' | 'q4' | 'bnb4' | 'q4f16'>;
	context_length?: number;
	task_instruction_prefixes?: [string, string][]; // [name, purpose]
}
export interface ModelConfig {
	id: string;
	name: string;
	meta: ModelMeta;
	base_model_id?: string | null;
	params: ModelParams;
}

type Params = {
	stop?: string | string[] | null;
	system?: string | null;
};

export type MapParams<T extends Record<string, any> = Record<string, any>> = {
	[Key in keyof T as Key]: T[Key];
};

export type ModelParams = MapParams<Params> & { [key: string]: any };

export type AdvancedModelParams = ModelParams &
	Partial<{
		seed: number | null;
		temperature: number | null;
		max_tokens: number | null;
		mirostat: number | null;
		mirostat_eta: number | null;
		mirostat_tau: number | null;
		use_mlock?: boolean;
		use_mmap?: boolean;
		num_batch: number | null;
		num_ctx: number | null;
		num_keep: number | null;
		num_thread: number | null;
		repeat_last_n: number | null;
		tfs_z: number | null;
		top_k: number | null;
		top_p: number | null;
		template: string | null;
		frequency_penalty: number | null;
		proficiency: number;
	}>;

export type GlobalModelConfig = ModelConfig[];

type ChunkConfigForm = {
	chunk_size: number;
	chunk_overlap: number;
};

type ContentExtractConfigForm = {
	engine: string;
	tika_server_url: string | null;
};

type YoutubeConfigForm = {
	language: string[];
	translation?: string | null;
};

type WebSearchConfig = {
	enabled: boolean;
	engine?: string;
	searxng_query_url?: string;
	google_pse_api_key?: string;
	google_pse_engine_id?: string;
	brave_search_api_key?: string;
	serpstack_api_key?: string;
	serpstack_https?: boolean;
	serper_api_key?: string;
	serply_api_key?: string;
	tavily_api_key?: string;
	result_count?: number;
	concurrent_requests?: number;
};
export type WebConfig = {
	search: WebSearchConfig;
	ssl_verification?: boolean;
};

export type RAGConfigForm = {
	pdf_extract_images?: boolean;
	chunk?: ChunkConfigForm;
	content_extraction?: ContentExtractConfigForm;
	youtube?: YoutubeConfigForm;
	web?: WebConfig;
};
