'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import {
    Chat,
    Message,
    ChatDetail,
    createChat,
    getChat,
    listChats,
    deleteChat,
    sendMessageStream,
    ChatListResponse,
    updateChatTitle,
} from '@/lib/chat-api';

interface UseChatOptions {
    chatId?: string;
    onError?: (error: Error) => void;
}

interface UseChatReturn {
    // State
    chat: ChatDetail | null;
    messages: Message[];
    isLoading: boolean;
    isStreaming: boolean;
    streamingContent: string;
    thinkingLogs: string[];
    error: Error | null;
    
    // Actions
    sendMessage: (content: string) => Promise<string | undefined>;
    loadChat: (chatId: string) => Promise<void>;
    createNewChat: (title?: string) => Promise<Chat>;
    clearError: () => void;
}

/**
 * Hook for managing chat interactions with streaming support
 */
export function useChat({ chatId, onError }: UseChatOptions = {}): UseChatReturn {
    const [chat, setChat] = useState<ChatDetail | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamingContent, setStreamingContent] = useState('');
    const [thinkingLogs, setThinkingLogs] = useState<string[]>([]);
    const [error, setError] = useState<Error | null>(null);
    
    // Load chat on mount or chatId change
    useEffect(() => {
        if (chatId) {
            // Only load if the ID is different from what we currently have
            // This prevents reloading when we just created the chat and updated the URL
            if (chat?.id !== chatId) {
                loadChat(chatId);
            }
        } else {
            // If no chat ID, reset state (New Chat mode)
            setChat(null);
            setMessages([]);
            setThinkingLogs([]);
            setError(null);
        }
    }, [chatId]);
    
    const loadChat = useCallback(async (id: string) => {
        setIsLoading(true);
        setError(null);
        setThinkingLogs([]);
        
        try {
            const chatData = await getChat(id);
            setChat(chatData);
            // Deduplicate messages just in case, or just set them
            setMessages(chatData.messages);
        } catch (err) {
            const error = err instanceof Error ? err : new Error('Failed to load chat');
            setError(error);
            onError?.(error);
        } finally {
            setIsLoading(false);
        }
    }, [onError]);
    
    // "Create" just prepares the state. Actual creation happens on first message.
    const createNewChat = useCallback(async (title?: string): Promise<Chat> => {
        setChat(null);
        setMessages([]);
        setThinkingLogs([]);
        setError(null);
        // Return a placeholder that makes the component clear the ID
        return { id: '', title: title || 'New Chat' } as Chat;
    }, []);
    
    const sendMessage = useCallback(async (content: string): Promise<string | undefined> => {
        if (isStreaming) return;
        
        setError(null);
        
        let activeChat: Chat | ChatDetail | null = chat;
        let isNewChat = false;

        // 1. Create chat if it doesn't exist
        if (!activeChat) {
            try {
                // Generate a title from the first message
                const title = content.slice(0, 50) + '...';
                // createChat returns Chat (not ChatDetail)
                const newChat = await createChat(title);
                activeChat = newChat;
                
                // Initialize with empty messages as it's new
                // We cast to ChatDetail because we are adding the missing 'messages' property
                setChat({ ...newChat, messages: [] } as ChatDetail);
                isNewChat = true;
            } catch (err) {
                const error = err instanceof Error ? err : new Error('Failed to create chat');
                setError(error);
                onError?.(error);
                return;
            }
        }
        
        // Ensure activeChat is present (it should be by now)
        if (!activeChat) return;

        // Add user message immediately
        const userMessage: Message = {
            id: crypto.randomUUID(),
            chat_id: activeChat.id,
            role: 'user',
            content,
            created_at: new Date().toISOString(),
        };
        
        setMessages((prev) => [...prev, userMessage]);
        setIsStreaming(true);
        setStreamingContent('');
        setThinkingLogs([]);
        
        // Create placeholder for assistant message
        const assistantMessageId = crypto.randomUUID();
        let fullContent = '';
        
        try {
            await sendMessageStream(activeChat.id, content, (event) => {
                if (event.event === 'token' && event.data.content) {
                    fullContent += event.data.content;
                    setStreamingContent(fullContent);
                } else if (event.event === 'tool_call') {
                    // Show tool usage indicator
                    setStreamingContent((prev) => prev + `\n_${event.data.content}_\n`);
                } else if (event.event === 'thinking') {
                    setThinkingLogs((prev) => [...prev, event.data.content]);
                } else if (event.event === 'error') {
                   // If error is "Stream error", we might want to catch it
                   console.error("Stream event error:", event.data);
                }
            });
            
            // Add final assistant message
            const assistantMessage: Message = {
                id: assistantMessageId,
                chat_id: activeChat.id,
                role: 'assistant',
                content: fullContent,
                created_at: new Date().toISOString(),
            };
            
            setMessages((prev) => [...prev, assistantMessage]);

            return activeChat.id; // Return ID so component can update URL
            
        } catch (err) {
            const error = err instanceof Error ? err : new Error('Failed to send message');
            setError(error);
            onError?.(error);
            
            // Remove the user message on error
            setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
        } finally {
            setIsStreaming(false);
            setStreamingContent('');
        }
    }, [chat, isStreaming, onError]);
    
    const clearError = useCallback(() => {
        setError(null);
    }, []);
    
    return {
        chat,
        messages,
        isLoading,
        isStreaming,
        streamingContent,
        thinkingLogs,
        error,
        sendMessage,
        loadChat,
        createNewChat,
        clearError,
    };
}

