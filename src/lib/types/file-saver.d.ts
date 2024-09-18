declare module 'file-saver' {
	interface FileSaverOptions {
		/**
		 * Automatically provide Unicode text encoding hints
		 * @default false
		 */
		autoBom: boolean;
	}
	export function saveAs(data: Blob | string, filename?: string, options?: FileSaverOptions): void;
}
