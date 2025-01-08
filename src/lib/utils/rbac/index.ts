import { ACCESS_LEVELS, type AccessLevel, ROLES, type Role } from '$lib/constants';
import { type SessionUser } from '$lib/stores';

export const hasRole = (role: Role, user: SessionUser): boolean => {
	return user.role.toLowerCase() === role.toLowerCase();
};

export const hasAccessLevel = (accessLevel: number, user: SessionUser): boolean => {
	return user.access_level >= accessLevel;
};

export const canAccessProtectedRoute = (user: SessionUser): boolean => {
	return (hasRole(ROLES.ADMIN, user) || hasRole(ROLES.USER, user)) && hasAccessLevel(ACCESS_LEVELS.EMPLOYEE, user);
};

export const hasAccess = (
	roles: Role[],
	accessLevel: AccessLevel,
	requiredRoles: Role[],
	requiredAccessLevel: AccessLevel
): boolean => {
	return roles.some((role) => requiredRoles.includes(role)) && accessLevel >= requiredAccessLevel;
};
