import { redirect } from '@sveltejs/kit';

export function load() {
	let articleId = '3558b09f-cd53-4462-99c3-21ed1e7ec32f';
	throw redirect(301, `/article/${articleId}`);
}
