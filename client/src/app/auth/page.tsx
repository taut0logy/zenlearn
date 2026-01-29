"use client";

import { use } from "react";
import LoginForm from "@/components/auth/login-form";
import SignupForm from "@/components/auth/signup-form";
import { useEffect } from "react";
import { toast } from "sonner";

export default function AuthPage({
    searchParams,
}: {
    searchParams: Promise<{ q?: string }>
}) {
    const params= use(searchParams);
    const mode = params?.q || "login";
    const message = params?.q;

    useEffect(() => {
        if (message) {
            switch (message) {
                case "session-expired":
                    toast.error(
                        "Your session has expired. Please sign in again.",
                    );
                    break;
                case "unauthorized-admin":
                    toast.error(
                        "You do not have permission to access that page.",
                    );
                    break;
                case "error-checking-permissions":
                    toast.error(
                        "An error occurred while checking permissions.",
                    );
                    break;
                default:
                    toast.error(decodeURIComponent(message));
            }
        }
    }, [message]);

    return mode === "signup" ? <SignupForm /> : <LoginForm />;
}
