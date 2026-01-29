"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { FaFacebook } from "react-icons/fa";
import { FcGoogle } from "react-icons/fc";
import { Button } from "@/components/ui/button";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import {
    signIn,
    signInWithOAuth,
    resendConfirmationEmail,
} from "@/actions/auth";

const loginSchema = z.object({
    email: z.string().email("Please enter a valid email address"),
    password: z.string().min(6, "Password must be at least 6 characters"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginForm() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);
    const [pendingEmail, setPendingEmail] = useState<string | null>(null);

    const form = useForm<LoginFormValues>({
        resolver: zodResolver(loginSchema),
        defaultValues: {
            email: "",
            password: "",
        },
    });

    async function onSubmit(data: LoginFormValues) {
        setIsLoading(true);

        try {
            const result = await signIn(data);

            if (result.error) {
                if (result.error === "email-not-confirmed") {
                    setPendingEmail(data.email);
                    toast.error(
                        result.message ||
                            "Please confirm your email before signing in",
                        {
                            action: {
                                label: "Resend Email",
                                onClick: async () => {
                                    const resendResult =
                                        await resendConfirmationEmail(
                                            data.email,
                                        );
                                    if (resendResult.error) {
                                        toast.error(resendResult.error);
                                    } else {
                                        toast.success(
                                            resendResult.data?.message ||
                                                "Confirmation email sent",
                                        );
                                    }
                                },
                            },
                            duration: 10000,
                        },
                    );
                } else {
                    toast.error(result.error);
                }
                return;
            }

            toast.success("Signed in successfully");
            router.push("/dashboard");
            router.refresh();
        } catch (error) {
            console.error("Sign in error:", error);
            toast.error("An unexpected error occurred");
        } finally {
            setIsLoading(false);
        }
    }

    const handleOAuthSignIn = async (provider: "facebook" | "google") => {
        setIsLoading(true);
        try {
            await signInWithOAuth(provider);
        } catch (error) {
            // Re-throw redirect errors (they're expected)
            if (error instanceof Error && error.message === "NEXT_REDIRECT") {
                throw error;
            }
            console.error("OAuth error:", error);
            toast.error("Failed to sign in with OAuth");
            setIsLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center px-4 py-36 sm:px-6 lg:px-8">
            <div className="w-full max-w-md space-y-8">
                <div className="text-center">
                    <h1 className="text-3xl font-bold">Welcome back</h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Sign in to your account
                    </p>
                </div>

                <div className="mt-8">
                    <div className="space-y-6">
                        <Form {...form}>
                            <form
                                onSubmit={form.handleSubmit(onSubmit)}
                                className="space-y-4"
                            >
                                <FormField
                                    control={form.control}
                                    name="email"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Email</FormLabel>
                                            <FormControl>
                                                <Input
                                                    type="email"
                                                    placeholder="name@example.com"
                                                    disabled={isLoading}
                                                    {...field}
                                                />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                                <FormField
                                    control={form.control}
                                    name="password"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Password</FormLabel>
                                            <FormControl>
                                                <Input
                                                    type="password"
                                                    placeholder="••••••••"
                                                    disabled={isLoading}
                                                    {...field}
                                                />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />

                                <div className="flex items-center justify-between">
                                    <div className="text-sm">
                                        <Link
                                            href="/auth/forgot-password"
                                            className="text-sm text-primary hover:underline"
                                        >
                                            Forgot password?
                                        </Link>
                                    </div>
                                </div>

                                <Button
                                    type="submit"
                                    className="w-full"
                                    disabled={isLoading}
                                >
                                    {isLoading ? "Signing in..." : "Sign in"}
                                </Button>
                            </form>
                        </Form>

                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <Separator className="w-full" />
                            </div>
                            <div className="relative flex justify-center text-xs uppercase">
                                <span className="bg-background px-2 text-muted-foreground">
                                    Or continue with
                                </span>
                            </div>
                        </div>

                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                className="flex-1"
                                onClick={() => handleOAuthSignIn("facebook")}
                                disabled={isLoading}
                            >
                                <FaFacebook className="mr-2 h-4 w-4" /> Facebook
                            </Button>
                            <Button
                                variant="outline"
                                className="flex-1 items-center justify-center"
                                onClick={() => handleOAuthSignIn("google")}
                                disabled={isLoading}
                            >
                                <FcGoogle className="mr-2 h-4 w-4" /> Google
                            </Button>
                        </div>

                        <div className="text-center text-sm">
                            Don&apos;t have an account?{" "}
                            <Link
                                href="/auth?mode=signup"
                                className="text-primary hover:underline"
                            >
                                Sign up
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
