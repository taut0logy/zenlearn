import { pgTable, text, timestamp, uuid, pgEnum, boolean, jsonb, integer } from 'drizzle-orm/pg-core';

// Define role enum
export const roleEnum = pgEnum('role', ['user', 'admin']);

// Define message role enum
export const messageRoleEnum = pgEnum('message_role', ['user', 'assistant', 'system']);

// Profiles table
export const profiles = pgTable('profiles', {
    id: uuid('id').primaryKey(),
    name: text('name').notNull(),
    email: text('email').notNull().unique(),
    role: roleEnum('role').notNull().default('user'),
    avatarUrl: text('avatar_url'),
    hasPassword: boolean('has_password').notNull().default(false),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

// Chats table
export const chats = pgTable('chats', {
    id: uuid('id').primaryKey().defaultRandom(),
    userId: uuid('user_id').notNull().references(() => profiles.id, { onDelete: 'cascade' }),
    title: text('title').notNull(),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

// Messages table
export const messages = pgTable('messages', {
    id: uuid('id').primaryKey().defaultRandom(),
    chatId: uuid('chat_id').notNull().references(() => chats.id, { onDelete: 'cascade' }),
    role: text('role').notNull(), // 'user' | 'assistant' | 'system'
    content: text('content').notNull(),
    metadata: jsonb('metadata'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
});

// Notes table - for digitized handwritten notes
export const notes = pgTable('notes', {
    id: uuid('id').primaryKey().defaultRandom(),
    userId: uuid('user_id').notNull().references(() => profiles.id, { onDelete: 'cascade' }),
    title: text('title').notNull(),
    originalImageUrl: text('original_image_url'),
    extractedText: text('extracted_text').notNull(),
    latexContent: text('latex_content').notNull(),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

// ============ Community Tables ============

// Community post category enum
export const postCategoryEnum = pgEnum('post_category', ['theory', 'lab', 'general']);

// Community posts table
export const communityPosts = pgTable('community_posts', {
    id: uuid('id').primaryKey().defaultRandom(),
    authorId: uuid('author_id').notNull().references(() => profiles.id, { onDelete: 'cascade' }),
    title: text('title').notNull(),
    content: text('content').notNull(),
    category: postCategoryEnum('category').notNull().default('general'),
    courseTopic: text('course_topic'),
    isResolved: boolean('is_resolved').notNull().default(false),
    viewCount: integer('view_count').notNull().default(0),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

// Community comments table
export const communityComments = pgTable('community_comments', {
    id: uuid('id').primaryKey().defaultRandom(),
    postId: uuid('post_id').notNull().references(() => communityPosts.id, { onDelete: 'cascade' }),
    authorId: uuid('author_id').references(() => profiles.id, { onDelete: 'set null' }), // NULL for bot
    parentId: uuid('parent_id'), // For nested replies (self-reference)
    content: text('content').notNull(),
    isBotReply: boolean('is_bot_reply').notNull().default(false),
    mentionedUserId: uuid('mentioned_user_id').references(() => profiles.id, { onDelete: 'set null' }),
    botMetadata: jsonb('bot_metadata'), // Sources, confidence, etc.
    createdAt: timestamp('created_at').defaultNow().notNull(),
});

// User presence table for online/offline tracking
export const userPresence = pgTable('user_presence', {
    userId: uuid('user_id').primaryKey().references(() => profiles.id, { onDelete: 'cascade' }),
    lastSeen: timestamp('last_seen').defaultNow().notNull(),
    isOnline: boolean('is_online').notNull().default(false),
});

// Export types
export type Profile = typeof profiles.$inferSelect;
export type NewProfile = typeof profiles.$inferInsert;

export type Chat = typeof chats.$inferSelect;
export type NewChat = typeof chats.$inferInsert;

export type Message = typeof messages.$inferSelect;
export type NewMessage = typeof messages.$inferInsert;

export type Note = typeof notes.$inferSelect;
export type NewNote = typeof notes.$inferInsert;

export type CommunityPost = typeof communityPosts.$inferSelect;
export type NewCommunityPost = typeof communityPosts.$inferInsert;

export type CommunityComment = typeof communityComments.$inferSelect;
export type NewCommunityComment = typeof communityComments.$inferInsert;

export type UserPresence = typeof userPresence.$inferSelect;
export type NewUserPresence = typeof userPresence.$inferInsert;

