"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BookOpen, Star, Clock, Cloud, Settings, Plus } from "lucide-react";

interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> {
    onNavigate?: (path: string) => void;
}

export function CMSSidebar({ className, onNavigate }: SidebarProps) {
    return (
        <div className={cn("pb-12 bg-muted/20 border-r h-full", className)}>
            <div className="space-y-4 py-4">
                <div className="px-3 py-2">
                    <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight">
                        ZenDrive
                    </h2>
                    <div className="space-y-1">
                        <Button variant="secondary" className="w-full justify-start" onClick={() => onNavigate?.("all")}>
                            <BookOpen className="mr-2 h-4 w-4" />
                            All Courses
                        </Button>
                        <Button variant="ghost" className="w-full justify-start" onClick={() => onNavigate?.("recent")}>
                            <Clock className="mr-2 h-4 w-4" />
                            Recent
                        </Button>
                        <Button variant="ghost" className="w-full justify-start" onClick={() => onNavigate?.("starred")}>
                            <Star className="mr-2 h-4 w-4" />
                            Starred
                        </Button>
                    </div>
                </div>
            </div>
        </div>

    );
}