interface UseChatListOptions {
    pageSize?: number;
}

interface UseChatListReturn {
    chats: Chat[];
    isLoading: boolean;
    error: Error | null;
    page: number;
    totalPages: number;
    loadChats: () => Promise<void>;
    loadMore: () => Promise<void>;
    removeChat: (chatId: string) => Promise<void>;
    renameChat: (chatId: string, newTitle: string) => Promise<void>;
}

/**
 * Hook for managing chat list
 */
export function useChatList({ pageSize = 20 }: UseChatListOptions = {}): UseChatListReturn {
    const [chats, setChats] = useState<Chat[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    
    const loadChats = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        
        try {
            const response = await listChats(1, pageSize);
            setChats(response.chats);
            setTotal(response.total);
            setPage(1);
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Failed to load chats'));
        } finally {
            setIsLoading(false);
        }
    }, [pageSize]);
    
    const loadMore = useCallback(async () => {
        if (isLoading || chats.length >= total) return;
        
        setIsLoading(true);
        
        try {
            const response = await listChats(page + 1, pageSize);
            setChats((prev) => [...prev, ...response.chats]);
            setPage((p) => p + 1);
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Failed to load more chats'));
        } finally {
            setIsLoading(false);
        }
    }, [isLoading, chats.length, total, page, pageSize]);
    
    const removeChat = useCallback(async (chatId: string) => {
        try {
            await deleteChat(chatId);
            setChats((prev) => prev.filter((c) => c.id !== chatId));
            setTotal((t) => t - 1);
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Failed to delete chat'));
        }
    }, []);
    
    const renameChat = useCallback(async (chatId: string, newTitle: string) => {
        try {
            const updatedChat = await updateChatTitle(chatId, newTitle);
            setChats((prev) => prev.map((c) => c.id === chatId ? { ...c, title: updatedChat.title } : c));
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Failed to rename chat'));
            throw err;
        }
    }, []);
    
    // Load chats on mount
    useEffect(() => {
        loadChats();
    }, [loadChats]);
    
    return {
        chats,
        isLoading,
        error,
        page,
        totalPages: Math.ceil(total / pageSize),
        loadChats,
        loadMore,
        removeChat,
        renameChat,
    };
}
