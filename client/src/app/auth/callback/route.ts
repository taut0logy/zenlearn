import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { db } from '@/db';
import { profiles } from '@/db/schema';
import { eq } from 'drizzle-orm';

export async function GET(request: NextRequest) {
    const requestUrl = new URL(request.url);
    const code = requestUrl.searchParams.get('code');
    const next = requestUrl.searchParams.get('next') || '/dashboard';
    const origin = requestUrl.origin;

    if (code) {
        const supabase = await createClient();

        // Exchange code for session
        const { data, error } = await supabase.auth.exchangeCodeForSession(code);

        if (error) {
            console.error('OAuth callback error:', error);
            return NextResponse.redirect(
                `${origin}/auth?message=${encodeURIComponent('Authentication failed. Please try again.')}`
            );
        }

        if (data.user) {
            // Check if profile exists
            const [existingProfile] = await db
                .select()
                .from(profiles)
                .where(eq(profiles.id, data.user.id))
                .limit(1);

            // If profile doesn't exist, create it from OAuth metadata
            if (!existingProfile) {
                try {
                    const { user_metadata } = data.user;

                    await db.insert(profiles).values({
                        id: data.user.id,
                        name: user_metadata?.full_name || user_metadata?.name || data.user.email?.split('@')[0] || 'User',
                        email: data.user.email!,
                        role: 'user',
                        avatarUrl: user_metadata?.avatar_url || user_metadata?.picture || null,
                    });
                } catch (insertError) {
                    console.error('Profile creation error:', insertError);
                    // Continue anyway - user is authenticated
                }
            }
            
            return NextResponse.redirect(`${origin}${next}`);
        }
    }

    return NextResponse.redirect(`${origin}/auth?message=${encodeURIComponent('Authentication failed')}`);
}
