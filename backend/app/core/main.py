import os
import logging
import uvicorn
import re
import random
import string
import smtplib
import time
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import jwt
import bcrypt
import tempfile
import shutil
import warnings
import json
from openai import OpenAI
import openai

# Import professional log formatter
from app.core.log_formatter import LogFormatter, StructuredLogHandler, LogLevel

# Import custom RAG system
try:
    from app.services.custom_rag import CustomEmbedder, CustomRAGSystem, WebSearchTool
    # Temporarily disable reranker to avoid slow config saves (will lazy-load later)
    # from rerankers import Reranker
    CUSTOM_RAG_AVAILABLE = True
    RERANKER_AVAILABLE = False  # Disabled for now - causes slow config saves
except ImportError as e:
    CUSTOM_RAG_AVAILABLE = False
    RERANKER_AVAILABLE = False
    logging.warning(f"Custom RAG or Reranker not available: {e}")

# Sensitive services list for error sanitization
SENSITIVE_SERVICES = [
    'gemini', 'Gemini', 'GEMINI',
    'google', 'Google', 'GOOGLE',
    'jina', 'Jina', 'JINA',
    'voyage', 'Voyage', 'VOYAGE',
    'bge', 'BGE',
    'cohere', 'Cohere', 'COHERE',
    'openai', 'OpenAI', 'OPENAI',
    'anthropic', 'Anthropic', 'ANTHROPIC',
    'claude', 'Claude', 'CLAUDE'
]

def sanitize_error_message(error_msg: str) -> str:
    """Sanitize error messages to prevent sensitive information leakage"""
    if not error_msg:
        return "An internal error occurred. Please try again."

    error_lower = error_msg.lower()

    for service in SENSITIVE_SERVICES:
        if service.lower() in error_lower:
            return "An internal error occurred. Please try again."

    error_msg = re.sub(r'https?://[^\s]+', '[URL_REMOVED]', error_msg)
    error_msg = re.sub(r'api[_-]?key[=:]\s*\S+', '[API_KEY_REMOVED]', error_msg, flags=re.IGNORECASE)
    error_msg = re.sub(r'sk-[^\s]+', '[API_KEY_REMOVED]', error_msg)

    if len(error_msg) > 200 or any(keyword in error_lower for keyword in ['traceback', 'stack', 'exception', 'raise']):
        return "An internal error occurred. Please try again."

    return error_msg

class SanitizedLogFilter(logging.Filter):
    """Filter to sanitize log messages"""
    def filter(self, record):
        if hasattr(record, 'msg') and record.msg:
            record.msg = sanitize_error_message(str(record.msg))
        if hasattr(record, 'args') and record.args:
            record.args = tuple(sanitize_error_message(str(arg)) if isinstance(arg, str) else arg for arg in record.args)
        return True

# Configure professional structured logging
log_formatter = LogFormatter(use_colors=True, filter_sensitive=True)
structured_handler = StructuredLogHandler(log_formatter)
structured_handler.setLevel(logging.INFO)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[structured_handler],
    format='%(message)s'  # The StructuredLogHandler handles formatting
)

logger = logging.getLogger(__name__)

# Keep the sanitized log filter for additional security
log_filter = SanitizedLogFilter()
logger.addFilter(log_filter)

# Suppress verbose logging from external libraries
logging.getLogger("rerankers").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*torch.classes.*")
warnings.filterwarnings("ignore")

# Initialize FastAPI app
app = FastAPI(title="RAG Chat API", version="1.0.0")

# CORS middleware - Allow all origins for development
print("\n" + "="*60)
print("CONFIGURING CORS: allow_origins=['*']")
print("="*60 + "\n")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)
print("CORS middleware added successfully\n")

# Security
security = HTTPBearer()
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours for better UX

# RAG System Prompt
RAG_SYSTEM_PROMPT = """
你是一个专业且友好的知识助手，基于提供的上下文信息回答用户问题。

**核心要求：**
- 仅使用提供的上下文信息回答问题
- 绝不提及「上下文」、「文档」、「材料」等字眼，将信息视为你的记忆
- 回答必须完整、深入、有见解

**格式规范：**

1. **整体结构**
   - 采用分段式呈现，段落清晰，行间距适中
   - 先总述后分述，核心结论前置

2. **标题与列表**
   - 核心模块用三级标题（### 标题）标注
   - 步骤类内容用有序列表（1. 2. 3.）
   - 并列类内容用无序列表（- ）

3. **内容强调**
   - 关键术语用加粗（**内容**）突出
   - 单行代码用反引号 `代码` 包裹
   - 多行代码块用 ```语言类型 包裹

4. **分隔与过渡**
   - 不同模块间用「---」分隔
   - 示例用引用格式（> 内容）

5. **风格调性**
   - 语言正式且易懂，逻辑连贯
   - 技术类回复：先方案，再细节，后注意事项
   - 需求响应：先确认需求，再说明
""".strip()

# Import database functions
from database import (
    get_user_by_username, get_user_by_email, get_user_by_id,
    create_user, update_user_password, user_exists, email_exists,
    create_conversation, get_user_conversations, get_conversation_by_id,
    get_conversation_messages, add_message, delete_conversation,
    update_conversation_title,
    add_user_document, get_user_documents, has_user_documents
)

# Import session isolation enhancement
from session_isolation_enhanced import (
    validate_conversation_access,
    is_conversation_expired,
    check_conversation_health,
    session_validator
)

# Import key encryption and rate limiting
from key_encryption import key_manager, encrypt_api_key, decrypt_api_key
from rate_limiting import rate_limiter, check_rate_limit

# Import thread-safe config manager
from config_manager import config_manager, UserConfig, UserSession

# Email configuration
EMAIL_CONFIG = {
    "sender_email": "tomybeloved@foxmail.com",
    "smtp_server": "smtp.qq.com",
    "smtp_port": 587,
    "smtp_password": os.environ.get("EMAIL_PASSWORD", "xajhzindwfrwbgde")  # Default for development
}

# ============ Pydantic Models ============

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    verification_code: str = Field(..., min_length=6, max_length=6)

class SendVerificationCode(BaseModel):
    email: str = Field(..., min_length=5, max_length=100)

class ResetPassword(BaseModel):
    email: str = Field(..., min_length=5, max_length=100)
    verification_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class APIConfig(BaseModel):
    apiKey: Optional[str] = None  # Unified API key for OpenAI + Cohere + Claude proxy
    baseUrl: Optional[str] = None  # Proxy base URL (e.g., https://api.pumpkinaigc.online)
    rerankerKey: Optional[str] = None  # API key for reranker service
    rerankerBaseUrl: Optional[str] = None  # Reranker API base URL
    claudeModelName: str = "claude-3-5-sonnet-20241022"  # Claude model name (called through unified API)
    databaseUrl: str = "sqlite:///raglite.sqlite"
    # Legacy fields for backwards compatibility
    openaiApiKey: Optional[str] = None
    cohereApiKey: Optional[str] = None


# No longer need GPT4Reranker, using BAAI/bge-reranker-v2-m3 from rerankers library

class ChatMessage(BaseModel):
    content: str
    conversationId: Optional[int] = None
    systemPrompt: Optional[str] = None  # Custom system prompt for special modes like Prompt Assistant

class InstructionRequest(BaseModel):
    instruction: str

class InstructionOptimizeRequest(BaseModel):
    instruction: str
    mode: str  # 'scene', 'analysis', or 'intelligent'

# ============ Utility Functions ============

async def retry_with_exponential_backoff(
    func,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
):
    """
    Retry a function with exponential backoff strategy.

    Args:
        func: Async or sync function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to delay
    """
    num_retries = 0
    delay = initial_delay

    while True:
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except Exception as e:
            error_str = str(e)
            error_lower = error_str.lower()

            # Check if error is retryable
            is_rate_limit = (
                "429" in error_str or
                "rate" in error_lower or
                "limit" in error_lower or
                "饱和" in error_str or
                "too many requests" in error_lower or
                "503" in error_str or
                "service unavailable" in error_lower or
                "timeout" in error_lower
            )

            num_retries += 1

            # If not retryable or max retries reached, raise the error
            if not is_rate_limit or num_retries > max_retries:
                # Temporarily show full error for debugging
                logger.error(f"Request failed after {num_retries} retries: {error_str}")
                logger.error(f"Full exception: {repr(e)}")
                raise

            # Calculate delay with exponential backoff
            delay = min(delay * exponential_base, max_delay)

            # Add jitter to prevent thundering herd
            if jitter:
                delay = delay * (0.5 + random.random())

            logger.warning(
                f"Rate limit hit (attempt {num_retries}/{max_retries}). "
                f"Retrying in {delay:.2f} seconds... Error: {sanitize_error_message(error_str)}"
            )

            # Wait before retrying
            await asyncio.sleep(delay)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return username
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except (jwt.exceptions.DecodeError, jwt.exceptions.InvalidTokenError, Exception):
        raise HTTPException(status_code=401, detail="Invalid token")

