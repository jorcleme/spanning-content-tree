import type { Article, Message, MessageHistory } from '$lib/types';
import type { Chat } from '$lib/types';

import { WEBUI_BASE_URL } from '$lib/constants';
import sha256 from 'js-sha256';
import { v4 as uuidv4 } from 'uuid';

//////////////////////////
// Helper functions
//////////////////////////

export const sanitizeResponseContent = (content: string) => {
	// First, temporarily replace valid <video> tags with a placeholder
	const videoTagRegex = /<video\s+src="([^"]+)"\s+controls><\/video>/gi;
	const placeholders: string[] = [];
	content = content.replace(videoTagRegex, (_, src) => {
		const placeholder = `{{VIDEO_${placeholders.length}}}`;
		placeholders.push(`<video src="${src}" controls></video>`);
		return placeholder;
	});

	// Now apply the sanitization to the rest of the content
	content = content
		.replace(/<\|[a-z]*$/, '')
		.replace(/<\|[a-z]+\|$/, '')
		.replace(/<$/, '')
		.replaceAll(/<\|[a-z]+\|>/g, ' ')
		.replaceAll('<', '&lt;')
		.replaceAll('>', '&gt;')
		.trim();

	// Replace placeholders with original <video> tags
	placeholders.forEach((placeholder, index) => {
		content = content.replace(`{{VIDEO_${index}}}`, placeholder);
	});

	return content.trim();
};

export const replaceTokens = (content: string, char?: string, user?: string) => {
	const charToken = /{{char}}/gi;
	const userToken = /{{user}}/gi;
	const videoIdToken = /{{VIDEO_FILE_ID_([a-f0-9-]+)}}/gi; // Regex to capture the video ID
	const htmlIdToken = /{{HTML_FILE_ID_([a-f0-9-]+)}}/gi; // Regex to capture the HTML ID

	// Replace {{char}} if char is provided
	if (char !== undefined && char !== null) {
		content = content.replace(charToken, char);
	}

	// Replace {{user}} if user is provided
	if (user !== undefined && user !== null) {
		content = content.replace(userToken, user);
	}

	// Replace video ID tags with corresponding <video> elements
	content = content.replace(videoIdToken, (match, fileId) => {
		const videoUrl = `${WEBUI_BASE_URL}/api/v1/files/${fileId}/content`;
		return `<video src="${videoUrl}" controls></video>`;
	});

	// Replace HTML ID tags with corresponding HTML content
	content = content.replace(htmlIdToken, (match, fileId) => {
		const htmlUrl = `${WEBUI_BASE_URL}/api/v1/files/${fileId}/content`;
		return `<iframe src="${htmlUrl}" width="100%" frameborder="0" onload="this.style.height=(this.contentWindow.document.body.scrollHeight+20)+'px';"></iframe>`;
	});

	return content;
};

export const revertSanitizedResponseContent = (content: string) => {
	return content.replaceAll('&lt;', '<').replaceAll('&gt;', '>');
};

export const capitalizeFirstLetter = (string: string) => {
	return string.charAt(0).toUpperCase() + string.slice(1);
};

export const splitStream = (splitOn: string) => {
	let buffer = '';
	return new TransformStream<any, any>({
		transform(chunk, controller) {
			buffer += chunk;
			const parts = buffer.split(splitOn);
			parts.slice(0, -1).forEach((part) => controller.enqueue(part));
			buffer = parts[parts.length - 1];
		},
		flush(controller) {
			if (buffer) controller.enqueue(buffer);
		}
	});
};

export const convertMessagesToHistory = (messages: Message[]) => {
	const history: MessageHistory = {
		messages: {},
		currentId: null
	};

	let parentMessageId = null;
	let messageId = null;

	for (const message of messages) {
		messageId = uuidv4();

		if (parentMessageId !== null) {
			history.messages[parentMessageId].childrenIds = [...history.messages[parentMessageId].childrenIds!, messageId];
		}

		history.messages[messageId] = {
			...message,
			id: messageId,
			parentId: parentMessageId,
			childrenIds: []
		};

		parentMessageId = messageId;
	}

	history.currentId = messageId;
	return history;
};

