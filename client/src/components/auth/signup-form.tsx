"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
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
import { signUp, signInWithOAuth } from "@/actions/auth";

const registerSchema = z
    .object({
        name: z.string().min(2, "Name must be at least 2 characters"),
        email: z.string().email("Please enter a valid email address"),
        password: z.string().min(6, "Password must be at least 6 characters"),
        confirmPassword: z
            .string()
            .min(6, "Confirm password must be at least 6 characters"),
    })
    .refine((data) => data.password === data.confirmPassword, {
        message: "Passwords do not match",
        path: ["confirmPassword"],
    });

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function SignupForm() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);

    const form = useForm<RegisterFormValues>({
        resolver: zodResolver(registerSchema),
        defaultValues: {
            name: "",
            email: "",
            password: "",
            confirmPassword: "",
        },
    });

    async function onSubmit(data: RegisterFormValues) {
        setIsLoading(true);

        try {
            const result = await signUp(data);

            if (result.error) {
                toast.error(result.error);
                return;
            }

            toast.success(
                result.data?.message ||
                    "Account created! Please check your email to confirm.",
            );
            router.push("/auth/sign-up-success");
        } catch (error) {
            console.error("Sign up error:", error);
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
        <div className="flex items-center justify-center px-4 py-8 sm:px-6 lg:px-8">
            <div className="w-full max-w-md space-y-8">
                <div className="text-center">
                    <h1 className="text-3xl font-bold">Create an account</h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Sign up to get started
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
                                    name="name"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Name</FormLabel>
                                            <FormControl>
                                                <Input
                                                    placeholder="John"
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
                                <FormField
                                    control={form.control}
                                    name="confirmPassword"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>
                                                Confirm Password
                                            </FormLabel>
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

                                <Button
                                    type="submit"
                                    className="w-full"
                                    disabled={isLoading}
                                >
                                    {isLoading
                                        ? "Creating account..."
                                        : "Create account"}
                                </Button>
                            </form>
                        </Form>

                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <Separator className="w-full" />
                            </div>
                            <div className="relative flex justify-center text-xs uppercase">
                                <span className="bg-background px-2 text-muted-foreground">
                                    Or Sign Up with
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
                            Already have an account?{" "}
                            <Link
                                href="/auth?mode=login"
                                className="text-primary hover:underline"
                            >
                                Sign in
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
