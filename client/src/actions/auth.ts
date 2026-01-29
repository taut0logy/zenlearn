'use server';

import { createClient } from '@/lib/supabase/server';
import { createClient as createAdminClient } from '@/lib/supabase/admin';
import { revalidatePath } from 'next/cache';
import type { User } from '@/lib/types';
import { headers } from 'next/headers';
import { redirect } from 'next/navigation';
import { db } from '@/db';
import { profiles } from '@/db/schema';
import { eq } from 'drizzle-orm';

interface SignUpOptions {
    name: string;
    email: string;
    password: string;
    confirmPassword: string;
}

interface SignInOptions {
    email: string;
    password: string;
}

export async function signUp({ name, email, password, confirmPassword }: SignUpOptions) {
    const supabase = await createClient();

    if (password !== confirmPassword) {
        return { error: 'Passwords do not match' };
    }

    // Create auth user
    const { data: authData, error: authError } = await supabase.auth.signUp({
        email,
        password,
        options: {
            emailRedirectTo: `${process.env.NEXT_PUBLIC_APP_URL}/auth/callback?next=/dashboard`,
        },
    });

    if (authError) {
        return { error: authError.message };
    }

    if (!authData.user) {
        return { error: 'User creation failed' };
    }

    try {
        // Create profile in database using Drizzle
        await db.insert(profiles).values({
            id: authData.user.id,
            name,
            email,
            role: 'user', // Default role
            avatarUrl: null,
            hasPassword: true, // Email signup has password
        });

        return {
            data: { success: true, message: 'Please check your email to confirm your account' },
        };
    } catch (error) {
        console.error('Profile creation error:', error);

        // If profile creation fails, delete the auth user
        const adminClient = createAdminClient();
        await adminClient.auth.admin.deleteUser(authData.user.id);

        return { error: 'Failed to create profile. Please try again.' };
    }
}

export async function signIn({ email, password }: SignInOptions) {
    const supabase = await createClient();

    const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
    });

    if (error) {
        return { error: error.message };
    }

    // Check if email is confirmed
    if (data.user && !data.user.email_confirmed_at) {
        // Sign out the user
        await supabase.auth.signOut();
        return {
            error: 'email-not-confirmed',
            message: 'Please confirm your email before signing in',
        };
    }

    revalidatePath('/', 'layout');
    return { data: { success: true } };
}

export async function signInWithOAuth(provider: 'google' | 'facebook') {
    const supabase = await createClient();
    const origin = process.env.NEXT_PUBLIC_APP_URL || (await headers()).get('origin');

    const { data, error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
            redirectTo: `${origin}/auth/callback?next=/dashboard`,
        },
    });

    if (error) {
        return { error: error.message };
    }

    return redirect(data.url);
}

export async function resendConfirmationEmail(email: string) {
    const supabase = await createClient();

    const { error } = await supabase.auth.resend({
        type: 'signup',
        email,
    });

    if (error) {
        return { error: error.message };
    }

    return { data: { success: true, message: 'Confirmation email sent' } };
}

export async function forgotPassword(email: string) {
    const supabase = await createClient();
    const origin = process.env.NEXT_PUBLIC_APP_URL || (await headers()).get('origin');

    if (!email) {
        return { error: 'Email is required' };
    }

    const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${origin}/auth/callback?next=/auth/reset-password`,
    });

    if (error) {
        console.error('Password reset error:', error.message);
        return { error: 'Could not send password reset email' };
    }

    return { data: { success: true, message: 'Check your email for a password reset link' } };
}

export async function resetPassword(password: string, confirmPassword: string) {
    const supabase = await createClient();

    if (!password || !confirmPassword) {
        return { error: 'Password and confirm password are required' };
    }

    if (password !== confirmPassword) {
        return { error: 'Passwords do not match' };
    }

    const { error } = await supabase.auth.updateUser({
        password,
    });

    if (error) {
        return { error: 'Password update failed' };
    }

    return { data: { success: true, message: 'Password updated successfully' } };
}

export async function getUser(): Promise<{ data?: User | null; error?: string }> {
    try {
        const supabase = await createClient();

        const {
            data: { user },
        } = await supabase.auth.getUser();

        if (!user) {
            return { data: null };
        }

        // Get profile from database using Drizzle
        const [profile] = await db.select().from(profiles).where(eq(profiles.id, user.id)).limit(1);

        if (!profile) {
            return { data: null };
        }

        return {
            data: {
                ...user,
                profile: {
                    id: profile.id,
                    name: profile.name,
                    avatarUrl: profile.avatarUrl,
                    role: profile.role,
                },
            } as User,
        };
    } catch (error) {
        console.error('Get user error:', error);
        return { error: 'Failed to fetch user' };
    }
}

export async function setPassword(password: string, confirmPassword: string) {
    const supabase = await createClient();

    if (!password || !confirmPassword) {
        return { error: 'Password and confirm password are required' };
    }

    if (password !== confirmPassword) {
        return { error: 'Passwords do not match' };
    }

    if (password.length < 6) {
        return { error: 'Password must be at least 6 characters' };
    }

    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
        return { error: 'Not authenticated' };
    }

    const { error } = await supabase.auth.updateUser({ password });

    if (error) {
        return { error: error.message };
    }

    // Update hasPassword flag in profile
    await db.update(profiles)
        .set({ hasPassword: true, updatedAt: new Date() })
        .where(eq(profiles.id, user.id));

    revalidatePath('/', 'layout');
    return { data: { success: true, message: 'Password set successfully' } };
}

export async function changePassword(currentPassword: string, newPassword: string) {
    const supabase = await createClient();

    const { data: { user } } = await supabase.auth.getUser();

    if (!user?.email) {
        return { error: 'Not authenticated' };
    }

    if (!currentPassword || !newPassword) {
        return { error: 'Current and new password are required' };
    }

    if (newPassword.length < 6) {
        return { error: 'New password must be at least 6 characters' };
    }

    // Verify current password
    const { error: signInError } = await supabase.auth.signInWithPassword({
        email: user.email,
        password: currentPassword,
    });

    if (signInError) {
        return { error: 'Current password is incorrect' };
    }

    // Update to new password
    const { error } = await supabase.auth.updateUser({ password: newPassword });

    if (error) {
        return { error: 'Failed to update password' };
    }

    return { data: { success: true, message: 'Password changed successfully' } };
}

export async function hasPassword(): Promise<boolean> {
    const supabase = await createClient();

    const { data: { user } } = await supabase.auth.getUser();

    if (!user) return false;

    // Check if user has email identity (users with email identity have a password)
    const hasEmailIdentity = user.identities?.some(
        (identity) => identity.provider === 'email'
    );

    return !!hasEmailIdentity;
}

export async function signOut() {
    const supabase = await createClient();

    const { error } = await supabase.auth.signOut();

    if (error) {
        return { error: error.message };
    }

    revalidatePath('/', 'layout');
    return { data: { success: true } };
}
