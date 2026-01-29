import json
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException,
    status,
    BackgroundTasks,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from config.settings import settings
from cms_agent.schemas import (
    CourseCreate,
    CourseResponse,
    CourseMaterialCreate,
    CourseMaterialUpdate,
    CourseMaterialResponse,
    TagResponse,
)
from cms_agent.service import CMSService
from cms_agent.rag_integration import get_rag_integration
from rag_engine.semantic_search import get_semantic_search

router = APIRouter(prefix="/cms", tags=["CMS"])


@router.post(
    "/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED
)
async def create_course(course: CourseCreate, db: AsyncSession = Depends(get_db)):
    return await CMSService.create_course(db, course)


@router.get("/courses", response_model=List[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db)):
    return await CMSService.get_courses(db)


@router.post("/courses/{course_id}/materials", response_model=CourseMaterialResponse)
async def upload_material(
    course_id: UUID,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    type: str = Form(..., description="theory or lab"),
    file_type: str = Form(..., description="pdf, pptx, or code"),
    description: Optional[str] = Form(None),
    tags: str = Form("[]", description="JSON string array of tag names"),
    week: Optional[int] = Form(None, description="Week number"),
    metadata: str = Form("{}", description="JSON string of metadata"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        tags_list = json.loads(tags)
        metadata_dict = json.loads(metadata)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON for tags or metadata")

    material_in = CourseMaterialCreate(
        title=title,
        type=type,
        file_type=file_type,
        description=description,
        tags=tags_list,
        week=week,
        metadata_=metadata_dict,
    )

    material = await CMSService.upload_material(db, course_id, file, material_in)

    # Get course info for metadata
    course = await CMSService.get_course(db, course_id)

    # Schedule RAG ingestion in background
    if course:
        rag_service = get_rag_integration()
        file_path = str(Path(settings.BASE_DIR) / material.url.lstrip("/"))
        background_tasks.add_task(
            rag_service.ingest_material,
            file_path,
            str(material.id),
            str(course_id),
            course.course_no,
            type,
            {"title": title, "week": week},
        )

    return material


@router.put(
    "/courses/{course_id}/materials/{material_id}",
    response_model=CourseMaterialResponse,
)
async def update_material(
    course_id: UUID,
    material_id: UUID,
    update_data: CourseMaterialUpdate,
    db: AsyncSession = Depends(get_db),
):
    # course_id not strictly needed for update if material_id is unique, but good for validation
    return await CMSService.update_material(db, material_id, update_data)


@router.delete(
    "/courses/{course_id}/materials/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_material(
    course_id: UUID,
    material_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    # Cleanup RAG chunks before deleting
    rag_service = get_rag_integration()
    rag_service.delete_material_chunks_by_id(str(material_id))

    await CMSService.delete_material(db, material_id)
    return None


@router.get("/materials/recent", response_model=List[CourseMaterialResponse])
async def list_recent_materials(limit: int = 20, db: AsyncSession = Depends(get_db)):
    return await CMSService.get_recent_materials(db, limit)


@router.delete("/courses/{course_id}/materials", status_code=status.HTTP_204_NO_CONTENT)
async def delete_materials_by_type(
    course_id: UUID, type: str, db: AsyncSession = Depends(get_db)
):
    await CMSService.delete_materials_by_type(db, course_id, type)
    return None


@router.get("/tags", response_model=List[TagResponse])
async def search_tags(query: str = "", db: AsyncSession = Depends(get_db)):
    return await CMSService.search_tags(db, query)


@router.get(
    "/courses/{course_id}/materials", response_model=List[CourseMaterialResponse]
)
async def list_materials(
    course_id: UUID, type: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    return await CMSService.get_materials(db, course_id, type)


# --- Semantic Search Endpoint ---
@router.get("/search")
async def semantic_search(
    q: str = Query(..., min_length=1, description="Search query"),
    type: Optional[str] = Query(
        None, description="Filter by file type: pdf, pptx, code"
    ),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
):
    """
    Semantic search across all course materials.

    Uses hybrid search (dense embeddings + BM25) with reranking.
    Returns relevant files with matching sections and citations.
    """
    import logging

    logger = logging.getLogger(__name__)

    logger.info(f"[SEARCH] Starting search: query='{q}', type={type}, limit={limit}")

    try:
        search_service = get_semantic_search()
        logger.debug(f"[SEARCH] Got search service: {search_service}")

        logger.info(f"[SEARCH] Calling search_files...")
        results = await search_service.search_files(
            query=q,
            top_k=limit,
            file_type=type,
            return_sections=True,
            max_sections_per_file=3,
        )

        logger.info(f"[SEARCH] Got {len(results)} results")
        for i, r in enumerate(results):
            logger.debug(
                f"[SEARCH] Result {i + 1}: {r.filename} (score={r.relevance_score:.3f})"
            )

        response = {
            "query": q,
            "count": len(results),
            "results": [r.to_dict() for r in results],
        }

        logger.info(f"[SEARCH] Returning {response['count']} results")
        return response

    except Exception as e:
        logger.error(f"[SEARCH] Error during search: {e}", exc_info=True)
        raise
