"""
Job Application Tracker - FastAPI Application (Advanced)
"""

from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
import csv
import io

from .database import engine, get_db, Base
from .models import JobApplication

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(title="Job Application Tracker", version="2.0.0")

# Mount static files and templates using absolute paths
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ============================================
# WEB ROUTES
# ============================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    view: str = "table",
    search: str = "",
    status_filter: str = "all",
    db: Session = Depends(get_db),
):
    """Main dashboard with stats, charts, and applications."""

    # Base query
    query = db.query(JobApplication)

    # Search filter
    if search:
        query = query.filter(
            (JobApplication.company.ilike(f"%{search}%")) |
            (JobApplication.role.ilike(f"%{search}%")) |
            (JobApplication.location.ilike(f"%{search}%"))
        )

    # Status filter
    interview_statuses = ["Phone Screen", "Technical Interview", "Final Interview"]
    if status_filter and status_filter != "all":
        if status_filter == "interviewing":
            query = query.filter(JobApplication.status.in_(interview_statuses))
        elif status_filter == "Saved":
            query = query.filter(JobApplication.status == "Saved")
        else:
            query = query.filter(JobApplication.status == status_filter)

    applications = query.order_by(JobApplication.updated_date.desc()).all()

    # Get ALL applications for stats (unfiltered)
    all_apps = db.query(JobApplication).all()
    total = len(all_apps)

    stats = {
        "total": total,
        "saved": sum(1 for a in all_apps if a.status == "Saved"),
        "applied": sum(1 for a in all_apps if a.status == "Applied"),
        "interviewing": sum(1 for a in all_apps if a.status in interview_statuses),
        "offers": sum(1 for a in all_apps if a.status in ["Offer Received", "Accepted"]),
        "rejected": sum(1 for a in all_apps if a.status == "Rejected"),
        "withdrawn": sum(1 for a in all_apps if a.status == "Withdrawn"),
    }

    responded = stats["interviewing"] + stats["offers"] + stats["rejected"]
    stats["response_rate"] = round((responded / total * 100) if total > 0 else 0)

    # Status breakdown for chart
    status_counts = {}
    for s in JobApplication.STATUSES:
        count = sum(1 for a in all_apps if a.status == s)
        if count > 0:
            status_counts[s] = count

    # Weekly activity (last 8 weeks)
    weekly_activity = []
    for i in range(7, -1, -1):
        week_start = datetime.now() - timedelta(weeks=i+1)
        week_end = datetime.now() - timedelta(weeks=i)
        count = sum(1 for a in all_apps if a.applied_date and week_start <= a.applied_date.replace(tzinfo=None) < week_end)
        weekly_activity.append({
            "label": week_start.strftime("%b %d"),
            "count": count
        })

    # Upcoming interviews
    upcoming = [a for a in all_apps if a.interview_date and a.interview_date.replace(tzinfo=None) >= datetime.now() and a.status in interview_statuses]
    upcoming.sort(key=lambda a: a.interview_date)

    # Group by status for kanban
    kanban = {}
    for s in JobApplication.STATUSES:
        kanban[s] = [a for a in all_apps if a.status == s]

    return templates.TemplateResponse(request, "dashboard.html", {
        "applications": applications,
        "stats": stats,
        "status_counts": status_counts,
        "weekly_activity": weekly_activity,
        "upcoming": upcoming[:5],
        "kanban": kanban,
        "statuses": JobApplication.STATUSES,
        "job_types": JobApplication.JOB_TYPES,
        "priorities": JobApplication.PRIORITIES,
        "view": view,
        "search": search,
        "status_filter": status_filter,
    })


@app.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    return templates.TemplateResponse(request, "add.html", {
        "statuses": JobApplication.STATUSES,
        "job_types": JobApplication.JOB_TYPES,
        "priorities": JobApplication.PRIORITIES,
    })


@app.post("/add")
async def add_application(
    company: str = Form(...),
    role: str = Form(...),
    status: str = Form("Applied"),
    salary_min: Optional[float] = Form(None),
    salary_max: Optional[float] = Form(None),
    location: Optional[str] = Form(None),
    job_type: str = Form("Full-time"),
    url: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    contact_name: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    interview_date: Optional[str] = Form(None),
    priority: str = Form("Medium"),
    db: Session = Depends(get_db),
):
    parsed_interview = None
    if interview_date:
        try:
            parsed_interview = datetime.fromisoformat(interview_date)
        except ValueError:
            pass

    application = JobApplication(
        company=company, role=role, status=status,
        salary_min=salary_min if salary_min else None,
        salary_max=salary_max if salary_max else None,
        location=location if location else None,
        job_type=job_type,
        url=url if url else None,
        notes=notes if notes else None,
        contact_name=contact_name if contact_name else None,
        contact_email=contact_email if contact_email else None,
        interview_date=parsed_interview,
        priority=priority,
    )
    db.add(application)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/edit/{app_id}", response_class=HTMLResponse)
