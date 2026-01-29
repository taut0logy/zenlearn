// Role-Based Access Control (RBAC) utilities

import type { User } from '@/lib/types';

export type Role = 'user' | 'admin';

export function isAdmin(user: User | null | undefined): boolean {
    return user?.profile?.role === 'admin';
}

export function hasRole(user: User | null | undefined, role: Role): boolean {
    return user?.profile?.role === role;
}

export function canAccessRoute(user: User | null | undefined, path: string): boolean {
    // Public routes are always accessible
    const publicRoutes = ['/auth', '/auth/forgot-password', '/auth/reset-password', '/auth/sign-up-success'];
    if (publicRoutes.some((route) => path.startsWith(route))) {
        return true;
    }

    // Protected routes require authentication
    if (path.startsWith('/(protected)') || path.includes('/dashboard') || path.includes('/profile')) {
        if (!user) return false;
    }

    // Admin routes require admin role
    if (path.includes('/admin')) {
        return isAdmin(user);
    }

    return true;
}

export function canManageUsers(user: User | null | undefined): boolean {
    return isAdmin(user);
}

export function canDeleteUser(user: User | null | undefined): boolean {
    return isAdmin(user);
}

export function canUpdateUserRole(user: User | null | undefined): boolean {
    return isAdmin(user);
}

export function getRoleLabel(role: Role): string {
    const labels: Record<Role, string> = {
        user: 'User',
        admin: 'Admin',
    };
    return labels[role];
}

export function getRoleBadgeColor(role: Role): string {
    const colors: Record<Role, string> = {
        user: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
        admin: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
    };
    return colors[role];
}
