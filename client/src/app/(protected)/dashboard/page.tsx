'use client';

import { useCallback, useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useChat } from '@/hooks/use-chat';
import {
    ChatHeader,
    ChatMessageList,
    ChatInput,
    ChatError,
} from '@/components/chat/chat-components';
import { ChatSidebar, MobileChatSidebar } from '@/components/chat/chat-sidebar';

import { ContentViewerModal } from '@/components/chat/content-viewer-modal';

export default function ChatPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const chatId = searchParams.get('id') || undefined;

    // Content Viewer State
    const [viewContentUrl, setViewContentUrl] = useState<string | undefined>(undefined);

    const {
        chat,
        messages,
        isLoading,
        isStreaming,
        streamingContent,
        error,
        sendMessage,
        loadChat,
        createNewChat,
        clearError,
    } = useChat({ chatId });

    const [sidebarOpen, setSidebarOpen] = useState(true);

    const handleNewChat = useCallback(async () => {
        try {
            const newChat = await createNewChat();
            router.push(`/dashboard?id=${newChat.id}`);
        } catch (err) {
            // Error handled by hook
        }
    }, [createNewChat, router]);

    const handleSelectChat = useCallback((id: string) => {
        router.push(`/dashboard?id=${id}`);
    }, [router]);

    const handleSendMessage = useCallback(async (content: string) => {
        // If no chat exists, create one first
        if (!chat) {
            try {
                const newChat = await createNewChat(content.slice(0, 50) + '...');
                router.push(`/dashboard?id=${newChat.id}`, { scroll: false });

                // Wait a bit for navigation then send
                setTimeout(() => {
                    sendMessage(content);
                }, 100);
            } catch (err) {
                // Error handled by hook
            }
        } else {
            sendMessage(content);
        }
    }, [chat, createNewChat, router, sendMessage]);

    const handleViewContent = useCallback((url: string) => {
        setViewContentUrl(url);
    }, []);

    return (
        <div className="flex h-[calc(100vh-4rem)] bg-background">
            {/* Desktop Sidebar */}
            <div className="hidden md:block w-72 border-r border-border shrink-0">
                <ChatSidebar
                    currentChatId={chatId}
                    onSelectChat={handleSelectChat}
                    onNewChat={handleNewChat}
                />
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Header */}
                <div className="flex items-center gap-2 md:hidden px-2">
                    <MobileChatSidebar
                        currentChatId={chatId}
                        onSelectChat={handleSelectChat}
                        onNewChat={handleNewChat}
                    />
                </div>

                <ChatHeader
                    title={chat?.title}
                    onNewChat={handleNewChat}
                />

                {/* Messages */}
                <ChatMessageList
                    messages={messages}
                    isStreaming={isStreaming}
                    streamingContent={streamingContent}
                    onViewContent={handleViewContent}
                />

                {/* Error */}
                {error && (
                    <ChatError
                        error={error}
                        onRetry={clearError}
                    />
                )}

                {/* Input */}
                <ChatInput
                    onSend={handleSendMessage}
                    isStreaming={isStreaming}
                />

                {/* Content Viewer Modal */}
                <ContentViewerModal
                    open={!!viewContentUrl}
                    onOpenChange={(open) => !open && setViewContentUrl(undefined)}
                    contentUrl={viewContentUrl}
                    title="Generated Content"
                />
            </div>
        </div>
    );
}
