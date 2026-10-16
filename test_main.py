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


