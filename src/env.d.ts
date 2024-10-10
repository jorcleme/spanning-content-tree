// env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
	readonly APP_VERSION: string;
	readonly APP_BUILD_HASH: string;
	readonly BUILD_HASH: string;
	// Add other environment variables here
}

interface ImportMeta {
	readonly env: ImportMetaEnv;
}
