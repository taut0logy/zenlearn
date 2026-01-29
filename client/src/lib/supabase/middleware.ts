import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

export async function updateSession(request: NextRequest) {
    let supabaseResponse = NextResponse.next({
        request,
    });

    const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
        {
            cookies: {
                getAll() {
                    return request.cookies.getAll();
                },
                setAll(cookiesToSet) {
                    cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
                    supabaseResponse = NextResponse.next({
                        request,
                    });
                    cookiesToSet.forEach(({ name, value, options }) =>
                        supabaseResponse.cookies.set(name, value, options)
                    );
                },
            },
        }
    );

    // IMPORTANT: Do not write any logic between createServerClient and
    // supabase.auth.getUser(). A simple mistake could make your application
    // vulnerable to security issues.

    const {
        data: { user },
    } = await supabase.auth.getUser();

    const pathname = request.nextUrl.pathname;

    // Check if user needs to set password (from database via Supabase)
    let needsPassword = false;
    if (user) {
        try {
            const { data: profile } = await supabase
                .from('profiles')
                .select('has_password')
                .eq('id', user.id)
                .single();
            needsPassword = !profile?.has_password;
        } catch (error) {
            console.error('Error checking password status:', error);
        }
    }

    // Allow public routes
    if (
        pathname.startsWith('/auth') ||
        pathname === '/' ||
        pathname.startsWith('/_next') ||
        pathname.startsWith('/api')
    ) {
        // Allow set-password page for users who need to set password
        if (pathname === '/auth/set-password') {
            if (!user) {
                const url = request.nextUrl.clone();
                url.pathname = '/auth';
                return NextResponse.redirect(url);
            }
            if (!needsPassword) {
                const url = request.nextUrl.clone();
                url.pathname = '/dashboard';
                return NextResponse.redirect(url);
            }
            return supabaseResponse;
        }

        // Redirect authenticated users away from auth pages
        if (user && pathname.startsWith('/auth') && !pathname.includes('/callback')) {
            // If user needs password, redirect to set-password
            if (needsPassword) {
                const url = request.nextUrl.clone();
                url.pathname = '/auth/set-password';
                return NextResponse.redirect(url);
            }
            const url = request.nextUrl.clone();
            url.pathname = '/dashboard';
            return NextResponse.redirect(url);
        }

        return supabaseResponse;
    }

    // Check if session expired - redirect to auth with message
    if (!user) {
        const url = request.nextUrl.clone();
        url.pathname = '/auth';

        // Add session expired message if coming from protected route
        if (pathname.startsWith('/(protected)') || pathname.includes('/dashboard') || pathname.includes('/profile') || pathname.includes('/admin')) {
            url.searchParams.set('message', 'session-expired');
        }

        return NextResponse.redirect(url);
    }

    // Protected routes - require authentication and password
    if (pathname.includes('/dashboard') || pathname.includes('/profile') || pathname.includes('/settings')) {
        // Redirect to set-password if user needs to set password
        if (needsPassword) {
            const url = request.nextUrl.clone();
            url.pathname = '/auth/set-password';
            return NextResponse.redirect(url);
        }
        return supabaseResponse;
    }

    // Admin routes - require admin role
    if (pathname.includes('/admin')) {
        try {
            // Get user profile with role from database via Supabase
            const { data: profile } = await supabase
                .from('profiles')
                .select('role')
                .eq('id', user.id)
                .single();

            if (!profile || profile.role !== 'admin') {
                const url = request.nextUrl.clone();
                url.pathname = '/dashboard';
                url.searchParams.set('message', 'unauthorized-admin');
                return NextResponse.redirect(url);
            }
        } catch (error) {
            console.error('Error checking admin role:', error);
            const url = request.nextUrl.clone();
            url.pathname = '/dashboard';
            url.searchParams.set('message', 'error-checking-permissions');
            return NextResponse.redirect(url);
        }
    }

    return supabaseResponse;
}
