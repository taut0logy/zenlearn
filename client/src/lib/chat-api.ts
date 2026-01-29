/**
 * API Client for Chat Agent
 * 
 * Handles all communication with the chat backend API,
 * including SSE streaming for real-time responses.
 */

import { createClient } from '@/lib/supabase/client';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Types for chat API
export interface Chat {
    id: string;
    user_id: string;
    title: string;
    created_at: string;
    updated_at: string;
    message_count?: number;
}

export interface Message {
    id: string;
    chat_id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    metadata?: Record<string, unknown>;
    created_at: string;
}

export interface ChatDetail extends Chat {
    messages: Message[];
}

export interface ChatListResponse {
    chats: Chat[];
    total: number;
    page: number;
    page_size: number;
}

export interface StreamEvent {
    event: 'start' | 'token' | 'tool_call' | 'tool_result' | 'end' | 'error';
    data: { content: string };
}

/**
 * Get the authentication token from Supabase
 */
async function getAuthToken(): Promise<string | null> {
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token || null;
}

/**
 * Make an authenticated API request
 */
async function apiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const token = await getAuthToken();
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers,
        },
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || 'Request failed');
    }
    
    return response.json();
}

/**
 * Create a new chat session
 */
export async function createChat(title?: string): Promise<Chat> {
    return apiRequest<Chat>('/chat', {
        method: 'POST',
        body: JSON.stringify({ title }),
    });
}

/**
 * List all chats for the current user
 */
export async function listChats(page = 1, pageSize = 20): Promise<ChatListResponse> {
    return apiRequest<ChatListResponse>(`/chat?page=${page}&page_size=${pageSize}`);
}

/**
 * Get a chat with all messages
 */
export async function getChat(chatId: string): Promise<ChatDetail> {
    return apiRequest<ChatDetail>(`/chat/${chatId}`);
}

/**
 * Delete a chat
 */
export async function deleteChat(chatId: string): Promise<void> {
    await apiRequest(`/chat/${chatId}`, { method: 'DELETE' });
}

/**
 * Update chat title
 */
export async function updateChatTitle(chatId: string, title: string): Promise<Chat> {
    return apiRequest<Chat>(`/chat/${chatId}/title?title=${encodeURIComponent(title)}`, {
        method: 'PATCH',
    });
}

/**
 * Send a message with SSE streaming response
 * 
 * @param chatId - Chat ID
 * @param content - Message content
 * @param onEvent - Callback for each stream event
 * @returns Promise that resolves when streaming is complete
 */
export async function sendMessageStream(
    chatId: string,
    content: string,
    onEvent: (event: StreamEvent) => void
): Promise<void> {
    const token = await getAuthToken();
    
    const response = await fetch(
        `${API_BASE_URL}/chat/${chatId}/message?stream=true`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({ content }),
        }
    );
    
    if (!response.ok) {
        throw new Error('Failed to send message');
    }
    
    if (!response.body) {
        throw new Error('No response body');
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Parse SSE events from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        let currentEvent = '';
        for (const line of lines) {
            if (line.startsWith('event:')) {
                currentEvent = line.slice(6).trim();
            } else if (line.startsWith('data:')) {
                const data = line.slice(5).trim();
                if (data && currentEvent) {
                    try {
                        const parsed = JSON.parse(data);
                        onEvent({
                            event: currentEvent as StreamEvent['event'],
                            data: parsed,
                        });
                    } catch {
                        // Ignore parse errors
                    }
                }
            }
        }
    }
}

/**
 * Send a message without streaming
 */
export async function sendMessage(
    chatId: string,
    content: string
): Promise<{ role: string; content: string }> {
    return apiRequest(`/chat/${chatId}/message?stream=false`, {
        method: 'POST',
        body: JSON.stringify({ content }),
    });
}
