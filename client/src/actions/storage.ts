'use server';

import { createClient } from '@/lib/supabase/server';

const MAX_FILE_SIZE = 2 * 1024 * 1024; // 2MB
const ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const AVATARS_BUCKET = 'avatars';

export async function uploadAvatar(formData: FormData) {
    try {
        const supabase = await createClient();
        const file = formData.get('file') as File;

        if (!file) {
            return { error: 'No file provided' };
        }

        // Validate file size
        if (file.size > MAX_FILE_SIZE) {
            return { error: 'File size must be less than 2MB' };
        }

        // Validate file type
        if (!ALLOWED_FILE_TYPES.includes(file.type)) {
            return { error: 'File type must be JPEG, PNG, WebP, or GIF' };
        }

        // Get current user
        const {
            data: { user },
        } = await supabase.auth.getUser();

        if (!user) {
            return { error: 'Unauthorized' };
        }

        // Create unique file name
        const fileExt = file.name.split('.').pop();
        const fileName = `${user.id}/${Date.now()}.${fileExt}`;

        // Upload file to Supabase Storage
        const { data, error } = await supabase.storage
            .from(AVATARS_BUCKET)
            .upload(fileName, file, {
                cacheControl: '3600',
                upsert: false,
            });

        if (error) {
            console.error('Upload error:', error);
            return { error: 'Failed to upload file' };
        }

        // Get public URL
        const {
            data: { publicUrl },
        } = supabase.storage.from(AVATARS_BUCKET).getPublicUrl(data.path);

        return { data: { path: data.path, url: publicUrl } };
    } catch (error) {
        console.error('Upload avatar error:', error);
        return { error: 'An unexpected error occurred' };
    }
}

export async function deleteAvatar(path: string) {
    try {
        const supabase = await createClient();

        // Get current user
        const {
            data: { user },
        } = await supabase.auth.getUser();

        if (!user) {
            return { error: 'Unauthorized' };
        }

        // Verify the path belongs to the user
        if (!path.startsWith(`${user.id}/`)) {
            return { error: 'Unauthorized to delete this file' };
        }

        // Delete file from storage
        const { error } = await supabase.storage.from(AVATARS_BUCKET).remove([path]);

        if (error) {
            console.error('Delete error:', error);
            return { error: 'Failed to delete file' };
        }

        return { data: { success: true } };
    } catch (error) {
        console.error('Delete avatar error:', error);
        return { error: 'An unexpected error occurred' };
    }
}

export async function getAvatarUrl(path: string) {
    try {
        const supabase = await createClient();

        const {
            data: { publicUrl },
        } = supabase.storage.from(AVATARS_BUCKET).getPublicUrl(path);

        return { data: { url: publicUrl } };
    } catch (error) {
        console.error('Get avatar URL error:', error);
        return { error: 'Failed to get avatar URL' };
    }
}

export async function deleteOldAvatar(currentAvatarUrl: string | null) {
    if (!currentAvatarUrl) return { data: { success: true } };

    try {
        // Extract path from URL
        const url = new URL(currentAvatarUrl);
        const pathParts = url.pathname.split(`${AVATARS_BUCKET}/`);

        if (pathParts.length < 2) {
            return { error: 'Invalid avatar URL' };
        }

        const path = pathParts[1];
        return await deleteAvatar(path);
    } catch (error) {
        console.error('Delete old avatar error:', error);
        return { error: 'Failed to delete old avatar' };
    }
}
