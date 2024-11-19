import type { FileUpload } from '$lib/apis/files';

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

export interface Banner extends BaseEntity {
	type: string;
	title?: string;
	content: string;
	url?: string;
	dismissible?: boolean;
	timestamp: number;
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

export interface Message extends BaseMessage {
	id: string;
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

export interface ChatResponse extends BaseEntity, UserEntity, TimestampEntity {
	title: string;
	chat: Chat;
	share_id?: Nullable<string>;
	archived: boolean;
	time_range: string;
}

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
	applicable_devices: ArticleDevice[];
	introduction: string;
	steps: ArticleStep[];
	revision_history: ArticleRevisionHistory[];
	created_at: number;
	updated_at: number;
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
