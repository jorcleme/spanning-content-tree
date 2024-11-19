import { redirect } from '@sveltejs/kit';

export function load() {
	let articleId = '256b5500-9938-4c82-8675-ea973c3eb55f';
	throw redirect(301, `/article/${articleId}`);
}
