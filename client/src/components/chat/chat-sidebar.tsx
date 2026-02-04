'use client';

import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Chat } from '@/lib/chat-api';
import { useChatList } from '@/hooks/use-chat';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
    Sheet,
    SheetContent,
    SheetTrigger,
} from '@/components/ui/sheet';
import { Skeleton } from '@/components/ui/skeleton';
import {
    MessageSquare,
    Plus,
    Trash2,
    MoreHorizontal,
    History,
    Menu,
    Loader2,
    Pencil,
    Check,
    X,
} from 'lucide-react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';

interface ChatSidebarProps {
    currentChatId?: string;
    onSelectChat: (chatId: string) => void;
    onNewChat: () => void;
    isStreaming?: boolean; // When streaming ends, refetch to get updated title
}

// Loading skeleton for chat list items
function ChatListSkeleton() {
    return (
        <div className="space-y-2 p-2">
            {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center gap-2 px-2 py-2 rounded-lg">
                    <Skeleton className="h-4 w-4 rounded-full shrink-0" />
                    <div className="flex-1 min-w-0 space-y-1.5">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-3 w-16" />
                    </div>
                </div>
            ))}
        </div>
    );
}

export function ChatSidebar({
    currentChatId,
    onSelectChat,
    onNewChat,
    isStreaming,
}: ChatSidebarProps) {
    const { chats, isLoading, removeChat, renameChat, loadMore, loadChats, totalPages, page } = useChatList();
    const [wasStreaming, setWasStreaming] = useState(false);

    // Refetch chat list when streaming ends (to pick up auto-generated titles)
    useEffect(() => {
        if (wasStreaming && !isStreaming) {
            // Streaming just ended, refetch to get new title
            const timer = setTimeout(() => {
                loadChats();
            }, 500); // Small delay to ensure backend has updated
            return () => clearTimeout(timer);
        }
        setWasStreaming(!!isStreaming);
    }, [isStreaming, wasStreaming, loadChats]);

    return (
        <div className="flex flex-col h-full bg-sidebar text-sidebar-foreground">
            {/* Header */}
            <div className="p-4 border-b border-sidebar-border">
                <Button
                    onClick={onNewChat}
                    className="w-full justify-start gap-2 bg-gradient-to-r from-primary to-emerald-600 cursor-pointer"
                >
                    <Plus className="h-4 w-4" />
                    New Chat
                </Button>
            </div>

            {/* Chat List */}
            <div className="flex-1 overflow-y-auto">
                <div className="p-2">
                    <p className="text-xs font-medium text-sidebar-foreground/60 px-2 py-2">
                        Recent Conversations
                    </p>

                    {isLoading && chats.length === 0 ? (
                        <ChatListSkeleton />
                    ) : chats.length === 0 ? (
                        <div className="text-center py-8 px-4">
                            <History className="h-8 w-8 mx-auto text-muted-foreground/50 mb-2" />
                            <p className="text-sm text-muted-foreground">
                                No conversations yet
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-1">
                            {chats.map((chat) => (
                                <ChatListItem
                                    key={chat.id}
                                    chat={chat}
                                    isActive={chat.id === currentChatId}
                                    onSelect={() => onSelectChat(chat.id)}
                                    onDelete={() => removeChat(chat.id)}
                                    onRename={(newTitle) => renameChat(chat.id, newTitle)}
                                />
                            ))}

                            {page < totalPages && (
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={loadMore}
                                    disabled={isLoading}
                                    className="w-full mt-2"
                                >
                                    {isLoading ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                        'Load more'
                                    )}
                                </Button>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

interface ChatListItemProps {
    chat: Chat;
    isActive: boolean;
    onSelect: () => void;
    onDelete: () => void;
    onRename: (newTitle: string) => Promise<void>;
}

function ChatListItem({ chat, isActive, onSelect, onDelete, onRename }: ChatListItemProps) {
    const [isEditing, setIsEditing] = useState(false);
    const [editTitle, setEditTitle] = useState(chat.title);
    const [isRenaming, setIsRenaming] = useState(false);

    const formattedDate = new Date(chat.updated_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
    });

    const handleStartEdit = (e: React.MouseEvent) => {
        e.stopPropagation();
        setEditTitle(chat.title);
        setIsEditing(true);
    };

    const handleCancelEdit = (e?: React.MouseEvent) => {
        e?.stopPropagation();
        setIsEditing(false);
        setEditTitle(chat.title);
    };

    const handleSaveEdit = async (e?: React.MouseEvent | React.FormEvent) => {
        e?.stopPropagation();
        e?.preventDefault();

        if (!editTitle.trim() || editTitle === chat.title) {
            handleCancelEdit();
            return;
        }

        setIsRenaming(true);
        try {
            await onRename(editTitle.trim());
            setIsEditing(false);
        } catch {
            // Error handled in hook
        } finally {
            setIsRenaming(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSaveEdit();
        } else if (e.key === 'Escape') {
            handleCancelEdit();
        }
    };

    if (isEditing) {
        return (
            <div
                className={cn(
                    'flex items-center gap-2 px-2 py-2 rounded-lg',
                    'bg-sidebar-accent'
                )}
                onClick={(e) => e.stopPropagation()}
            >
                <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />

                <div className="flex-1 min-w-0">
                    <Input
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="h-7 text-sm"
                        autoFocus
                        disabled={isRenaming}
                    />
                </div>

                <div className="flex gap-1">
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={handleSaveEdit}
                        disabled={isRenaming}
                    >
                        {isRenaming ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                            <Check className="h-3 w-3 text-primary" />
                        )}
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={handleCancelEdit}
                        disabled={isRenaming}
                    >
                        <X className="h-3 w-3" />
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div
            className={cn(
                'group flex items-center gap-2 px-2 py-2 rounded-lg cursor-pointer transition-colors',
                isActive
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                    : 'hover:bg-sidebar-accent/50'
            )}
            onClick={onSelect}
        >
            <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />

            <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                    {chat.title}
                </p>
                <p className="text-xs text-muted-foreground">
                    {formattedDate}
                </p>
            </div>

            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 opacity-0 group-hover:opacity-100"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <MoreHorizontal className="h-4 w-4" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={handleStartEdit}>
                        <Pencil className="h-4 w-4 mr-2" />
                        Rename
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                        className="text-destructive focus:text-destructive"
                        onClick={(e) => {
                            e.stopPropagation();
                            onDelete();
                        }}
                    >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    );
}

// ====================
// Mobile Sidebar (Sheet)
// ====================

interface MobileChatSidebarProps extends ChatSidebarProps { }

export function MobileChatSidebar(props: MobileChatSidebarProps) {
    const [open, setOpen] = useState(false);

    return (
        <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden">
                    <Menu className="h-5 w-5" />
                </Button>
            </SheetTrigger>
            <SheetContent side="left" className="p-0 w-80">
                <ChatSidebar
                    {...props}
                    onSelectChat={(id) => {
                        props.onSelectChat(id);
                        setOpen(false);
                    }}
                    onNewChat={() => {
                        props.onNewChat();
                        setOpen(false);
                    }}
                />
            </SheetContent>
        </Sheet>
    );
}
