import pytest
from fastapi.testclient import TestClient
from main import app
import json
import os

client = TestClient(app)

# Mock DB interaction is tricky without a separate test DB setup in this environment.
# But we can try to hit endpoints if the local DB is running and accessible (which it should be if user ran migration).
# If not, this test might fail on connection.

# For now, let's assume we can hit the endpoints.


def test_create_course():
    response = client.post(
        "/api/v1/cms/courses",
        json={
            "name": "Test Course",
            "course_no": "TEST101",
            "description": "A test course",
        },
    )
    # 201 Created or 400 if already exists
    assert response.status_code in [201, 400]
    if response.status_code == 201:
        data = response.json()
        assert data["course_no"] == "TEST101"
        return data["id"]
    else:
        # Fetch existing to get ID
        response = client.get("/api/v1/cms/courses")
        assert response.status_code == 200
        courses = response.json()
        for c in courses:
            if c["course_no"] == "TEST101":
                return c["id"]
    return None


def test_upload_material():
    # Get or create course
    course_id = test_create_course()
    assert course_id is not None

    # Create dummy file
    file_content = b"Dummy PDF content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}

    data = {
        "title": "Test Lecture",
        "type": "theory",
        "file_type": "pdf",
        "description": "Test file",
        "tags": json.dumps(["test_tag", "new_tag"]),
        "metadata": json.dumps({"pages": 10}),
    }

    response = client.post(
        f"/api/v1/cms/courses/{course_id}/materials", data=data, files=files
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Lecture"
    assert len(data["tags"]) == 2
    assert data["tags"][0]["name"] in ["test_tag", "new_tag"]

    print("Upload Test Passed")


if __name__ == "__main__":
    # Ensure contents dir exists for test
    os.makedirs("contents", exist_ok=True)
    try:
        test_upload_material()
        print("All CMS Tests Passed!")
    except Exception as e:
        print(f"Test Failed: {e}")
