'use client';

import { FormEvent, useRef, useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { Message } from '@/lib/chat-api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
    Send,
    Bot,
    User,
    Loader2,
    RefreshCw,
    Sparkles,
    AlertCircle,
    Copy,
    Check,
} from 'lucide-react';
import { MarkdownRenderer } from './markdown-renderer';
import { CopyButton } from './copy-button';

// ====================
// Message Bubble
// ====================

interface ChatMessageProps {
    message: Message;
    isStreaming?: boolean;
}

export function ChatMessage({ message, isStreaming }: ChatMessageProps) {
    const isUser = message.role === 'user';
    
    return (
        <div
            className={cn(
                'group flex gap-3 p-4 rounded-lg transition-all',
                isUser
                    ? 'bg-primary/10 ml-8'
                    : 'bg-muted/50 mr-8'
            )}
        >
            <Avatar className="h-8 w-8 shrink-0">
                {isUser ? (
                    <>
                        <AvatarFallback className="bg-primary text-primary-foreground">
                            <User className="h-4 w-4" />
                        </AvatarFallback>
                    </>
                ) : (
                    <>
                        <AvatarFallback className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
                            <Bot className="h-4 w-4" />
                        </AvatarFallback>
                    </>
                )}
            </Avatar>
            
            <div className="flex-1 space-y-1 overflow-hidden min-w-0">
                <div className="flex items-center justify-between">
                    <p className="text-xs font-medium text-muted-foreground">
                        {isUser ? 'You' : 'ZenLearn Assistant'}
                    </p>
                    {!isUser && !isStreaming && (
                        <CopyButton 
                            text={message.content} 
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                        />
                    )}
                </div>
                <div className="prose prose-sm dark:prose-invert max-w-none">
                    {isUser ? (
                        <p className="whitespace-pre-wrap break-words">{message.content}</p>
                    ) : (
                        <>
                            <MarkdownRenderer content={message.content} isStreaming={isStreaming} />
                            {isStreaming && (
                                <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse rounded-sm" />
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

// ====================
// Streaming Message
// ====================

interface StreamingMessageProps {
    content: string;
}

export function StreamingMessage({ content }: StreamingMessageProps) {
    if (!content) {
        return (
            <div className="flex gap-3 p-4 rounded-lg bg-muted/50 mr-8">
                <Avatar className="h-8 w-8 shrink-0">
                    <AvatarFallback className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
                        <Bot className="h-4 w-4" />
                    </AvatarFallback>
                </Avatar>
                <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                </div>
            </div>
        );
    }
    
    return (
        <ChatMessage
            message={{
                id: 'streaming',
                chat_id: '',
                role: 'assistant',
                content,
                created_at: new Date().toISOString(),
            }}
            isStreaming={true}
        />
    );
}

// ====================
// Message List
// ====================

interface ChatMessageListProps {
    messages: Message[];
    isStreaming: boolean;
    streamingContent: string;
}

export function ChatMessageList({
    messages,
    isStreaming,
    streamingContent,
}: ChatMessageListProps) {
    const bottomRef = useRef<HTMLDivElement>(null);
    
    // Auto-scroll to bottom on new messages
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, streamingContent]);
    
    if (messages.length === 0 && !isStreaming) {
        return (
            <div className="flex-1 flex items-center justify-center p-8">
                <div className="text-center space-y-4 max-w-md">
                    <div className="mx-auto w-16 h-16 rounded-full bg-gradient-to-br from-emerald-500/20 to-teal-600/20 flex items-center justify-center">
                        <Sparkles className="h-8 w-8 text-primary" />
                    </div>
                    <h3 className="text-xl font-semibold">Start a Conversation</h3>
                    <p className="text-muted-foreground">
                        Ask me anything about your courses, request explanations, or search through your materials.
                    </p>
                </div>
            </div>
        );
    }
    
    return (
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
            ))}
            
            {isStreaming && (
                <StreamingMessage content={streamingContent} />
            )}
            
            <div ref={bottomRef} />
        </div>
    );
}

// ====================
// Input Form
// ====================

interface ChatInputProps {
    onSend: (content: string) => void;
    isStreaming: boolean;
    placeholder?: string;
}

export function ChatInput({
    onSend,
    isStreaming,
    placeholder = 'Ask about your courses...',
}: ChatInputProps) {
    const [value, setValue] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    
    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        if (!value.trim() || isStreaming) return;
        
        onSend(value.trim());
        setValue('');
        
        // Reset textarea height
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    };
    
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };
    
    // Auto-resize textarea
    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
        }
    }, [value]);
    
    return (
        <form
            onSubmit={handleSubmit}
            className="border-t bg-background/80 backdrop-blur-sm p-4"
        >
            <div className="flex gap-2 items-end max-w-4xl mx-auto">
                <div className="flex-1 relative">
                    <Textarea
                        ref={textareaRef}
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={placeholder}
                        disabled={isStreaming}
                        className="min-h-[48px] max-h-[200px] resize-none pr-12 rounded-xl"
                        rows={1}
                    />
                </div>
                
                <Button
                    type="submit"
                    size="icon"
                    disabled={!value.trim() || isStreaming}
                    className="h-12 w-12 rounded-xl shrink-0 bg-gradient-to-r from-primary to-emerald-600 hover:from-primary/90 hover:to-emerald-600/90"
                >
                    {isStreaming ? (
                        <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                        <Send className="h-5 w-5" />
                    )}
                </Button>
            </div>
            
            <p className="text-xs text-center text-muted-foreground mt-2">
                Press Enter to send, Shift + Enter for new line
            </p>
        </form>
    );
}

// ====================
// Error Display
// ====================

interface ChatErrorProps {
    error: Error;
    onRetry?: () => void;
}

export function ChatError({ error, onRetry }: ChatErrorProps) {
    return (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-destructive/10 border border-destructive/20 mx-4 mb-4">
            <AlertCircle className="h-5 w-5 text-destructive shrink-0" />
            <div className="flex-1">
                <p className="text-sm font-medium text-destructive">
                    Something went wrong
                </p>
                <p className="text-xs text-muted-foreground">
                    {error.message}
                </p>
            </div>
            {onRetry && (
                <Button
                    variant="outline"
                    size="sm"
                    onClick={onRetry}
                    className="shrink-0"
                >
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Retry
                </Button>
            )}
        </div>
    );
}

// ====================
// Chat Header
// ====================

interface ChatHeaderProps {
    title?: string;
    onNewChat?: () => void;
}

export function ChatHeader({ title, onNewChat }: ChatHeaderProps) {
    return (
        <div className="flex items-center justify-between p-4 border-b bg-background/80 backdrop-blur-sm">
            <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                    <Bot className="h-5 w-5 text-white" />
                </div>
                <div>
                    <h2 className="font-semibold">
                        {title || 'ZenLearn Assistant'}
                    </h2>
                    <p className="text-xs text-muted-foreground">
                        Your AI-powered learning companion
                    </p>
                </div>
            </div>
            
            {onNewChat && (
                <Button variant="outline" size="sm" onClick={onNewChat}>
                    <Sparkles className="h-4 w-4 mr-2" />
                    New Chat
                </Button>
            )}
        </div>
    );
}
