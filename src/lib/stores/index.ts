import type { Article, ChatListResponse, TagsByUserResponse, Tool } from '$lib/types';
import type { ModelConfig } from '$lib/types';
import { type Writable, derived, writable } from 'svelte/store';
import { APP_NAME } from '$lib/constants';
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
export const functions = writable<_Function[]>([]);

export const banners: Writable<Banner[]> = writable([]);

export const settings: Writable<Settings> = writable({ chatDirection: 'LTR' });

export const showSidebar = writable(false);
export const showSettings = writable(false);
export const showArchivedChats = writable(false);
export const showChangelog = writable(false);
export const showCallOverlay = writable(false);

type FunctionMeta = {
	description: string;
} & { [key: string]: any };

export type _Function = {
	id: string;
	user_id: string;
	type: string;
	name: string;
	meta: FunctionMeta;
	content: string;
	is_active: boolean;
	is_global: boolean;
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
	preset?: boolean;
	actions?: any[];
};

export interface Banner {
	id: string;
	type: string;
	title?: string;
	content: string;
	url?: string;
	dismissible?: boolean;
	timestamp: number;
}

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
	showEmojiInCall?: boolean;
	voiceInterruption?: boolean;
	widescreenMode?: boolean;
};

// Cisco Defined Types
type CiscoPromptVariable = {
	subject?: string;
} & {
	[key: string]: string;
};

export const ExpGradeSelected = writable('Fully Guided');
export const activeSupportSection = writable('Objective');
export const activeSupportStep = writable(1);
export const isSupportWidgetOpen = writable(false);
export const hideSupportWidgetBtn = writable(false);
export const mostRecentStep = writable(-1);
export const activeArticle = writable<null | Article>(null);

export const activeArticleId = derived([activeArticle], ([$activeArticle]) => {
	if ($activeArticle) {
		return $activeArticle.id;
	}
	return '';
});

export const mountedArticleSteps = derived([activeArticle], ([$activeArticle]) => {
	if ($activeArticle) {
		return $activeArticle.steps;
	}
	return [];
});

export const mountedArticlePreambleObjective = derived([activeArticle], ([$activeArticle]) => {
	if ($activeArticle) {
		return $activeArticle.objective;
	}
	return '';
});

export const mountedArticlePreambleDevices = derived(
	[activeArticle],
	([$activeArticle]) =>
		($activeArticle?.applicable_devices ?? [])
			.map((device) => `${device?.device} (Firmware Version: ${device?.software})`)
			.join(' and ') || ''
);

export const isSupportStepDetailsOpen = writable(false);

// PersistentConfig Settings
export type PersistentConfigSettings = {
	ui: Settings;
};

export interface _CiscoArticleMessage {
	id: string;
	role: string;
	content: string;
	timestamp: number;
	model: string;
	sources?: Record<string, any>[];
	associatedQuestion?: string | null;
	qnaBtnId?: string;
	error?: any;
	done?: boolean;
	info?: Record<string, any>;
	originalContent?: string;
	annotation?: {
		rating?: number;
		reasons?: string[];
		comment?: string;
	};
}

interface _CiscoArticleQuestion {
	id: string;
	text: string;
	clicked: boolean;
	stepIndex: number;
}
export const globalMessages = writable<Map<number, _CiscoArticleMessage[]>>(new Map());
export const ciscoArticleMessages = writable<_CiscoArticleMessage[]>([]);
export const ciscoArticleQuestions = writable<_CiscoArticleQuestion[]>([]);

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
	stt?: Record<string, any>;
	tts?: Record<string, any>;
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
	collection_name?: string;
	filename: string;
	name: string;
	title: string;
	content: DocumentContent;
	type?: string;
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
	token?: string;
	token_type?: string;
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
