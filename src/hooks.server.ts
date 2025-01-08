import { get } from 'svelte/store';
import { ACCESS_LEVELS, ROLES } from '$lib/constants';
import { user } from '$lib/stores';
import { hasAccess } from '$lib/utils/rbac';
import { redirect } from '@sveltejs/kit';
import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	const sessionUser = get(user);

	if (!sessionUser) {
		if (event.url.pathname.startsWith('/admin/editor')) {
			throw redirect(302, '/auth');
		}
		return resolve(event);
	}

	const { role, access_level } = sessionUser;

	if (event.url.pathname.startsWith('/admin/editor')) {
		if (!hasAccess([role], access_level, [ROLES.ADMIN, ROLES.USER], ACCESS_LEVELS.EMPLOYEE)) {
			throw redirect(302, '/unauthorized');
		}
	}

	return resolve(event);
};
