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
    error: Error | null;
    
    // Actions
    sendMessage: (content: string) => Promise<void>;
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
    const [error, setError] = useState<Error | null>(null);
    
    const abortControllerRef = useRef<AbortController | null>(null);
    
    // Load chat on mount or chatId change
    useEffect(() => {
        if (chatId) {
            loadChat(chatId);
        }
    }, [chatId]);
    
    const loadChat = useCallback(async (id: string) => {
        setIsLoading(true);
        setError(null);
        
        try {
            const chatData = await getChat(id);
            setChat(chatData);
            setMessages(chatData.messages);
        } catch (err) {
            const error = err instanceof Error ? err : new Error('Failed to load chat');
            setError(error);
            onError?.(error);
        } finally {
            setIsLoading(false);
        }
    }, [onError]);
    
    const createNewChat = useCallback(async (title?: string): Promise<Chat> => {
        setIsLoading(true);
        setError(null);
        
        try {
            const newChat = await createChat(title);
            setChat({ ...newChat, messages: [] });
            setMessages([]);
            return newChat;
        } catch (err) {
            const error = err instanceof Error ? err : new Error('Failed to create chat');
            setError(error);
            onError?.(error);
            throw error;
        } finally {
            setIsLoading(false);
        }
    }, [onError]);
    
    const sendMessage = useCallback(async (content: string) => {
        if (!chat || isStreaming) return;
        
        setError(null);
        
        // Add user message immediately
        const userMessage: Message = {
            id: crypto.randomUUID(),
            chat_id: chat.id,
            role: 'user',
            content,
            created_at: new Date().toISOString(),
        };
        
        setMessages((prev) => [...prev, userMessage]);
        setIsStreaming(true);
        setStreamingContent('');
        
        // Create placeholder for assistant message
        const assistantMessageId = crypto.randomUUID();
        let fullContent = '';
        
        try {
            await sendMessageStream(chat.id, content, (event) => {
                if (event.event === 'token' && event.data.content) {
                    fullContent += event.data.content;
                    setStreamingContent(fullContent);
                } else if (event.event === 'tool_call') {
                    // Show tool usage indicator
                    setStreamingContent((prev) => prev + `\n_${event.data.content}_\n`);
                } else if (event.event === 'error') {
                    throw new Error(event.data.content || 'Streaming error');
                }
            });
            
            // Add final assistant message
            const assistantMessage: Message = {
                id: assistantMessageId,
                chat_id: chat.id,
                role: 'assistant',
                content: fullContent,
                created_at: new Date().toISOString(),
            };
            
            setMessages((prev) => [...prev, assistantMessage]);
            
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
    };
}
