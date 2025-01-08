// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
	interface Document {
		pyodideMplTarget: HTMLElement | null;
		caretRangeFromPoint: (x: number, y: number) => Range | null;
		caretPositionFromPoint: (x: number, y: number) => CaretPosition | null;
	}
	interface Node {
		__lexicalListType: string;
		__lexicalEditor: any;
	}
	namespace App {
		interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface Platform {}
	}
}

export {};
