from uuid import uuid4
from contextlib import asynccontextmanager
from collections import defaultdict

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    WebSocket
)

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import (
    init_db,
    create_user,
    get_user_by_email,
    save_analysis,
    get_history
)

from auth import (
    hash_password,
    verify_password,
    create_token,
    get_current_user
)

from azure_scanner import (
    get_resource_groups,
    scan_resource_group
)

from ai_analyzer import (
    analyze_resources
)


@asynccontextmanager
async def lifespan(app):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connections = defaultdict(list)


class ConnectionManager:
    async def connect(
        self,
        websocket,
        analysis_id
    ):
        await websocket.accept()
        connections[
            analysis_id
        ].append(websocket)

    def disconnect(
        self,
        websocket,
        analysis_id
    ):
        if websocket in connections[
            analysis_id
        ]:
            connections[
                analysis_id
            ].remove(websocket)

    async def send(
        self,
        analysis_id,
        message
    ):
        for ws in connections[
            analysis_id
        ]:
            try:
                await ws.send_json(
                    {"message": message}
                )
            except:
                pass


manager = ConnectionManager()


class AuthRequest(BaseModel):
    email: str
    password: str


class AnalyzeRequest(BaseModel):
    analysis_id: str
    resource_group: str


@app.post("/api/auth/signup")
async def signup(data: AuthRequest):
    user = await get_user_by_email(
        data.email
    )

    if user:
        raise HTTPException(
            400,
            "Email already exists"
        )

    user_id = await create_user(
        data.email,
        hash_password(
            data.password
        )
    )

    return {
        "token":
            create_token(user_id)
    }


@app.post("/api/auth/login")
async def login(data: AuthRequest):
    user = await get_user_by_email(
        data.email
    )

    if not user:
        raise HTTPException(
            401,
            "Invalid credentials"
        )

    if not verify_password(
        data.password,
        user["password_hash"]
    ):
        raise HTTPException(
            401,
            "Invalid credentials"
        )

    return {
        "token":
            create_token(
                user["id"]
            )
    }


@app.get(
    "/api/resource-groups"
)
async def resource_groups(
    user_id=Depends(
        get_current_user
    )
):
    return {
        "success": True,
        "resource_groups":
            get_resource_groups()
    }


@app.post(
    "/api/analyze/start"
)
async def start_analysis(
    user_id=Depends(
        get_current_user
    )
):
    return {
        "analysis_id":
            str(uuid4())
    }


@app.websocket(
    "/ws/progress/{analysis_id}"
)
async def ws_progress(
    websocket: WebSocket,
    analysis_id: str
):
    await manager.connect(
        websocket,
        analysis_id
    )

    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect(
            websocket,
            analysis_id
        )


@app.post("/api/analyze")
async def analyze(
    payload: AnalyzeRequest,
    user_id=Depends(
        get_current_user
    )
):
    await manager.send(
        payload.analysis_id,
        "Scanning resources..."
    )

    resources = scan_resource_group(
        payload.resource_group
    )

    await manager.send(
        payload.analysis_id,
        "Analyzing costs with AI..."
    )

    analysis = await analyze_resources(
        resources
    )

    await manager.send(
        payload.analysis_id,
        "Saving analysis..."
    )

    await save_analysis(
        user_id=user_id,
        resource_group=
            payload.resource_group,
        resources_scanned=
            len(resources),
        issues_found=
            len(
                analysis["issues"]
            ),
        estimated_savings=
            analysis[
                "estimated_monthly_savings_usd"
            ],
        analysis_result=
            analysis
    )

    await manager.send(
        payload.analysis_id,
        "Analysis complete"
    )

    return {
        "success": True,
        "resource_count":
            len(resources),
        "resources":
            resources,
        "analysis":
            analysis
    }


@app.get("/api/history")
async def history(
    user_id=Depends(
        get_current_user
    )
):
    return {
        "success": True,
        "history":
            await get_history(
                user_id
            )
    }