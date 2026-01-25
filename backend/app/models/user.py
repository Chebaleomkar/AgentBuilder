"""
User Models
Pydantic schemas for MongoDB user documents
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


# ========== Enums ==========

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


# ========== Pydantic Schemas ==========

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    """Schema for user responses"""
    id: str = Field(alias="_id")
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class UserInDB(UserResponse):
    """User stored in database (includes hashed password)"""
    hashed_password: str


# ========== Project Schemas ==========

class ProjectBase(BaseModel):
    """Base project schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project"""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project responses"""
    id: str = Field(alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


# ========== MongoDB Document Helpers ==========

def user_to_doc(user: UserCreate, hashed_password: str) -> Dict[str, Any]:
    """Convert UserCreate to MongoDB document"""
    now = datetime.utcnow()
    
    return {
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "hashed_password": hashed_password,
        "role": UserRole.USER.value,
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }


def doc_to_user(doc: Dict[str, Any]) -> UserResponse:
    """Convert MongoDB document to UserResponse"""
    doc["_id"] = str(doc["_id"])
    doc["role"] = UserRole(doc.get("role", "user"))
    return UserResponse(**doc)


def project_to_doc(project: ProjectCreate, user_id: str) -> Dict[str, Any]:
    """Convert ProjectCreate to MongoDB document"""
    now = datetime.utcnow()
    
    return {
        "name": project.name,
        "description": project.description,
        "user_id": user_id,
        "created_at": now,
        "updated_at": now
    }


def doc_to_project(doc: Dict[str, Any]) -> ProjectResponse:
    """Convert MongoDB document to ProjectResponse"""
    doc["_id"] = str(doc["_id"])
    return ProjectResponse(**doc)
