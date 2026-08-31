"""
Main entry point.
This file only handles wiring: registers routers and translates
Domain Exceptions to the appropriate HTTP status codes. No business logic here.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app import models  # noqa: F401  - to register all models on Base.metadata
from app.core.exceptions import (
    NotFoundError, DuplicateError, BusinessRuleError,
    AuthenticationError, PermissionDeniedError,
)
from app.api.routers import auth, catalog, books, members, borrowing, reservations, test_results
from fastapi.staticfiles import StaticFiles
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Library Management System",
    description="Library management system with layered architecture and authentication",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(books.router)
app.include_router(members.router)
app.include_router(borrowing.router)
app.include_router(reservations.router)
app.include_router(test_results.router)

# Mount test reports as static files
_reports_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "reports")
os.makedirs(_reports_dir, exist_ok=True)
app.mount("/static/reports", StaticFiles(directory=_reports_dir), name="test-reports")


@app.get("/")
def root():
    return {"message": "Library Management System API", "docs": "/docs"}


# ---------- Translate Domain Exceptions to HTTP responses ----------
@app.exception_handler(NotFoundError)
def handle_not_found(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DuplicateError)
def handle_duplicate(request: Request, exc: DuplicateError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(BusinessRuleError)
def handle_business_rule(request: Request, exc: BusinessRuleError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(AuthenticationError)
def handle_auth_error(request: Request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(PermissionDeniedError)
def handle_permission_denied(request: Request, exc: PermissionDeniedError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})