export const getGravatarURL = (email: any) => {
	// Trim leading and trailing whitespace from
	// an email address and force all characters
	// to lower case
	const address = String(email).trim().toLowerCase();

	// Create a SHA256 hash of the final string
	// @ts-expect-error - TS doesn't know about the global `sha256` function
	const hash = sha256(address);

	// Grab the actual image URL
	return `https://www.gravatar.com/avatar/${hash}`;
};

export const canvasPixelTest = () => {
	// Test a 1x1 pixel to potentially identify browser/plugin fingerprint blocking or spoofing
	// Inspiration: https://github.com/kkapsner/CanvasBlocker/blob/master/test/detectionTest.js
	const canvas = document.createElement('canvas');
	const ctx = canvas.getContext('2d') as CanvasRenderingContext2D;
	canvas.height = 1;
	canvas.width = 1;
	const imageData = new ImageData(canvas.width, canvas.height);
	const pixelValues = imageData.data;

	// Generate RGB test data
	for (let i = 0; i < imageData.data.length; i += 1) {
		if (i % 4 !== 3) {
			pixelValues[i] = Math.floor(256 * Math.random());
		} else {
			pixelValues[i] = 255;
		}
	}

	ctx.putImageData(imageData, 0, 0);
	const p = ctx.getImageData(0, 0, canvas.width, canvas.height).data;

	// Read RGB data and fail if unmatched
	for (let i = 0; i < p.length; i += 1) {
		if (p[i] !== pixelValues[i]) {
			console.log(
				'canvasPixelTest: Wrong canvas pixel RGB value detected:',
				p[i],
				'at:',
				i,
				'expected:',
				pixelValues[i]
			);
			console.log('canvasPixelTest: Canvas blocking or spoofing is likely');
			return false;
		}
	}

	return true;
};

export const generateInitialsImage = (name: string) => {
	const canvas = document.createElement('canvas') as HTMLCanvasElement;
	const ctx = canvas.getContext('2d') as CanvasRenderingContext2D;
	canvas.width = 100;
	canvas.height = 100;

	if (!canvasPixelTest()) {
		console.log('generateInitialsImage: failed pixel test, fingerprint evasion is likely. Using default image.');
		return '/user.png';
	}

	ctx.fillStyle = '#0D5CBD';
	ctx.fillRect(0, 0, canvas.width, canvas.height);

	ctx.fillStyle = '#FFFFFF';
	ctx.font = '40px Helvetica';
	ctx.textAlign = 'center';
	ctx.textBaseline = 'middle';

	const sanitizedName = name.trim();
	const initials =
		sanitizedName.length > 0
			? sanitizedName[0] +
			  (sanitizedName.split(' ').length > 1 ? sanitizedName[sanitizedName.lastIndexOf(' ') + 1] : '')
			: '';

	ctx.fillText(initials.toUpperCase(), canvas.width / 2, canvas.height / 2);

	return canvas.toDataURL();
};

export const copyToClipboard = async (text: string) => {
	let result = false;
	if (!navigator.clipboard) {
		const textArea = document.createElement('textarea');
		textArea.value = text;

		// Avoid scrolling to bottom
		textArea.style.top = '0';
		textArea.style.left = '0';
		textArea.style.position = 'fixed';

		document.body.appendChild(textArea);
		textArea.focus();
		textArea.select();

		try {
			const successful = document.execCommand('copy');
			const msg = successful ? 'successful' : 'unsuccessful';
			console.log('Fallback: Copying text command was ' + msg);
			result = true;
		} catch (err) {
			console.error('Fallback: Oops, unable to copy', err);
		}

		document.body.removeChild(textArea);
		return result;
	}

	result = await navigator.clipboard
		.writeText(text)
		.then(() => {
			console.log('Async: Copying to clipboard was successful!');
			return true;
		})
		.catch((error) => {
			console.error('Async: Could not copy text: ', error);
			return false;
		});

	return result;
};

export const compareVersion = (latest: string, current: string) => {
	return current === '0.0.0'
		? false
		: current.localeCompare(latest, undefined, {
				numeric: true,
				sensitivity: 'case',
				caseFirst: 'upper'
		  }) < 0;
};

