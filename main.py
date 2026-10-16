from typing import Annotated
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field, StringConstraints
app = FastAPI(title="Student Management API")
students = {}
next_id = 1
StudentName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=100,
    ),
]


class StudentCreate(BaseModel):
    name: StudentName
    email: EmailStr
    age: int = Field(ge=1, le=120)


class StudentUpdate(BaseModel):
    name: StudentName
    email: EmailStr
    age: int = Field(ge=1, le=120)


@app.get("/")
def home():
    return {"message": "Student Management API is running"}


@app.post("/students/", status_code=201)
def create_student(student: StudentCreate):
    global next_id
    student_data = {
        "id": next_id,
        "name": student.name,
        "email": student.email,
        "age": student.age,
    }
    students[next_id] = student_data
    next_id += 1
    return student_data


@app.get("/students/")
def list_students():
    return list(students.values())


@app.get("/students/{student_id}")
def get_student(student_id: int):
    student = students.get(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.put("/students/{student_id}")
def update_student(student_id: int, data: StudentUpdate):
    if student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")
    students[student_id].update(data.model_dump())
    return students[student_id]


@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    if student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")
    del students[student_id]
    return {"message": "Student deleted successfully"}

