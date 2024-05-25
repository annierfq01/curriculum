from datetime import timedelta
import json
import os
import uvicorn

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Body, Form
from fastapi.responses import Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.requests import Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from PIL import Image
from io import BytesIO

import crud
import models
from database import SessionLocal, engine
import security
import schemas
import controller

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


URI_BASE = os.getcwd().replace('\\', '/')

app = FastAPI()


app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.post("/update-status/") 
async def get_asesor(current_user: schemas.User = Depends(security.get_current_active_user)):
  controller.update_assesor(current_user.username)
  raise HTTPException(
    status_code=status.HTTP_200_OK,
    detail="Succes",
  )

# Users
@app.post("/users/")
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
  db_user = crud.get_user_by_email(db, email=user.email)
  if db_user:
      raise HTTPException(status_code=400, detail="Email already registered")
  if crud.create_user(db=db, user=user):
    raise HTTPException(status_code=200, detail="Done")
  else:
    raise HTTPException(status_code=400, detail="Something fail")

@app.get("/validate/")
async def validate_user(token: str, user:str, db: Session = Depends(get_db)):
  if crud.validate_user(db, token, user):
    raise HTTPException(status_code=200, detail="Done")
  else:
    raise HTTPException(status_code=400, detail="Validate fail")

@app.get("/users/", response_model=list[schemas.User]) # 
async def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user}")
async def read_user(user: str):
    db_user = crud.get_user(user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.post("/avatar")
async def save_avatar(file: UploadFile, current_user: schemas.User = Depends(security.get_current_active_user)):
  img = Image.open(BytesIO(await file.read()))

  # Resize the image to 300px x 300px
  resized_img = img.resize((400, 400), Image.Resampling.LANCZOS)

  # Define the file path and name
  file_path = URI_BASE + "/files/users"
  file_name = current_user.username + ".jpg"

  # Save the resized image to the specified location
  resized_img.save(os.path.join(file_path, file_name))

  raise HTTPException(status_code=200, detail="Success2")

# Security
@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> schemas.Token:
    user = security.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return schemas.Token(access_token=access_token, token_type="bearer")

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(security.get_current_active_user)):
    return current_user

@app.put("/user/edit")
async def edit_user(
  user: schemas.UserEdit,
  current_user: schemas.User = Depends(security.get_current_active_user),
  db: Session = Depends(get_db)
  ):
  if crud.edit_user(current_user.username, user.university, user.password, user.country, user.year, db):
    raise HTTPException(status_code=200, detail="Success")
  raise HTTPException(status_code=200, detail="Error")

@app.put("/user/admin")
async def edit_admin(user:str, st:bool, current_user: schemas.User = Depends(security.get_current_active_user), db: Session = Depends(get_db)):
  if not current_user.is_super:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Not autorized",
    )
  
  crud.edit_admin(user, st, db)
  raise HTTPException(status_code=200, detail="Success")

@app.put("/user/enable")
async def enable_user(user:str, st:bool, current_user: schemas.User = Depends(security.get_current_active_user), db: Session = Depends(get_db)):
  if not current_user.is_admin:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Not autorized",
    )
  
  if crud.enable_user(user, st, db):
    raise HTTPException(status_code=200, detail="Success")
  else:
    raise HTTPException(status_code=400, detail="User not Found")

@app.delete("/user")
async def enable_user(user:str, current_user: schemas.User = Depends(security.get_current_active_user), db: Session = Depends(get_db)):
  if not current_user.is_admin:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Not autorized",
    )
  
  if crud.del_user(user, db):
    raise HTTPException(status_code=200, detail="Success")
  else:
    raise HTTPException(status_code=400, detail="User not Found")

#Services
@app.get("/images/{service}/{id}") #http://localhost:8000/images/[]/[]
async def get_image(service:str, id:str):
  directory = ""
  try:
    if(service == "avatar"):
      directory = URI_BASE + '/files/users/' + id + '.jpg'
    if(service == "certificate"):
      directory = URI_BASE + '/files/certificates/' + id + '.jpg'
  except:
    raise HTTPException( 
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Worn request",
        headers={"WWW-Authenticate": "Bearer"},
    )   
  
  return FileResponse(directory)


@app.get("/certificates")
async def get_certificates(current_user: schemas.User = Depends(security.get_current_active_user), db: Session = Depends(get_db)):
  certificates = crud.get_certificates(db, current_user.username)
  return certificates

@app.post("/certificate")
async def save_sertificate(file:UploadFile, tipo: str = Form(), area: str = Form(), level: str = Form(), name: str = Form(), db: Session = Depends(get_db), current_user: schemas.User = Depends(security.get_current_active_user)):
  file_name = controller.generate_ramdon_id()
  crud.save_certify(db=db, username=current_user.username, hash_id=file_name, name=name, status=0, tipo=tipo, area=area, level=level)

  img = Image.open(BytesIO(await file.read()))
  max_size = (600, 600)
  img.thumbnail(max_size, Image.Resampling.LANCZOS)
  if img.mode == "RGBA":
    img = img.convert("RGB")
  file_path = URI_BASE + "/files/certificates"
  file_name_ext = file_name + ".jpg"
  img.save(os.path.join(file_path, file_name_ext))

  raise HTTPException(status_code=200, detail="Success")


@app.get("/unverified")
async def unvalidated(db: Session = Depends(get_db)):
  return crud.get_unverified(db)

@app.get("/certify/{id}")
async def get_certify_status(id: str, db: Session = Depends(get_db)):
  return crud.get_certify(db, id)

@app.put("/verify")
async def verify(hash_id:str, act:bool, db: Session = Depends(get_db), current_user: schemas.User = Depends(security.get_current_active_user)):
  if not current_user.is_admin:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Unautorized user"
    )
  
  res = crud.verify_certificate(db, act, hash_id)
  if res:
    raise HTTPException(
      status_code=status.HTTP_200_OK,
      detail="Success"
    )
  else:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Request not found"
    )

@app.delete("/certify/delete/{id}")
async def delete_certify(id:str, db: Session = Depends(get_db), current_user: schemas.User = Depends(security.get_current_active_user)):
  res = crud.delete_certify(db, current_user.username, id)
  if res:
    raise HTTPException(
      status_code=status.HTTP_200_OK,
      detail="Success"
    )
  else:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Request not found"
    )

@app.get("/filter/{limit}")
async def filter(limit:int = 3, area:str = "p_tot", year:str = "all", university:str = "all", db: Session = Depends(get_db)):
  return crud.filter(area, year, university, limit, db)

if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)