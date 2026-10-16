from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
app = FastAPI(title="Student Management API")
students = {}
next_id = 1
class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    age: int


class StudentUpdate(BaseModel):
    name: str
    email: EmailStr
    age: int


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