def get_password_hash(password: str):
    # Bcrypt has a 72-byte limit, encode to bytes and truncate
    password_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    # Bcrypt has a 72-byte limit, encode to bytes and truncate
    password_bytes = plain_password.encode('utf-8')[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))

async def generate_conversation_title(user_question: str, ai_response: str, api_key: str, base_url: str = None) -> str:
    """
    Generate a high-quality, intelligent conversation title based on user question and AI's COMPLETE response.

    CRITICAL: This function uses the AI's FULL response (not truncated) to deeply analyze:
    - What technical solutions/methods AI provided
    - What concepts/principles AI explained
    - What specific technologies/tools AI discussed
    - The core value AI delivered to the user

    The title reflects AI's contribution, not just user's problem.

    Uses an intelligent title generation system that:
    - Refuses generic/vague words (no "问题", "讨论", "分析", "文档")
    - Accurately reflects conversation core value extracted from COMPLETE AI response
    - Has high information density (8-10 Chinese chars or 4-6 English words with meaningful info)
    - Helps users quickly identify and recall conversations

    Args:
        user_question: The user's first question
        ai_response: The AI's COMPLETE response (FULL TEXT, not truncated)
        api_key: OpenAI API key
        base_url: Optional base URL for API

    Returns:
        A high-quality title (8-10 Chinese characters or 4-6 English words)
    """
    try:
        # Import intelligent title generator
        from intelligent_title_generator import (
            create_title_generation_prompt,
            validate_and_process_title,
            IntelligentTitleGenerator
        )

        # IMPORTANT: Pass the COMPLETE ai_response (no truncation)
        # The generator will analyze the full content to extract core value
        logger.info(f"Generating title from FULL AI response ({len(ai_response)} chars)")
        title_prompt = create_title_generation_prompt(user_question, ai_response)

        # Call OpenAI API to generate title
        openai_base_url = base_url.rstrip('/') + '/v1' if base_url else None
        client = OpenAI(api_key=api_key, base_url=openai_base_url, timeout=30.0)

        # Use gpt-4-turbo for title generation with retry
        def make_title_request():
            return client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": title_prompt}],
                max_tokens=50,  # Reduced for concise titles
                temperature=0.3  # Lower temperature for more focused, consistent titles
            )

        response = await retry_with_exponential_backoff(
            make_title_request,
            max_retries=2,
            initial_delay=1.0,
            max_delay=10.0
        )

        raw_title = response.choices[0].message.content.strip()

        # Validate and process the title
        final_title = validate_and_process_title(raw_title, user_question)

        logger.info(f"Generated title: '{final_title}' (from raw: '{raw_title}')")
        return final_title

    except Exception as e:
        logger.error(f"Failed to generate title: {e}")
        # Fallback: use intelligent fallback generator
        try:
            from intelligent_title_generator import IntelligentTitleGenerator
            fallback_title = IntelligentTitleGenerator.generate_fallback_title(user_question)
            logger.info(f"Using fallback title: '{fallback_title}'")
            return fallback_title
        except Exception as fallback_error:
            logger.error(f"Fallback title generation failed: {fallback_error}")
            # Ultimate fallback: first 10 characters
            return user_question[:10]

async def generate_follow_up_questions(user_question: str, ai_response: str, api_key: str, base_url: str = None) -> list:
    """
    Generate 3 intelligent follow-up questions based on user question and AI response.

    The questions are designed to encourage deeper exploration with three angles:
    1. 细节补充 (Detail Supplement) - Ask for more specific details or clarifications
    2. 场景延伸 (Scenario Extension) - Explore practical applications or related scenarios
    3. 实操疑问 (Practical Question) - Ask about implementation, best practices, or troubleshooting

    Args:
        user_question: The user's original question
        ai_response: The AI's complete response
        api_key: OpenAI API key
        base_url: Optional base URL for API

    Returns:
        List of 3 follow-up questions (15-25 characters each)
    """
    try:
        # Create specialized prompt for question generation
        question_generation_prompt = f"""你是一个专业的对话引导助手。基于以下对话内容，生成3个高质量的联想问题。

用户问题：{user_question}

AI回复：{ai_response}

请生成3个联想问题，要求：

1. **细节补充**：针对AI回复中的某个关键点，询问更具体的细节或进一步解释
2. **场景延伸**：基于回复内容，延伸到相关的应用场景或实际案例
3. **实操疑问**：关于如何实际操作、最佳实践或常见问题的询问

每个问题必须：
- 长度：15-25个中文字符
- 相关性：紧密关联AI回复的核心内容
- 实用性：能引导用户进行有价值的深入探讨
- 多样性：三个问题角度不同，避免重复
- 自然性：像真实用户会问的问题

以JSON数组格式返回，例如：
["如何在实际项目中应用这个方法？", "这种方案的性能瓶颈在哪里？", "有没有更简单的替代方案？"]

只返回JSON数组，不要任何其他解释。"""

        openai_base_url = base_url.rstrip('/') + '/v1' if base_url else None
        client = OpenAI(api_key=api_key, base_url=openai_base_url, timeout=30.0)

        # Define the API call function for retry
        def make_question_request():
            return client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": question_generation_prompt}],
                max_tokens=200,  # Enough for 3 short questions
                temperature=0.7  # Moderate creativity for diverse questions
            )

        response = await retry_with_exponential_backoff(
            make_question_request,
            max_retries=2,
            initial_delay=1.0,
            max_delay=10.0
        )

        raw_response = response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            # Extract JSON array from response (may have markdown code blocks)
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', raw_response)
            if json_match:
                raw_response = json_match.group(1)
            elif raw_response.startswith('['):
                pass  # Already JSON
            else:
                # Try to find JSON array boundaries
                start_idx = raw_response.find('[')
                end_idx = raw_response.rfind(']')
                if start_idx != -1 and end_idx != -1:
                    raw_response = raw_response[start_idx:end_idx+1]

            questions = json.loads(raw_response)

            # Validate we got exactly 3 questions
            if isinstance(questions, list) and len(questions) >= 3:
                # Take first 3 questions and ensure they're strings
                validated_questions = [str(q).strip() for q in questions[:3]]
                logger.info(f"Generated {len(validated_questions)} follow-up questions")
                return validated_questions
            else:
                logger.warning(f"Invalid question format, got {len(questions) if isinstance(questions, list) else 0} questions")
                raise ValueError("Invalid question count")

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse follow-up questions: {e}, using fallback")
            # Fallback: generic but useful questions
            return [
                "能否详细说明一下具体步骤？",
                "这个方案有哪些实际应用场景？",
                "实现过程中需要注意什么？"
            ]

    except Exception as e:
        logger.error(f"Failed to generate follow-up questions: {e}")
        # Fallback: generic questions
        return [
            "能否详细说明一下具体步骤？",
            "这个方案有哪些实际应用场景？",
            "实现过程中需要注意什么？"
        ]

def get_or_create_reranker(username: str):
    """Lazy load reranker for a user on first use

    Returns reranker if successfully initialized, None otherwise
    """
    user_config = get_user_config(username)

    # Return existing reranker if already initialized
    if user_config.get("reranker") is not None:
        return user_config["reranker"]

    # Try to initialize reranker
    if not RERANKER_AVAILABLE:
        return None

    try:
        reranker_key = user_config["api_keys"].get("reranker_key")
        api_key = user_config["api_keys"].get("api_key")
        reranker_base_url = user_config["api_keys"].get("reranker_base_url") or "https://api.vectorengine.ai/v1"

        # Use reranker key if available, otherwise fall back to api key
        reranker_api_key = reranker_key or api_key

        if not reranker_api_key:
            logger.warning(f"No API key available for reranker initialization for user: {username}")
            return None

        # Set very short timeout for HuggingFace Hub to fail fast
        os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '5'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'  # Try offline mode first

        logger.info(f"Lazily initializing reranker for user: {username}")

        # Set a timeout for the entire operation
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                Reranker,
                "BAAI/bge-reranker-v2-m3",
                api_key=reranker_api_key,
                base_url=reranker_base_url
            )
            try:
                reranker = future.result(timeout=15)  # 15 second total timeout
            except concurrent.futures.TimeoutError:
                raise TimeoutError("Reranker initialization timed out after 15 seconds")

        # Store reranker in config for future use
        user_config["reranker"] = reranker
        config_manager.set_config(username, user_config)

        logger.info(f"Reranker successfully initialized for user: {username}")
        return reranker

    except Exception as e:
        logger.warning(f"Failed to initialize reranker for user {username}: {sanitize_error_message(str(e))}")
        return None

