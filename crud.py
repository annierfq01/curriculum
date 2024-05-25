import json
import os

from sqlalchemy.orm import Session
from fastapi import Depends

import models
import schemas
import security
import database
import controller

def get_user(username: str):
    db = database.SessionLocal()
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first() 


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = security.get_password_hash(user.password)

    if not controller.sendActivate(user.email, user.username, security.get_password_hash(user.username)):
       return False

    db_user = models.User(
        username=user.username,
        email=user.email, 
        hashed_password=fake_hashed_password,
        country=user.country,
        university=user.university,
        telef=user.telef,
        full_name=user.full_name,
        year = user.year,
        is_admin = False,
        is_super = False,
        p_inv = 0,
        p_doc = 0,
        p_cul = 0,
        p_dep = 0,
        p_pol = 0,
        p_tot = 0,
        is_active=False)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return security.get_password_hash(user.username)
    return True

def validate_user(db:Session, token:str, user:str): 
    if not security.verify_password(user, token):
        return False

    usuario = db.query(models.User).filter(models.User.username == user).first()
    if usuario:
        usuario.is_active = True
        db.commit()

        return True

    return False

def get_unverified(db: Session):
    return db.query(models.Certify).filter(models.Certify.status == 0).all()

def save_certify(db: Session, username, hash_id, name, status, tipo, area, level):
    db_certify = models.Certify(
        username=username,
        hash_id=hash_id, 
        name=name,
        status=status,
        area=area,
        tipo=tipo,
        level=level)
    db.add(db_certify)
    db.commit()
    db.refresh(db_certify)

def get_certificates(db:Session, username):
    certify = db.query(models.Certify).filter(models.Certify.username == username).all()
    return certify

def get_certify(db:Session, id):
    certify = db.query(models.Certify).filter(models.Certify.hash_id == id).first()
    if not certify:
        return -1
    return certify

def verify_certificate(db:Session, st:bool, hash_id): 
    certify = db.query(models.Certify).filter(models.Certify.hash_id == hash_id).first()
    user = db.query(models.User).filter(models.User.username == certify.username).first()
    if not certify or not user:
        return False

    if not st and certify.status == 2:
        return True
    if st and certify.status == 1:
        return True

    points = controller.get_points(certify.area, certify.tipo, certify.level)
    if not st and certify.status == 1:
        points *= -1
    
    if st:
        certify.status = 1
    else:
        certify.status = 2
    
    if certify.area == "inv":
        user.p_inv += points
    elif certify.area == "doc":
        user.p_doc += points
    elif certify.area == "dep":
        user.p_dep += points
    elif certify.area == "cul":
        user.p_cul += points
    elif certify.area == "pol":
        user.p_pol += points
    user.p_tot += points
    

    db.commit()
    return True

def delete_certify(db:Session, username:str, hash_id:str):
    row = db.query(models.Certify).filter(models.Certify.hash_id == hash_id).first()

    if row.status == 1:
        return False

    if row:
        if row.username != username:
            return False

        file_path = os.getcwd().replace('\\', '/') + "/files/certificates/" + hash_id + '.jpg'
        os.remove(file_path)

        db.delete(row)
        db.commit()
        return True

    return False

def filter(area:str, year:str, university:str , x:int, db: Session):
    if university != "all" and year != "all":
        data = db.query(models.User).filter(models.User.university == university and models.User.year == year)
        return data.order_by(getattr(models.User, area).desc()).limit(x).all()
    elif university != "all":
        data = db.query(models.User).filter(models.User.university == university)
        return data.order_by(getattr(models.User, area).desc()).limit(x).all()
    elif year != "all":
        data = db.query(models.User).filter(models.User.year == year)
        return data.order_by(getattr(models.User, area).desc()).limit(x).all()
    else:
        data = db.query(models.User)
        return data.order_by(getattr(models.User, area).desc()).limit(x).all()

def edit_user(username, university, password, country, year, db:Session):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return False

    if university:
        user.university = university
    if password:
        user.password = security.get_password_hash(password)
    if country:
        user.country = country
    if year:
        user.year = year

    db.commit()
    db.refresh(user) 
    return True

def edit_admin(username, st:bool, db:Session):
    user = db.query(models.User).filter(models.User.username == username).first()
    if user:
        user.is_admin = st
        db.commit()
        return True
    return False

def del_user(user, db:Session):
    usuario = db.query(models.User).filter(models.User.username == user).first()
    if usuario:
        db.delete(usuario)
        db.commit()  # del certificates
        return True
    return False

def enable_user(user, st:bool, db:Session):
    usuario = db.query(models.User).filter(models.User.username == user).first()
    if usuario:
        usuario.is_active = st
        db.commit()
        return True
    return False