export const findWordIndices = (text: string) => {
	const regex = /\[([^\]]+)\]/g;
	const matches = [];
	let match;

	while ((match = regex.exec(text)) !== null) {
		matches.push({
			word: match[1],
			startIndex: match.index,
			endIndex: regex.lastIndex - 1
		});
	}

	return matches;
};

export const removeFirstHashWord = (inputString: string) => {
	// Split the string into an array of words
	const words = inputString.split(' ');

	// Find the index of the first word that starts with #
	const index = words.findIndex((word) => word.startsWith('#'));

	// Remove the first word with #
	if (index !== -1) {
		words.splice(index, 1);
	}

	// Join the remaining words back into a string
	const resultString = words.join(' ');

	return resultString;
};

export const transformFileName = (fileName: string) => {
	// Convert to lowercase
	const lowerCaseFileName = fileName.toLowerCase();

	// Remove special characters using regular expression
	const sanitizedFileName = lowerCaseFileName.replace(/[^\w\s]/g, '');

	// Replace spaces with dashes
	const finalFileName = sanitizedFileName.replace(/\s+/g, '-');

	return finalFileName;
};

export const calculateSHA256 = async (file: Blob) => {
	// Create a FileReader to read the file asynchronously
	const reader = new FileReader();

	// Define a promise to handle the file reading
	const readFile: Promise<ArrayBuffer> = new Promise((resolve, reject) => {
		reader.onload = () => resolve(reader.result as ArrayBuffer);
		reader.onerror = reject;
	});

	// Read the file as an ArrayBuffer
	reader.readAsArrayBuffer(file);

	try {
		// Wait for the FileReader to finish reading the file
		const buffer = await readFile;

		// Convert the ArrayBuffer to a Uint8Array
		const uint8Array = new Uint8Array(buffer);

		// Calculate the SHA-256 hash using Web Crypto API
		const hashBuffer = await crypto.subtle.digest('SHA-256', uint8Array);

		// Convert the hash to a hexadecimal string
		const hashArray = Array.from(new Uint8Array(hashBuffer));
		const hashHex = hashArray.map((byte) => byte.toString(16).padStart(2, '0')).join('');

		return `${hashHex}`;
	} catch (error) {
		console.error('Error calculating SHA-256 hash:', error);
		throw error;
	}
};

export const getImportOrigin = (_chats: Array<{ mapping?: string }>) => {
	// Check what external service chat imports are from
	if ('mapping' in _chats[0]) {
		return 'openai';
	}
	return 'webui';
};

export const getUserPosition = async (raw: boolean = false) => {
	// Get the user's location using the Geolocation API
	const position: GeolocationPosition = await new Promise<GeolocationPosition>((resolve, reject) => {
		navigator.geolocation.getCurrentPosition(resolve, reject);
	}).catch((error) => {
		console.error('Error getting user location:', error);
		throw error;
	});

	if (!position) {
		return 'Location not available';
	}

	// Extract the latitude and longitude from the position
	const { latitude, longitude } = position.coords;

	if (raw) {
		return { latitude, longitude };
	} else {
		return `${latitude.toFixed(3)}, ${longitude.toFixed(3)} (lat, long)`;
	}
};

const convertOpenAIMessages = (convo: any) => {
	// Parse OpenAI chat messages and create chat dictionary for creating new chats
	const mapping = convo['mapping'];
	const messages = [];
	let currentId = '';
	let lastId = null;

	for (const message_id in mapping) {
		const message = mapping[message_id];
		currentId = message_id;
		try {
			if (
				messages.length == 0 &&
				(message['message'] == null ||
					(message['message']['content']['parts']?.[0] == '' && message['message']['content']['text'] == null))
			) {
				// Skip chat messages with no content
				continue;
			} else {
				const new_chat = {
					id: message_id,
					parentId: lastId,
					childrenIds: message['children'] || [],
					role: message['message']?.['author']?.['role'] !== 'user' ? 'assistant' : 'user',
					content: message['message']?.['content']?.['parts']?.[0] || message['message']?.['content']?.['text'] || '',
					model: 'gpt-3.5-turbo',
					done: true,
					context: null
				};
				messages.push(new_chat);
				lastId = currentId;
			}
		} catch (error) {
			console.log('Error with', message, '\nError:', error);
		}
	}

	const history: { [id: string]: any } = {};
	messages.forEach((obj) => (history[obj.id] = obj));

	const chat = {
		history: {
			currentId: currentId,
			messages: history // Need to convert this to not a list and instead a json object
		},
		models: ['gpt-3.5-turbo'],
		messages: messages,
		options: {},
		timestamp: convo['create_time'],
		title: convo['title'] ?? 'New Chat'
	};
	return chat;
};

