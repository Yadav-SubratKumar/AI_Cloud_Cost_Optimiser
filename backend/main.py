import hashlib
import os
import secrets
import smtplib
from email.message import EmailMessage
from uuid import uuid4
from contextlib import asynccontextmanager
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from io import BytesIO

from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from db import (
    init_db,
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_role,
    save_password_reset_token,
    get_valid_password_reset_token,
    consume_password_reset_token,
    update_password,
    save_analysis,
    get_history,
    get_analysis,
)
from auth import (
    hash_password,
    verify_password,
    create_token,
    get_current_user,
    get_current_role,
)
from azure_scanner import get_resource_groups, scan_resource_group
from ai_analyzer import analyze_resources

load_dotenv()

ROLES = {
    "cloud_admin": "Cloud Administrator",
    "finance_manager": "Finance Manager",
    "it_manager": "IT Manager",
    "executive": "CTO/CIO",
}


def role_name(role: str) -> str:
    return ROLES.get(role, role)


def require_roles(*allowed_roles):
    def dependency(role=Depends(get_current_role)):
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="You do not have permission for this action")
        return role
    return dependency


@asynccontextmanager
async def lifespan(app):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connections = defaultdict(list)


class ConnectionManager:
    async def connect(self, websocket, analysis_id):
        await websocket.accept()
        connections[analysis_id].append(websocket)

    def disconnect(self, websocket, analysis_id):
        if websocket in connections[analysis_id]:
            connections[analysis_id].remove(websocket)

    async def send(self, analysis_id, message):
        for ws in connections[analysis_id]:
            try:
                await ws.send_json({"message": message})
            except Exception:
                pass


manager = ConnectionManager()


class AuthRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class SignupRequest(AuthRequest):
    role: str = "finance_manager"


class LoginRequest(AuthRequest):
    remember_me: bool = False


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)


class RoleUpdateRequest(BaseModel):
    role: str


class AnalyzeRequest(BaseModel):
    analysis_id: str
    resource_group: str


