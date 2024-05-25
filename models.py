from sqlalchemy import Boolean, Column, Integer, String

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    telef = Column(String, index=True)
    full_name = Column(String, unique=True, index=True)
    country = Column(String, index=True)
    university = Column(String, index=True)
    year = Column(String, index=True)
    is_admin = Column(Boolean, default=False, index=True)
    is_super = Column(Boolean, default=False, index=True)
    
    p_inv = Column(Integer, index=True)
    p_doc = Column(Integer, index=True)
    p_cul = Column(Integer, index=True)
    p_dep = Column(Integer, index=True)
    p_pol = Column(Integer, index=True)
    p_tot = Column(Integer, index=True)

    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class Certify(Base):
    __tablename__ = "certify"

    id = Column(Integer, primary_key=True)
    hash_id = Column(String, unique=True, index=True)
    username = Column(String, index=True)

    name = Column(String, default=False)
    status = Column(Integer, default=False)
    area = Column(String, default=False)
    tipo = Column(String, default=False)
    level = Column(String, default=False)