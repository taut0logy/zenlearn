"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { ThemeToggle } from "./theme-toggle";
import { Button } from "@/components/ui/button";
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import {
    Home,
    LogOut,
    Menu,
    MessageSquare,
    Settings,
    User,
    Video,
    FileText,
    Users,
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { UserMenu } from "./user-menu";
import { useAuth } from "@/hooks/use-auth";

const getNavItems = (role?: string) => {
    const items = [
        {
            title: "Dashboard",
            href: "/dashboard",
            icon: Home,
            roles: ["user", "admin"],
        },
        {
            title: "Materials",
            href: "/materials",
            icon: MessageSquare,
            roles: ["user", "admin"],
        },
        {
            title: "Notes",
            href: "/notes",
            icon: FileText,
            roles: ["user", "admin"],
        },
        {
            title: "Community",
            href: "/community",
            icon: Users,
            roles: ["user", "admin"],
        },
    ];

    const adminItems = [
        {
            title: "Admin",
            href: "/admin",
            icon: Settings,
            roles: ["admin"],
        },
    ];

    return [...items, ...(role === "admin" ? adminItems : [])];
};

export function Header() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const router = useRouter();
    const pathname = usePathname();
    const { user, isLoading, signOut: authSignOut } = useAuth();
    const navItems = getNavItems(user?.profile?.role);

    const closeMenu = () => setIsMenuOpen(false);

    const handleLogout = async () => {
        await authSignOut();
    };

    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth >= 768 && isMenuOpen) {
                setIsMenuOpen(false);
            }
        };

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, [isMenuOpen]);

    const getUserInitials = () => {
        if (!user?.profile?.name) return "U";
        const names = user.profile.name.split(" ");
        return names
            .map((n) => n[0])
            .join("")
            .toUpperCase()
            .slice(0, 2);
    };

    return (
        <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60 px-4">
            <div className="container mx-auto flex h-16 items-center justify-between">
                <Link
                    href="/"
                    className="flex items-center space-x-2 font-bold text-xl"
                >
                    <span className="hidden sm:inline-block">ZenLearn</span>
                </Link>

                <nav className="hidden md:flex items-center space-x-6">
                    {user && (
                        <div className="flex items-center space-x-6">
                            {navItems.map((item) => (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`flex items-center text-sm font-medium transition-colors hover:text-primary ${
                                        pathname === item.href
                                            ? "text-primary font-bold"
                                            : "text-muted-foreground"
                                    }`}
                                >
                                    {item.title}
                                </Link>
                            ))}
                        </div>
                    )}
                </nav>

                <div className="flex items-center gap-2">
                    <ThemeToggle />

                    {isLoading ? (
                        <div className="h-8 w-8 animate-pulse rounded-full bg-muted" />
                    ) : user ? (
                        <UserMenu user={user} onLogout={handleLogout} />
                    ) : (
                        <div className="hidden md:flex items-center gap-2">
                            <Button
                                variant="ghost"
                                onClick={() => router.push("/auth")}
                            >
                                Sign in
                            </Button>
                            <Button
                                onClick={() => router.push("/auth?mode=signup")}
                            >
                                Sign up
                            </Button>
                        </div>
                    )}

                    <Sheet open={isMenuOpen} onOpenChange={setIsMenuOpen}>
                        <SheetTrigger asChild className="md:hidden">
                            <Button
                                variant="ghost"
                                size="icon"
                                aria-label="Menu"
                            >
                                <Menu className="h-5 w-5" />
                            </Button>
                        </SheetTrigger>
                        <SheetContent
                            side="right"
                            className="w-[85vw] sm:w-87.5 pr-0"
                        >
                            <SheetHeader className="mb-4">
                                <SheetTitle className="flex items-center text-lg">
                                    <Video className="h-5 w-5 mr-2 text-primary" />
                                    My App
                                </SheetTitle>
                            </SheetHeader>

                            {user ? (
                                <>
                                    <div className="flex items-center space-x-4 mt-4 mb-6 px-4">
                                        <Avatar className="h-10 w-10">
                                            <AvatarImage
                                                src={
                                                    user?.profile?.avatarUrl ||
                                                    ""
                                                }
                                                alt={
                                                    user?.profile?.name ||
                                                    "User"
                                                }
                                            />
                                            <AvatarFallback>
                                                {getUserInitials()}
                                            </AvatarFallback>
                                        </Avatar>
                                        <div>
                                            <p className="text-sm font-medium">
                                                {user?.profile?.name}
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                {user?.email}
                                            </p>
                                        </div>
                                    </div>

                                    <Separator className="mb-4" />

                                    <div className="flex flex-col space-y-1 px-4">
                                        {navItems.map((item) => (
                                            <Button
                                                key={item.href}
                                                variant={
                                                    pathname === item.href
                                                        ? "secondary"
                                                        : "ghost"
                                                }
                                                className="justify-start"
                                                onClick={() => {
                                                    router.push(item.href);
                                                    closeMenu();
                                                }}
                                            >
                                                <item.icon className="mr-2 h-4 w-4" />
                                                {item.title}
                                            </Button>
                                        ))}
                                    </div>

                                    <Separator className="my-4" />

                                    <div className="px-4 pb-8">
                                        <Button
                                            variant="ghost"
                                            className="justify-start w-full"
                                            onClick={() => {
                                                router.push("/profile");
                                                closeMenu();
                                            }}
                                        >
                                            <User className="mr-2 h-4 w-4" />
                                            Profile
                                        </Button>

                                        <Button
                                            variant="ghost"
                                            className="justify-start w-full"
                                            onClick={() => {
                                                router.push("/settings");
                                                closeMenu();
                                            }}
                                        >
                                            <Settings className="mr-2 h-4 w-4" />
                                            Settings
                                        </Button>

                                        <Button
                                            variant="ghost"
                                            className="justify-start w-full text-destructive hover:text-destructive hover:bg-destructive/10"
                                            onClick={() => {
                                                handleLogout();
                                                closeMenu();
                                            }}
                                        >
                                            <LogOut className="mr-2 h-4 w-4" />
                                            Log out
                                        </Button>
                                    </div>
                                </>
                            ) : (
                                <div className="flex flex-col space-y-4 px-4 mt-6">
                                    <Button
                                        onClick={() => {
                                            router.push("/auth?mode=login");
                                            closeMenu();
                                        }}
                                        className="w-full"
                                    >
                                        Sign in
                                    </Button>
                                    <Button
                                        variant="outline"
                                        onClick={() => {
                                            router.push("/auth?mode=signup");
                                            closeMenu();
                                        }}
                                        className="w-full"
                                    >
                                        Sign up
                                    </Button>
                                </div>
                            )}

                            <div className="absolute bottom-6 left-6">
                                <ThemeToggle />
                            </div>
                        </SheetContent>
                    </Sheet>
                </div>
            </div>
        </header>
    );
}
