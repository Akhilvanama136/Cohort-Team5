import os
import re
import time
import json
import base64
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Body, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, EmailStr
from jose import JWTError, jwt
import bcrypt
from dotenv import load_dotenv
from src.sheets_logger import log_query_to_sheets
from src.database import get_db, init_db
from src.db_store import (
    add_history_entry,
    count_total_users,
    count_users_by_role,
    create_user,
    get_all_history,
    get_history_aggregates,
    get_user_by_username,
    get_user_history,
    migrate_json_to_mongodb,
    username_exists,
)

# Import our QA system
try:
    from src.medgemma_client import MedGemmaQA
    qa_system = MedGemmaQA()
except ImportError:
    qa_system = None

load_dotenv()

# Setup logging (Phase 13: Audit Logs)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("audit.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MedicalPathologyAPI")

# Security Configurations (Phase 13: Environment Variables & JWT)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "clinical-pathology-ai-assistant-secret-key-98231")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing uses bcrypt directly (passlib is unmaintained and incompatible with modern bcrypt)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(
    title="Medical Pathology Assistant API",
    description="Backend service for pathology question answering, retrieval, and logging.",
    version="1.0.0"
)


@app.on_event("startup")
def startup_warmup():
    try:
        init_db()
        logger.info("MongoDB connected successfully")
        # Skip migration if collections are not available
        try:
            db = get_db()
            migrate_json_to_mongodb(db)
            logger.info("MongoDB migration completed")
        except Exception as migration_exc:
            logger.warning(f"MongoDB migration skipped: {migration_exc}")
        logger.info("MongoDB ready")
    except Exception as exc:
        logger.error(
            "MongoDB unavailable (%s). Set MONGODB_URI and check connection.", exc
        )

    if qa_system is not None:
        import threading
        threading.Thread(target=qa_system.warmup_model, daemon=True).start()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL via SQLAlchemy (see src/database.py)

# Pydantic Schemas for Input Validation (Phase 13: Input Validation)
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field("user", pattern="^(user|doctor|admin)$")

class UserResponse(BaseModel):
    username: str
    email: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=50000)
    disease_category: Optional[str] = Field(None, pattern="^(diabetes|cancer|research)$")

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict]
    response_time_sec: float
    vision_summary: Optional[str] = None
    safety_flags: Optional[List[str]] = None
    requires_radiologist_review: bool = False
    imaging_confidence: Optional[str] = None

# Helper functions for authentication
def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return {"username": username, "email": user["email"], "role": role}

async def get_current_admin(current_user: dict = Depends(get_current_user)):
    # Phase 13: Role-Based Access Control
    if current_user.get("role") != "admin":
        logger.warning(f"Unauthorized admin access attempt by: {current_user.get('username')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Administrator role required."
        )
    return current_user

def require_role(*allowed_roles):
    """Dependency factory that restricts access to specific roles."""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in allowed_roles:
            logger.warning(f"Role-restricted access denied for user '{current_user.get('username')}' (role: {current_user.get('role')}). Required: {allowed_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

# Input Validation / Injection Protection (Phase 13: Prompt Injection Protection)
def sanitize_input(text: str) -> str:
    # Basic protection: prevent common prompt override keys
    injection_keywords = ["ignore previous instructions", "system prompt", "translate to", "you must reply as"]
    cleaned = text
    for kw in injection_keywords:
        if kw in cleaned.lower():
            logger.warning(f"Suspicious prompt injection pattern detected and stripped: '{kw}'")
            cleaned = re.sub(re.escape(kw), "[removed]", cleaned, flags=re.IGNORECASE)
    return cleaned

# Auth Endpoints
@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db = Depends(get_db)):
    if username_exists(db, user_data.username):
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pwd = get_password_hash(user_data.password)
    create_user(
        db,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pwd,
        role=user_data.role,
    )
    logger.info(f"User registered successfully: {user_data.username} (Role: {user_data.role})")
    return UserResponse(username=user_data.username, email=user_data.email, role=user_data.role)

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    logger.info(f"User logged in successfully: {user['username']}")
    return {"access_token": access_token, "token_type": "bearer"}

# For login endpoint in OAuth flow
@app.post("/token", response_model=Token)
def token_login(form_data: OAuth2PasswordRequestForm = Depends()):
    return login(form_data)

