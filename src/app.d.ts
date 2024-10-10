// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
	interface Document {
		pyodideMplTarget: HTMLElement | null;
	}
	namespace App {
		interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface Platform {}
	}
}

export {};
