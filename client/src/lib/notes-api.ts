/**
 * API Client for Notes Agent
 * 
 * Handles all communication with the notes backend API
 * for handwritten note digitization.
 */

import { createClient } from '@/lib/supabase/client';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

// Types for notes API
export interface ExtractedBlock {
    type: string;
    content: string;
    confidence: number;
}

export interface DigitizeRequest {
    image_base64: string;
    title?: string;
}

export interface DigitizeResponse {
    id: string;
    title: string;
    extracted_text: string;
    latex_content: string;
    blocks: ExtractedBlock[];
    success: boolean;
    error?: string;
}

export interface Note {
    id: string;
    user_id: string;
    title: string;
    original_image_url?: string;
    extracted_text: string;
    latex_content: string;
    created_at: string;
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
    
    if (!token) {
        throw new Error('Please log in to use this feature');
    }
    
    const response = await fetch(`${API_BASE_URL}${API_PREFIX}${endpoint}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
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
 * Digitize a handwritten note image
 */
export async function digitizeNote(imageBase64: string, title?: string): Promise<DigitizeResponse> {
    return apiRequest<DigitizeResponse>('/notes/digitize', {
        method: 'POST',
        body: JSON.stringify({
            image_base64: imageBase64,
            title,
        }),
    });
}

/**
 * Check notes service health
 */
export async function checkNotesHealth(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${API_BASE_URL}${API_PREFIX}/notes/health`);
    if (!response.ok) {
        throw new Error('Notes service is unavailable');
    }
    return response.json();
}
