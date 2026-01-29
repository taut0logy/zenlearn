import { pgTable, text, timestamp, uuid, pgEnum, boolean, primaryKey, jsonb, integer } from 'drizzle-orm/pg-core';

// Define role enum
export const roleEnum = pgEnum('role', ['user', 'admin']);
export const courseTypeEnum = pgEnum('course_type', ['theory', 'lab']);
export const fileTypeEnum = pgEnum('file_type', ['pdf', 'pptx', 'code']);

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

// Courses table
export const courses = pgTable('courses', {
    id: uuid('id').defaultRandom().primaryKey(),
    name: text('name').notNull(),
    courseNo: text('course_no').notNull().unique(),
    description: text('description'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

// Tags table
export const tags = pgTable('tags', {
    id: uuid('id').defaultRandom().primaryKey(),
    name: text('name').notNull().unique(),
});

// Course Materials table
export const courseMaterials = pgTable('course_materials', {
    id: uuid('id').defaultRandom().primaryKey(),
    courseId: uuid('course_id').references(() => courses.id).notNull(),
    title: text('title').notNull(),
    description: text('description'),
    type: courseTypeEnum('type').notNull(),
    fileType: fileTypeEnum('file_type').notNull(),
    url: text('url').notNull(), // Path to storage
    week: integer('week'), // Week number
    metadata: jsonb('metadata'), // JSONified metadata
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

// Junction table for Material Tags
export const materialTags = pgTable('material_tags', {
    materialId: uuid('material_id').references(() => courseMaterials.id).notNull(),
    tagId: uuid('tag_id').references(() => tags.id).notNull(),
}, (t) => [
    primaryKey({ columns: [t.materialId, t.tagId] })
]);

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

// Export types
export type Profile = typeof profiles.$inferSelect;
export type NewProfile = typeof profiles.$inferInsert;
export type Course = typeof courses.$inferSelect;
export type NewCourse = typeof courses.$inferInsert;
export type Tag = typeof tags.$inferSelect;
export type NewTag = typeof tags.$inferInsert;
export type CourseMaterial = typeof courseMaterials.$inferSelect;
export type NewCourseMaterial = typeof courseMaterials.$inferInsert;

export type Chat = typeof chats.$inferSelect;
export type NewChat = typeof chats.$inferInsert;

export type Message = typeof messages.$inferSelect;
export type NewMessage = typeof messages.$inferInsert;
