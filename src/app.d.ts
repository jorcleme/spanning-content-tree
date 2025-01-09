// See https://kit.svelte.dev/docs/types#app

// for information about these interfaces
declare global {
	interface Document {
		pyodideMplTarget: HTMLElement | null;
		caretRangeFromPoint: (x: number, y: number) => Range | null;
		caretPositionFromPoint: (x: number, y: number) => CaretPosition | null;
	}

	interface GPUDevice {
		label: string;
	}

	interface GPUDeviceDescriptor {
		label?: string;
	}

	interface GPUAdapter {
		requestDevice(descriptor?: GPUDeviceDescriptor): Promise<GPUDevice>;
	}

	interface GPURequestAdapterOptions {
		powerPreference?: 'low-power' | 'high-performance';
	}
	interface GPU {
		requestAdapter(options?: GPURequestAdapterOptions): Promise<GPUAdapter | null>;
	}

	interface Navigator {
		gpu?: GPU;
		msMaxTouchPoints: number;
	}
	interface Node {
		__lexicalListType: string;
		__lexicalEditor: any;
	}
	namespace App {
		interface Error {
			message: string;
			status: number;
		}
		interface Locals {}
		// interface PageData {}
		interface Platform {}
	}
}

export {};