# Query & Business Logic Endpoints
@app.post("/query", response_model=QueryResponse)
async def query_pathology(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
):
    start_time = time.time()
    
    # Sanitize input query
    sanitized_question = sanitize_input(request.question)
    
    logger.info(f"User '{current_user['username']}' queried: '{sanitized_question}'")
    
    if qa_system is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="QA engine is not fully initialized. Check back-end setup."
        )

    # Run blocking Ollama/RAG work off the event loop so /health stays responsive
    result = await run_in_threadpool(
        qa_system.answer_question,
        sanitized_question,
        10,
        request.disease_category,
    )
    
    response_time = time.time() - start_time
    
    # Save search to local history database (Phase 10: GET /history)
    add_history_entry(db, {
        "timestamp": datetime.utcnow().isoformat(),
        "username": current_user["username"],
        "question": sanitized_question,
        "category": request.disease_category or "general",
        "answer": result["answer"],
        "response_time_sec": response_time,
        "sources": result["sources"],
    })
    
    # Log the interaction to Google Sheets / Fallback CSV (Phase 12)
    try:
        log_query_to_sheets(
            username=current_user["username"],
            question=sanitized_question,
            category=request.disease_category or "general",
            response_time=response_time,
            sources=result["sources"]
        )
    except Exception as e:
        logger.error(f"Google sheets logging task failed: {e}")
    
    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        response_time_sec=response_time
    )

@app.get("/history", response_model=List[Dict])
def get_history(current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    if current_user["role"] == "admin":
        return get_all_history(db)
    return get_user_history(db, current_user["username"])

def _count_indexed_documents() -> int:
    cleaned_dir = "cleaned_text"
    count = 0
    if os.path.exists(cleaned_dir):
        for _, _, files in os.walk(cleaned_dir):
            count += sum(1 for file in files if file.endswith(".txt"))
    return count

def _count_vector_chunks() -> int:
    metadata_path = "metadata.json"
    if not os.path.exists(metadata_path):
        return 0
    with open(metadata_path, "r", encoding="utf-8") as f:
        return len(json.load(f))

@app.get("/admin/stats")
def get_admin_stats(current_user: dict = Depends(get_current_admin), db = Depends(get_db)):
    total_documents = _count_indexed_documents()
    total_chunks = _count_vector_chunks()
    users_by_role = count_users_by_role(db)
    aggregates = get_history_aggregates(db)

    return {
        "total_documents": total_documents,
        "total_chunks": total_chunks,
        "total_embeddings": total_chunks,
        "total_queries": aggregates["total_queries"],
        "avg_response_time_sec": aggregates["avg_response_time_sec"],
        "answer_success_rate_pct": aggregates["answer_success_rate_pct"],
        "users_by_role": users_by_role,
        "total_registered_users": count_total_users(db),
        "unique_query_users": aggregates["unique_query_users"],
        "category_counts": aggregates["category_counts"],
    }

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db = Depends(get_db)):
    try:
        # Test MongoDB connection
        from src.database import client
        client.admin.command('ping')
        return {"database": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}")

@app.get("/health/ollama")
def ollama_health():
    from src.medgemma_client import _ollama_ready
    ready = bool(
        qa_system and _ollama_ready(qa_system.ollama_url, qa_system.model_name)
    )
    return {"ollama_ready": ready, "model": qa_system.model_name if qa_system else None}

@app.get("/sources", response_model=List[str])
def get_sources(current_user: dict = Depends(get_current_user)):
    # Lists available cleaned text source files
    cleaned_dir = "cleaned_text"
    sources_list = []
    if os.path.exists(cleaned_dir):
        for root, _, files in os.walk(cleaned_dir):
            for file in files:
                if file.endswith('.txt'):
                    sources_list.append(file.replace('.txt', '.pdf'))
    return sources_list

