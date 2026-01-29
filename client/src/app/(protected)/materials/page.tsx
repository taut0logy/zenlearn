"use client";

import * as React from "react";
import { toast } from "sonner";
import { CMSLayout } from "@/components/cms/CMSLayout";
import { DriveExplorer, FileItem } from "@/components/cms/DriveExplorer";
import { getCourses, getMaterials, getRecentMaterials } from "@/lib/api/cms";

export default function StudentCMSPage() {
    // Navigation State
    const [view, setView] = React.useState<"all" | "recent" | "starred">("all");
    const [path, setPath] = React.useState<{ name: string; id?: string; type?: string }[]>([
        { name: "My Courses" }
    ]);

    // Data State
    const [items, setItems] = React.useState<FileItem[]>([]);
    const [loading, setLoading] = React.useState(true);

    const currentLevel = view === "all" ? path.length - 1 : -1;
    const currentCourseId = view === "all" && path.length > 1 ? path[1].id : null;
    const currentType = view === "all" && path.length > 2 ? path[2].type : null; // theory or lab

    // --- Data Loading ---
    React.useEffect(() => {
        loadData();
    }, [path, view]);

    const loadData = async () => {
        setLoading(true);
        setItems([]);
        try {
            if (view === "recent") {
                const materials = await getRecentMaterials();
                setItems(materials.map(m => ({
                    id: m.id,
                    name: m.title,
                    type: "file",
                    fileType: m.file_type,
                    url: m.url,
                    description: m.description,
                    updatedAt: m.created_at,
                    courseId: m.course_id
                })));
                return;
            }

            if (currentLevel === 0) {
                // Root: Courses
                const courses = await getCourses();
                setItems(courses.map(c => ({
                    id: c.id,
                    name: `${c.course_no} - ${c.name}`,
                    type: "folder",
                    description: c.description
                })));
            } else if (currentLevel === 1) {
                // Course Level: Theory / Lab folders
                setItems([
                    { id: "theory", name: "Theory", type: "folder", description: "Course materials and slides" },
                    { id: "lab", name: "Lab", type: "folder", description: "Lab assignments and code" }
                ]);
            } else if (currentLevel === 2 && currentCourseId && currentType) {
                // Material Level
                const materials = await getMaterials(currentCourseId, currentType);
                setItems(materials.map(m => ({
                    id: m.id,
                    name: m.title,
                    type: "file",
                    fileType: m.file_type,
                    url: m.url,
                    description: m.description,
                    updatedAt: m.created_at,
                    courseId: m.course_id
                })));
            }
        } catch (error) {
            console.error(error);
            toast.error("Failed to load content");
        } finally {
            setLoading(false);
        }
    };

    // --- Navigation ---
    const handleSidebarNavigate = (newView: string) => {
        if (newView === "all") {
            setView("all");
            setPath([{ name: "My Courses" }]);
        } else if (newView === "recent") {
            setView("recent");
            setPath([{ name: "Recent Files" }]);
        } else {
            toast.info("Coming soon");
        }
    };

    const handleNavigate = (item: FileItem) => {
        if (item.type === "folder") {
            if (currentLevel === 0) {
                setPath([...path, { name: item.name, id: item.id }]);
            } else if (currentLevel === 1) {
                setPath([...path, { name: item.name, id: item.id, type: item.id.toLowerCase() }]);
            }
        } else if (item.url) {
            const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
            window.open(`${backendUrl}${item.url}`, "_blank");
        }
    };

    const handleBreadcrumbClick = (index: number) => {
        if (view !== "all") return;
        setPath(path.slice(0, index + 1));
    };

    return (
        <CMSLayout onNavigate={handleSidebarNavigate}>
            <div className="flex flex-col h-full">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-2xl font-bold tracking-tight">
                        {view === "recent" ? "Recent Files" : (path.length > 1 ? path[path.length - 1].name : "My Courses")}
                    </h1>
                </div>

                <DriveExplorer
                    items={items}
                    loading={loading}
                    onNavigate={handleNavigate}
                    currentPath={path}
                    onBreadcrumbClick={handleBreadcrumbClick}
                />
            </div>
        </CMSLayout>
    );
}
