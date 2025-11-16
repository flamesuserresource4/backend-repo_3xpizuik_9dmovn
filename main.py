import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Article as ArticleSchema, Issue as IssueSchema, EditorialMember as EditorialMemberSchema, Submission as SubmissionSchema, Author as AuthorSchema, Section as SectionSchema, CitationFormats as CitationFormatsSchema

app = FastAPI(title="E-Planet Journal API", description="Backend for E-Planet Journal website")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------
# Utility & Seed Data
# ----------------------

def collection(name: str):
    if db is None:
        return None
    return db[name]


def seed_if_needed():
    """Seed demo content if collections are empty."""
    try:
        # Seed Editorial Board
        coll = collection("editorialmember")
        if coll is not None and coll.count_documents({}) == 0:
            members = [
                {
                    "role": "Chief Editor",
                    "name": "Prof. A. K. Sharma",
                    "designation": "Professor of Environmental Sciences",
                    "affiliation": "Green Earth University",
                    "country": "India",
                    "photo_url": "https://images.unsplash.com/photo-1607746882042-944635dfe10e?w=400&auto=format&fit=crop&q=60"
                },
                {
                    "role": "Editor",
                    "name": "Dr. Maria López",
                    "designation": "Senior Research Scientist",
                    "affiliation": "Institute for Agroecology",
                    "country": "Spain",
                    "photo_url": "https://images.unsplash.com/photo-1544723795-3fb6469f5b39?w=400&auto=format&fit=crop&q=60"
                },
                {
                    "role": "Editor",
                    "name": "Dr. James O. Carter",
                    "designation": "Associate Professor",
                    "affiliation": "Midwest State University",
                    "country": "USA",
                    "photo_url": "https://images.unsplash.com/photo-1502685104226-ee32379fefbe?w=400&auto=format&fit=crop&q=60"
                },
                {
                    "role": "Reviewer",
                    "name": "Dr. Lin Wei",
                    "designation": "Soil Scientist",
                    "affiliation": "SinoAgri Research Center",
                    "country": "China",
                    "photo_url": "https://images.unsplash.com/photo-1547425260-76bcadfb4f2c?w=400&auto=format&fit=crop&q=60"
                },
                {
                    "role": "Reviewer",
                    "name": "Dr. Amina El-Sayed",
                    "designation": "Environmental Analyst",
                    "affiliation": "Cairo Institute of Technology",
                    "country": "Egypt",
                    "photo_url": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=400&auto=format&fit=crop&q=60"
                },
            ]
            coll.insert_many(members)

        # Seed Issues and Articles
        articles_coll = collection("article")
        issues_coll = collection("issue")
        if articles_coll is not None and issues_coll is not None:
            if issues_coll.count_documents({}) == 0:
                issues = [
                    {"year": 2025, "volume": 23, "issue": 1, "title": "Volume 23, Issue 1 (2025)"},
                    {"year": 2025, "volume": 23, "issue": 2, "title": "Volume 23, Issue 2 (2025)"},
                ]
                issues_coll.insert_many(issues)

            if articles_coll.count_documents({}) == 0:
                base_articles = []
                for issue_num in [1, 2]:
                    for i in range(1, 6):
                        slug = f"sustainable-farming-{issue_num}-{i}"
                        base_articles.append({
                            "title": f"Sustainable Farming Practices {issue_num}.{i} for Climate Resilience",
                            "slug": slug,
                            "authors": [
                                {"name": "R. Gupta", "affiliation": "AgriTech Lab, Delhi", "country": "India"},
                                {"name": "S. Miller", "affiliation": "GreenFields Institute", "country": "USA"}
                            ],
                            "affiliations": ["AgriTech Lab, Delhi", "GreenFields Institute"],
                            "abstract": "This study evaluates sustainable agricultural techniques improving yield while reducing environmental impact.",
                            "keywords": ["sustainability", "agriculture", "climate", "soil"],
                            "doi": None,
                            "pdf_url": None,
                            "year": 2025,
                            "volume": 23,
                            "issue": issue_num,
                            "sections": [
                                {"heading": "Introduction", "content": "Background, motivation, and objectives of the research."},
                                {"heading": "Materials and Methods", "content": "Experimental design and data collection methods."},
                                {"heading": "Results", "content": "Key findings with analysis and figures."},
                                {"heading": "Discussion", "content": "Interpretation of results and implications."},
                                {"heading": "Conclusion", "content": "Summary and future work."}
                            ],
                            "references": [
                                "Smith J. (2022). Advances in Agroecology. Journal of Green Science.",
                                "Lee K. (2021). Climate-smart Agriculture: A Review."
                            ],
                            "citation_formats": {
                                "apa": f"Gupta, R., & Miller, S. (2025). Sustainable Farming Practices {issue_num}.{i} for Climate Resilience. E-Planet Journal, 23({issue_num}).",
                                "mla": f"Gupta, R., and S. Miller. 'Sustainable Farming Practices {issue_num}.{i} for Climate Resilience.' E-Planet Journal 23.{issue_num} (2025).",
                                "chicago": f"Gupta, R., and S. Miller. 2025. 'Sustainable Farming Practices {issue_num}.{i} for Climate Resilience.' E-Planet Journal 23, no. {issue_num}."
                            },
                            "cover_image": "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?w=1200&auto=format&fit=crop&q=60"
                        })
                articles_coll.insert_many(base_articles)
    except Exception:
        # If seeding fails (e.g., DB not configured), we silently ignore.
        pass


