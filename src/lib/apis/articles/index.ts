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
