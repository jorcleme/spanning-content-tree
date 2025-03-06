import { redirect } from '@sveltejs/kit';

export function load() {
	let articleId = 'a48f767e-5d10-4b03-ad07-c1e7ed6bb070';
	throw redirect(301, `/article/${articleId}`);
}
