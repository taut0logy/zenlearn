"use client";

import * as React from "react";
import { CMSSidebar } from "./CMSSidebar";
import { Input } from "@/components/ui/input";
import { Search, Bell, User } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CMSLayoutProps {
    children: React.ReactNode;
    onNavigate?: (path: string) => void;
}

export function CMSLayout({ children, onNavigate }: CMSLayoutProps) {
    return (
        <div className="flex h-screen overflow-hidden bg-background">
            {/* Sidebar - Hidden on mobile, can be toggled (todo) */}
            <aside className="hidden w-64 flex-col md:flex">
                <CMSSidebar onNavigate={onNavigate} />
            </aside>

            {/* Main Content */}
            <div className="flex flex-1 flex-col overflow-hidden">
                {/* Header */}
                <header className="flex h-14 items-center gap-4 border-b bg-muted/20 px-6 justify-between">
                    <div className="font-semibold text-lg">ZenLearn</div>
                    {/* Add actual user menu here later if needed */}
                </header>

                {/* Content Area */}
                <main className="flex-1 overflow-y-auto p-6">
                    {children}
                </main>
            </div>
        </div>
    );
}
