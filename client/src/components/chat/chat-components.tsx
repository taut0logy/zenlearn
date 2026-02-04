'use client';

import { FormEvent, useRef, useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { Message } from '@/lib/chat-api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
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
    BookOpen,
    Search,
    FileText,
    Lightbulb,
    MessageSquare,
    GraduationCap,
    Code,
} from 'lucide-react';
import { MarkdownRenderer } from './markdown-renderer';
import { CopyButton } from './copy-button';

// ====================
// Message Skeleton (Loading State)
// ====================

export function ChatMessageSkeleton({ isUser = false }: { isUser?: boolean }) {
    return (
        <div
            className={cn(
                'flex gap-3 p-4 rounded-lg animate-pulse',
                isUser ? 'bg-primary/5 ml-8' : 'bg-muted/30 mr-8'
            )}
        >
            <Skeleton className="h-8 w-8 rounded-full shrink-0" />
            <div className="flex-1 space-y-2">
                <Skeleton className="h-3 w-24" />
                <div className="space-y-1.5">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    {!isUser && <Skeleton className="h-4 w-5/6" />}
                </div>
            </div>
        </div>
    );
}

export function ChatLoadingSkeleton() {
    return (
        <div className="flex-1 overflow-hidden p-4 space-y-4">
            <ChatMessageSkeleton isUser={true} />
            <ChatMessageSkeleton isUser={false} />
            <ChatMessageSkeleton isUser={true} />
            <ChatMessageSkeleton isUser={false} />
        </div>
    );
}

// ====================
// Empty State
// ====================

interface ChatEmptyStateProps {
    onSuggestionClick?: (suggestion: string) => void;
}