def initialize_rag_config(config: APIConfig, username: str, is_encrypted: bool = False):
    """Initialize RAG configuration for a user with Custom RAG system

    Args:
        config: API configuration
        username: Username
        is_encrypted: Whether the API keys in config are encrypted
    """
    try:
        # Handle unified API key (new style) or legacy separate keys
        api_key = config.apiKey or config.openaiApiKey
        base_url = config.baseUrl

        if not api_key:
            raise ValueError("API key is required")

        # ===== DECRYPTION: Decrypt API keys if encrypted =====
        if is_encrypted:
            try:
                api_key = decrypt_api_key(api_key)
                if config.rerankerKey:
                    reranker_key_decrypted = decrypt_api_key(config.rerankerKey)
                else:
                    reranker_key_decrypted = None
                logger.info(f"✓ Decrypted API keys for user: {username}")
            except Exception as e:
                logger.error(f"Failed to decrypt API keys: {e}")
                raise ValueError("Failed to decrypt API keys - they may be corrupted")

        # Create CustomEmbedder with text-embedding-3-large
        embedder = None
        rag_system = None
        reranker = None
        llm_client = None

        if CUSTOM_RAG_AVAILABLE:
            try:
                # Normalize base_url
                openai_base_url = base_url.rstrip('/') + '/v1' if base_url else None

                # Create embedder
                embedder = CustomEmbedder(
                    api_key=api_key,
                    base_url=openai_base_url,
                    model="text-embedding-3-large"
                )

                # Create RAG system with user-specific database
                user_db_path = f"custom_rag_{username}.db"
                rag_system = CustomRAGSystem(
                    embedder=embedder,
                    db_path=user_db_path,
                    enable_web_search=True
                )

                # Create LLM client for gpt-4-turbo
                llm_client = OpenAI(
                    api_key=api_key,
                    base_url=openai_base_url
                )

                # Skip reranker initialization during config save to avoid long waits
                # Reranker will be lazily initialized on first use instead
                reranker = None
                logger.info(f"Reranker initialization deferred (will load on first use) for user: {username}")

                logger.info(f"Custom RAG system initialized for user: {username}")
            except Exception as e:
                logger.error(f"Could not initialize Custom RAG: {sanitize_error_message(str(e))}")
                raise

        # Save configuration using thread-safe manager
        config_manager.set_config(username, {
            "rag_system": rag_system,
            "llm_client": llm_client,
            "reranker": reranker,
            "embedder": embedder,
            "api_keys": {
                "api_key": api_key,
                "base_url": base_url,
                "reranker_key": config.rerankerKey,
                "reranker_base_url": config.rerankerBaseUrl,
                # Legacy compatibility
                "openai": api_key,
                "cohere": api_key
            },
            "db_url": config.databaseUrl,
            "claudeModelName": config.claudeModelName
        })

        # Ensure user session exists
        config_manager.ensure_session(username)

        return rag_system
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(f"Configuration error: {sanitized_error}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {sanitized_error}")

def get_user_config(username: str):
    """Get user's RAG configuration (thread-safe)"""
    config = config_manager.get_config(username)
    if config is None:
        raise HTTPException(status_code=400, detail="Configuration not initialized. Please configure API keys first.")
    return config

