import { WEBUI_API_BASE_URL } from '$lib/constants';
import type { Nullable, Article } from '$lib/types';

export const getArticles = async (
	token: string,
	skip: number = 0,
	limit: number = 200
): Promise<Nullable<Article[]>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}}/articles?skip=${skip}&limit=${limit}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getArticleById = async (token: string, articleId: string): Promise<Nullable<Article>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/articles/${articleId}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getArticlesBySeriesId = async (token: string, seriesId: string): Promise<Nullable<Article[]>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/articles/series/${seriesId}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getArticleByUrl = async (token: string, url: string): Promise<Nullable<Article>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/articles/url`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ url })
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getArticleByDocumentId = async (token: string, documentId: string): Promise<Nullable<Article>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/articles/document/${documentId}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const addNewArticle = async (token: string, data: object): Promise<Article> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/articles/add`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(data)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}
	return res;
};

export const generateArticleSupportQuestions = async (token: string, context: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/openai/generate_questions`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Accept: 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ context })
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

export const updateArticle = async (token: string, articleId: string, update: Partial<Article>) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/articles/${articleId}`, {
		method: 'PUT',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(update)
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

interface UpdateArticleStepForm {
	step: Article['steps'][number];
	step_index: number;
}

export const updateArticleStep = async (
	token: string,
	articleId: string,
	update: UpdateArticleStepForm
): Promise<Nullable<Article>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/articles/${articleId}/steps`, {
		method: 'PUT',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(update)
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

export const createNewArticle = async (
	token: string,
	query: string,
	device: string = 'Cisco Catalyst 1200 Series Switches'
): Promise<Article> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/articles/generate`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`,
			Accept: 'application/json'
		},
		body: JSON.stringify({ query, device })
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