seed_if_needed()


# ----------------------
# API Schemas (responses)
# ----------------------

class IssueResponse(BaseModel):
    year: int
    volume: int
    issue: int
    title: Optional[str] = None
    description: Optional[str] = None


class ArticleCard(BaseModel):
    title: str
    slug: str
    authors: List[str]
    doi: Optional[str] = None
    year: int
    volume: int
    issue: int


# ----------------------
# Routes
# ----------------------

@app.get("/")
def root():
    return {"name": "E-Planet Journal API", "status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/api/issues", response_model=List[IssueResponse])
def list_issues():
    try:
        issues = get_documents("issue")
        # Sort by year desc, issue desc
        issues_sorted = sorted(issues, key=lambda x: (x.get("year", 0), x.get("volume", 0), x.get("issue", 0)), reverse=True)
        return [IssueResponse(year=i.get("year"), volume=i.get("volume"), issue=i.get("issue"), title=i.get("title"), description=i.get("description")) for i in issues_sorted]
    except Exception:
        # Fallback demo data if DB not available
        return [
            IssueResponse(year=2025, volume=23, issue=2, title="Volume 23, Issue 2 (2025)"),
            IssueResponse(year=2025, volume=23, issue=1, title="Volume 23, Issue 1 (2025)")
        ]


@app.get("/api/issues/{year}/{volume}/{issue}")
def get_issue(year: int, volume: int, issue: int):
    try:
        articles = get_documents("article", {"year": year, "volume": volume, "issue": issue})
        issue_info = {"year": year, "volume": volume, "issue": issue, "articles": []}
        for a in articles:
            issue_info["articles"].append({
                "title": a.get("title"),
                "authors": ", ".join([auth.get("name") for auth in a.get("authors", [])]),
                "doi": a.get("doi"),
                "slug": a.get("slug"),
            })
        return issue_info
    except Exception:
        # Fallback structure
        return {
            "year": year, "volume": volume, "issue": issue,
            "articles": [
                {"title": "Demo Article 1", "authors": "A. Author, B. Author", "doi": None, "slug": "demo-article-1"},
                {"title": "Demo Article 2", "authors": "C. Researcher", "doi": None, "slug": "demo-article-2"},
            ]
        }


@app.get("/api/articles", response_model=List[ArticleCard])
def list_articles(year: Optional[int] = None, volume: Optional[int] = None, issue: Optional[int] = None):
    filt = {}
    if year is not None:
        filt["year"] = year
    if volume is not None:
        filt["volume"] = volume
    if issue is not None:
        filt["issue"] = issue
    try:
        articles = get_documents("article", filt)
        cards = []
        for a in articles:
            cards.append(ArticleCard(
                title=a.get("title"),
                slug=a.get("slug"),
                authors=[auth.get("name") for auth in a.get("authors", [])],
                doi=a.get("doi"),
                year=a.get("year"),
                volume=a.get("volume"),
                issue=a.get("issue"),
            ))
        # Newest first
        cards.sort(key=lambda x: (x.year, x.volume, x.issue), reverse=True)
        return cards
    except Exception:
        return [
            ArticleCard(title="Demo Article", slug="demo-article", authors=["A. Author"], doi=None, year=2025, volume=23, issue=1)
        ]


