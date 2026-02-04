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

import { Suspense } from 'react';

function ChatContent() {
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
        thinkingLogs,
        error,
        sendMessage,
        stopStreaming,
        regenerateLastResponse,
        sendFeedback,
        loadChat,
        createNewChat,
        clearError,
    } = useChat({ chatId });

    const [sidebarOpen, setSidebarOpen] = useState(true);

    const handleNewChat = useCallback(async () => {
        // Just clear the URL, useChat will handle state reset
        router.push('/dashboard');
        // createNewChat() in hook effectively just resets state now
        await createNewChat();
    }, [createNewChat, router]);

    const handleSelectChat = useCallback((id: string) => {
        router.push(`/dashboard?id=${id}`);
    }, [router]);

    const handleSendMessage = useCallback(async (content: string) => {
        // Send message - if no chat exists, hook will create one and return ID
        const newChatId = await sendMessage(content);

        // If a new chat was created, update URL without reloading page
        if (newChatId && !chat) {
            router.push(`/dashboard?id=${newChatId}`, { scroll: false });
        }
    }, [chat, createNewChat, router, sendMessage]);

    const handleViewContent = useCallback((url: string) => {
        setViewContentUrl(url);
    }, []);

    return (
        <div className="flex h-[calc(100vh-65px)] bg-background">
            {/* Desktop Sidebar */}
            <div className="hidden md:block w-72 border-r border-border shrink-0">
                <ChatSidebar
                    currentChatId={chatId}
                    onSelectChat={handleSelectChat}
                    onNewChat={handleNewChat}
                    isStreaming={isStreaming}
                />
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <ChatHeader
                    title={chat?.title}
                    onNewChat={handleNewChat}
                    mobileSidebar={
                        <MobileChatSidebar
                            currentChatId={chatId}
                            onSelectChat={handleSelectChat}
                            onNewChat={handleNewChat}
                            isStreaming={isStreaming}
                        />
                    }
                />

                {/* Messages */}
                <ChatMessageList
                    messages={messages}
                    isStreaming={isStreaming}
                    streamingContent={streamingContent}
                    thinkingLogs={thinkingLogs}
                    isLoading={isLoading}
                    onViewContent={handleViewContent}
                    onSuggestionClick={handleSendMessage}
                    onFeedback={sendFeedback}
                    onStop={stopStreaming}
                    onRegenerate={regenerateLastResponse}
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

export default function ChatPage() {
    return (
        <Suspense fallback={<div className="flex h-[calc(100vh-4rem)] items-center justify-center">Loading...</div>}>
            <ChatContent />
        </Suspense>
    );
}
