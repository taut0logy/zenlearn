"use client";

import * as React from "react";
import { useTheme } from "next-themes";
import { motion } from "motion/react";
import { Sun, Moon, SunMoon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const ThemeIcons = {
    light: Sun,
    dark: Moon,
    system: SunMoon,
};

export function ThemeToggle() {
    const { setTheme, theme } = useTheme();
    const [mounted, setMounted] = React.useState(false);

    React.useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        return <ThemeToggleSkeleton />;
    }

    const currentTheme = theme || "system";
    const IconComponent = ThemeIcons[currentTheme as keyof typeof ThemeIcons];

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="ghost"
                    size="icon"
                    className="relative h-10 w-10 rounded-full"
                >
                    <motion.div
                        key={currentTheme}
                        initial={{ scale: 0.5, opacity: 0, y: 5 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.5, opacity: 0, y: 5 }}
                        transition={{ duration: 0.2 }}
                        className="absolute inset-0 flex items-center justify-center"
                    >
                        <IconComponent className="h-8 w-8" />
                    </motion.div>
                    <span className="sr-only">Toggle theme</span>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setTheme("light")}>
                    <Sun className="mr-2 h-4 w-4" />
                    <span>Light</span>
                    {currentTheme === "light" && (
                        <motion.span
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="ml-auto flex h-2 w-2 rounded-full bg-primary"
                        />
                    )}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("dark")}>
                    <Moon className="mr-2 h-4 w-4" />
                    <span>Dark</span>
                    {currentTheme === "dark" && (
                        <motion.span
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="ml-auto flex h-2 w-2 rounded-full bg-primary"
                        />
                    )}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("system")}>
                    <SunMoon className="mr-2 h-4 w-4" />
                    <span>System</span>
                    {currentTheme === "system" && (
                        <motion.span
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="ml-auto flex h-2 w-2 rounded-full bg-primary"
                        />
                    )}
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}

function ThemeToggleSkeleton() {
    return (
        <Button
            variant="ghost"
            size="icon"
            disabled
            className="h-9 w-9 rounded-full"
        >
            <div className="h-8 w-8 rounded-full bg-muted animate-pulse" />
            <span className="sr-only">Toggle theme</span>
        </Button>
    );
}
