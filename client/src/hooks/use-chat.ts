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
    regenerateResponse,
    recordFeedback,
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
    stopStreaming: () => void;
    regenerateLastResponse: () => Promise<void>;
    sendFeedback: (messageId: string, feedback: 'like' | 'dislike' | 'none') => Promise<void>;
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
    const abortControllerRef = useRef<AbortController | null>(null);
    
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
        
        let activeChatId = chat?.id || 'new';
        let isNewChat = !chat;

        // Add user message immediately
        const userMessage: Message = {
            id: crypto.randomUUID(),
            chat_id: activeChatId === 'new' ? '' : activeChatId,
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
        
        // Setup AbortController for stopping
        const controller = new AbortController();
        abortControllerRef.current = controller;

        try {
            await sendMessageStream(activeChatId, content, (event) => {
                if (event.event === 'token' && event.data.content) {
                    fullContent += event.data.content;
                    setStreamingContent(fullContent);
                } else if (event.event === 'tool_call') {
                    // Show tool usage indicator
                    setStreamingContent((prev) => prev + `\n_${event.data.content}_\n`);
                } else if (event.event === 'thinking') {
                    setThinkingLogs((prev) => [...prev, event.data.content]);
                } else if (event.event === 'chat_created') {
                    // Implicitly created chat - update ID and state
                    const newId = event.data.content;
                    activeChatId = newId;
                    setChat({
                        id: newId,
                        title: content.slice(0, 50) + '...',
                        messages: [],
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString(),
                        user_id: '', // Placeholder
                    } as ChatDetail);
                } else if (event.event === 'error') {
                   // Recognize quota errors
                   if (event.data.content.includes('QUOTA_EXCEEDED')) {
                       setError(new Error('AI Model quota reached. Please try again later.'));
                   } else {
                       console.error("Stream event error:", event.data);
                   }
                }
            }, controller.signal);
            
            abortControllerRef.current = null;
            
            // Add final assistant message
            const assistantMessage: Message = {
                id: assistantMessageId,
                chat_id: activeChatId,
                role: 'assistant',
                content: fullContent,
                created_at: new Date().toISOString(),
            };
            
            setMessages((prev) => [...prev, assistantMessage]);

            return activeChatId; // Return ID so component can update URL
            
        } catch (err) {
            const error = err instanceof Error ? err : new Error('Failed to send message');
            setError(error);
            onError?.(error);
            
            // Remove the user message on error
            setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
        } finally {
            setIsStreaming(false);
            setStreamingContent('');
            abortControllerRef.current = null;
        }
    }, [chat, isStreaming, onError]);
    
    const stopStreaming = useCallback(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
            setIsStreaming(false);
        }
    }, []);

    const regenerateLastResponse = useCallback(async () => {
        if (!chat || isStreaming) return;
        
        setError(null);
        setIsStreaming(true);
        setStreamingContent('');
        setThinkingLogs([]);
        
        // Remove the last assistant message from local state if it exists
        setMessages(prev => {
            const last = prev[prev.length - 1];
            if (last && last.role === 'assistant') {
                return prev.slice(0, -1);
            }
            return prev;
        });

        const controller = new AbortController();
        abortControllerRef.current = controller;
        let fullContent = '';
        const assistantMessageId = crypto.randomUUID();

        try {
            await regenerateResponse(chat.id, (event) => {
                if (event.event === 'token' && event.data.content) {
                    fullContent += event.data.content;
                    setStreamingContent(fullContent);
                } else if (event.event === 'thinking') {
                    setThinkingLogs((prev) => [...prev, event.data.content]);
                } else if (event.event === 'error') {
                    if (event.data.content.includes('QUOTA_EXCEEDED')) {
                        setError(new Error('AI Model quota reached. Please try again later.'));
                    }
                }
            }, controller.signal);

            const assistantMessage: Message = {
                id: assistantMessageId,
                chat_id: chat.id,
                role: 'assistant',
                content: fullContent,
                created_at: new Date().toISOString(),
            };
            
            setMessages((prev) => [...prev, assistantMessage]);
        } catch (err) {
            // If it's an abort error, we don't necessarily want to show it as a big failed state
            if (err instanceof Error && err.name === 'AbortError') {
                return;
            }
            const error = err instanceof Error ? err : new Error('Failed to regenerate response');
            setError(error);
            onError?.(error);
        } finally {
            setIsStreaming(false);
            setStreamingContent('');
            abortControllerRef.current = null;
        }
    }, [chat, isStreaming, onError]);

    const sendFeedback = useCallback(async (messageId: string, feedback: 'like' | 'dislike' | 'none') => {
        if (!chat) return;

        // Optimistic update
        setMessages(prev => prev.map(m => {
            if (m.id === messageId) {
                return {
                    ...m,
                    metadata: {
                        ...m.metadata,
                        user_feedback: feedback
                    }
                };
            }
            return m;
        }));

        try {
            await recordFeedback(chat.id, messageId, feedback);
        } catch (err) {
            console.error('Failed to record feedback:', err);
            // Revert on failure could be added here
        }
    }, [chat]);
    
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
        stopStreaming,
        regenerateLastResponse,
        sendFeedback,
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
