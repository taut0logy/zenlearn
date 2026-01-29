export interface Course {
    id: string;
    name: string;
    course_no: string;
    description?: string;
    created_at: string;
    updated_at: string;
}

export interface Tag {
    id: string;
    name: string;
}

export interface Material {
    id: string;
    course_id: string;
    title: string;
    description?: string;
    type: "theory" | "lab";
    file_type: "pdf" | "pptx" | "code";
    url: string;
    created_at: string;
    updated_at: string;
    tags: Tag[];
    metadata?: any;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function getCourses(): Promise<Course[]> {
    const res = await fetch(`${API_URL}/cms/courses`);
    if (!res.ok) throw new Error("Failed to fetch courses");
    return res.json();
}

export async function createCourse(data: { name: string; course_no: string; description?: string }): Promise<Course> {
    const res = await fetch(`${API_URL}/cms/courses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to create course");
    }
    return res.json();
}

export async function getMaterials(courseId: string, type?: string): Promise<Material[]> {
    const url = new URL(`${API_URL}/cms/courses/${courseId}/materials`);
    if (type) url.searchParams.append("type", type);
    
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error("Failed to fetch materials");
    return res.json();
}

export async function getRecentMaterials(): Promise<Material[]> {
    const res = await fetch(`${API_URL}/cms/materials/recent`);
    if (!res.ok) throw new Error("Failed to fetch recent materials");
    return res.json();
}

export async function uploadMaterial(courseId: string, formData: FormData): Promise<Material> {
    const res = await fetch(`${API_URL}/cms/courses/${courseId}/materials`, {
        method: "POST",
        body: formData,
    });
    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to upload material");
    }
    return res.json();
}

export async function updateMaterial(courseId: string, materialId: string, data: any): Promise<Material> {
    const res = await fetch(`${API_URL}/cms/courses/${courseId}/materials/${materialId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to update material");
    }
    return res.json();
}

export async function deleteMaterial(courseId: string, materialId: string): Promise<void> {
    const res = await fetch(`${API_URL}/cms/courses/${courseId}/materials/${materialId}`, {
        method: "DELETE",
    });
    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to delete material");
    }
}

export async function deleteCourseMaterials(courseId: string, type: string): Promise<void> {
    const res = await fetch(`${API_URL}/cms/courses/${courseId}/materials?type=${type}`, {
        method: "DELETE",
    });
    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to delete materials");
    }
}

export async function searchTags(query: string): Promise<Tag[]> {
    const res = await fetch(`${API_URL}/cms/tags?query=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error("Failed to fetch tags");
    return res.json();
}

// --- Semantic Search ---

export interface SearchSection {
    content_preview: string;
    location: string;
    location_type: string;
    score: number;
}

export interface SearchResult {
    filename: string;
    filepath: string;
    file_type: string;
    relevance_score: number;
    matching_sections: SearchSection[];
    summary?: string;
}

export interface SearchResponse {
    query: string;
    count: number;
    results: SearchResult[];
}

export interface SearchOptions {
    type?: "pdf" | "pptx" | "code";
    limit?: number;
}

export async function searchMaterials(query: string, options?: SearchOptions): Promise<SearchResponse> {
    const url = new URL(`${API_URL}/cms/search`);
    url.searchParams.set("q", query);
    if (options?.type) url.searchParams.set("type", options.type);
    if (options?.limit) url.searchParams.set("limit", String(options.limit));
    
    const res = await fetch(url.toString());
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || "Search failed");
    }
    return res.json();
}
