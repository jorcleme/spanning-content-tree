// Shared Utility
export type Nullable<T> = T | null;
export type Or<T, U> = T | U;

interface BaseEntity {
	id: string;
}

interface TimestampEntity extends BaseEntity {
	created_at: number; // epoch time in seconds
	updated_at: number; // epoch time in seconds
}

interface UserEntity extends BaseEntity {
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

// type MessageInfo = {
// 	total_duration?: number;
// 	load_duration?: number;
// 	prompt_eval_count?: number;
// 	prompt_eval_duration?: number;
// 	eval_count?: number;
// 	eval_duration?: number;
// 	sample_count?: number;
// 	sample_duration?: number;
// 	openai?: boolean;
// 	ollama?: boolean;
// 	prompt_tokens?: number;
// 	completion_tokens?: number;
// 	total_tokens?: number;
// };

type StatusHistory = {
	done?: boolean;
	error?: boolean;
	action?: string;
	description?: string;
	query?: any;
	urls?: string[];
};

// type FileHistory = {
// 	collection_name?: string;
// 	name?: string;
// 	type?: string;
// 	urls?: string[];
// 	url?: string;
// };

export type BaseMessage = {
	role: string;
	content: string;
};

export type EditedMessage = Partial<Message>;

export type Message = BaseMessage & {
	id: string;
	parentId: string | null;
	childrenIds?: string[];
	timestamp: number; // epoch time in seconds
	models?: string[];
	model?: string;
	modelName?: string;
	userContext?: any;
	lastSentence?: string;
	done?: boolean;
	context?: any;
	info?: MessageInfo;
	statusHistory?: StatusHistory[];
	files?: ClientFile[];
	citations?: any[];
	error?: any;
	images?: any;
	raContent?: string;
	originalContent?: string;
	status?: StatusHistory;
};

// File object shape:
// -------------------
// collection_name: "2a1113258f84e36ba0f4734b33092836936e538c539b2c741218fa9bc7aef13"
// error: ""
// file: {id: '362ec854-789f-4563-8981-92c0f196cd47', user_id: 'b7ad0b4d-972a-4225-8cbf-b592b4a51a90', filename: '362ec854-789f-4563-8981-92c0f196cd47_auto-surveillance-vlan-catalyst-1200-1300-switches.pdf', meta: {…}, created_at: 1724870348}
// id: "362ec854-789f-4563-8981-92c0f196cd47"
// name: "auto-surveillance-vlan-catalyst-1200-1300-switches.pdf"
// status: "processed"
// type: "file"
// url: "/api/v1/files/362ec854-789f-4563-8981-92c0f196cd47"
// -------------------

import type { _FileUploadRes } from '$lib/apis/files';

export interface ClientFile {
	collection_name?: string;
	error?: string;
	file?: _FileUploadRes;
	id?: string;
	name?: string;
	status?: boolean | string;
	type?: string;
	url?: string;
	urls?: string[];
}

export type ChatFile = Pick<ClientFile, 'name' | 'url' | 'type'>;

export type MessageHistory = {
	messages: {
		[id: string]: Message;
	};
	currentId: Nullable<string>;
	state?: any;
};

export interface Chat extends TimestampEntity {
	title: string;
	models: string[];
	params: Record<string, any>;
	messages: Message[];
	history: MessageHistory;
	tags: string[];
	timestamp: number; // epoch time in seconds
	files: ClientFile[];
}

interface TagByUser extends UserEntity {
	name: string;
	data?: string | null;
}

interface ChatTag extends UserEntity {
	name: string;
	data?: any;
}

export interface ChatResponse extends UserEntity, TimestampEntity {
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

export interface Memory extends UserEntity, TimestampEntity {
	id: string;
	user_id: string;
	content: string;
	updated_at: number;
	created_at: number;
}

type ApplicableDevice = {
	device?: string;
	software?: string;
	datasheet_link?: string;
	software_link?: string;
};

type ArticleStep = {
	section: string;
	step_number: number;
	text: string;
	src: string | null;
	alt: string | null;
	note: string | null;
	emphasized_text: string[];
	emphasized_tags: string[];
};

export interface Article {
	id: string;
	title: string;
	document_id: string;
	objective: string;
	category: string;
	url: string;
	applicable_devices: ApplicableDevice[];
	introduction: string;
	steps: ArticleStep[];
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
	meta: {
		description: string;
		manifest: {
			title: string;
			author: string;
			version: string;
			license: string;
			description: string;
			GitHub: string;
			Notes: string;
		};
	};
}