const validateChat = (chat: any) => {
	// Because ChatGPT sometimes has features we can't use like DALL-E or migh have corrupted messages, need to validate
	const messages = chat.messages;

	// Check if messages array is empty
	if (messages.length === 0) {
		return false;
	}

	// Last message's children should be an empty array
	const lastMessage = messages[messages.length - 1];
	if (lastMessage.childrenIds?.length !== 0) {
		return false;
	}

	// First message's parent should be null
	const firstMessage = messages[0];
	if (firstMessage.parentId !== null) {
		return false;
	}

	// Every message's content should be a string
	for (const message of messages) {
		if (typeof message.content !== 'string') {
			return false;
		}
	}

	return true;
};

export const convertOpenAIChats = (_chats: Chat[]) => {
	// Create a list of dictionaries with each conversation from import
	const chats = [];
	let failed = 0;
	for (const convo of _chats) {
		const chat = convertOpenAIMessages(convo);

		if (validateChat(chat)) {
			chats.push({
				id: convo['id'],
				user_id: '',
				title: convo['title'],
				chat: chat,
				timestamp: convo['timestamp']
			});
		} else {
			failed++;
		}
	}
	console.log(failed, 'Conversations could not be imported');
	return chats;
};

export const isValidHttpUrl = (str: string) => {
	let url;

	try {
		url = new URL(str);
	} catch (_) {
		return false;
	}

	return url.protocol === 'http:' || url.protocol === 'https:';
};

export const removeEmojis = (str: string) => {
	// Regular expression to match emojis
	const emojiRegex = /[\uD800-\uDBFF][\uDC00-\uDFFF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDE4F]/g;

	// Replace emojis with an empty string
	return str.replace(emojiRegex, '');
};

