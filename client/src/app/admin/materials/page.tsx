"use client";

import * as React from "react";
import { Plus, Upload } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

import { CMSLayout } from "@/components/cms/CMSLayout";
import { DriveExplorer, FileItem } from "@/components/cms/DriveExplorer";
import { TagInput } from "@/components/cms/TagInput";
import { ConfirmDialog } from "@/components/cms/ConfirmDialog";
import { getCourses, createCourse, getMaterials, uploadMaterial, deleteMaterial, updateMaterial, getRecentMaterials, deleteCourseMaterials, searchTags } from "@/lib/api/cms";

export default function AdminCMSPage() {
    // Navigation State
    const [view, setView] = React.useState<"all" | "recent" | "starred">("all");
    const [path, setPath] = React.useState<{ name: string; id?: string; type?: string }[]>([
        { name: "All Courses" }
    ]);

    // Data State
    const [items, setItems] = React.useState<FileItem[]>([]);
    const [loading, setLoading] = React.useState(true);

    // Modals & Dialogs State
    const [isCreateCourseOpen, setIsCreateCourseOpen] = React.useState(false);
    const [isUploadOpen, setIsUploadOpen] = React.useState(false);
    const [isRenameOpen, setIsRenameOpen] = React.useState(false);
    const [isDeleteOpen, setIsDeleteOpen] = React.useState(false);

    // Action State
    const [itemToRename, setItemToRename] = React.useState<FileItem | null>(null);
    const [renameValue, setRenameValue] = React.useState("");
    const [itemsToDelete, setItemsToDelete] = React.useState<FileItem[]>([]);
    const [isProcessing, setIsProcessing] = React.useState(false);

    // Form Data
    const [newCourse, setNewCourse] = React.useState({ name: "", course_no: "", description: "" });
    const [uploadData, setUploadData] = React.useState<{
        title: string;
        description: string;
        file_type: "pdf" | "pptx" | "code";
        week: string; // use string for input, parse later
        tags: string[];
        file: File | null;
    }>({
        title: "",
        description: "",
        file_type: "pdf",
        week: "",
        tags: [],
        file: null
    });

    const currentLevel = view === "all" ? path.length - 1 : -1;
    const currentCourseId = view === "all" && path.length > 1 ? path[1].id : null;
    const currentType = view === "all" && path.length > 2 ? path[2].type : null; // theory or lab

    // Tag Search State
    const [tagSuggestions, setTagSuggestions] = React.useState<string[]>([]);

    const handleTagSearch = async (query: string) => {
        try {
            if (!query) {
                setTagSuggestions(["vintage", "lecture", "assignment", "reference"]); // default fallback
                return;
            }
            const found = await searchTags(query);
            setTagSuggestions(found.map(t => t.name));
        } catch (error) {
            console.error(error);
        }
    };

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
                    courseId: m.course_id // We need this for context ops if generalized
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
            setPath([{ name: "All Courses" }]);
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
                setPath([...path, { name: item.name, id: item.id, type: item.id.toLowerCase() }]); // item.id is theory/lab
            }
        } else if (item.url) {
            const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
            window.open(`${backendUrl}${item.url}`, "_blank");
        }
    };

    const handleBreadcrumbClick = (index: number) => {
        if (view !== "all") return; // No breadcrumb nav in Recent view yet
        setPath(path.slice(0, index + 1));
    };

    const handleCreateCourse = async () => {
        try {
            if (!newCourse.name || !newCourse.course_no) {
                toast.error("Please fill required fields");
                return;
            }
            await createCourse(newCourse);
            toast.success("Course created");
            setIsCreateCourseOpen(false);
            setNewCourse({ name: "", course_no: "", description: "" });
            loadData();
        } catch (error: any) {
            toast.error(error.message);
        }
    };

    const handleUpload = async () => {
        try {
            if (!currentCourseId || !currentType) return;
            if (!uploadData.file || !uploadData.title) {
                toast.error("File and title are required");
                return;
            }

            const formData = new FormData();
            formData.append("title", uploadData.title);
            formData.append("description", uploadData.description);
            formData.append("type", currentType);
            formData.append("file_type", uploadData.file_type);
            if (uploadData.week) formData.append("week", uploadData.week);
            formData.append("tags", JSON.stringify(uploadData.tags));
            formData.append("metadata", JSON.stringify({}));
            formData.append("file", uploadData.file);

            await uploadMaterial(currentCourseId, formData);
            toast.success("Material uploaded");
            setIsUploadOpen(false);
            setUploadData({ title: "", description: "", file_type: "pdf", week: "", tags: [], file: null });
            loadData();
        } catch (error: any) {
            toast.error(error.message);
        }
    };

    const getAcceptedFileTypes = (type: string) => {
        switch (type) {
            case "pdf": return ".pdf";
            case "pptx": return ".pptx,.ppt";
            case "code": return ".py,.js,.ts,.cpp,.java,.txt,.zip";
            default: return "*";
        }
    };

    // --- Delete Logic ---
    const handleDeleteClick = (items: FileItem[]) => {
        setItemsToDelete(items);
        setIsDeleteOpen(true);
    };

    const handleConfirmDelete = async () => {
        setIsProcessing(true);
        try {
            // Check if we are deleting special folders (Theory/Lab) which means "Empty Folder"
            const specialFolders = itemsToDelete.filter(i => (i.id === "theory" || i.id === "lab") && i.type === "folder");
            const filesToDelete = itemsToDelete.filter(i => i.type === "file");

            if (specialFolders.length > 0) {
                if (!currentCourseId) {
                    toast.error("Cannot determine course for folder operation");
                    return;
                }

                for (const folder of specialFolders) {
                    await deleteCourseMaterials(currentCourseId, folder.id); // folder.id is 'theory' or 'lab'
                }
                toast.success(`Emptied ${specialFolders.length} folder(s)`);
            }

            if (filesToDelete.length > 0) {
                for (const item of filesToDelete) {
                    const cId = (item as any).courseId || currentCourseId;
                    if (!cId) {
                        console.error("Missing course ID for deletion", item);
                        continue;
                    }

                    await deleteMaterial(cId, item.id);
                }
                toast.success(`Deleted ${filesToDelete.length} items`);
            }

            loadData();
            setIsDeleteOpen(false);
            setItemsToDelete([]);
        } catch (error: any) {
            toast.error(error.message);
        } finally {
            setIsProcessing(false);
        }
    };

    // --- Rename Logic ---
    const handleRenameClick = (item: FileItem) => {
        setItemToRename(item);
        setRenameValue(item.name);
        setIsRenameOpen(true);
    };

    const handleRenameSubmit = async () => {
        if (!itemToRename) return;
        const cId = (itemToRename as any).courseId || currentCourseId;

        if (!cId) return;

        try {
            if (itemToRename.type === "file") {
                await updateMaterial(cId, itemToRename.id, { title: renameValue });
                toast.success("Renamed successfully");
                setIsRenameOpen(false);
                loadData();
            } else {
                toast.info("Renaming folders not supported yet");
                setIsRenameOpen(false);
            }
        } catch (error: any) {
            toast.error(error.message);
        }
    };

    return (
        <CMSLayout onNavigate={handleSidebarNavigate}>
            <div className="flex flex-col h-full">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-2xl font-bold tracking-tight">
                        {view === "recent" ? "Recent Files" : (path.length > 1 ? path[path.length - 1].name : "My Courses")}
                    </h1>

                    {currentLevel === 0 && (
                        <Dialog open={isCreateCourseOpen} onOpenChange={setIsCreateCourseOpen}>
                            <DialogTrigger asChild>
                                <Button className="shadow-sm"><Plus className="mr-2 h-4 w-4" /> New Course</Button>
                            </DialogTrigger>
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle>Create New Course</DialogTitle>
                                    <DialogDescription>Add a new course to the platform.</DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-4 py-4">
                                    <div className="grid gap-2">
                                        <Label htmlFor="name">Course Name</Label>
                                        <Input id="name" value={newCourse.name} onChange={e => setNewCourse({ ...newCourse, name: e.target.value })} placeholder="Introduction to AI" />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="course_no">Course Number</Label>
                                        <Input id="course_no" value={newCourse.course_no} onChange={e => setNewCourse({ ...newCourse, course_no: e.target.value })} placeholder="CSE422" />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="description">Description</Label>
                                        <Textarea id="description" value={newCourse.description} onChange={e => setNewCourse({ ...newCourse, description: e.target.value })} />
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button onClick={handleCreateCourse}>Create Course</Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    )}

                    {currentLevel === 2 && (
                        <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
                            <DialogTrigger asChild>
                                <Button className="shadow-sm"><Upload className="mr-2 h-4 w-4" /> Upload Material</Button>
                            </DialogTrigger>
                            <DialogContent className="sm:max-w-[500px]">
                                <DialogHeader>
                                    <DialogTitle>Upload Material</DialogTitle>
                                    <DialogDescription>
                                        Add content to {path[1].name} / {path[2].name}
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-4 py-4">
                                    <div className="grid gap-2">
                                        <Label htmlFor="title">Title</Label>
                                        <Input id="title" value={uploadData.title} onChange={e => setUploadData({ ...uploadData, title: e.target.value })} placeholder="Lecture 1 Slides" />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="file_type">File Type</Label>
                                        <Select value={uploadData.file_type} onValueChange={(v: any) => setUploadData({ ...uploadData, file_type: v, file: null })}>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select type" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="pdf">PDF</SelectItem>
                                                <SelectItem value="pptx">PowerPoint</SelectItem>
                                                <SelectItem value="code">Code</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="week">Week Number (Optional)</Label>
                                        <Input
                                            id="week"
                                            type="number"
                                            value={uploadData.week}
                                            onChange={e => setUploadData({ ...uploadData, week: e.target.value })}
                                            placeholder="e.g. 1"
                                        />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label>Tags</Label>
                                        <TagInput
                                            value={uploadData.tags}
                                            onChange={tags => setUploadData({ ...uploadData, tags })}
                                            suggestions={tagSuggestions}
                                            onSearch={handleTagSearch}
                                        />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="file">File</Label>
                                        <Input
                                            id="file"
                                            type="file"
                                            accept={getAcceptedFileTypes(uploadData.file_type)}
                                            onChange={e => setUploadData({ ...uploadData, file: e.target.files?.[0] || null })}
                                        />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="desc">Description</Label>
                                        <Textarea id="desc" value={uploadData.description} onChange={e => setUploadData({ ...uploadData, description: e.target.value })} />
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button onClick={handleUpload}>Upload</Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    )}
                </div>

                <DriveExplorer
                    items={items}
                    loading={loading}
                    onNavigate={handleNavigate}
                    currentPath={path}
                    onBreadcrumbClick={handleBreadcrumbClick}
                    onDelete={handleDeleteClick}
                    onRename={handleRenameClick}
                />

                <Dialog open={isRenameOpen} onOpenChange={setIsRenameOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Rename Item</DialogTitle>
                        </DialogHeader>
                        <div className="py-4">
                            <Input value={renameValue} onChange={(e) => setRenameValue(e.target.value)} />
                        </div>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setIsRenameOpen(false)}>Cancel</Button>
                            <Button onClick={handleRenameSubmit}>Save</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                <ConfirmDialog
                    open={isDeleteOpen}
                    onOpenChange={setIsDeleteOpen}
                    title="Are you absolutely sure?"
                    description={`This will permanently delete ${itemsToDelete.length} item(s). This action cannot be undone.`}
                    onConfirm={handleConfirmDelete}
                    loading={isProcessing}
                />
            </div>
        </CMSLayout>
    );
}
