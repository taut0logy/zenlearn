'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/use-auth';

// Types
interface Author {
    id: string;
    name: string;
    avatar_url?: string;
}

interface Post {
    id: string;
    author: Author;
    title: string;
    content: string;
    category: 'theory' | 'lab' | 'general';
    course_topic?: string;
    is_resolved: boolean;
    view_count: number;
    comment_count: number;
    created_at: string;
    updated_at: string;
}

interface PostListResponse {
    posts: Post[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
}

const CATEGORY_COLORS = {
    theory: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    lab: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    general: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
};

const CATEGORY_LABELS = {
    theory: '📚 Theory',
    lab: '💻 Lab',
    general: '💬 General'
};

export default function CommunityPage() {
    const { user } = useAuth();
    const [posts, setPosts] = useState<Post[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    const [showResolved, setShowResolved] = useState<boolean | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [showCreateModal, setShowCreateModal] = useState(false);

    useEffect(() => {
        fetchPosts();
    }, [selectedCategory, showResolved, searchQuery]);

    const fetchPosts = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (selectedCategory !== 'all') {
                params.append('category', selectedCategory);
            }
            if (showResolved !== null) {
                params.append('is_resolved', String(showResolved));
            }
            if (searchQuery) {
                params.append('search', searchQuery);
            }

            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/community/posts?${params}`
            );
            
            if (!response.ok) {
                throw new Error('Failed to fetch posts');
            }
            
            const data: PostListResponse = await response.json();
            setPosts(data.posts);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load posts');
        } finally {
            setLoading(false);
        }
    };

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
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-800">
            {/* Header */}
            <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
                <div className="max-w-6xl mx-auto px-4 py-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                                <span className="text-4xl">🎓</span>
                                Community Discussion
                            </h1>
                            <p className="text-gray-600 dark:text-gray-400 mt-1">
                                Ask questions, share knowledge, help each other learn
                            </p>
                        </div>
                        <button
                            onClick={() => setShowCreateModal(true)}
                            className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-6 py-3 rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
                        >
                            <span>✏️</span>
                            New Post
                        </button>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="max-w-6xl mx-auto px-4 py-4">
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4 flex flex-wrap gap-4 items-center">
                    {/* Category Filter */}
                    <div className="flex gap-2">
                        {['all', 'theory', 'lab', 'general'].map((cat) => (
                            <button
                                key={cat}
                                onClick={() => setSelectedCategory(cat)}
                                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                                    selectedCategory === cat
                                        ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-200'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                                }`}
                            >
                                {cat === 'all' ? '📋 All' : CATEGORY_LABELS[cat as keyof typeof CATEGORY_LABELS]}
                            </button>
                        ))}
                    </div>

                    {/* Resolved Filter */}
                    <div className="flex gap-2 border-l border-gray-200 dark:border-gray-600 pl-4">
                        <button
                            onClick={() => setShowResolved(null)}
                            className={`px-3 py-2 rounded-lg text-sm ${
                                showResolved === null ? 'bg-indigo-100 text-indigo-700' : 'text-gray-500 hover:bg-gray-100'
                            }`}
                        >
                            All Status
                        </button>
                        <button
                            onClick={() => setShowResolved(false)}
                            className={`px-3 py-2 rounded-lg text-sm ${
                                showResolved === false ? 'bg-yellow-100 text-yellow-700' : 'text-gray-500 hover:bg-gray-100'
                            }`}
                        >
                            ❓ Unanswered
                        </button>
                        <button
                            onClick={() => setShowResolved(true)}
                            className={`px-3 py-2 rounded-lg text-sm ${
                                showResolved === true ? 'bg-green-100 text-green-700' : 'text-gray-500 hover:bg-gray-100'
                            }`}
                        >
                            ✅ Resolved
                        </button>
                    </div>

                    {/* Search */}
                    <div className="flex-1 min-w-[200px]">
                        <input
                            type="text"
                            placeholder="🔍 Search posts..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                    </div>
                </div>
            </div>

            {/* Posts List */}
            <div className="max-w-6xl mx-auto px-4 pb-8">
                {loading ? (
                    <div className="text-center py-12">
                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-500 border-t-transparent"></div>
                        <p className="text-gray-500 mt-4">Loading discussions...</p>
                    </div>
                ) : error ? (
                    <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-4 rounded-xl text-center">
                        {error}
                    </div>
                ) : posts.length === 0 ? (
                    <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl">
                        <div className="text-6xl mb-4">💭</div>
                        <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300">No posts yet</h3>
                        <p className="text-gray-500 mt-2">Be the first to start a discussion!</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {posts.map((post) => (
                            <Link key={post.id} href={`/community/${post.id}`}>
                                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-md transition-shadow p-5 cursor-pointer border border-gray-100 dark:border-gray-700">
                                    <div className="flex items-start gap-4">
                                        {/* Author Avatar */}
                                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                                            {post.author.avatar_url ? (
                                                <img src={post.author.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
                                            ) : (
                                                post.author.name.charAt(0).toUpperCase()
                                            )}
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                                                    {post.title}
                                                </h3>
                                                {post.is_resolved && (
                                                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                                                        ✅ Resolved
                                                    </span>
                                                )}
                                                <span className={`px-2 py-0.5 text-xs rounded-full ${CATEGORY_COLORS[post.category]}`}>
                                                    {CATEGORY_LABELS[post.category]}
                                                </span>
                                            </div>
                                            
                                            <p className="text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                                                {post.content}
                                            </p>

                                            <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                                                <span className="flex items-center gap-1">
                                                    <span>👤</span>
                                                    {post.author.name}
                                                </span>
                                                <span className="flex items-center gap-1">
                                                    <span>💬</span>
                                                    {post.comment_count} comments
                                                </span>
                                                <span className="flex items-center gap-1">
                                                    <span>👁️</span>
                                                    {post.view_count} views
                                                </span>
                                                <span>{formatDate(post.created_at)}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>

            {/* Create Post Modal */}
            {showCreateModal && user && (
                <CreatePostModal
                    userId={user.id}
                    onClose={() => setShowCreateModal(false)}
                    onCreated={() => {
                        setShowCreateModal(false);
                        fetchPosts();
                    }}
                />
            )}
        </div>
    );
}

// Create Post Modal Component
function CreatePostModal({ userId, onClose, onCreated }: { userId: string; onClose: () => void; onCreated: () => void }) {
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [category, setCategory] = useState<'theory' | 'lab' | 'general'>('general');
    const [courseTopic, setCourseTopic] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);

        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/community/posts?user_id=${userId}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title,
                        content,
                        category,
                        course_topic: courseTopic || null
                    })
                }
            );

            if (!response.ok) {
                throw new Error('Failed to create post');
            }

            onCreated();
        } catch (err) {
            alert('Failed to create post');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-auto">
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <span>✏️</span>
                        Create New Post
                    </h2>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Title
                        </label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="What's your question or topic?"
                            className="w-full px-4 py-3 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Category
                        </label>
                        <div className="flex gap-2">
                            {(['theory', 'lab', 'general'] as const).map((cat) => (
                                <button
                                    key={cat}
                                    type="button"
                                    onClick={() => setCategory(cat)}
                                    className={`px-4 py-2 rounded-lg font-medium transition-all ${
                                        category === cat
                                            ? CATEGORY_COLORS[cat]
                                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                                    }`}
                                >
                                    {CATEGORY_LABELS[cat]}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Course Topic (optional)
                        </label>
                        <input
                            type="text"
                            value={courseTopic}
                            onChange={(e) => setCourseTopic(e.target.value)}
                            placeholder="e.g., Data Structures, Machine Learning"
                            className="w-full px-4 py-3 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Content
                        </label>
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            placeholder="Describe your question or share your thoughts... (Markdown supported)"
                            rows={8}
                            className="w-full px-4 py-3 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                            required
                        />
                    </div>

                    <div className="flex gap-3 justify-end pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-6 py-2 rounded-lg text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={submitting}
                            className="px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg font-semibold hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50"
                        >
                            {submitting ? 'Creating...' : 'Create Post'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
