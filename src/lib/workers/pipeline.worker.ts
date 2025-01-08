import {
	type AliasType,
	type Chat,
	type PipelineType,
	type TextGenerationPipeline,
	TextStreamer,
	env,
	pipeline
} from '@huggingface/transformers';

// Skip local model check
env.allowLocalModels = false;

// Use the Singleton pattern to enable lazy construction of the pipeline.
class PipelineSingleton {
	static task: PipelineType | AliasType = 'text-classification';
	static model = 'Xenova/distilbert-base-uncased-finetuned-sst-2-english';
	static instance: any | null = null;

	static async getInstance(progress_callback?: (...args: any[]) => void): Promise<TextGenerationPipeline> {
		if (this.instance === null) {
			this.instance = pipeline(this.task, this.model, { progress_callback, dtype: 'q4' });
		}
		return this.instance;
	}
}

interface EventData {
	data: {
		messages: string[] | string | Chat[] | Chat;
		options: Record<string, string>;
	};
}

// Listen for messages from the main thread
self.addEventListener('message', async (event: EventData) => {
	const { messages, options } = event.data;
	console.log(messages, options);

	const generator = await PipelineSingleton.getInstance((progress) => {
		self.postMessage({ status: 'progress', progress });
	});

	const streamer = new TextStreamer(generator.tokenizer, {
		skip_prompt: true,
		callback_function: (text: string) => {
			self.postMessage({ status: 'stream', text });
		}
	});

	try {
		const result = await generator(messages, { ...options, streamer });
		self.postMessage({ status: 'complete', result });
	} catch (error) {
		if (error instanceof Error) {
			self.postMessage({ status: 'error', error: error.message });
		} else {
			self.postMessage({ status: 'error', error: String(error) });
		}
	}
});
