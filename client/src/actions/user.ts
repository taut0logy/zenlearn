'use server';

import { createClient } from '@/lib/supabase/server';
import { revalidatePath } from 'next/cache';
import { db } from '@/db';
import { profiles } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { deleteOldAvatar } from './storage';

interface UpdateProfileData {
    name?: string;
    avatarUrl?: string;
}

export async function updateProfile(data: UpdateProfileData) {
    try {
        const supabase = await createClient();

        const {
            data: { user },
        } = await supabase.auth.getUser();

        if (!user) {
            return { error: 'Unauthorized' };
        }

        // Get current profile to check for old avatar
        const [currentProfile] = await db
            .select()
            .from(profiles)
            .where(eq(profiles.id, user.id))
            .limit(1);

        if (!currentProfile) {
            return { error: 'Profile not found' };
        }

        // If updating avatar and there's an old one, delete it
        if (data.avatarUrl && currentProfile.avatarUrl && data.avatarUrl !== currentProfile.avatarUrl) {
            await deleteOldAvatar(currentProfile.avatarUrl);
        }

        // Update profile in database
        await db
            .update(profiles)
            .set({
                ...data,
                updatedAt: new Date(),
            })
            .where(eq(profiles.id, user.id));

        revalidatePath('/', 'layout');
        return { data: { success: true, message: 'Profile updated successfully' } };
    } catch (error) {
        console.error('Update profile error:', error);
        return { error: 'Failed to update profile' };
    }
}

export async function deleteProfile(password: string) {
    try {
        const supabase = await createClient();

        const {
            data: { user },
        } = await supabase.auth.getUser();

        if (!user) {
            return { error: 'Unauthorized' };
        }

        // Verify password before deletion
        const { error: signInError } = await supabase.auth.signInWithPassword({
            email: user.email!,
            password,
        });

        if (signInError) {
            return { error: 'Invalid password' };
        }

        // Get current profile to delete avatar
        const [profile] = await db.select().from(profiles).where(eq(profiles.id, user.id)).limit(1);

        if (profile?.avatarUrl) {
            await deleteOldAvatar(profile.avatarUrl);
        }

        // Delete profile from database
        await db.delete(profiles).where(eq(profiles.id, user.id));

        // Delete user from Supabase Auth (hard delete)
        const { error: deleteError } = await supabase.auth.admin.deleteUser(user.id);

        if (deleteError) {
            console.error('Error deleting auth user:', deleteError);
            return { error: 'Failed to delete account' };
        }

        // Sign out
        await supabase.auth.signOut();

        revalidatePath('/', 'layout');
        return { data: { success: true, message: 'Account deleted successfully' } };
    } catch (error) {
        console.error('Delete profile error:', error);
        return { error: 'Failed to delete profile' };
    }
}
