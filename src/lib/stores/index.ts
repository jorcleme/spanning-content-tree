import { APP_NAME } from '$lib/constants';
import { type Writable, writable } from 'svelte/store';
import type { ChatListResponse, TagsByUserResponse } from '$lib/types';
import type { GlobalModelConfig, ModelConfig } from '$lib/apis';
import type { Banner } from '$lib/types';
import type { Socket } from 'socket.io-client';

// Backend
export const WEBUI_NAME = writable(APP_NAME);
export const config: Writable<Config | undefined> = writable(undefined);
export const user: Writable<SessionUser | undefined> = writable(undefined);

// Cisco Frontend
export const promptStore = writable('');
export const variablesStore = writable<CiscoPromptVariable>({});
export const explanationStore = writable('');

// Frontend
export const MODEL_DOWNLOAD_POOL = writable<ModelDownloadPool>({});

export const mobile = writable(false);

export const socket: Writable<null | Socket> = writable(null);
export const activeUserCount: Writable<null | number> = writable(null);
export const USAGE_POOL: Writable<null | string[]> = writable(null);

export const theme = writable('system');
export const chatId = writable('');

export const chats = writable<ChatListResponse>([]);
export const pinnedChats = writable<ChatListResponse>([]);
export const tags = writable<TagsByUserResponse>([]);

export const models: Writable<Model[]> = writable([]);
export const prompts: Writable<Prompt[]> = writable([]);
export const documents: Writable<Document[]> = writable([]);

export const tools = writable<Tool[]>([]);
export const functions = writable([]);

export const banners: Writable<Banner[]> = writable([]);

export const settings: Writable<Settings> = writable({ chatDirection: 'LTR' });

export const showSidebar = writable(false);
export const showSettings = writable(false);
export const showArchivedChats = writable(false);
export const showChangelog = writable(false);
export const showCallOverlay = writable(false);

type CiscoPromptVariable = {
	subject?: string;
} & {
	[key: string]: string;
};

type ToolMeta = {
	description: string | null;
	manifest: {
		title: string;
		author: string;
		version: string;
		license: string;
		description: string;
		GitHub: string;
		Notes: string;
		funding_url?: string;
	};
};

export type Tool = {
	id: string;
	user_id: string;
	name: string;
	meta: ToolMeta;
	content: string;
	updated_at: number;
	created_at: number;
};

export type Model = OpenAIModel | OllamaModel;

type BaseModel = {
	id: string;
	name: string;
	info?: ModelConfig;
	ollama?: OllamaPullDetails;
	openai?: OpenAIModelDetails;
};

export interface OpenAIModel extends BaseModel {
	external: boolean;
	source?: string;
	owned_by?: 'openai';
	pipe?: Record<string, any>;
}

export interface OllamaModel extends BaseModel {
	details: OllamaModelDetails;
	size: number;
	description: string;
	model: string;
	modified_at: string;
	digest: string;
	owned_by?: 'ollama';
	pipe?: Record<string, any>;
}

type OpenAIModelDetails = {
	created: number;
	id: string;
	object: string;
	owned_by: 'openai';
};

type OllamaPullDetails = {
	details: OllamaModelDetails;
	digest: string;
	model: string;
	modified_at: string;
	name: string;
	size: number;
	urls: string[];
};

type OllamaModelDetails = {
	parent_model: string;
	format: string;
	family: string;
	families: string[] | null;
	parameter_size: string;
	quantization_level: string;
};

export type Settings = {
	models?: string[];
	conversationMode?: boolean;
	speechAutoSend?: boolean;
	responseAutoPlayback?: boolean;
	audio?: AudioSettings;
	showUsername?: boolean;
	saveChatHistory?: boolean;
	notificationEnabled?: boolean;
	title?: TitleSettings;
	splitLargeDeltas?: boolean;
	chatDirection: 'LTR' | 'RTL';
	system?: string;
	requestFormat?: string;
	keepAlive?: string;
	seed?: number;
	temperature?: string;
	repeat_penalty?: string;
	top_k?: string;
	top_p?: string;
	num_ctx?: string;
	num_batch?: string;
	num_keep?: string;
	options?: ModelOptions;
	memory?: boolean;
	userLocation?: string | { latitude: any; longitude: any };
	params?: Record<string, any>;
	responseAutoCopy?: boolean;
	splitLargeChunks?: boolean;
	backgroundImageUrl?: string;
	chatBubble?: boolean;
};

// Cisco Defined Types

// PersistentConfig Settings
export type PersistentConfigSettings = {
	ui: Settings;
};

type ModelDownloadPool = Record<string, any>;

// End Cisco Defined Types
type ModelOptions = {
	stop?: boolean;
};

type AudioSettings = {
	STTEngine?: string;
	TTSEngine?: string;
	speaker?: string;
	model?: string;
	nonLocalVoices?: boolean;
	stt?: Record<string, string>;
	tts?: Record<string, string>;
};

type TitleSettings = {
	auto?: boolean;
	model?: string;
	modelExternal?: string;
	prompt?: string;
};

type Prompt = {
	command: string;
	user_id: string;
	title: string;
	content: string;
	timestamp: number;
};

type DocumentContent = {
	tags?: {
		name: string;
	}[];
};
export type Document = {
	collection_name: string;
	filename: string;
	name: string;
	title: string;
	content: DocumentContent;
};

type Audio = {
	tts?: Record<string, string>;
	stt?: Record<string, string>;
};

type Config = {
	status: boolean;
	name: string;
	version: string;
	default_locale: string;
	default_models: string;
	audio?: Audio;
	default_prompt_suggestions: PromptSuggestion[];
	features: {
		auth: boolean;
		auth_trusted_header: boolean;
		enable_signup: boolean;
		enable_web_search?: boolean;
		enable_image_generation: boolean;
		enable_admin_export: boolean;
		enable_community_sharing: boolean;
	};
	oauth: {
		providers: {
			[key: string]: string;
		};
	};
};

export type PromptSuggestion = {
	content: string;
	title: [string, string];
};

export type SessionUser = {
	id: string;
	email: string;
	name: string;
	username?: string;
	role: string;
	profile_image_url: string;
	last_active_at: number; // epoch time in seconds
	updated_at: number; // epoch time in seconds
	created_at: number; // epoch time in seconds
	api_key: string;
	settings?: PersistentConfigSettings;
	info?: Record<string, string>;
	oauth_sub?: string;
	community?: string;
};

export type Params<T> = {
	[key in keyof T]: T[key] | null;
};

export type ChatParams =
	| {
			// Advanced
			system: string | null;
			seed: number | null;
			stop: string | null;
			temperature: number | null;
			frequency_penalty: number | null;
			repeat_last_n: number | null;
			mirostat: number | null;
			mirostat_eta: number | null;
			mirostat_tau: number | null;
			top_k: number | null;
			top_p: number | null;
			tfs_z: number | null;
			num_ctx: number | null;
			num_batch: number | null;
			num_keep: number | null;
			max_tokens: number | null;
			use_mmap: boolean | null;
			use_mlock: boolean | null;
			num_thread: number | null;
			template: string | null;
			proficiency: number;
	  }
	| {
			[key: string]: any;
	  };
