"""
Test Video Generation Pipeline.

Tests for the programmatic video generation system.
"""

import asyncio
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_gen_engine.video_gen.schemas import (
    VideoScript, ScriptSegment, SceneSpec, ScenePlan, 
    SceneType, VisualType, VideoConfig, PipelineState
)
from content_gen_engine.video_gen.agents import get_script_writer, get_scene_planner
from content_gen_engine.video_gen.generators import (
    get_slide_renderer, get_manim_generator, get_tts_engine
)
from content_gen_engine.video_gen.pipeline import get_video_pipeline


async def test_script_generation():
    """Test script generation from topic."""
    print("\n=== Test 1: Script Generation ===")
    
    writer = get_script_writer()
    
    script = await writer.generate(
        topic="Binary Search Algorithm",
        context="Binary search is an efficient O(log n) algorithm for finding items in sorted arrays.",
        duration_seconds=120
    )
    
    print(f"✓ Title: {script.title}")
    print(f"✓ Segments: {len(script.segments)}")
    print(f"✓ Duration: {script.total_duration_estimate}s")
    print(f"✓ Key takeaways: {script.key_takeaways}")
    
    for i, seg in enumerate(script.segments[:3]):
        print(f"  [{seg.segment_id}] {seg.section}: {seg.text[:80]}...")
    
    return script


async def test_scene_planning(script: VideoScript):
    """Test scene planning from script."""
    print("\n=== Test 2: Scene Planning ===")
    
    planner = get_scene_planner()
    
    plan = await planner.plan(script)
    
    print(f"✓ Total scenes: {plan.total_scenes}")
    
    for scene in plan.scenes[:5]:
        print(f"  [{scene.scene_id}] {scene.scene_type.value} - {scene.visual_type.value}")
        if scene.manim_description:
            print(f"    Manim: {scene.manim_description[:60]}...")
    
    return plan


async def test_slide_rendering(scenes: list):
    """Test slide rendering."""
    print("\n=== Test 3: Slide Rendering ===")
    
    renderer = get_slide_renderer("./test_output/slides")
    
    # Create test scenes
    test_scenes = [
        SceneSpec(
            scene_id="title_1",
            segment_id="seg_1",
            scene_type=SceneType.TITLE,
            title="Binary Search",
            content="An efficient search algorithm",
            duration=3.0
        ),
        SceneSpec(
            scene_id="content_1",
            segment_id="seg_2",
            scene_type=SceneType.CONTENT,
            title="How It Works",
            content="Binary search divides the search interval in half repeatedly. Starting with the middle element, we compare it to the target value. If the target is less than the middle, we search the left half. If greater, we search the right half.",
            visual_type=VisualType.STATIC,
            duration=10.0
        ),
        SceneSpec(
            scene_id="code_1",
            segment_id="seg_3",
            scene_type=SceneType.CODE,
            title="Implementation",
            code='''def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1''',
            code_language="python",
            highlight_lines=[4, 5, 6],
            duration=15.0
        )
    ]
    
    slides = await renderer.render_all(test_scenes)
    
    print(f"✓ Rendered {len(slides)} slides")
    for scene_id, path in slides.items():
        print(f"  {scene_id}: {path}")
    
    return slides


async def test_tts_engine():
    """Test TTS synthesis."""
    print("\n=== Test 4: TTS Engine ===")
    
    try:
        tts = get_tts_engine("./test_output/audio")
        
        text = "Binary search is like looking for a word in a dictionary. Instead of checking every page, you open to the middle and decide which half to search next."
        
        audio_path = await tts.synthesize(text, "test_segment")
        print(f"✓ Generated audio: {audio_path}")
        
        # Test with timing
        audio_path2, timings = await tts.synthesize_with_timing(
            "Hello world, this is a test.",
            "test_timing"
        )
        print(f"✓ Audio with timing: {len(timings)} words")
        
    except ImportError as e:
        print(f"⚠ TTS not available (install edge-tts): {e}")


async def test_manim_generator():
    """Test Manim code generation."""
    print("\n=== Test 5: Manim Generator ===")
    
    generator = get_manim_generator("./test_output/manim")
    
    scene = SceneSpec(
        scene_id="manim_test",
        segment_id="seg_1",
        scene_type=SceneType.MANIM,
        visual_type=VisualType.ANIMATED,
        manim_description="Create a simple animation showing an array [1, 3, 5, 7, 9] as squares, then highlight the middle element turning it yellow",
        duration=5.0
    )
    
    if generator._manim_available:
        result = await generator.generate(scene)
        if result:
            print(f"✓ Manim video: {result}")
        else:
            print("⚠ Manim generation failed (may need fixes)")
    else:
        print("⚠ Manim not installed, skipping")


async def test_full_pipeline():
    """Test full video generation pipeline."""
    print("\n=== Test 6: Full Pipeline ===")
    
    pipeline = get_video_pipeline("./test_output")
    
    config = VideoConfig(
        target_duration_minutes=1.0,
        save_slides=True
    )
    
    try:
        state = await pipeline.generate(
            topic="QuickSort Algorithm",
            context="QuickSort is a divide-and-conquer algorithm with average O(n log n) complexity. It works by selecting a pivot element and partitioning the array around it.",
            duration_minutes=1.0
        )
        
        print(f"✓ Pipeline complete!")
        print(f"  Job ID: {state.job_id}")
        print(f"  Video: {state.final_video_path}")
        print(f"  Slides: {state.slides_output_dir}")
        print(f"  Scenes: {len(state.slides)}")
        print(f"  Audio: {len(state.audio_files)}")
        
        if state.errors:
            print(f"  Errors: {state.errors}")
        if state.warnings:
            print(f"  Warnings: {state.warnings}")
            
    except Exception as e:
        print(f"⚠ Pipeline error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Video Generation Pipeline Tests")
    print("=" * 60)
    
    # # Test 1: Script generation
    # try:
    #     script = await test_script_generation()
    # except Exception as e:
    #     print(f"Script generation failed: {e}")
    #     return
    
    # # Test 2: Scene planning
    # try:
    #     plan = await test_scene_planning(script)
    # except Exception as e:
    #     print(f"Scene planning failed: {e}")
    #     plan = None
    
    # # Test 3: Slide rendering (standalone)
    # try:
    #     slides = await test_slide_rendering(plan.scenes if plan else [])
    # except Exception as e:
    #     print(f"Slide rendering failed: {e}")
    
    # # Test 4: TTS
    # await test_tts_engine()
    
    # # Test 5: Manim
    # await test_manim_generator()
    
    # Test 6: Full pipeline (optional)
    run_full = input("\nRun full pipeline test? (y/N): ").strip().lower() == 'y'
    if run_full:
        await test_full_pipeline()
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