function ChatEmptyState({ onSuggestionClick }: ChatEmptyStateProps) {
    const capabilities = [
        {
            icon: <Search className="h-5 w-5 text-blue-500" />,
            title: "Search Knowledge",
            description: "Find concepts in slides, PDFs & notes.",
            suggestion: "Search for 'recursion in slides'"
        },
        {
            icon: <BookOpen className="h-5 w-5 text-emerald-500" />,
            title: "Generate Materials",
            description: "Create notes, summaries or flashcards.",
            suggestion: "Generate notes for Week 3"
        },
        {
            icon: <Code className="h-5 w-5 text-orange-500" />,
            title: "Lab Help",
            description: "Debug code and explain syntax.",
            suggestion: "Explain my syntax error"
        },
        {
            icon: <GraduationCap className="h-5 w-5 text-purple-500" />,
            title: "Explain Concepts",
            description: "Clear explanations of theories.",
            suggestion: "Explain TCP vs UDP"
        }
    ];

    return (
        <div className="flex-1 flex flex-col items-center justify-center p-4 animate-in fade-in duration-500 overflow-y-auto">
            <div className="text-center space-y-2 max-w-lg mb-8">
                <div className="mx-auto w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/10 to-primary/30 flex items-center justify-center mb-4 shadow-md shadow-primary/5">
                    <Sparkles className="h-8 w-8 text-primary" />
                </div>
                <h2 className="text-2xl font-bold tracking-tight">
                    ZenLearn Assistant
                </h2>
                <p className="text-muted-foreground text-base">
                    Your AI companion for course materials, labs, and exam prep.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-3xl w-full">
                {capabilities.map((cap, index) => (
                    <button
                        key={index}
                        onClick={() => onSuggestionClick?.(cap.suggestion)}
                        className={cn(
                            "flex items-start gap-3 p-3 rounded-xl border border-border/50",
                            "bg-card/50 hover:bg-card hover:border-border transition-all duration-200",
                            "text-left group hover:shadow-sm"
                        )}
                    >
                        <div className="p-2 rounded-lg bg-background shadow-sm border border-border/50 group-hover:scale-105 transition-transform duration-200">
                            {cap.icon}
                        </div>
                        <div className="space-y-0.5">
                            <h3 className="font-semibold text-sm flex items-center gap-2">
                                {cap.title}
                            </h3>
                            <p className="text-xs text-muted-foreground leading-snug">
                                {cap.description}
                            </p>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
}

// ====================
// Message Bubble
// ====================

interface ChatMessageProps {
    message: Message;
    isStreaming?: boolean;
    onViewContent?: (url: string) => void;
}

export function ChatMessage({ message, isStreaming, onViewContent }: ChatMessageProps) {
    const isUser = message.role === 'user';

    return (
        <div
            className={cn(
                'group flex gap-3 p-4 rounded-lg transition-all',
                isUser
                    ? 'bg-primary/10 ml-0 md:ml-8'
                    : 'bg-muted/50 mr-0 md:mr-0 lg:mr-8'
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
                            <MarkdownRenderer
                                content={message.content}
                                isStreaming={isStreaming}
                                onViewContent={onViewContent}
                            />
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
    thinkingLogs?: string[];
    onViewContent?: (url: string) => void;
}

export function StreamingMessage({ content, thinkingLogs = [], onViewContent }: StreamingMessageProps) {
    // Show thinking indicator if no content yet
    if (!content && thinkingLogs.length === 0) {
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

    // Render thinking logs and content
    return (
        <div className="flex gap-3 p-4 rounded-lg bg-muted/50 mr-8 animate-in fade-in duration-300">
            <Avatar className="h-8 w-8 shrink-0">
                <AvatarFallback className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
                    <Bot className="h-4 w-4" />
                </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0 space-y-2">
                <p className="text-xs font-medium text-muted-foreground">
                    ZenLearn Assistant
                </p>

                {/* Thinking Process */}
                {thinkingLogs.length > 0 && (
                    <div className="text-xs bg-background/50 rounded-md border border-border/50 overflow-hidden">
                        <details className="group" open>
                            <summary className="flex items-center gap-2 p-2 bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors select-none">
                                <Loader2 className="h-3 w-3 animate-spin text-primary" />
                                <span className="font-medium text-muted-foreground">Thinking Process</span>
                            </summary>
                            <div className="p-2 space-y-1 max-h-[200px] overflow-y-auto font-mono text-[10px] text-muted-foreground/80">
                                {thinkingLogs.map((log, i) => (
                                    <div key={i} className="border-l-2 border-primary/20 pl-2">
                                        {log}
                                    </div>
                                ))}
                            </div>
                        </details>
                    </div>
                )}

                {/* Content */}
                {content && (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                        <MarkdownRenderer
                            content={content}
                            isStreaming={true}
                            onViewContent={onViewContent}
                        />
                        <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse rounded-sm" />
                    </div>
                )}
            </div>
        </div>
    );
}

// ====================
// Message List
// ====================

interface ChatMessageListProps {
    messages: Message[];
    isStreaming: boolean;
    streamingContent: string;
    thinkingLogs?: string[];
    isLoading?: boolean;
    onViewContent?: (url: string) => void;
    onSuggestionClick?: (suggestion: string) => void;
}

export function ChatMessageList({
    messages,
    isStreaming,
    streamingContent,
    thinkingLogs,
    isLoading,
    onViewContent,
    onSuggestionClick,
}: ChatMessageListProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, streamingContent]);

    // Show loading skeleton when loading chat
    if (isLoading) {
        return <ChatLoadingSkeleton />;
    }

    if (messages.length === 0 && !isStreaming) {
        return (
            <ChatEmptyState onSuggestionClick={onSuggestionClick} />
        );
    }

    return (
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
                <ChatMessage key={message.id} message={message} onViewContent={onViewContent} />
            ))}

            {isStreaming && (
                <StreamingMessage content={streamingContent} onViewContent={onViewContent} />
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
        <div className="p-4 bg-background/80 backdrop-blur-sm border-t">
            <form
                onSubmit={handleSubmit}
                className="max-w-3xl mx-auto relative"
            >
                <div className="relative flex items-end gap-2 bg-muted/40 p-2 rounded-2xl border border-transparent focus-within:border-primary/20 focus-within:bg-muted/30 focus-within:shadow-sm transition-all duration-200">
                    <Textarea
                        ref={textareaRef}
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={placeholder}
                        className="min-h-[44px] w-full resize-none border-0 shadow-none bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 px-3 py-3 max-h-[200px]"
                        rows={1}
                    />
                    <Button
                        type="submit"
                        size="icon"
                        className={cn(
                            "h-9 w-9 shrink-0 rounded-xl mb-1 transition-all",
                            value.trim()
                                ? "bg-primary text-primary-foreground shadow-sm hover:bg-primary/90"
                                : "bg-muted-foreground/20 text-muted-foreground hover:bg-muted-foreground/30"
                        )}
                        disabled={!value.trim() || isStreaming}
                    >
                        {isStreaming ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Send className="h-4 w-4" />
                        )}
                    </Button>
                </div>

                <p className="text-[10px] text-center text-muted-foreground/60 mt-2 select-none">
                    ZenLearn may generate inaccurate info, including about people, so double-check its responses.
                </p>
            </form>
        </div>
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
    mobileSidebar?: React.ReactNode;
}

export function ChatHeader({ title, onNewChat, mobileSidebar }: ChatHeaderProps) {
    return (
        <div className="flex items-center justify-between p-3 border-b bg-background/80 backdrop-blur-sm shrink-0 h-14">
            <div className="flex items-center gap-3 overflow-hidden">
                {mobileSidebar}

                <div className="flex items-center gap-3 overflow-hidden">
                    <div className="hidden md:flex h-9 w-9 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 items-center justify-center shrink-0">
                        <Bot className="h-5 w-5 text-white" />
                    </div>
                    <div className="overflow-hidden">
                        <h2 className="font-semibold truncate text-sm md:text-base">
                            {title || 'ZenLearn'}
                        </h2>
                        <p className="hidden md:block text-xs text-muted-foreground truncate">
                            Your AI-powered learning companion
                        </p>
                    </div>
                </div>
            </div>

            {onNewChat && (
                <Button variant="outline" size="sm" onClick={onNewChat} className="shrink-0 ml-2">
                    <Sparkles className="h-4 w-4 md:mr-2" />
                    <span className="hidden md:inline">New Chat</span>
                </Button>
            )}
        </div>
    );
}
