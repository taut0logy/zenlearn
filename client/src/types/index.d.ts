import type { User as SupabaseUser } from "@supabase/supabase-js";

export type SignUpOptions = {
    name: string;
    email: string;
    password: string;
    confirmPassword: string;
    avatarUrl?: string;
}

export type SignInOptions = {
    email: string;
    password: string;
}



export type User = SupabaseUser & {
    profile: {
        id: string;
        name: string;
        bio?: string;
        avatarUrl?: string;
        role?: string;
    };
}