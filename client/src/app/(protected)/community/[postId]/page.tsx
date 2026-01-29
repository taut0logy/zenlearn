'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/use-auth';
import { MarkdownRenderer } from '@/components/chat/markdown-renderer';

// Types
interface Author {
    id: string;
    name: string;
    avatar_url?: string;
}

interface Comment {
    id: string;
    post_id: string;
    author: Author | null;
    parent_id?: string;
    content: string;
    is_bot_reply: boolean;
    mentioned_user_id?: string;
    bot_metadata?: {
        sources?: Array<{ title: string; url?: string }>;
        generated_at?: string;
        course_context?: string;
    };
    created_at: string;
    replies: Comment[];
}

interface PostDetail {
    id: string;
    author: Author;
    title: string;
    content: string;
    category: 'theory' | 'lab' | 'general';
    course_topic?: string;
    is_resolved: boolean;
    view_count: number;
    created_at: string;
    updated_at: string;
    comments: Comment[];
}

const CATEGORY_COLORS = {
    theory: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    lab: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    general: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
};

export default function PostDetailPage() {
    const params = useParams();
    const router = useRouter();
    const { user } = useAuth();
    const postId = params.postId as string;
    
    const [post, setPost] = useState<PostDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [replyContent, setReplyContent] = useState('');
    const [replyingTo, setReplyingTo] = useState<{ id: string; authorName: string } | null>(null);
    const [submittingReply, setSubmittingReply] = useState(false);
    
    const replyInputRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (postId) {
            fetchPost();
        }
    }, [postId]);

    useEffect(() => {
        // Focus reply input when replying to a comment
        if (replyingTo && replyInputRef.current) {
            replyInputRef.current.focus();
        }
    }, [replyingTo]);

    const fetchPost = async () => {
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/community/posts/${postId}`
            );
            
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Post not found');
                }
                throw new Error('Failed to fetch post');
            }
            
            const data: PostDetail = await response.json();
            setPost(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load post');
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const handleSubmitReply = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!replyContent.trim() || !user) return;

        setSubmittingReply(true);
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/community/posts/${postId}/comments?user_id=${user.id}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        content: replyContent,
                        parent_id: replyingTo?.id || null,
                        mentioned_user_id: replyingTo ? null : null // Can be enhanced to detect @mentions
                    })
                }
            );

            if (!response.ok) {
                throw new Error('Failed to post comment');
            }

            setReplyContent('');
            setReplyingTo(null);
            await fetchPost(); // Refresh to see new comment and potential bot reply
        } catch (err) {
            alert('Failed to post comment');
        } finally {
            setSubmittingReply(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
                <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-indigo-500 border-t-transparent"></div>
                    <p className="text-gray-500 mt-4">Loading discussion...</p>
                </div>
            </div>
        );
    }

    if (error || !post) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
                <div className="text-center">
                    <div className="text-6xl mb-4">😕</div>
                    <h2 className="text-2xl font-bold text-gray-700 dark:text-gray-300">{error || 'Post not found'}</h2>
                    <Link href="/community" className="text-indigo-500 hover:underline mt-4 inline-block">
                        ← Back to Community
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-800">
            {/* Header */}
            <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
                <div className="max-w-4xl mx-auto px-4 py-4">
                    <Link href="/community" className="text-indigo-500 hover:text-indigo-600 flex items-center gap-1 text-sm">
                        ← Back to Community
                    </Link>
                </div>
            </div>

            <div className="max-w-4xl mx-auto px-4 py-6">
                {/* Post Content */}
                <article className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden">
                    <div className="p-6">
                        {/* Post Header */}
                        <div className="flex items-start gap-4">
                            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-bold text-xl flex-shrink-0">
                                {post.author.avatar_url ? (
                                    <img src={post.author.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
                                ) : (
                                    post.author.name.charAt(0).toUpperCase()
                                )}
                            </div>
                            <div className="flex-1">
                                <div className="flex items-center gap-2 flex-wrap">
                                    <span className={`px-2 py-0.5 text-xs rounded-full ${CATEGORY_COLORS[post.category]}`}>
                                        {post.category}
                                    </span>
                                    {post.is_resolved && (
                                        <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                                            ✅ Resolved
                                        </span>
                                    )}
                                    {post.course_topic && (
                                        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                                            📚 {post.course_topic}
                                        </span>
                                    )}
                                </div>
                                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                                    {post.title}
                                </h1>
                                <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
                                    <span className="font-medium text-gray-700 dark:text-gray-300">{post.author.name}</span>
                                    <span>•</span>
                                    <span>{formatDate(post.created_at)}</span>
                                    <span>•</span>
                                    <span>👁️ {post.view_count} views</span>
                                </div>
                            </div>
                        </div>

                        {/* Post Body */}
                        <div className="mt-6 prose prose-slate dark:prose-invert max-w-none">
                            <p className="whitespace-pre-wrap">{post.content}</p>
                        </div>
                    </div>
                </article>

                {/* Comments Section */}
                <section className="mt-8">
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <span>💬</span>
                        {post.comments.length} Comments
                    </h2>

                    {/* Reply Form */}
                    <form onSubmit={handleSubmitReply} className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm mb-6">
                        {replyingTo && (
                            <div className="mb-2 flex items-center gap-2 text-sm text-gray-500">
                                <span>Replying to <span className="font-medium">{replyingTo.authorName}</span></span>
                                <button
                                    type="button"
                                    onClick={() => setReplyingTo(null)}
                                    className="text-red-500 hover:text-red-600"
                                >
                                    ✕ Cancel
                                </button>
                            </div>
                        )}
                        <textarea
                            ref={replyInputRef}
                            value={replyContent}
                            onChange={(e) => setReplyContent(e.target.value)}
                            placeholder="Write a comment... (Markdown supported)"
                            rows={3}
                            className="w-full px-4 py-3 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                        />
                        <div className="flex justify-end mt-2">
                            <button
                                type="submit"
                                disabled={submittingReply || !replyContent.trim()}
                                className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {submittingReply ? 'Posting...' : 'Post Comment'}
                            </button>
                        </div>
                    </form>

                    {/* Comments List */}
                    <div className="space-y-4">
                        {post.comments.map((comment) => (
                            <CommentCard
                                key={comment.id}
                                comment={comment}
                                onReply={(id, authorName) => setReplyingTo({ id, authorName })}
                            />
                        ))}
                    </div>
                </section>
            </div>
        </div>
    );
}

// Comment Card Component
function CommentCard({ 
    comment, 
    onReply,
    depth = 0 
}: { 
    comment: Comment; 
    onReply: (id: string, authorName: string) => void;
    depth?: number;
}) {
    const maxDepth = 3;
    const isNested = depth > 0;

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    return (
        <div className={`${isNested ? 'ml-8 border-l-2 border-gray-200 dark:border-gray-600 pl-4' : ''}`}>
            <div className={`rounded-xl p-4 ${
                comment.is_bot_reply 
                    ? 'bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 border border-purple-200 dark:border-purple-700' 
                    : 'bg-white dark:bg-gray-800 shadow-sm'
            }`}>
                <div className="flex items-start gap-3">
                    {/* Avatar */}
                    {comment.is_bot_reply ? (
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-xl flex-shrink-0">
                            🤖
                        </div>
                    ) : (
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-400 to-gray-500 flex items-center justify-center text-white font-bold flex-shrink-0">
                            {comment.author?.avatar_url ? (
                                <img src={comment.author.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
                            ) : (
                                comment.author?.name.charAt(0).toUpperCase() || '?'
                            )}
                        </div>
                    )}

                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900 dark:text-white">
                                {comment.is_bot_reply ? 'ZenLearn Bot' : (comment.author?.name || 'Unknown')}
                            </span>
                            {comment.is_bot_reply && (
                                <span className="px-2 py-0.5 bg-purple-100 text-purple-700 dark:bg-purple-800 dark:text-purple-200 text-xs rounded-full">
                                    🤖 AI Auto-Reply
                                </span>
                            )}
                            <span className="text-sm text-gray-500">
                                {formatDate(comment.created_at)}
                            </span>
                        </div>

                        {comment.is_bot_reply ? (
                            <div className="mt-2">
                                <MarkdownRenderer content={comment.content} />
                            </div>
                        ) : (
                            <div className="mt-2 text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                                {comment.content}
                            </div>
                        )}

                        {/* Bot metadata */}
                        {comment.is_bot_reply && comment.bot_metadata && (
                            <div className="mt-3 text-xs text-gray-500 dark:text-gray-400 bg-white/50 dark:bg-gray-800/50 rounded-lg p-2">
                                <p className="italic">
                                    💡 This is an AI-generated response. The mentioned user was offline when this reply was created.
                                </p>
                            </div>
                        )}

                        {/* Reply Button */}
                        {!comment.is_bot_reply && depth < maxDepth && (
                            <button
                                onClick={() => onReply(comment.id, comment.author?.name || 'Unknown')}
                                className="mt-2 text-sm text-indigo-500 hover:text-indigo-600"
                            >
                                ↩️ Reply
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Nested Replies */}
            {comment.replies && comment.replies.length > 0 && (
                <div className="mt-3 space-y-3">
                    {comment.replies.map((reply) => (
                        <CommentCard
                            key={reply.id}
                            comment={reply}
                            onReply={onReply}
                            depth={depth + 1}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
