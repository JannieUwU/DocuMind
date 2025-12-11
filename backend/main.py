"""
FastAPI 主入口文件 - 向后兼容层
整理后的实际主入口在 app/core/main.py
"""
import sys
from pathlib import Path

# Add paths to sys.path for backward compatibility with old imports
backend_dir = Path(__file__).parent
app_dir = backend_dir / 'app'
core_dir = app_dir / 'core'
services_dir = app_dir / 'services'
utils_dir = app_dir / 'utils'

for path in [str(core_dir), str(services_dir), str(utils_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

from app.core.main import *

# 保持向后兼容，允许 python main.py 和 uvicorn main:app 正常工作