export const removeFormattings = (str: string) => {
	return str.replace(/(\*)(.*?)\1/g, '').replace(/(```)(.*?)\1/gs, '');
};

export const extractSentences = (text: string) => {
	// This regular expression matches code blocks marked by triple backticks
	const codeBlockRegex = /```[\s\S]*?```/g;

	const codeBlocks: string[] = [];
	let index = 0;

	// Temporarily replace code blocks with placeholders and store the blocks separately
	text = text.replace(codeBlockRegex, (match) => {
		const placeholder = `\u0000${index}\u0000`; // Use a unique placeholder
		codeBlocks[index++] = match;
		return placeholder;
	});

	// Split the modified text into sentences based on common punctuation marks, avoiding these blocks
	let sentences = text.split(/(?<=[.!?])\s+/);

	// Restore code blocks and process sentences
	sentences = sentences.map((sentence) => {
		// Check if the sentence includes a placeholder for a code block
		// eslint-disable-next-line no-control-regex
		return sentence.replace(/\u0000(\d+)\u0000/g, (_, idx) => codeBlocks[idx]);
	});

	return sentences.map((sentence) => removeFormattings(removeEmojis(sentence.trim()))).filter((sentence) => sentence);
};

export const extractSentencesForAudio = (text: string) => {
	return extractSentences(text).reduce((mergedTexts, currentText) => {
		const lastIndex = mergedTexts.length - 1;
		if (lastIndex >= 0) {
			const previousText = mergedTexts[lastIndex];
			const wordCount = previousText.split(/\s+/).length;
			if (wordCount < 2) {
				mergedTexts[lastIndex] = previousText + ' ' + currentText;
			} else {
				mergedTexts.push(currentText);
			}
		} else {
			mergedTexts.push(currentText);
		}
		return mergedTexts;
	}, [] as string[]);
};

export const blobToFile = (blob: Blob, fileName: string) => {
	// Create a new File object from the Blob
	const file = new File([blob], fileName, { type: blob.type });
	return file;
};

export const promptTemplate = (
	template: string,
	user_name?: string,
	user_location?: string | { latitude: number; longitude: number }
): string => {
	// Get the current date
	const currentDate = new Date();

	// Format the date to YYYY-MM-DD
	const formattedDate =
		currentDate.getFullYear() +
		'-' +
		String(currentDate.getMonth() + 1).padStart(2, '0') +
		'-' +
		String(currentDate.getDate()).padStart(2, '0');

	// Format the time to HH:MM:SS AM/PM
	const currentTime = currentDate.toLocaleTimeString('en-US', {
		hour: 'numeric',
		minute: 'numeric',
		second: 'numeric',
		hour12: true
	});

	// Replace {{CURRENT_DATETIME}} in the template with the formatted datetime
	template = template.replace('{{CURRENT_DATETIME}}', `${formattedDate} ${currentTime}`);

	// Replace {{CURRENT_DATE}} in the template with the formatted date
	template = template.replace('{{CURRENT_DATE}}', formattedDate);

	// Replace {{CURRENT_TIME}} in the template with the formatted time
	template = template.replace('{{CURRENT_TIME}}', currentTime);

	if (user_name) {
		// Replace {{USER_NAME}} in the template with the user's name
		template = template.replace('{{USER_NAME}}', user_name);
	}

	if (user_location) {
		// If the user location is an object, extract the latitude and longitude
		if (typeof user_location !== 'string') {
			const { latitude, longitude } = user_location;
			const replacer = `${latitude.toFixed(3)}, ${longitude.toFixed(3)} (lat, long)`;
			// Replace {{USER_LOCATION}} in the template with the current location
			template = template.replace('{{USER_LOCATION}}', replacer);
		} else {
			// Replace {{USER_LOCATION}} in the template with the current location
			template = template.replace('{{USER_LOCATION}}', user_location);
		}
		// Replace {{USER_LOCATION}} in the template with the current location
		// template = template.replace('{{USER_LOCATION}}', user_location);
	}

	return template;
};

/**
 * This function is used to replace placeholders in a template string with the provided prompt.
 * The placeholders can be in the following formats:
 * - `{{prompt}}`: This will be replaced with the entire prompt.
 * - `{{prompt:start:<length>}}`: This will be replaced with the first <length> characters of the prompt.
 * - `{{prompt:end:<length>}}`: This will be replaced with the last <length> characters of the prompt.
 * - `{{prompt:middletruncate:<length>}}`: This will be replaced with the prompt truncated to <length> characters, with '...' in the middle.
 *
 * @param {string} template - The template string containing placeholders.
 * @param {string} prompt - The string to replace the placeholders with.
 * @returns {string} The template string with the placeholders replaced by the prompt.
 */
export const titleGenerationTemplate = (template: string, prompt: string): string => {
	template = template.replace(
		/{{prompt}}|{{prompt:start:(\d+)}}|{{prompt:end:(\d+)}}|{{prompt:middletruncate:(\d+)}}/g,
		(match, startLength, endLength, middleLength) => {
			if (match === '{{prompt}}') {
				return prompt;
			} else if (match.startsWith('{{prompt:start:')) {
				return prompt.substring(0, startLength);
			} else if (match.startsWith('{{prompt:end:')) {
				return prompt.slice(-endLength);
			} else if (match.startsWith('{{prompt:middletruncate:')) {
				if (prompt.length <= middleLength) {
					return prompt;
				}
				const start = prompt.slice(0, Math.ceil(middleLength / 2));
				const end = prompt.slice(-Math.floor(middleLength / 2));
				return `${start}...${end}`;
			}
			return '';
		}
	);

	template = promptTemplate(template);

	return template;
};

export const approximateToHumanReadable = (nanoseconds: number) => {
	const seconds = Math.floor((nanoseconds / 1e9) % 60);
	const minutes = Math.floor((nanoseconds / 6e10) % 60);
	const hours = Math.floor((nanoseconds / 3.6e12) % 24);

	const results: string[] = [];

	if (seconds >= 0) {
		results.push(`${seconds}s`);
	}

	if (minutes > 0) {
		results.push(`${minutes}m`);
	}

	if (hours > 0) {
		results.push(`${hours}h`);
	}

	return results.reverse().join(' ');
};

export const getTimeRange = (timestamp: number) => {
	const now = new Date();
	const date = new Date(timestamp * 1000); // Convert Unix timestamp to milliseconds

	// Calculate the difference in milliseconds
	const diffTime = now.getTime() - date.getTime();
	const diffDays = diffTime / (1000 * 3600 * 24);

	const nowDate = now.getDate();
	const nowMonth = now.getMonth();
	const nowYear = now.getFullYear();

	const dateDate = date.getDate();
	const dateMonth = date.getMonth();
	const dateYear = date.getFullYear();

	if (nowYear === dateYear && nowMonth === dateMonth && nowDate === dateDate) {
		return 'Today';
	} else if (nowYear === dateYear && nowMonth === dateMonth && nowDate - dateDate === 1) {
		return 'Yesterday';
	} else if (diffDays <= 7) {
		return 'Previous 7 days';
	} else if (diffDays <= 30) {
		return 'Previous 30 days';
	} else if (nowYear === dateYear) {
		return date.toLocaleString('default', { month: 'long' });
	} else {
		return date.getFullYear().toString();
	}
};

export const extractFrontmatter = (content: string) => {
	const frontmatter: { [key: string]: string } = {};
	let frontmatterStarted = false;
	let frontmatterEnded = false;
	const frontmatterPattern = /^\s*([a-z_]+):\s*(.*)\s*$/i;

	// Split content into lines
	const lines = content.split('\n');

	// Check if the content starts with triple quotes
	if (lines[0].trim() !== '"""') {
		return {};
	}

	frontmatterStarted = true;

	for (let i = 1; i < lines.length; i++) {
		const line = lines[i];

		if (line.includes('"""')) {
			if (frontmatterStarted) {
				frontmatterEnded = true;
				break;
			}
		}

		if (frontmatterStarted && !frontmatterEnded) {
			const match = frontmatterPattern.exec(line);
			if (match) {
				const [, key, value] = match;
				frontmatter[key.trim()] = value.trim();
			}
		}
	}

	return frontmatter;
};

// Function to determine the best matching language
export const bestMatchingLanguage = (supportedLanguages: any[], preferredLanguages: any[], defaultLocale: string) => {
	const languages = supportedLanguages.map((lang) => lang.code);

	const match = preferredLanguages.map((prefLang) => languages.find((lang) => lang.startsWith(prefLang))).find(Boolean);

	console.log(languages, preferredLanguages, match, defaultLocale);
	return match || defaultLocale;
};

export const isErrorWithDetail = (error: unknown): error is { detail: string } => {
	return typeof error === 'object' && error !== null && 'detail' in error;
};

export const isErrorWithMessage = (error: unknown): error is { message: string } => {
	return typeof error === 'object' && error !== null && 'message' in error;
};

export const isErrorAsString = (error: unknown): error is string => typeof error === 'string';

export const isErrorWithError = (error: unknown): error is { error: string } => {
	return typeof error === 'object' && error !== null && 'error' in error;
};

export const debounce = (func: (...args: any[]) => void, delay = 200) => {
	let timer: Timer;
	return (...args: any[]) => {
		clearTimeout(timer);
		timer = setTimeout(() => func(...args), delay);
	};
};

export const stripHtml = (text: string) => {
	return text
		.replace(/<[^>]*>?/g, '')
		.replace(/&gt;/g, '>')
		.replace(/&lt;/g, '<')
		.replace(/&amp;/g, '&') // Convert &amp; to &
		.replace(/&quot;/g, '"') // Convert &quot; to "
		.replace(/&apos;/g, "'"); // Convert &apos; to ';
};

export const titleizeWords = (str: string) => {
	return str.replace(/\w\S*/g, (text) => text.charAt(0).toUpperCase() + text.substring(1).toLowerCase());
};

const isStringArray = (arr: any): arr is string[] => {
	return Array.isArray(arr) && arr.every((item) => typeof item === 'string');
};

interface FilterSelectParams {
	filterText: string;
	items: Array<{ [key: string]: any }> | Array<string>;
	multiple: boolean;
	value: Array<{ [key: string]: any }>;
	itemId: string;
	filterSelectedItems: boolean;
	itemFilter: (label: string, filterText: string) => boolean;
	convertStringItemsToObjects: (items: string[]) => Array<{ [key: string]: any }>;
	filterGroupedItems: (items: Array<{ [key: string]: any }>) => Array<{ [key: string]: any }>;
	label: string;
}
export const filterSelect = ({
	filterText,
	items,
	multiple,
	value,
	itemId,
	filterSelectedItems,
	itemFilter,
	convertStringItemsToObjects,
	filterGroupedItems,
	label
}: FilterSelectParams): Array<{ [key: string]: any }> => {
	if (!items) return [];

	if (items && items.length > 0 && isStringArray(items)) {
		items = convertStringItemsToObjects(items);
	}

	let filterResults = items.filter((item: any) => {
		let matchesFilter = itemFilter(item[label], filterText);
		if (matchesFilter && multiple && value?.length) {
			matchesFilter = !value.some((x: any) => {
				return filterSelectedItems ? x[itemId] === item[itemId] : false;
			});
		}

		return matchesFilter;
	}) as unknown as { [key: string]: any }[];

	filterResults = filterGroupedItems(filterResults);

	return filterResults;
};

export const getSelectItems = async ({ dispatch, loadOptions, convertStringItemsToObjects, filterText }: any) => {
	let res = await loadOptions(filterText).catch((err: unknown) => {
		console.warn('svelte-select loadOptions error :>> ', err);
		dispatch('error', { type: 'loadOptions', details: err });
	});

	if (res && !res.cancelled) {
		if (res) {
			if (res && res.length > 0 && typeof res[0] !== 'object') {
				res = convertStringItemsToObjects(res);
			}

			dispatch('loaded', { items: res });
		} else {
			res = [];
		}

		return {
			filteredItems: res,
			loading: false,
			focused: true,
			listOpen: true
		};
	}
};

export const generateReadingText = (article: Article) => {
	return [
		article.title,
		article.objective,
		article.document_id,
		article.introduction,
		...article.applicable_devices.map((device) => `${device.device || ''} ${device.software || ''}`),
		article.category,
		...article.steps.map((step) => `${step.section} Step ${step.step_number} ${step.text} ${step.note || ''}`),
		...article.revision_history.map(
			(revision) => `${revision.revision ?? ''} ${revision.publish_date ?? ''} ${revision.comments ?? ''}`
		)
	].join(' ');
};

export const appendCiscoSources = (sections: Record<string, string>[]): string => {
	const minStylesheet = 'https://www.cisco.com/etc/designs/cdc/fw/b/responsive/css/eot.min.css';
	const sansStylesheet = 'https://www.cisco.com/etc/designs/cdc/clientlibs/responsive/css/cisco-sans.min.css';
	const responsiveStylesheet = 'https://www.cisco.com/etc/designs/cdc/transformation/support-responsive.css';

	const wrapper = `<div id="eot-doc-wrapper">
					<link rel="stylesheet" href="${minStylesheet}">
					<link rel="stylesheet" href="${sansStylesheet}">
					<link rel="stylesheet" href="${responsiveStylesheet}">
    
                {{objective}}
                
                {{applicable_devices}}
                
                {{introduction}}
                
                <h2>Create an ASV VLAN</h2>
                
                <p>ASV can be enabled only on a static VLAN and the VLAN configured as an ASV VLAN cannot be deleted. </p>
                
                <h4>Step 1</h4>
                
                <p>Login to the Catalyst switch and navigate to <strong>VLAN Management &gt; VLAN Settings. </strong></p>
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-1.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-1.png"></a>
                
                <h4>Step 2</h4>
                
                <p>To add a VLAN, click on the <strong>plus</strong> symbol. </p>
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-2.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-2.png"></a>
                
                <h4>Step 3</h4>
                
                <p>Configure the <em>VLAN ID</em> and <em>VLAN Name</em> and click <strong>Apply</strong>. In this example, the VLAN ID is 5 and the VLAN Name is Auto Surveillance. </p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-3.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-3.png"></a>
                
                <h2>Configure ASV Settings </h2>
                
                <h4>Step 1</h4>
                <p>To select the VLAN for ASV, navigate to <strong>VLAN Management &gt; Auto-Surveillance VLAN &gt; ASV General Settings</strong>.  </p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-4.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-4.png"></a>
                
                <h4>Step 2</h4>
                
                <p>From the <em>Auto-Surveillance-VLAN ID</em> drop-down menu, select the VLAN ID for ASV. </p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-5.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-5.png"></a>
                
                <h4>Step 3</h4>
                
                <p>Under the <em>Surveillance Traffic Source Table</em>, click the <strong>plus icon</strong>. </p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-6.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-6.png"></a>
                
                <h4>Step 4</h4>
                
                <p>To add the surveillance traffic source, select <em>Source Type</em> as either <em>OUI Prefix</em> or <em>MAC Address</em>. Enter the <em>Source</em> in the field provided. Optionally, you can add a <em>Description</em> and click <strong>Apply</strong>. </p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-7.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-7.png"></a>
                
                
                <h4>Step 5</h4>
                
                <p>To enable the ASV VLAN on a specific port, navigate to <strong>VLAN Management &gt; Auto-Surveillance VLAN &gt; ASV Interface Settings</strong>.</p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-8.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-8.png"></a>
                
                <h4>Step 6</h4>
                
                <p>Select the interface and click edit. </p><a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-9.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-9.png"></a>
                
                <h4>Step 7</h4>
                
                <p><strong>Enable</strong> the <em>Auto Surveillance VLAN Membership</em> for the interface and click <strong>Apply</strong>. </p>
                
                <a href="https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-10.png" class="show-image-alone" title="Related image, diagram or screenshot." data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links"><img src="/c/dam/en/us/support/docs/smb/switches/Catalyst-switches/images/kmgmt3629-auto-surveillance-vlan-catalyst-1200-1300-switches-image-10.png"></a>
                
                <h2>Conclusion</h2>
                
                <p>There you go! You have configured ASV on your Catalyst 1200 or 1300 switch. </p>
                
                <p>Check out the following pages for more information on the Catalyst 1200 and 1300 switches. </p>
                
                <ul>
                    <li><a href="https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1200-series-switches/nb-06-cat1200-1300-ser-upgrade-cte-en.html" data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links">Why Upgrade to Cisco Catalyst 1200 or 1300 Series Switches Feature Comparison</a></li>
                    
                    <li><a href="https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1200-series-switches/nb-06-cat1200-1300-ser-aag-cte-en.html" data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links">Cisco Catalyst 1200 and 1300 Series Switches At-a-Glance</a></li>
                
                </ul>
                
                <p>For other configurations and features, refer to the Catalyst series <a href="https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/catalyst-1200-1300/AdminGuide/catalyst-1200-admin-guide.html" data-config-metrics-group="dest_pg_body" data-config-metrics-title="dest_pg_body_links">Administration Guide</a>. </p>
            
            </div>`;

	let title = '';
	let objective = '';
	let applicable_devices = '';
	let introduction = '';
	let steps = '';

	if (sections && sections.find(({ section }) => section === 'objective')) {
		objective += `<h2>Objective</h2>
					  <p>${sections.find(({ section }) => section === 'objective')?.content}</p>`;

		wrapper.replace('{{objective}}', objective);
	}
	if (sections && sections.find(({ section }) => section === 'applicable devices')) {
		applicable_devices += `<h2>Applicable Devices | Software Version</h2>
							   ${sections.find(({ section }) => section === 'applicable devices')?.content}
							   `;

		wrapper.replace('{{applicable_devices}}', applicable_devices);
	}

	if (sections && sections.find(({ section }) => section === 'introduction')) {
		introduction += `<h3>Introduction</h3>
						<p>${sections.find(({ section }) => section === 'introduction')?.content}</p>`;

		wrapper.replace('{{introduction}}', introduction);
	}

	return wrapper;
};
