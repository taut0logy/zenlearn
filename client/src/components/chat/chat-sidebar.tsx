'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Chat } from '@/lib/chat-api';
import { useChatList } from '@/hooks/use-chat';
import { Button } from '@/components/ui/button';
import { 
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from '@/components/ui/sheet';
import {
    MessageSquare,
    Plus,
    Trash2,
    MoreHorizontal,
    History,
    Menu,
    Loader2,
} from 'lucide-react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface ChatSidebarProps {
    currentChatId?: string;
    onSelectChat: (chatId: string) => void;
    onNewChat: () => void;
}

export function ChatSidebar({
    currentChatId,
    onSelectChat,
    onNewChat,
}: ChatSidebarProps) {
    const { chats, isLoading, removeChat, loadMore, totalPages, page } = useChatList();
    
    return (
        <div className="flex flex-col h-full bg-sidebar text-sidebar-foreground">
            {/* Header */}
            <div className="p-4 border-b border-sidebar-border">
                <Button
                    onClick={onNewChat}
                    className="w-full justify-start gap-2 bg-gradient-to-r from-primary to-emerald-600"
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
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                        </div>
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
}

function ChatListItem({ chat, isActive, onSelect, onDelete }: ChatListItemProps) {
    const formattedDate = new Date(chat.updated_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
    });
    
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

interface MobileChatSidebarProps extends ChatSidebarProps {}

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
