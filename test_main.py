import pytest
import main
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor
client = TestClient(main.app)
@pytest.fixture(autouse=True)
def reset_students():
    main.students.clear()
    main.next_id = 1
    yield
    main.students.clear()
    main.next_id = 1


def payload(name="Badrinath", email="badri@example.com", age=25):
    return {"name": name, "email": email, "age": age}


def test_valid_student_creation():
    response = client.post("/students/", json=payload())
    assert response.status_code == 201
    assert response.json()["name"] == "Badrinath"


def test_whitespace_is_removed_from_name():
    response = client.post(
        "/students/",
        json=payload(name="  Badrinath  "),
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Badrinath"


def test_blank_name_is_rejected():
    response = client.post(
        "/students/",
        json=payload(name="   "),
    )
    assert response.status_code == 422


def test_short_name_is_rejected():
    response = client.post(
        "/students/",
        json=payload(name="A"),
    )
    assert response.status_code == 422


def test_invalid_email_is_rejected():
    response = client.post(
        "/students/",
        json=payload(email="invalid-email"),
    )
    assert response.status_code == 422


@pytest.mark.parametrize("age", [0, -1, 121])
def test_invalid_age_is_rejected(age):
    response = client.post(
        "/students/",
        json=payload(age=age),
    )
    assert response.status_code == 422


def test_age_boundary_values_are_accepted():
    for age in [1, 120]:
        response = client.post(
            "/students/",
            json=payload(
                email=f"student{age}@example.com",
                age=age,
            ),
        )
        assert response.status_code == 201


def test_update_rejects_blank_name():
    created = client.post("/students/", json=payload())
    student_id = created.json()["id"]
    response = client.put(
        f"/students/{student_id}",
        json=payload(name="   "),
    )
    assert response.status_code == 422


def test_duplicate_email_is_rejected():
    first = client.post(
        "/students/",
        json=payload(email="badri@example.com"),
    )
    assert first.status_code == 201
    second = client.post(
        "/students/",
        json=payload(
            name="Another Student",
            email="badri@example.com",
        ),
    )
    assert second.status_code == 409


def test_duplicate_email_is_rejected_case_insensitively():
    first = client.post(
        "/students/",
        json=payload(email="badri@example.com"),
    )
    assert first.status_code == 201
    second = client.post(
        "/students/",
        json=payload(
            name="Another Student",
            email="BADRI@example.com",
        ),
    )
    assert second.status_code == 409


def test_update_rejects_another_students_email():
    first = client.post(
        "/students/",
        json=payload(email="first@example.com"),
    )
    assert first.status_code == 201
    second = client.post(
        "/students/",
        json=payload(
            name="Second Student",
            email="second@example.com",
        ),
    )
    assert second.status_code == 201
    second_id = second.json()["id"]
    response = client.put(
        f"/students/{second_id}",
        json=payload(email="first@example.com"),
    )
    assert response.status_code == 409
    unchanged = client.get(f"/students/{second_id}")
    assert unchanged.status_code == 200
    assert unchanged.json()["email"] == "second@example.com"


def test_student_can_keep_own_email_during_update():
    created = client.post(
        "/students/",
        json=payload(email="badri@example.com"),
    )
    assert created.status_code == 201
    student_id = created.json()["id"]
    response = client.put(
        f"/students/{student_id}",
        json=payload(
            name="Updated Student",
            email="badri@example.com",
        ),
    )
    assert response.status_code == 200
    assert response.json()["id"] == student_id
    assert response.json()["name"] == "Updated Student"
    assert response.json()["email"] == "badri@example.com"


def test_update_rejects_case_insensitive_duplicate_email():
    first = client.post(
        "/students/",
        json=payload(email="first@example.com"),
    )
    assert first.status_code == 201
    second = client.post(
        "/students/",
        json=payload(
            name="Second Student",
            email="second@example.com",
        ),
    )
    assert second.status_code == 201
    second_id = second.json()["id"]
    response = client.put(
        f"/students/{second_id}",
        json=payload(email="FIRST@example.com"),
    )
    assert response.status_code == 409


def test_deleted_student_email_can_be_reused():
    created = client.post(
        "/students/",
        json=payload(email="reusable@example.com"),
    )
    assert created.status_code == 201
    student_id = created.json()["id"]
    deleted = client.delete(f"/students/{student_id}")
    assert deleted.status_code == 200
    recreated = client.post(
        "/students/",
        json=payload(
            name="New Student",
            email="reusable@example.com",
        ),
    )
    assert recreated.status_code == 201
    assert recreated.json()["email"] == "reusable@example.com"


def test_concurrent_requests_allow_only_one_duplicate_email():
    def create_student_request():
        with TestClient(main.app) as thread_client:
            response = thread_client.post(
                "/students/",
                json=payload(email="concurrent@example.com"),
            )
            return response.status_code
    with ThreadPoolExecutor(max_workers=8) as executor:
        statuses = list(
            executor.map(
                lambda _: create_student_request(),
                range(8),
            )
        )
    assert statuses.count(201) == 1
    assert statuses.count(409) == 7