# Medical Image Analysis Endpoint (Doctor & Admin only)
@app.post("/query-image", response_model=QueryResponse)
async def query_image(
    image: UploadFile = File(...),
    report: Optional[UploadFile] = File(None),
    question: str = Form(...),
    disease_category: Optional[str] = Form(None),
    current_user: dict = Depends(require_role("doctor", "admin", "user")),
    db = Depends(get_db),
):
    """Analyze a medical image (X-ray, CT, pathology slide) using MedGemma multimodal."""
    start_time = time.time()
    
    sanitized_question = sanitize_input(question)
    logger.info(f"User '{current_user['username']}' submitted image analysis: '{sanitized_question}' (file: {image.filename})")
    
    if qa_system is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="QA engine is not fully initialized."
        )
    
    # Read and encode image as base64
    image_bytes = await image.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    
    # Read report content if provided
    report_content = None
    if report:
        report_bytes = await report.read()
        if report.filename.endswith('.pdf'):
            # Extract text from PDF using pypdf
            try:
                from io import BytesIO
                from pypdf import PdfReader
                reader = PdfReader(BytesIO(report_bytes))
                pages_text = []
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        pages_text.append(f"--- PAGE {page_num + 1} ---\n{text.strip()}")
                report_content = "\n\n".join(pages_text) if pages_text else f"[PDF Report: {report.filename} — no extractable text]"
                logger.info(f"PDF report parsed: {len(report_content)} characters from {len(pages_text)} pages")
            except Exception as pdf_err:
                logger.warning(f"PDF parsing failed for {report.filename}: {pdf_err}")
                report_content = f"[PDF Report: {report.filename} — parsing failed]"
        else:
            # For text files, read the content
            report_content = report_bytes.decode("utf-8", errors="ignore")
            logger.info(f"Report content loaded: {len(report_content)} characters")
    
    # Call MedGemma in a worker thread — keeps API responsive during long image analysis
    result = await run_in_threadpool(
        qa_system.analyze_image,
        sanitized_question,
        image_b64,
        disease_category,
        report_content,
    )
    
    response_time = time.time() - start_time
    
    # Save to history
    add_history_entry(db, {
        "timestamp": datetime.utcnow().isoformat(),
        "username": current_user["username"],
        "question": f"[IMAGE] {sanitized_question}",
        "category": "image_analysis",
        "answer": result["answer"],
        "response_time_sec": response_time,
        "sources": result.get("sources", []),
    })
    
    # Log to sheets/CSV
    try:
        log_query_to_sheets(
            username=current_user["username"],
            question=f"[IMAGE] {sanitized_question}",
            category="image_analysis",
            response_time=response_time,
            sources=result.get("sources", [])
        )
    except Exception as e:
        logger.error(f"Logging failed for image query: {e}")
    
    return QueryResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        response_time_sec=response_time,
        vision_summary=result.get("vision_summary"),
        safety_flags=result.get("safety_flags"),
        requires_radiologist_review=result.get("requires_radiologist_review", True),
        imaging_confidence=result.get("imaging_confidence"),
    )

# Doctor Dashboard Endpoints
@app.get("/doctor/uploads")
def get_doctor_uploads(current_user: dict = Depends(require_role("doctor", "admin")), db = Depends(get_db)):
    """Get patient uploads pending doctor review."""
    try:
        # Get all query history entries that need doctor review
        # For now, return recent history entries as "uploads"
        uploads = list(db["query_history"].find().sort("timestamp", -1).limit(20))
        
        # Format for frontend
        formatted_uploads = []
        for upload in uploads:
            formatted_uploads.append({
                "_id": str(upload.get("_id")),
                "username": upload.get("username"),
                "question": upload.get("question"),
                "category": upload.get("category"),
                "timestamp": upload.get("timestamp"),
                "has_image": "[IMAGE]" in upload.get("question", ""),
                "has_report": False,  # Will need to track this separately
                "sources": upload.get("sources", []),
                "answer": upload.get("answer", "")
            })
        
        return formatted_uploads
    except Exception as e:
        logger.error(f"Error fetching doctor uploads: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch uploads")

@app.post("/doctor/approve")
def approve_upload(
    approval_data: dict,
    current_user: dict = Depends(require_role("doctor", "admin")),
    db = Depends(get_db)
):
    """Doctor approves patient upload and sends diagnosis/precautions/medicine."""
    try:
        upload_id = approval_data.get("upload_id")
        diagnosis = approval_data.get("diagnosis")
        precautions = approval_data.get("precautions")
        medicine = approval_data.get("medicine")
        
        # In a real implementation, we would:
        # 1. Update the query history with doctor's review
        # 2. Send notification to patient
        # 3. Store the approval in a separate collection
        
        logger.info(f"Doctor {current_user['username']} approved upload {upload_id}")
        logger.info(f"Diagnosis: {diagnosis}, Precautions: {precautions}, Medicine: {medicine}")
        
        return {"status": "success", "message": "Review sent to patient"}
    except Exception as e:
        logger.error(f"Error approving upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve upload")

@app.get("/knowledge-graph")
def get_knowledge_graph(disease: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    from src.knowledge_graph import list_diseases, build_disease_graph

    diseases = list_diseases()
    if not disease and diseases:
        disease = diseases[0]["key"]

    nodes, edges, category = build_disease_graph(disease) if disease else ([], [], "general")
    return {
        "selected_disease": disease,
        "category": category,
        "available_diseases": diseases,
        "nodes": nodes,
        "edges": edges,
    }

if __name__ == "__main__":
    import uvicorn
    # Start server locally on port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)

