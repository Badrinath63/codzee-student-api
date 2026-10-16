import pytest
import main
from fastapi.testclient import TestClient
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
    second = client.post(
        "/students/",
        json=payload(
            name="Second Student",
            email="second@example.com",
        ),
    )
    second_id = second.json()["id"]
    response = client.put(
        f"/students/{second_id}",
        json=payload(email="first@example.com"),
    )
    assert response.status_code == 409


def test_student_can_keep_own_email_during_update():
    created = client.post(
        "/students/",
        json=payload(email="badri@example.com"),
    )
    student_id = created.json()["id"]
    response = client.put(
        f"/students/{student_id}",
        json=payload(
            name="Updated Student",
            email="badri@example.com",
        ),
    )
    assert response.status_code == 200
    assert response.json()["email"] == "badri@example.com"