async def edit_form(app_id: int, request: Request, db: Session = Depends(get_db)):
    application = db.query(JobApplication).filter(JobApplication.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return templates.TemplateResponse(request, "edit.html", {
        "app": application,
        "statuses": JobApplication.STATUSES,
        "job_types": JobApplication.JOB_TYPES,
        "priorities": JobApplication.PRIORITIES,
    })


@app.post("/edit/{app_id}")
async def update_application(
    app_id: int,
    company: str = Form(...),
    role: str = Form(...),
    status: str = Form("Applied"),
    salary_min: Optional[float] = Form(None),
    salary_max: Optional[float] = Form(None),
    location: Optional[str] = Form(None),
    job_type: str = Form("Full-time"),
    url: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    contact_name: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    interview_date: Optional[str] = Form(None),
    priority: str = Form("Medium"),
    db: Session = Depends(get_db),
):
    application = db.query(JobApplication).filter(JobApplication.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    parsed_interview = None
    if interview_date:
        try:
            parsed_interview = datetime.fromisoformat(interview_date)
        except ValueError:
            pass

    application.company = company
    application.role = role
    application.status = status
    application.salary_min = salary_min if salary_min else None
    application.salary_max = salary_max if salary_max else None
    application.location = location if location else None
    application.job_type = job_type
    application.url = url if url else None
    application.notes = notes if notes else None
    application.contact_name = contact_name if contact_name else None
    application.contact_email = contact_email if contact_email else None
    application.interview_date = parsed_interview
    application.priority = priority

    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/delete/{app_id}")
async def delete_application(app_id: int, db: Session = Depends(get_db)):
    application = db.query(JobApplication).filter(JobApplication.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(application)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/update-status/{app_id}")
async def update_status(app_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    application = db.query(JobApplication).filter(JobApplication.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = status
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/export")
async def export_csv(db: Session = Depends(get_db)):
    """Export all applications as CSV."""
    applications = db.query(JobApplication).order_by(JobApplication.applied_date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Company", "Role", "Status", "Priority", "Location", "Job Type",
                      "Salary Min", "Salary Max", "URL", "Contact", "Contact Email",
                      "Interview Date", "Applied Date", "Notes"])

    for a in applications:
        writer.writerow([
            a.company, a.role, a.status, a.priority, a.location, a.job_type,
            a.salary_min, a.salary_max, a.url, a.contact_name, a.contact_email,
            str(a.interview_date) if a.interview_date else "",
            str(a.applied_date) if a.applied_date else "",
            a.notes
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=job_applications.csv"}
    )



# ============================================
# API ROUTES (JSON)
# ============================================

@app.get("/api/applications")
async def api_list(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(JobApplication)
    if status:
        query = query.filter(JobApplication.status == status)
    apps = query.order_by(JobApplication.updated_date.desc()).all()
    return [{
        "id": a.id, "company": a.company, "role": a.role, "status": a.status,
        "priority": a.priority, "salary_min": a.salary_min, "salary_max": a.salary_max,
        "location": a.location, "job_type": a.job_type, "url": a.url,
        "notes": a.notes, "contact_name": a.contact_name, "contact_email": a.contact_email,
        "interview_date": str(a.interview_date) if a.interview_date else None,
        "applied_date": str(a.applied_date) if a.applied_date else None,
    } for a in apps]


@app.get("/api/stats")
async def api_stats(db: Session = Depends(get_db)):
    apps = db.query(JobApplication).all()
    total = len(apps)
    return {
        "total": total,
        "by_status": {s: sum(1 for a in apps if a.status == s) for s in JobApplication.STATUSES},
        "by_type": {t: sum(1 for a in apps if a.job_type == t) for t in JobApplication.JOB_TYPES},
        "response_rate": round(sum(1 for a in apps if a.status != "Applied") / total * 100) if total > 0 else 0,
    }
