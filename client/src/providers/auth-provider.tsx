"use client";

import { useRouter } from "next/navigation";
import { AuthContext } from "@/hooks/use-auth";
import { useUser } from "@/hooks/use-user";
import { signOut as signOutAction } from "@/actions/auth";
import { toast } from "sonner";

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const { user, isLoading, mutate } = useUser();
    const router = useRouter();

    const handleSignOut = async () => {
        try {
            await mutate(null, { revalidate: false });

            const result = await signOutAction();
            if (result.error) {
                toast.error(result.error);
                await mutate();
                return;
            }

            toast.success("See you later!");

            router.push("/auth");
            router.refresh();
        } catch (error) {
            console.error("Sign out error:", error);
            toast.error("Failed to sign out");
            await mutate();
        }
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                isLoading,
                signOut: handleSignOut,
                mutate,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}
