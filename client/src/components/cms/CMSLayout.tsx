"use client";

import * as React from "react";
import { CMSSidebar } from "./CMSSidebar";
import { SearchCommand } from "./SearchCommand";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CMSLayoutProps {
    children: React.ReactNode;
    onNavigate?: (path: string) => void;
}

export function CMSLayout({ children, onNavigate }: CMSLayoutProps) {
    const [searchOpen, setSearchOpen] = React.useState(false);

    // Keyboard shortcut: Cmd/Ctrl + K
    React.useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "k") {
                e.preventDefault();
                setSearchOpen(true);
            }
        };

        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, []);

    return (
        <div className="flex h-[calc(100vh-65px)] overflow-hidden bg-background">
            {/* Sidebar - Hidden on mobile, can be toggled (todo) */}
            <aside className="hidden w-64 flex-col md:flex">
                <CMSSidebar onNavigate={onNavigate} />
            </aside>

            {/* Main Content */}
            <div className="flex flex-1 flex-col overflow-hidden">
                {/* Header */}
                <header className="flex h-14 items-center gap-4 border-b bg-muted/20 px-6 justify-between">
                    <div className="font-semibold text-lg">ZenLearn</div>

                    {/* Search Button */}
                    <Button
                        variant="outline"
                        size="sm"
                        className="w-64 justify-start text-muted-foreground"
                        onClick={() => setSearchOpen(true)}
                    >
                        <Search className="mr-2 h-4 w-4" />
                        <span>Search materials...</span>
                        <kbd className="ml-auto pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
                            <span className="text-xs">⌘</span>K
                        </kbd>
                    </Button>
                </header>

                {/* Content Area */}
                <main className="flex-1 overflow-y-auto p-6">
                    {children}
                </main>
            </div>

            {/* Search Command Dialog */}
            <SearchCommand open={searchOpen} onOpenChange={setSearchOpen} />
        </div>
    );
}

