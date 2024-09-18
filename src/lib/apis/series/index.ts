import { WEBUI_API_BASE_URL } from '$lib/constants';
import type { Nullable, Series } from '$lib/types';

export const getAllSeries = async (token: string): Promise<Nullable<Series[]>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/series`, {
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

export const getSeriesByName = async (token: string, seriesName: string): Promise<Nullable<Series>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/series/name/${encodeURIComponent(seriesName)}`, {
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