# ============ Email Functions ============

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_email(to_email: str, subject: str, body: str):
    """Send email using SMTP"""
    email_sent = False
    try:
        logger.info(f"Preparing to send email to {to_email}")
        logger.info(f"SMTP Server: {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}")
        logger.info(f"Sender: {EMAIL_CONFIG['sender_email']}")

        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender_email"]
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        logger.info(f"Connecting to SMTP server...")
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"], timeout=30)
        try:
            logger.info(f"Starting TLS...")
            server.starttls()
            logger.info(f"Logging in...")
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["smtp_password"])
            logger.info(f"Sending message to {to_email}...")
            server.send_message(msg)
            email_sent = True
            logger.info(f"✓ Email sent successfully to {to_email}")
        finally:
            # Try to quit gracefully, but ignore errors during disconnect
            # as they occur AFTER the email is already sent
            try:
                server.quit()
            except Exception:
                # Ignore quit errors - email was already sent
                pass

        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {str(e)}")
        logger.error("Please check your email password and ensure 'SMTP service' is enabled in QQ Mail settings")
        return False
    except smtplib.SMTPException as e:
        if email_sent:
            # Email was sent despite the error
            logger.warning(f"Email sent successfully, but SMTP error occurred: {str(e)}")
            return True
        logger.error(f"SMTP error: {str(e)}")
        return False
    except Exception as e:
        if email_sent:
            # Email was sent despite the error
            logger.warning(f"Email sent successfully, but error occurred: {str(e)}")
            return True
        logger.error(f"Failed to send email: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

# ============ Authentication Endpoints ============

@app.post("/api/auth/send-code")
async def send_verification_code(request: SendVerificationCode):
    """Send verification code to email"""
    email = request.email
    print(f"\n{'='*60}")
    print(f"EMAIL SEND REQUEST RECEIVED FOR: {email}")
    print(f"{'='*60}\n")
    logger.info(f"=== EMAIL SEND REQUEST RECEIVED FOR: {email} ===")

    # Check if email is already registered
    if email_exists(email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Generate verification code
    code = generate_verification_code()
    print(f"Generated verification code: {code}")
    print(f"{'='*60}\n")

    # Store code using thread-safe manager (auto-cleanup after 6 minutes)
    config_manager.set_verification_code(email, code)

    # Email content
    subject = "RAG AI Assistant - Registration Verification Code"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 500px; margin: 0 auto; background: #f9f9f9; padding: 30px; border-radius: 10px;">
            <h2 style="color: #333; text-align: center;">RAG AI Assistant</h2>
            <p style="color: #666;">Hello,</p>
            <p style="color: #666;">Your registration verification code is:</p>
            <div style="background: #fff; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px; border: 1px solid #ddd;">
                <span style="font-size: 32px; font-weight: bold; color: #409eff; letter-spacing: 8px;">{code}</span>
            </div>
            <p style="color: #999; font-size: 14px;">This code is valid for 10 minutes. Please complete your registration promptly.</p>
            <p style="color: #999; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
        </div>
    </body>
    </html>
    """

    # Try to send email
    logger.info(f"Attempting to send verification code to {email}")
    logger.info(f"SMTP Password configured: {bool(EMAIL_CONFIG['smtp_password'])}")

    if EMAIL_CONFIG["smtp_password"]:
        logger.info(f"Sending email to {email}...")
        success = send_email(email, subject, body)
        if success:
            logger.info(f"Email sent successfully to {email}")
        else:
            logger.error(f"Failed to send email to {email}, code: {code}")
            logger.info(f"[DEV] Verification code for {email}: {code}")
    else:
        logger.info(f"[DEV] No SMTP password configured. Verification code for {email}: {code}")

    # For development: return code in response
    return {"success": True, "message": "Verification code sent", "dev_code": code}

@app.post("/api/auth/register", response_model=dict)
async def register(user: UserRegister):
    """Register a new user with email verification"""
    # Check if username exists
    if user_exists(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check if email exists
    if email_exists(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate password strength
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if not re.search(r'[A-Z]', user.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', user.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', user.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one number")

    # Verify the code using thread-safe manager
    if not config_manager.verify_code(user.email, user.verification_code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    # Create user in database
    try:
        hashed_password = get_password_hash(user.password)
        user_id = create_user(user.username, user.email, hashed_password)
        logger.info(f"User registered: {user.username} (ID: {user_id})")
        return {"success": True, "message": "User registered successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/reset-password", response_model=dict)
async def reset_password_endpoint(reset_request: ResetPassword):
    """Reset user password with email verification"""
    # Find user by email
    user_found = get_user_by_email(reset_request.email)
    if not user_found:
        raise HTTPException(status_code=400, detail="Email not found")

    # Validate password strength first
    if len(reset_request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if not re.search(r'[A-Z]', reset_request.new_password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', reset_request.new_password):
        raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', reset_request.new_password):
        raise HTTPException(status_code=400, detail="Password must contain at least one number")

    # Verify the code using thread-safe manager
    if not config_manager.verify_code(reset_request.email, reset_request.verification_code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    # Update password in database
    hashed_password = get_password_hash(reset_request.new_password)
    success = update_user_password(reset_request.email, hashed_password)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")

    logger.info(f"Password reset for user: {user_found['username']}")
    return {"success": True, "message": "Password reset successfully"}

@app.post("/api/auth/login", response_model=Token)
async def login(user: UserLogin):
    """Login user and return JWT token"""
    user_data = get_user_by_username(user.username)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Run bcrypt verification in thread pool to avoid blocking event loop (bcrypt takes ~450ms)
    loop = asyncio.get_event_loop()
    password_valid = await loop.run_in_executor(None, verify_password, user.password, user_data["hashed_password"])

    if not password_valid:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"User logged in: {user.username}")

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me")
async def get_current_user(username: str = Depends(verify_token)):
    """Get current user information"""
    user_data = get_user_by_username(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user_data["id"],
        "username": user_data["username"],
        "nickname": f"用户_{user_data['username']}"
    }

# ============ Configuration Endpoints ============

@app.post("/api/config")
async def save_configuration(config: APIConfig, username: str = Depends(verify_token)):
    """Save API configuration for user with encrypted key storage"""
    # Rate limiting check
    is_allowed, error_msg = check_rate_limit(username, "config_update")
    if not is_allowed:
        raise HTTPException(status_code=429, detail=error_msg)

    # Check if API key is provided (new style or legacy)
    api_key = config.apiKey or config.openaiApiKey
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")

    try:
        # ===== ENCRYPTION: Encrypt API keys before storing =====
        encrypted_config = APIConfig(
            apiKey=encrypt_api_key(api_key) if api_key else None,
            baseUrl=config.baseUrl,
            rerankerKey=encrypt_api_key(config.rerankerKey) if config.rerankerKey else None,
            rerankerBaseUrl=config.rerankerBaseUrl,
            claudeModelName=config.claudeModelName,
            databaseUrl=config.databaseUrl,
            # Legacy fields
            openaiApiKey=encrypt_api_key(config.openaiApiKey) if config.openaiApiKey else None,
            cohereApiKey=encrypt_api_key(config.cohereApiKey) if config.cohereApiKey else None
        )

        # Store encrypted configuration
        initialize_rag_config(encrypted_config, username, is_encrypted=True)

        logger.info(f"✓ Configuration saved for user: {username} (keys encrypted)")
        return {"success": True, "message": "Configuration saved successfully (encrypted)"}

    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(f"Failed to save configuration: {sanitized_error}")
        raise HTTPException(status_code=500, detail=sanitized_error)

@app.get("/api/config")
async def get_configuration(username: str = Depends(verify_token)):
    """Get user's API configuration (without exposing keys)"""
    config_data = config_manager.get_config(username)

    if config_data is None:
        return {
            "apiKey": None,
            "baseUrl": None,
            "rerankerKey": None,
            "rerankerBaseUrl": None,
            "claudeModelName": "claude-3-5-sonnet-20241022",
            "databaseUrl": "sqlite:///raglite.sqlite",
            # Legacy fields
            "openaiApiKey": None,
            "cohereApiKey": None
        }

    # config_data is already available here
    return {
        "apiKey": "***" if config_data["api_keys"].get("api_key") else None,
        "baseUrl": config_data["api_keys"].get("base_url"),
        "rerankerKey": "***" if config_data["api_keys"].get("reranker_key") else None,
        "rerankerBaseUrl": config_data["api_keys"].get("reranker_base_url"),
        "claudeModelName": config_data.get("claudeModelName", "claude-3-5-sonnet-20241022"),
        "databaseUrl": config_data["db_url"],
        # Legacy fields
        "openaiApiKey": "***" if config_data["api_keys"]["openai"] else None,
        "cohereApiKey": "***" if config_data["api_keys"]["cohere"] else None
    }

@app.post("/api/config/test")
async def test_connections(username: str = Depends(verify_token)):
    """Test API connections with timeout"""
    user_config = get_user_config(username)
    results = {}

    api_key = user_config["api_keys"].get("api_key") or user_config["api_keys"].get("openai")
    base_url = user_config["api_keys"].get("base_url")

    # Test Unified API connection (OpenAI-compatible)
    if api_key:
        try:
            openai_base_url = base_url.rstrip('/') + '/v1' if base_url else None
            client = OpenAI(
                api_key=api_key,
                base_url=openai_base_url,
                timeout=10.0  # 10 second timeout
            )

            # Simple test with timeout - list models
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(client.models.list)
                try:
                    future.result(timeout=10)  # 10 second timeout
                    results["openai"] = {"status": "success", "message": "API Connected"}
                except concurrent.futures.TimeoutError:
                    results["openai"] = {"status": "error", "message": "Connection timeout. Please check your API endpoint."}
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                results["openai"] = {"status": "error", "message": "Connection timeout. Please check your API endpoint."}
            else:
                results["openai"] = {"status": "error", "message": sanitize_error_message(error_msg)}
    else:
        results["openai"] = {"status": "error", "message": "No API key configured"}

    # Test Database
    try:
        results["database"] = {"status": "success", "message": "Connected"}
    except Exception as e:
        results["database"] = {"status": "error", "message": sanitize_error_message(str(e))}

    return results

# ============ Document Upload Endpoints ============

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: Optional[int] = None,
    username: str = Depends(verify_token)
):
    """Upload and process a document, MUST be bound to a conversation for session isolation

    SECURITY ENHANCEMENTS:
    - conversation_id is REQUIRED
    - Strict ownership validation
    - Expiry detection (30 days inactive)
    - Health status checking
    - Rate limiting (10 uploads/minute)
    """
    # ===== RATE LIMITING =====
    is_allowed, error_msg = check_rate_limit(username, "upload")
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for user {username} on document upload")
        raise HTTPException(status_code=429, detail=error_msg)

    logger.info(f"=== Document upload started for user: {username}, file: {file.filename}, conversation: {conversation_id} ===")

    # CRITICAL: conversation_id is MANDATORY for strict isolation
    if conversation_id is None:
        raise HTTPException(
            status_code=400,
            detail="conversation_id is required. Please create a conversation first before uploading documents."
        )

    user_config = get_user_config(username)

    # Get user from database
    user_data = get_user_by_username(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user_data["id"]
    logger.info(f"User ID: {user_id}")

    # ===== ENHANCED VALIDATION =====
    # 1. Validate conversation access with expiry check
    is_valid, error_message = validate_conversation_access(
        conversation_id=conversation_id,
        user_id=user_id,
        require_active=True  # Require non-expired conversation
    )

    if not is_valid:
        logger.error(
            f"Conversation validation failed for user {username}, "
            f"conversation {conversation_id}: {error_message}"
        )
        raise HTTPException(
            status_code=400,
            detail=error_message
        )

    # 2. Check conversation health
    health = check_conversation_health(conversation_id, user_id)

    logger.info(
        f"Conversation {conversation_id} health: {health['health_status']}, "
        f"age: {health['age_days']} days, messages: {health['message_count']}"
    )

    # 3. Warn if conversation is expiring soon
    if health['health_status'] == 'expiring':
        logger.warning(
            f"Conversation {conversation_id} is approaching expiration "
            f"({health['age_days']} days old)"
        )

    logger.info(f"✓ Validated: conversation {conversation_id} belongs to user {username} and is active")

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    temp_path = None
    try:
        # Create temporary file
        logger.info("Creating temporary file...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        logger.info(f"Temporary file created: {temp_path}")

        # Process document with Custom RAG system
        if CUSTOM_RAG_AVAILABLE and user_config.get("rag_system"):
            try:
                logger.info("Processing with Custom RAG system...")
                rag_system = user_config["rag_system"]

                # DEBUG: Log upload details
                logger.info(f"[DEBUG] Uploading '{file.filename}' to conversation_id={conversation_id}, user={username}")
                logger.info(f"[DEBUG] RAG DB path: {rag_system.db.db_path}")

                # Pass conversation_id to ensure session isolation
                success = rag_system.add_pdf(Path(temp_path), conversation_id=conversation_id)
                if success:
                    logger.info(f"[SUCCESS] Document processed with Custom RAG for user: {username}, conversation: {conversation_id}")
                else:
                    raise Exception("Failed to process PDF with Custom RAG")
            except Exception as e:
                logger.error(f"Custom RAG processing failed: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
        else:
            logger.warning(f"Custom RAG not available or not configured. CUSTOM_RAG_AVAILABLE={CUSTOM_RAG_AVAILABLE}, rag_system={user_config.get('rag_system') is not None}")

        # Store document reference in database with conversation binding
        logger.info(f"Storing document reference in database...")
        doc_id = add_user_document(user_id, file.filename, temp_path, conversation_id=conversation_id)
        logger.info(f"Document reference stored in database with ID: {doc_id}, bound to conversation: {conversation_id}")

        # Update session using thread-safe manager
        config_manager.update_session(username, documents_loaded=True)
        logger.info(f"Session updated for user: {username}")

        logger.info(f"=== Document uploaded successfully for user: {username} ===")
        return {
            "success": True,
            "message": f"Document {file.filename} uploaded successfully",
            "filename": file.filename,
            "conversation_id": conversation_id
        }
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.get("/api/documents/status")
async def get_document_status(username: str = Depends(verify_token)):
    """Get document processing status"""
    # Get user from database
    user_data = get_user_by_username(username)
    if not user_data:
        return {"documents_loaded": False}

    # Check if user has any documents in database
    has_docs = has_user_documents(user_data["id"])
    return {"documents_loaded": has_docs}

@app.post("/api/documents/clear")
async def clear_documents(username: str = Depends(verify_token)):
    """Clear all documents for the current user"""
    # Get user from database
    user_data = get_user_by_username(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user_data["id"]

    try:
        user_db_path = f"custom_rag_{username}.db"

        # Try to get user config using thread-safe manager
        user_config = config_manager.get_config(username)

        # Close any existing RAG system connections
        if user_config and user_config.get("rag_system"):
            try:
                rag_sys = user_config["rag_system"]
                if hasattr(rag_sys, 'conn') and rag_sys.conn:
                    rag_sys.conn.close()
                    logger.info("Closed existing RAG system connection")
            except Exception as e:
                logger.warning(f"Failed to close RAG connection: {e}")

        # Delete the database file if it exists
        if os.path.exists(user_db_path):
            try:
                os.remove(user_db_path)
                logger.info(f"Deleted RAG database: {user_db_path}")
            except Exception as e:
                logger.error(f"Failed to delete database: {e}")
                # Wait a moment and try again
                import time
                time.sleep(0.5)
                try:
                    os.remove(user_db_path)
                    logger.info(f"Deleted RAG database after retry: {user_db_path}")
                except Exception as e2:
                    logger.error(f"Failed to delete database even after retry: {e2}")
                    # Continue anyway - we'll reinitialize

        # Reinitialize RAG system if user has config
        if user_config and CUSTOM_RAG_AVAILABLE:
            from custom_rag import CustomEmbedder, CustomRAGSystem

            api_key = user_config["api_keys"].get("api_key") or user_config["api_keys"].get("openai")
            base_url = user_config["api_keys"].get("base_url")

            if api_key:
                openai_base_url = base_url.rstrip('/') + '/v1' if base_url else None

                # Create new embedder
                embedder = CustomEmbedder(
                    api_key=api_key,
                    base_url=openai_base_url,
                    model="text-embedding-3-large"
                )

                # Create new empty RAG system
                new_rag_system = CustomRAGSystem(
                    embedder=embedder,
                    db_path=user_db_path,
                    enable_web_search=True
                )

                # Update user config with new empty RAG system
                user_config["rag_system"] = new_rag_system
                logger.info(f"Reinitialized RAG system for user: {username}")

        logger.info(f"Successfully cleared all documents for user: {username}")
        return {"success": True, "message": "All documents cleared successfully"}

    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

# ============ Chat Endpoints ============

@app.post("/api/chat/message")
async def send_message(message: ChatMessage, username: str = Depends(verify_token)):
    """Send a chat message and get AI response with enhanced session validation and rate limiting"""
    # ===== RATE LIMITING =====
    is_allowed, error_msg = check_rate_limit(username, "chat")
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for user {username} on chat")
        raise HTTPException(status_code=429, detail=error_msg)

    user_config = get_user_config(username)

    # Get user from database
    user_data = get_user_by_username(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user_data["id"]

    # ===== ENHANCED VALIDATION =====
    # Validate conversation if conversationId is provided
    if message.conversationId:
        is_valid, error_message = validate_conversation_access(
            conversation_id=message.conversationId,
            user_id=user_id,
            require_active=True
        )

        if not is_valid:
            logger.error(
                f"Chat validation failed for user {username}, "
                f"conversation {message.conversationId}: {error_message}"
            )
            raise HTTPException(
                status_code=400,
                detail=error_message
            )

        logger.info(f"✓ Validated: conversation {message.conversationId} is active for user {username}")

    try:
        # Get API keys (needed for both RAG and direct API, and for follow-up questions)
        api_key = user_config["api_keys"].get("api_key") or user_config["api_keys"].get("openai")
        base_url = user_config["api_keys"].get("base_url")

        if not api_key:
            raise HTTPException(status_code=400, detail="No API key configured")

        # Get conversation history from database
        conversation_history = []
        if message.conversationId:
            conversation = get_conversation_by_id(message.conversationId, user_id)
            if conversation:
                db_messages = get_conversation_messages(message.conversationId)
                conversation_history = db_messages

        # Format messages for API
        formatted_messages = []
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Try Custom RAG if available and documents are loaded
        # Check if user has documents in database for this conversation
        has_docs = has_user_documents(user_id, conversation_id=message.conversationId)

        # SECURITY LOG: Track conversation isolation
        logger.info(f"SECURITY: Processing message for conversation_id={message.conversationId}, user={username}, has_docs={has_docs}")

        ai_response = None
        web_search_used = False

        # Use RAG system if available (for both document search and web search)
        if CUSTOM_RAG_AVAILABLE and user_config.get("rag_system"):
            try:
                rag_system = user_config["rag_system"]
                llm_client = user_config["llm_client"]
                # Lazy load reranker on first use
                reranker = get_or_create_reranker(username)

                top_contexts = []

                # Only search documents if user has uploaded files
                if has_docs:
                    # CRITICAL: Perform search with MANDATORY conversation_id for strict isolation
                    if message.conversationId is None:
                        logger.error(f"SECURITY VIOLATION: Attempted RAG search without conversation_id")
                        raise ValueError("conversation_id is required for RAG search")

                    # DEBUG: Log search parameters
                    logger.info(f"[DEBUG] About to search with conversation_id={message.conversationId}, query='{message.content[:50]}...'")

                    # Perform search for relevant chunks WITH CONVERSATION ISOLATION
                    search_results = rag_system.search(
                        message.content,
                        top_k=10,
                        conversation_id=message.conversationId  # KEY: Only search in current conversation
                    )

                    logger.info(f"RAG Search: Found {len(search_results)} chunks for conversation {message.conversationId}")

                    # DEBUG: Log first result snippet
                    if search_results:
                        first_chunk = search_results[0][0][:100] if len(search_results[0][0]) > 100 else search_results[0][0]
                        logger.info(f"[DEBUG] First result preview: '{first_chunk}...'")
                    else:
                        logger.info(f"[DEBUG] No results found for conversation {message.conversationId}")

                    if search_results:
                        # Extract chunks from search results
                        chunks = [chunk for chunk, score in search_results]

                        # Rerank if reranker is available
                        if reranker and RERANKER_AVAILABLE:
                            try:
                                reranked = reranker.rank(query=message.content, docs=chunks)
                                top_contexts = [result.text for result in reranked.top_k(5)]  # Take top 5 after reranking
                                logger.info("Used reranker for chunk selection")
                            except Exception as e:
                                logger.warning(f"Reranker failed, using original order: {e}")
                                top_contexts = chunks[:5]
                        else:
                            top_contexts = chunks[:5]

                # Generate answer with automatic web search if needed
                # This will work even without documents - web search activates based on query type
                ai_response = rag_system.generate_answer_with_search(
                    message.content,
                    llm_client,
                    top_contexts,  # Empty list if no documents
                    model="gpt-4-turbo"
                )
                web_search_used = True

                logger.info(f"Used RAG system for response (conversation {message.conversationId}, web_search_enabled={rag_system.enable_web_search})")
            except Exception as e:
                logger.warning(f"RAG system failed, falling back to direct API: {e}")

        # Fallback to direct API call through unified API (using gpt-4-turbo)
        if not ai_response:
            if not api_key:
                raise HTTPException(status_code=400, detail="No API key configured")

            logger.info("Using gpt-4-turbo for chat")
            openai_base_url = base_url.rstrip('/') + '/v1' if base_url else None
            client = OpenAI(api_key=api_key, base_url=openai_base_url, timeout=60.0)

            # Use custom system prompt if provided (e.g., from Prompt Assistant)
            # Otherwise use default fallback prompt
            if message.systemPrompt:
                system_prompt = message.systemPrompt
                logger.info("Using custom system prompt for chat")
            else:
                system_prompt = """You are a professional AI assistant. Follow these rules strictly:

CRITICAL - FORBIDDEN PHRASES (NEVER use these):
- "根据上下文" / "根据Context" / "根据文档"
- "根据你提供的" / "根据你的" / "根据你的问题"
- "让我来" / "我来帮你" / "让我为你"
- "这个问题" / "这是" / "这个是"
- "Context 1" / "Context 2" / "Context 3" / "Context 4" / "Context 5" (or any Context N)
- "结合Context" / "参考Context" / "查看Context"
- ANY preamble or meta-commentary about answering

REQUIRED BEHAVIOR:
1. First sentence must directly answer the question - no introduction
2. Write like a confident human expert, not an AI
3. Use declarative statements, never reference the question or contexts
4. Provide concrete details, specific examples, actionable information
5. If uncertain, state facts clearly without apologies

RESPONSE STRUCTURE:
- Opening (1-2 sentences): Direct core answer
- Body: Supporting details, examples, step-by-step guidance
- Format: Use Markdown (###, **, lists, code blocks, ---)
- NO source references, NO meta-commentary

BAD EXAMPLES (NEVER do this):
"根据你的问题，让我来为你解答..."
"这个问题涉及到机器学习，让我详细说明..."
"结合Context 5的内容..."

GOOD EXAMPLES:
"Python是一门高级编程语言，以简洁易读著称。它广泛应用于Web开发、数据科学和AI领域。"
"机器学习让计算机通过数据自主学习模式，无需明确编程。"

Write as an expert colleague - professional, direct, informative."""

            # Add user message
            formatted_messages.append({"role": "user", "content": message.content})

            # Define the API call function for retry
            def make_chat_request():
                return client.chat.completions.create(
                    model="gpt-4-turbo",  # Changed to gpt-4-turbo
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *formatted_messages
                    ],
                    max_tokens=1024,
                    temperature=0.7
                )

            # Use gpt-4-turbo with retry mechanism
            response = await retry_with_exponential_backoff(
                make_chat_request,
                max_retries=3,
                initial_delay=2.0,
                max_delay=30.0
            )

            ai_response = response.choices[0].message.content

        # Save to database
        new_conv_id = message.conversationId
        if message.conversationId:
            # Verify conversation ownership
            conversation = get_conversation_by_id(message.conversationId, user_id)
            if conversation:
                # Add messages to existing conversation
                add_message(message.conversationId, "user", message.content)
                add_message(message.conversationId, "assistant", ai_response)
        else:
            # Create new conversation with AI-generated title
            # Generate title based on user question and AI response
            try:
                title = await generate_conversation_title(
                    user_question=message.content,
                    ai_response=ai_response,
                    api_key=api_key,
                    base_url=base_url
                )
                logger.info(f"Generated conversation title: {title}")
            except Exception as e:
                # Fallback to truncated user message if title generation fails
                logger.warning(f"Title generation failed, using fallback: {e}")
                title = message.content[:30] + "..." if len(message.content) > 30 else message.content

            new_conv_id = create_conversation(user_id, title)
            # Add messages to new conversation
            add_message(new_conv_id, "user", message.content)
            add_message(new_conv_id, "assistant", ai_response)

        # Generate follow-up questions based on the conversation
        try:
            suggested_questions = await generate_follow_up_questions(
                user_question=message.content,
                ai_response=ai_response,
                api_key=api_key,
                base_url=base_url
            )
            logger.info(f"Generated {len(suggested_questions)} follow-up questions for conversation {new_conv_id}")
        except Exception as e:
            logger.warning(f"Failed to generate follow-up questions: {e}")
            # Fallback to empty list if generation fails
            suggested_questions = []

        return {
            "success": True,
            "response": ai_response,
            "conversationId": new_conv_id,
            "suggestedQuestions": suggested_questions
        }

    except Exception as e:
        error_str = str(e)
        sanitized_error = sanitize_error_message(error_str)
        logger.error(f"Chat error: {sanitized_error}")

        # Provide user-friendly error messages based on error type
        error_lower = error_str.lower()
        if "429" in error_str or "rate" in error_lower or "饱和" in error_str:
            user_message = "API 服务当前负载较高，请稍后重试。我们已经自动重试了多次，但服务仍然繁忙。建议等待 1-2 minutes后再试。"
        elif "timeout" in error_lower:
            user_message = "请求超时，可能是网络问题或服务响应缓慢。请检查网络连接后重试。"
        elif "api key" in error_lower or "unauthorized" in error_lower:
            user_message = "API 密钥无效或已过期。请在配置页面检查并更新您的 API 密钥。"
        elif "quota" in error_lower or "insufficient" in error_lower:
            user_message = "API 配额不足。请检查您的账户余额或升级套餐。"
        else:
            user_message = f"发生错误: {sanitized_error}。请稍后重试或联系技术支持。"

        raise HTTPException(status_code=500, detail=user_message)

@app.get("/api/chat/conversations")
async def get_conversations(username: str = Depends(verify_token)):
    """Get user's conversation history"""
    # Get user from database
    user_data = get_user_by_username(username)
    if not user_data:
        return []

    # Get conversations from database
    conversations = get_user_conversations(user_data["id"])

    # Format for frontend (convert to expected format)
    formatted_conversations = []
    for conv in conversations:
        formatted_conversations.append({
            "id": conv["id"],
            "title": conv["title"],
            "createdAt": conv["created_at"],
            "updatedAt": conv["updated_at"],
            "messageCount": conv.get("message_count", 0)
        })

    return formatted_conversations

@app.delete("/api/chat/conversations/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: int, username: str = Depends(verify_token)):
    """Delete a conversation"""
    # Get user from database
    user_data = get_user_by_username(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete conversation (with ownership check)
    success = delete_conversation(conversation_id, user_data["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found or not owned by user")

    return {"success": True, "message": "Conversation deleted"}

class ConversationTitleUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)

@app.patch("/api/chat/conversations/{conversation_id}")
async def update_conversation_title_endpoint(
    conversation_id: int,
    update_data: ConversationTitleUpdate,
    username: str = Depends(verify_token)
):
    """Update conversation title"""
    # Get user from database
    user_data = get_user_by_username(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Update conversation title (with ownership check)
    success = update_conversation_title(conversation_id, user_data["id"], update_data.title)

    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found or not owned by user")

    return {"success": True, "message": "Conversation title updated"}

# ===== Session Isolation Enhancement Endpoints =====

@app.get("/api/chat/conversations/{conversation_id}/health")
async def get_conversation_health(
    conversation_id: int,
    username: str = Depends(verify_token)
):
    """Get conversation health status with expiry detection

    Returns detailed health information including:
    - Ownership validation
    - Expiry status
    - Activity metrics
    - Health status (healthy/expiring/expired/invalid)
    """
    # Get user from database
    user_data = get_user_by_username(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user_data["id"]

    # Check health
    health = check_conversation_health(conversation_id, user_id)

    return {
        "success": True,
        "conversation_id": conversation_id,
        "health": health
    }


@app.post("/api/chat/conversations/cleanup-expired")
async def cleanup_expired_conversations(username: str = Depends(verify_token)):
    """Clean up all expired conversations for the current user

    Removes conversations that have been inactive for more than 30 days.
    """
    # Get user from database
    user_data = get_user_by_username(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user_data["id"]

    # Run cleanup
    result = session_validator.cleanup_expired_conversations(user_id)

    logger.info(
        f"Cleaned up {result['deleted_count']}/{result['expired_count']} "
        f"expired conversations for user {username}"
    )

    return {
        "success": True,
        "message": f"Cleaned up {result['deleted_count']} expired conversations",
        "total_conversations": result['total_conversations'],
        "expired_count": result['expired_count'],
        "deleted_count": result['deleted_count'],
        "deleted_ids": result['deleted_ids']
    }


@app.get("/api/chat/conversations/validate/{conversation_id}")
async def validate_conversation_endpoint(
    conversation_id: int,
    username: str = Depends(verify_token)
):
    """Validate conversation access and check expiry status

    Use this endpoint before performing operations on a conversation
    to ensure it's valid and not expired.
    """
    # Get user from database
    user_data = get_user_by_username(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user_data["id"]

    # Validate
    is_valid, error_message = validate_conversation_access(
        conversation_id=conversation_id,
        user_id=user_id,
        require_active=True
    )

    if not is_valid:
        return {
            "success": False,
            "valid": False,
            "error": error_message
        }

    # Get additional info
    conversation = get_conversation_by_id(conversation_id, user_id)
    is_expired, expiry_msg = is_conversation_expired(conversation_id, user_id)

    return {
        "success": True,
        "valid": True,
        "expired": is_expired,
        "expiry_message": expiry_msg,
        "conversation": {
            "id": conversation["id"],
            "title": conversation["title"],
            "created_at": conversation["created_at"],
            "updated_at": conversation["updated_at"]
        }
    }

# =============================

# ============ Instruction Assistant Endpoint ============

@app.post("/api/instruction/enhance")
async def enhance_instruction(request: InstructionRequest, username: str = Depends(verify_token)):
    """Enhance user instruction using AI"""
    user_config = get_user_config(username)

    try:
        api_key = user_config["api_keys"].get("api_key") or user_config["api_keys"].get("openai")
        base_url = user_config["api_keys"].get("base_url")

        if not api_key:
            raise HTTPException(status_code=400, detail="No API key configured")

        openai_base_url = base_url.rstrip('/') + '/v1' if base_url else None
        client = OpenAI(api_key=api_key, base_url=openai_base_url, timeout=60.0)

        enhancement_prompt = f"""You are an AI instruction optimization assistant.
        Your task is to enhance the following user instruction to make it more detailed,
        clear, and effective for getting comprehensive responses.

        Original instruction: {request.instruction}

        Please provide an enhanced version that:
        1. Is more specific and detailed
        2. Includes context and background
        3. Specifies the desired output format
        4. Maintains the original intent

        Return only the enhanced instruction without explanations."""

        # Define the API call function for retry
        def make_enhancement_request():
            return client.chat.completions.create(
                model="gpt-4-turbo",  # Use gpt-4-turbo instead of Claude
                max_tokens=512,
                messages=[{"role": "user", "content": enhancement_prompt}],
                temperature=0.7
            )

        # Call with retry mechanism
        response = await retry_with_exponential_backoff(
            make_enhancement_request,
            max_retries=3,
            initial_delay=2.0,
            max_delay=30.0
        )

        enhanced = response.choices[0].message.content

        return {
            "success": True,
            "enhancedInstruction": enhanced
        }
    except Exception as e:
        logger.error(f"Instruction enhancement error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/instruction/optimize")
async def optimize_instruction(request: InstructionOptimizeRequest, username: str = Depends(verify_token)):
    """Optimize user's original instruction into a high-quality Prompt (NOT execute the instruction)

    This endpoint helps users refine their raw instructions into well-structured, precise prompts.
    It does NOT execute the instruction or generate the task result.

    Three optimization modes:
    - scene: Emphasize format requirements and content precision
    - analysis: Break down into detailed, executable steps
    - intelligent: Deep understanding with comprehensive enrichment
    """
    user_config = get_user_config(username)

    # Define optimization prompts for each mode
    # IMPORTANT: These prompts instruct the AI to OPTIMIZE the instruction, NOT execute it
    prompts = {
        "scene": f"""You are a professional Prompt Engineer. Your task is to OPTIMIZE the user's original instruction into a high-quality, well-structured prompt. DO NOT execute the instruction or generate its result.

Original Instruction: {request.instruction}

Your task is to transform this into a refined prompt that:
1. **Clarifies the format requirements**: Specify exact output format (code structure, parameter requirements, documentation style, etc.)
2. **Enhances content precision**: Add scenario context, define scope boundaries, specify constraints
3. **Provides clear structure**: Use numbered lists, clear sections, explicit requirements
4. **Maintains original intent**: Keep the core request while making it more actionable

Example transformation:
- Original: "帮我写个登录页代码"
- Optimized: "请使用 HTML+CSS+JavaScript 实现响应式登录页，要求：1. 适配移动端/PC端；2. 包含账号密码输入框、verification code模块、记住密码勾选框；3. 样式采用 Tailwind CSS，配色以蓝色为主；4. 输出完整代码（含 HTML 结构、CSS 样式、JS 校验逻辑），无需额外解释。"

Now optimize the original instruction above. Return ONLY the optimized prompt in Chinese, with clear structure and specific requirements. Do not generate code or execute the task.""",

        "analysis": f"""You are a professional Prompt Engineer. Your task is to OPTIMIZE the user's original instruction by breaking it down into detailed, executable steps. DO NOT execute the instruction or generate its result.

Original Instruction: {request.instruction}

Your task is to transform this into a step-by-step prompt that:
1. **Decomposes the task**: Break into clear, sequential steps
2. **Specifies each step**: Define exact requirements, inputs, outputs for each step
3. **Eliminates ambiguity**: Make every requirement explicit and measurable
4. **Provides execution path**: Show logical flow from start to finish

Example transformation:
- Original: "优化我的网页布局"
- Optimized: "请按以下步骤优化网页布局：1. 先明确布局核心组件（如左侧导航、右侧内容区、底部 footer）；2. 限定组件尺寸规则（左侧导航宽度固定 240px，右侧内容区自适应，footer 高度 60px）；3. 要求使用 Flexbox 布局实现，确保组件不会重叠；4. 补充响应式逻辑（屏幕宽度＜768px 时隐藏左侧导航，显示汉堡菜单）；5. 输出完整的 CSS 代码和关键 HTML 结构修改说明。"

Now optimize the original instruction above. Return ONLY the optimized prompt in Chinese, structured as numbered steps with detailed requirements. Do not generate code or execute the task.""",

        "intelligent": f"""You are an expert Prompt Engineer. Your task is to OPTIMIZE the user's original instruction through deep understanding and intelligent enrichment. DO NOT execute the instruction or generate its result.

Original Instruction: {request.instruction}

Your task is to transform this into a comprehensive, enriched prompt that:
1. **Understands core intent**: Identify underlying goals and implicit requirements
2. **Enriches with context**: Add relevant scenarios, best practices, edge cases
3. **Specifies quality criteria**: Define success metrics and validation standards
4. **Provides complete guidance**: Cover all aspects from planning to validation

Example transformation:
- Original: "帮我写个接口请求函数"
- Optimized: "请使用 JavaScript（Axios 库）实现一个用户信息查询接口的请求函数，要求：1. 支持 GET 方法，传入参数为 userId（必传）；2. 补充请求拦截器（添加 Token 校验）和响应拦截器（处理 401 未授权、500 服务器错误等异常）；3. 支持异步调用（async/await 语法）；4. 输出函数完整代码，并标注关键参数说明、异常处理逻辑；5. 补充调用示例（含成功/失败回调处理）。"

Now optimize the original instruction above. Return ONLY the optimized prompt in Chinese, with comprehensive requirements and quality criteria. Do not generate code or execute the task."""
    }

    if request.mode not in prompts:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'scene', 'analysis', or 'intelligent'")

    try:
        api_key = user_config["api_keys"].get("api_key") or user_config["api_keys"].get("openai")
        base_url = user_config["api_keys"].get("base_url")

        if not api_key:
            raise HTTPException(status_code=400, detail="No API key configured")

        openai_base_url = base_url.rstrip('/') + '/v1' if base_url else None
        client = OpenAI(api_key=api_key, base_url=openai_base_url, timeout=60.0)

        # Define the API call function for retry
        def make_optimization_request():
            model_name = "gpt-4-turbo"
            logger.info(f"[DEBUG] About to call API with model: {model_name}")
            logger.info(f"[DEBUG] Base URL: {openai_base_url}")
            logger.info(f"[DEBUG] Mode: {request.mode}")
            return client.chat.completions.create(
                model=model_name,  # Use gpt-4-turbo for instruction optimization
                max_tokens=2048,
                messages=[{"role": "user", "content": prompts[request.mode]}],
                temperature=0.7
            )

        # Call with retry mechanism
        response = await retry_with_exponential_backoff(
            make_optimization_request,
            max_retries=3,
            initial_delay=2.0,
            max_delay=30.0
        )

        optimized = response.choices[0].message.content

        logger.info(f"Instruction optimized with mode: {request.mode} for user: {username}")

        return {
            "success": True,
            "optimized_instruction": optimized,
            "mode": request.mode
        }
    except Exception as e:
        # Temporarily show full error for debugging
        import traceback
        full_error = traceback.format_exc()
        logger.error(f"Instruction optimization error: {full_error}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

# =============================

# ============ Rate Limiting and Security Endpoints ============

@app.get("/api/rate-limit/quota")
async def get_rate_limit_quota(username: str = Depends(verify_token)):
    """Get user's current rate limit quota for all operations"""
    quotas = {}

    operations = ["chat", "upload", "config_update", "search"]

    for operation in operations:
        quota = rate_limiter.get_remaining_quota(username, operation)
        quotas[operation] = quota

    return {
        "success": True,
        "quotas": quotas
    }


@app.post("/api/rate-limit/reset")
async def reset_rate_limits(username: str = Depends(verify_token)):
    """Reset rate limits for current user (for testing/admin purposes)

    WARNING: This should be restricted in production
    """
    rate_limiter.reset_user_limits(username)

    logger.info(f"Rate limits reset for user: {username}")

    return {
        "success": True,
        "message": "Rate limits reset successfully"
    }


@app.get("/api/security/stats")
async def get_security_stats(username: str = Depends(verify_token)):
    """Get security statistics (admin only in production)

    Returns rate limiting stats and blacklist information
    """
    stats = rate_limiter.get_stats()

    return {
        "success": True,
        "stats": stats
    }

# =============================

# ============ Academic Term Extraction ============

# Import academic term extractor
from academic_term_extractor import AcademicTermExtractor, create_ai_extraction_prompt

class TermExtractionRequest(BaseModel):
    content: str = Field(..., description="Content to extract terms from")
    use_ai: bool = Field(default=True, description="Whether to use AI for enhanced extraction")  # Always True for GPT-4 mode

@app.post("/api/extract-terms")
async def extract_academic_terms(
    request: TermExtractionRequest,
    username: str = Depends(verify_token)
):
    """
    Extract academic terms from given content using AI (GPT-4)

    纯AI模式：直接使用GPT-4识别学术术语并生成解释
    """
    try:
        logger.info(f"[TERM_EXTRACTION] Request received from user: {username}")
        logger.info(f"[TERM_EXTRACTION] Content length: {len(request.content)} characters")

        if not request.content or len(request.content.strip()) < 10:
            logger.warning(f"[TERM_EXTRACTION] Content too short: {len(request.content)} chars")
            return {
                "success": True,
                "terms": [],
                "message": "内容过短，无法提取术语"
            }

        # Get user configuration
        user_config = get_user_config(username)
        if not user_config:
            logger.warning(f"[TERM_EXTRACTION] No config found for user {username}")
            return {
                "success": False,
                "terms": [],
                "message": "请先配置API密钥"
            }

        # Get API configuration from nested structure
        api_key = user_config["api_keys"].get("api_key") or user_config["api_keys"].get("openai")
        base_url = user_config["api_keys"].get("base_url")

        if not api_key:
            logger.warning(f"[TERM_EXTRACTION] No API key configured for user {username}")
            return {
                "success": False,
                "terms": [],
                "message": "请先配置API密钥"
            }

        # Create AI prompt for academic term extraction
        logger.info(f"[TERM_EXTRACTION] Creating extraction prompt...")
        ai_prompt = create_ai_extraction_prompt(request.content)
        logger.info(f"[TERM_EXTRACTION] Prompt created, length: {len(ai_prompt)} characters")

        # Call LLM (GPT-4)
        openai_base_url = base_url.rstrip('/') + '/v1' if base_url else None
        logger.info(f"[TERM_EXTRACTION] Calling GPT-4 API (base_url: {openai_base_url})")

        client = OpenAI(api_key=api_key, base_url=openai_base_url, timeout=30.0)

        response = client.chat.completions.create(
            model="gpt-4-turbo",  # 使用gpt-4-turbo进行全领域术语识别（用户的API key有权访问）
            messages=[{"role": "user", "content": ai_prompt}],
            max_tokens=3000,  # 增加token限制以支持更多术语
            temperature=0.2  # 降低温度以提高准确性
        )

        ai_result = response.choices[0].message.content.strip()
        logger.info(f"[TERM_EXTRACTION] AI response received, length: {len(ai_result)} characters")
        logger.info(f"[TERM_EXTRACTION] First 200 chars of response: {ai_result[:200]}...")

        # Parse JSON response
        try:
            # Extract JSON from response (may have markdown code blocks)
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', ai_result)
            if json_match:
                logger.info(f"[TERM_EXTRACTION] Found JSON in markdown code block")
                ai_result = json_match.group(1)
            elif ai_result.startswith('['):
                logger.info(f"[TERM_EXTRACTION] Response is already JSON array")
                pass  # Already JSON
            else:
                logger.info(f"[TERM_EXTRACTION] Searching for JSON array boundaries...")
                # 尝试找到JSON数组的开始和结束
                start_idx = ai_result.find('[')
                end_idx = ai_result.rfind(']')
                if start_idx != -1 and end_idx != -1:
                    logger.info(f"[TERM_EXTRACTION] Found JSON array at positions {start_idx} to {end_idx}")
                    ai_result = ai_result[start_idx:end_idx+1]
                else:
                    logger.error(f"[TERM_EXTRACTION] Could not find JSON array in response")

            terms = json.loads(ai_result)
            logger.info(f"[TERM_EXTRACTION] Successfully parsed JSON, found {len(terms)} raw terms")

            # Validate and clean terms
            valid_terms = []
            for i, term in enumerate(terms):
                if isinstance(term, dict) and 'term' in term and 'definition' in term:
                    # Add isFavorite field
                    term['isFavorite'] = False
                    # Ensure all required fields exist
                    term.setdefault('category', '专业术语')
                    term.setdefault('example', '')
                    valid_terms.append(term)
                    logger.debug(f"[TERM_EXTRACTION] Valid term #{i+1}: {term.get('term', 'N/A')}")
                else:
                    logger.warning(f"[TERM_EXTRACTION] Invalid term #{i+1}: {term}")

            logger.info(f"[TERM_EXTRACTION] AI extracted {len(valid_terms)} valid academic terms from content")

            # Return up to 30 terms for comprehensive coverage
            result_terms = valid_terms[:30]

            logger.info(f"[TERM_EXTRACTION] Returning {len(result_terms)} terms to frontend")

            return {
                "success": True,
                "terms": result_terms,
                "total_found": len(valid_terms),
                "message": f"成功提取 {len(result_terms)} 个学术术语" + (f"（共找到{len(valid_terms)}个）" if len(valid_terms) > 30 else "")
            }

        except json.JSONDecodeError as e:
            logger.error(f"[TERM_EXTRACTION] Failed to parse AI response as JSON: {e}")
            logger.error(f"[TERM_EXTRACTION] Raw AI response:\n{ai_result}")
            return {
                "success": False,
                "terms": [],
                "message": "AI返回格式错误，请重试"
            }

    except Exception as e:
        logger.error(f"[TERM_EXTRACTION] Term extraction failed: {e}")
        logger.error(f"[TERM_EXTRACTION] Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"[TERM_EXTRACTION] Traceback:\n{traceback.format_exc()}")
        return {
            "success": False,
            "terms": [],
            "message": f"术语提取失败: {str(e)}"
        }

# =============================

# ============ Health Check ============

@app.get("/")
async def root():
    return {"message": "RAG Chat API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ============ Run Server ============

if __name__ == "__main__":
    # Print startup header
    print(log_formatter.format_section_header("RAG Chat API Server Starting"))

    # Log startup information
    logger.info(f"Custom RAG available: {CUSTOM_RAG_AVAILABLE}")
    logger.info(f"Reranker available: {RERANKER_AVAILABLE}")
    logger.info("Server starting on http://0.0.0.0:8000")

    # Start uvicorn server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Force reload