@app.get("/api/articles/{slug}")
def get_article(slug: str):
    try:
        coll = collection("article")
        if coll is None:
            raise Exception("No DB")
        a = coll.find_one({"slug": slug})
        if not a:
            raise HTTPException(status_code=404, detail="Article not found")
        a["_id"] = str(a.get("_id"))
        return a
    except HTTPException:
        raise
    except Exception:
        # Fallback demo article
        return {
            "title": "Demo Article Title",
            "slug": slug,
            "authors": [{"name": "A. Author", "affiliation": "Demo University", "country": "USA"}],
            "affiliations": ["Demo University"],
            "abstract": "This is a demonstration abstract for the E-Planet Journal article page.",
            "keywords": ["demo", "journal"],
            "doi": None,
            "pdf_url": None,
            "year": 2025,
            "volume": 23,
            "issue": 1,
            "sections": [
                {"heading": "Introduction", "content": "Intro content."},
                {"heading": "Methods", "content": "Methods content."},
                {"heading": "Results", "content": "Results content."},
                {"heading": "Discussion", "content": "Discussion content."},
                {"heading": "Conclusion", "content": "Conclusion content."}
            ],
            "references": ["Reference 1", "Reference 2"],
            "citation_formats": {
                "apa": "Author, A. (2025). Demo Article Title. E-Planet Journal, 23(1).",
                "mla": "Author, A. 'Demo Article Title.' E-Planet Journal 23.1 (2025).",
                "chicago": "Author, A. 2025. 'Demo Article Title.' E-Planet Journal 23, no. 1."
            },
            "cover_image": "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?w=1200&auto=format&fit=crop&q=60"
        }


@app.get("/api/editorial-board")
def editorial_board():
    try:
        return get_documents("editorialmember")
    except Exception:
        return [
            {"role": "Chief Editor", "name": "Prof. A. K. Sharma", "designation": "Professor", "affiliation": "Green Earth University", "country": "India"}
        ]


@app.get("/api/guidelines")
def guidelines():
    return {
        "author_guidelines": [
            "Manuscripts must be original and not under consideration elsewhere.",
            "Follow IMRAD structure: Introduction, Methods, Results, and Discussion.",
            "Maximum 6000 words, 6 figures, and 40 references for research articles.",
            "Use APA style for citations and references.",
            "Include ORCID IDs where available."
        ],
        "publication_ethics": [
            "We follow COPE guidelines for publication ethics.",
            "All submissions are screened for plagiarism using standard tools.",
            "Conflicts of interest must be declared by all authors."
        ],
        "peer_review_process": "Double-blind peer review with at least two independent reviewers.",
        "formatting_template_url": "#",
        "submission_email": "submit@e-planetjournal.org"
    }


@app.get("/api/about")
def about():
    return {
        "name": "E-Planet: An International Journal of Environmental & Agricultural Research",
        "issn_online": "XXXX-XXXX",
        "issn_print": "XXXX-XXXX",
        "naas_rating": 4.73,
        "mission": "To publish high-quality research in environmental and agricultural sciences that advances knowledge and informs practice.",
        "scope": [
            "Sustainable agriculture and agroecology",
            "Climate change impact and adaptation",
            "Soil science and water resource management",
            "Biodiversity and ecosystem services",
            "Environmental policy and governance"
        ],
        "frequency": "Quarterly",
        "indexing": ["Google Scholar", "CrossRef", "Directory of Open Access Journals (DOAJ) - placeholder"],
        "timeline": "Average time to first decision: 4-6 weeks. Online-first publication upon acceptance.",
        "contact": {
            "email": "info@e-planetjournal.org",
            "address": "E-Planet Journal Editorial Office, 123 Green Avenue, New Delhi, India",
        }
    }


@app.post("/api/submit")
def submit_paper(payload: SubmissionSchema):
    try:
        doc_id = create_document("submission", payload)
        return {"status": "received", "id": doc_id}
    except Exception:
        return {"status": "received", "id": None}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
