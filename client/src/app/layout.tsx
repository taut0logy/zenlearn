import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { Toaster } from "@/components/ui/sonner";
import { Header } from "@/components/layout/header";
import { AuthProvider } from "@/providers/auth-provider";
import "./globals.css";

const geistSans = Geist({
    variable: "--font-geist-sans",
    subsets: ["latin"],
});

const geistMono = Geist_Mono({
    variable: "--font-geist-mono",
    subsets: ["latin"],
});

export const metadata: Metadata = {
    title: "ZenLearn",
    description: "An AI-Powered Supplementary Learning Platform for University Courses",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body
                className={`${geistSans.variable} ${geistMono.variable} antialiased`}
            >
                <ThemeProvider
                    attribute="class"
                    defaultTheme="system"
                    enableSystem
                    disableTransitionOnChange
                >
                    <AuthProvider>
                        <div className="flex flex-col min-h-screen">
                            <Header />
                            <main className="flex-1">{children}</main>
                        </div>
                    </AuthProvider>
                    <Toaster
                        toastOptions={{
                            className: "sonner",
                            style: {
                                fontFamily: "var(--geist-font-mono)",
                                fontSize: "0.875rem",
                                lineHeight: "1.25rem",
                            },
                        }}
                        closeButton
                        richColors
                    />
                </ThemeProvider>
            </body>
        </html>
    );
}
