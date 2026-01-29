import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

// Check for database URL
if (!process.env.DATABASE_URL) {
    throw new Error('DATABASE_URL environment variable is not set');
}

// Create postgres connection
const connectionString = process.env.DATABASE_URL;

// For queries - use max 1 connection (good for serverless)
const queryClient = postgres(connectionString, { max: 1 });

// Create drizzle instance
export const db = drizzle(queryClient, { schema });

// Export schema for convenience
export { schema };
