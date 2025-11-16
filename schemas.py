"""
Database Schemas for E-Planet Journal

Each Pydantic model corresponds to a MongoDB collection (lowercased class name).
"""
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class Author(BaseModel):
    name: str = Field(..., description="Author full name")
    affiliation: Optional[str] = Field(None, description="Affiliation / Institution")
    country: Optional[str] = Field(None, description="Country")


class CitationFormats(BaseModel):
    apa: Optional[str] = None
    mla: Optional[str] = None
    chicago: Optional[str] = None


class Section(BaseModel):
    heading: str
    content: str


class Article(BaseModel):
    title: str
    slug: str = Field(..., description="URL-friendly unique identifier")
    authors: List[Author]
    affiliations: Optional[List[str]] = Field(default=None, description="Aggregated affiliations for SEO")
    abstract: str
    keywords: List[str] = []
    doi: Optional[str] = Field(None, description="DOI placeholder")
    pdf_url: Optional[HttpUrl] = None
    year: int
    volume: int
    issue: int
    sections: List[Section] = []
    references: List[str] = []
    citation_formats: Optional[CitationFormats] = None
    cover_image: Optional[HttpUrl] = None


class Issue(BaseModel):
    year: int
    volume: int
    issue: int
    title: Optional[str] = None
    description: Optional[str] = None


class EditorialMember(BaseModel):
    role: str = Field(..., description="Chief Editor, Editor, Reviewer")
    name: str
    designation: Optional[str] = None
    affiliation: Optional[str] = None
    country: Optional[str] = None
    photo_url: Optional[HttpUrl] = None


class Submission(BaseModel):
    title: str
    corresponding_author: str
    email: str
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    notes: Optional[str] = None