@app.post("/api/auth/signup")
async def signup(data: SignupRequest):
    email = data.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "Enter a valid email address")
    if data.role not in ROLES:
        raise HTTPException(400, "Please select a valid role")
    if len(data.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")

    user = await get_user_by_email(email)
    if user:
        raise HTTPException(400, "An account with this email already exists")

    user_id = await create_user(email, hash_password(data.password), role=data.role)
    return {
        "token": create_token(user_id, data.role, remember_me=False),
        "role": data.role,
        "role_name": role_name(data.role),
    }


@app.post("/api/auth/login")
async def login(data: LoginRequest):
    email = data.email.strip().lower()
    user = await get_user_by_email(email)
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    return {
        "token": create_token(user["id"], user["role"], data.remember_me),
        "role": user["role"],
        "role_name": role_name(user["role"]),
    }


@app.get("/api/auth/me")
async def me(user_id=Depends(get_current_user)):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(401, "User no longer exists")
    return {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "role_name": role_name(user["role"]),
    }


@app.post("/api/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    # Always return the same response to avoid account enumeration.
    generic = {"message": "If an account exists for that email, a password reset link has been generated."}
    user = await get_user_by_email(data.email.lower())
    if not user:
        return generic

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    await save_password_reset_token(user["id"], token_hash, expires_at.strftime("%Y-%m-%d %H:%M:%S"))

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    reset_url = f"{frontend_url}/reset-password?token={raw_token}"

    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM") or smtp_user

    if smtp_host and smtp_user and smtp_password and smtp_from:
        msg = EmailMessage()
        msg["Subject"] = "AI Cloud Cost Optimiser - Password Reset"
        msg["From"] = smtp_from
        msg["To"] = user["email"]
        msg.set_content(
            "A password reset was requested for your account.\n\n"
            f"Reset your password using this link (valid for 30 minutes):\n{reset_url}\n\n"
            "If you did not request this, you can ignore this email."
        )
        try:
            with smtplib.SMTP(smtp_host, int(os.getenv("SMTP_PORT", "587")), timeout=15) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        except Exception:
            # Do not reveal email delivery details to the client.
            pass
    elif os.getenv("PASSWORD_RESET_DEV_MODE", "false").lower() == "true":
        # Local/demo convenience when SMTP is intentionally not configured.
        return {**generic, "dev_reset_url": reset_url}

    return generic


@app.post("/api/auth/reset-password")
async def reset_password(data: ResetPasswordRequest):
    token_hash = hashlib.sha256(data.token.encode()).hexdigest()
    reset = await get_valid_password_reset_token(token_hash)
    if not reset:
        raise HTTPException(400, "Reset link is invalid or has expired")

    await update_password(reset["user_id"], hash_password(data.password))
    await consume_password_reset_token(reset["id"])
    return {"message": "Password reset successfully. You can now log in."}


@app.patch("/api/users/{target_user_id}/role")
async def change_role(
    target_user_id: int,
    data: RoleUpdateRequest,
    current_user_id=Depends(get_current_user),
    current_role=Depends(require_roles("cloud_admin")),
):
    if data.role not in ROLES:
        raise HTTPException(400, "Invalid role")
    target = await get_user_by_id(target_user_id)
    if not target:
        raise HTTPException(404, "User not found")
    await update_user_role(target_user_id, data.role)
    return {"success": True, "user_id": target_user_id, "role": data.role, "role_name": role_name(data.role)}


@app.get("/api/resource-groups")
async def resource_groups(
    user_id=Depends(get_current_user),
    role=Depends(require_roles("cloud_admin", "it_manager")),
):
    return {"success": True, "resource_groups": get_resource_groups()}


@app.post("/api/analyze/start")
async def start_analysis(
    user_id=Depends(get_current_user),
    role=Depends(require_roles("cloud_admin", "it_manager")),
):
    return {"analysis_id": str(uuid4())}


@app.websocket("/ws/progress/{analysis_id}")
async def ws_progress(websocket: WebSocket, analysis_id: str):
    await manager.connect(websocket, analysis_id)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket, analysis_id)


@app.post("/api/analyze")
async def analyze(
    payload: AnalyzeRequest,
    user_id=Depends(get_current_user),
    role=Depends(require_roles("cloud_admin", "it_manager")),
):
    await manager.send(payload.analysis_id, "Scanning resources...")
    resources = scan_resource_group(payload.resource_group)
    await manager.send(payload.analysis_id, "Analyzing costs with AI...")
    analysis = await analyze_resources(resources)
    await manager.send(payload.analysis_id, "Saving analysis...")

    saved_id = await save_analysis(
        user_id=user_id,
        resource_group=payload.resource_group,
        resources_scanned=len(resources),
        issues_found=len(analysis["issues"]),
        estimated_savings=analysis["estimated_monthly_savings_usd"],
        analysis_result=analysis,
    )
    await manager.send(payload.analysis_id, "Analysis complete")

    return {
        "success": True,
        "analysis_id": saved_id,
        "resource_count": len(resources),
        "resources": resources,
        "analysis": analysis,
    }


@app.get("/api/history")
async def history(
    user_id=Depends(get_current_user),
    role=Depends(require_roles("cloud_admin", "finance_manager", "it_manager", "executive")),
):
    # Finance Managers need organisation-wide visibility for financial review;
    # other roles see only analyses they created.
    include_all = role == "finance_manager"
    return {"success": True, "history": await get_history(user_id, include_all=include_all)}


@app.get("/api/reports/{analysis_id}/pdf")
async def pdf_report(
    analysis_id: int,
    user_id=Depends(get_current_user),
    role=Depends(require_roles("cloud_admin", "finance_manager", "it_manager", "executive")),
):
    # Finance Managers may export reports for any analysis they can review.
    include_all = role == "finance_manager"
    record = await get_analysis(user_id, analysis_id, include_all=include_all)
    if not record:
        raise HTTPException(404, "Analysis not found")

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib import colors
    except ImportError:
        raise HTTPException(500, "PDF support is not installed. Run pip install -r requirements.txt")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=18)
    story = [
        Paragraph("AI Cloud Cost Optimiser", title_style),
        Paragraph("Cloud Cost Analysis Report", styles["Heading2"]),
        Spacer(1, 8),
        Paragraph(f"Resource Group: {record['resource_group']}", styles["BodyText"]),
        Paragraph(f"Generated: {record['created_at']}", styles["BodyText"]),
        Paragraph(f"Resources Scanned: {record['resources_scanned']}", styles["BodyText"]),
        Paragraph(f"Issues Found: {record['issues_found']}", styles["BodyText"]),
        Paragraph(f"Estimated Monthly Savings: ${record['estimated_savings']}", styles["BodyText"]),
        Spacer(1, 18),
        Paragraph("Recommendations", styles["Heading2"]),
    ]

    issues = (record.get("analysis_result") or {}).get("issues", [])
    table_data = [["Severity", "Issue", "Resource", "Estimated Savings"]]
    for issue in issues:
        table_data.append([
            str(issue.get("severity", "")).title(),
            str(issue.get("title", "")),
            str(issue.get("resource_name", "")),
            f"${issue.get('estimated_monthly_savings_usd', issue.get('estimated_savings_usd', 0))}",
        ])

    if len(table_data) == 1:
        story.append(Paragraph("No recommendations were returned for this analysis.", styles["BodyText"]))
    else:
        table = Table(table_data, repeatRows=1, colWidths=[65, 175, 125, 85])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#27272a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f4f5")]),
        ]))
        story.append(table)

    story.extend([Spacer(1, 18), Paragraph("Note: This report contains recommendations generated from the stored analysis result. Applying Azure changes remains a user-controlled action.", styles["Italic"])])
    doc.build(story)
    buffer.seek(0)

    filename = f"cloud-cost-analysis-{analysis_id}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
