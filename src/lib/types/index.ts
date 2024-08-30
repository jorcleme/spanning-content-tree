// Shared Utility
export type Nullable<T> = T | null;

export type Banner = {
	id: string;
	type: string;
	title?: string;
	content: string;
	url?: string;
	dismissible?: boolean;
	timestamp: number;
};

type MessageInfo = {
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
};

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

export type Message = BaseMessage & {
	id: string;
	parentId?: string | null;
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

export interface ClientFile {
	collection_name: string;
	error?: string;
	file: {
		id: string;
		user_id: string;
		filename: string;
		meta: any;
		created_at: number;
	};
	id: string;
	name: string;
	status: string;
	type: string;
	url: string;
}

export type MessageHistory = {
	messages: {
		[id: string]: Message;
	};
	currentId: Nullable<string>;
	state?: any;
};

type Chat = {
	id: string;
	title: string;
	models: string[];
	params: Record<string, any>;
	messages: Message[];
	history: MessageHistory;
	tags: string[];
	timestamp: number; // epoch time in seconds
	files: ClientFile[];
};

type TagByUser = {
	id: string;
	name: string;
	user_id: string;
	data?: string | null;
};

type ChatTag = {
	id: string;
	name: string;
	user_id: string;
	data?: any;
};

type FilteredChat = {
	id: string;
	title: string;
	updated_at: number;
	created_at: number;
};

export type ChatResponse = {
	id: string;
	user_id: string;
	title: string;
	chat: Chat;
	updated_at: number; // epoch time in seconds
	created_at: number; // epoch time in seconds
	share_id?: Nullable<string>;
	archived: boolean;
};
export type ChatListResponse = ChatResponse[];
export type ChatTagListResponse = Array<ChatTag>;
export type FilteredChatList = Array<FilteredChat>;
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

export interface Memory {
	id: string;
	user_id: string;
	content: string;
	updated_at: number;
	created_at: number;
}
