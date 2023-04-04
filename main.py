import os
import secrets

import numpy as np
import uvicorn
from face_recognition import compare_faces, face_encodings, load_image_file
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from numpy import ndarray
from PIL import Image
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import schemas
from models import Base, Employee, Encoding
from models import Image as ImageModel

app = FastAPI()
engine = create_engine("sqlite:///app.db", pool_pre_ping=True)
DBSession = Session(bind=engine, autoflush=False, autocommit=False)


app.mount("/static", StaticFiles(directory="static"), name="static")

if not os.path.exists("images"):
    os.mkdir("images")
app.mount("/images", StaticFiles(directory="images"), name="employee_images")


templates = Jinja2Templates(directory="templates")


def get_db():
    db = DBSession
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/upload-image")
async def upload_image(file: UploadFile, db: Session = Depends(get_db)):
    if not file.content_type in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only jpg/png image allow.",
        )
    if not file.size < 5 * 1000 * 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload file < 5mb",
        )
    image = load_image_file(file.file)
    encoding: list[ndarray] = face_encodings(image)
    if not len(encoding) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The image does not contain any faces.",
        )
    if len(encoding) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload image with 1 face only.",
        )

    # Resize image
    img = Image.open(file.file)
    img_out_size = (512, 512)
    img.thumbnail(img_out_size)
    # Save image
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(file.filename)  # type: ignore
    image_fn = random_hex + f_ext  # type: ignore
    to_save_path = os.path.join("images", image_fn)
    img.save(to_save_path)
    img.close()

    encoding_obj = Encoding(encoding=encoding[0])
    db.add(encoding_obj)
    image_obj = ImageModel(path="/images/" + image_fn)
    db.add_all([encoding_obj, image_obj])
    db.commit()
    db.refresh(encoding_obj)
    db.refresh(image_obj)
    return {
        "encoding_id": encoding_obj.id,
        "image_id": image_obj.id,
        "image_url": "/images/" + image_fn,
    }


@app.post("/api/signup")
async def signup_api(*, db: Session = Depends(get_db), employee_in: schemas.Employee):
    employee_exist = db.scalar(
        select(Employee).filter_by(fullname=employee_in.fullname)
    )
    if employee_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Employee name existed"
        )
    employee_obj = Employee(
        fullname=employee_in.fullname,
        encoding_id=employee_in.encoding_id,
        image_id=employee_in.image_id,
    )
    db.add(employee_obj)
    db.commit()
    db.refresh(employee_obj)
    return employee_obj


@app.get("/checkin", response_class=HTMLResponse)
async def checkin(request: Request):
    return templates.TemplateResponse("checkin.html", {"request": request})


@app.post("/api/checkin")
async def checkin_api(*, db: Session = Depends(get_db), file: UploadFile):
    known_encoding_bytes = db.scalars(select(Encoding.encoding)).all()
    known_encoding_ids = db.scalars(select(Encoding.id)).all()
    known_encoding = []
    for b in known_encoding_bytes:
        known_encoding.append(np.frombuffer(b))
    unknown_image = load_image_file(file.file)
    unknown_image_encoding = face_encodings(unknown_image)[0]
    results = compare_faces(known_encoding, unknown_image_encoding)
    for index, result in enumerate(results):
        if result:
            found_encoding_id = known_encoding_ids[index]
            encoding = db.scalar(select(Encoding).filter_by(id=found_encoding_id))
            employee = encoding.employee
            if not employee:
                continue
            return employee.fullname
    return False


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    uvicorn.run("main:app", reload=True)
