import { WEBUI_API_BASE_URL } from '$lib/constants';
import { getTimeRange } from '$lib/utils';
import {
	type Nullable,
	type ChatResponse,
	type ChatListResponse,
	type ChatTagListResponse,
	type FilteredChatList,
	type TagsByUserResponse
} from '$lib/types';

export const createNewChat = async (token: string, chat: object): Promise<ChatResponse | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/new`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			chat: chat
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getChatList = async (token: string = ''): Promise<Nullable<FilteredChatList>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data: FilteredChatList = await res.json();
			return data;
		})
		.catch((err) => {
			error = err;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res
		? res.map((chat) => ({
				...chat,
				time_range: getTimeRange(chat.updated_at)
		  }))
		: null;
};

export const getChatListByUserId = async (
	token: string = '',
	userId: string
): Promise<Nullable<FilteredChatList>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/list/user/${userId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data: FilteredChatList = await res.json();
			return data;
		})
		.catch((err) => {
			error = err;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res
		? res.map((chat) => ({
				...chat,
				time_range: getTimeRange(chat.updated_at)
		  }))
		: null;

	// return res.map((chat) => ({
	// 	...chat,
	// 	time_range: getTimeRange(chat.updated_at)
	// }));
};

export const getArchivedChatList = async (
	token: string = ''
): Promise<Nullable<FilteredChatList>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/archived`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getAllChats = async (token: string): Promise<Nullable<ChatListResponse>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/all`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getAllArchivedChats = async (token: string): Promise<Nullable<ChatListResponse>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/all/archived`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getAllUserChats = async (token: string): Promise<Nullable<ChatListResponse>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/all/db`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data: ChatListResponse = await res.json();
			return data;
		})
		.catch((err) => {
			error = err;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getAllChatTags = async (token: string): Promise<Nullable<TagsByUserResponse>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/tags/all`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data: TagsByUserResponse = await res.json();
			return data;
		})
		.catch((err) => {
			error = err;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getChatListByTagName = async (
	token: string = '',
	tagName: string
): Promise<Nullable<FilteredChatList>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/tags`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			name: tagName
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data: FilteredChatList = await res.json();
			return data;
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}
	if (res === null) {
		return null;
	}

	return res.map((chat) => ({
		...chat,
		time_range: getTimeRange(chat.updated_at)
	}));
};

// Get a chat by the chat id
// This is used in the Chat.svelte page where the chatIdProp or $chatId is used to get the chat by id
export const getChatById = async (token: string, id: string): Promise<Nullable<ChatResponse>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${id}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			const data = await res.json();
			console.log(
				'[getChatById:apis/chats/index.ts] Get Chat By Id res.json ->: ',
				JSON.stringify(data, null, 2)
			);
			return data;
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getChatByShareId = async (
	token: string,
	share_id: string
): Promise<Nullable<ChatResponse>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/share/${share_id}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const cloneChatById = async (token: string, id: string): Promise<Nullable<ChatResponse>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${id}/clone`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err;

			if ('detail' in err) {
				error = err.detail;
			} else {
				error = err;
			}

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const shareChatById = async (token: string, id: string): Promise<ChatResponse | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${id}/share`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const archiveChatById = async (token: string, id: string): Promise<ChatResponse | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${id}/archive`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			error = err;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const deleteSharedChatById = async (token: string, id: string): Promise<boolean | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${id}/share`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})

		.catch((err) => {
			error = err;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateChatById = async (
	token: string,
	id: string,
	chat: object
): Promise<ChatResponse | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${id}`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			chat: chat
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})

		.catch((err) => {
			error = err;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const deleteChatById = async (token: string, id: string): Promise<boolean | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${id}`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})

		.catch((err) => {
			error = err.detail;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getTagsById = async (
	token: string,
	id: string
): Promise<ChatTagListResponse | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${id}/tags`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const addTagById = async (token: string, id: string, tagName: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${id}/tags`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			tag_name: tagName,
			chat_id: id
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const deleteTagById = async (token: string, id: string, tagName: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${id}/tags`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			tag_name: tagName,
			chat_id: id
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
export const deleteTagsById = async (token: string, id: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${id}/tags/all`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const deleteAllChats = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const archiveAllChats = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/chats/archive/all`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
