from pydantic import BaseModel
from typing import List
from fastapi import UploadFile

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserBase(BaseModel):
    email: str
    username: str
    telef: str
    full_name: str
    country: str
    university: str
    full_name: str
    year: str

class UserInDB(UserBase):
    hashed_password: str
    is_active: bool
    is_admin: bool
    is_super: bool

    p_inv: int
    p_doc: int
    p_cul: int
    p_dep: int
    p_pol: int

    p_tot: int

class UserCreate(UserBase):
    password: str


class User(UserBase):
    is_active: bool
    is_admin: bool
    is_super: bool

    class Config:
        orm_mode = True

class UserEdit(BaseModel):
    university:str | None = None
    year:str | None = None
    password:str | None = None
    country:str | None = None
