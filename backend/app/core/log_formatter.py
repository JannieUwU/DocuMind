"""
Professional Log Formatter
基于 UniLog 设计理念的日志格式优化处理系统

Features:
- 行号标记 (Line markers)
- 结构化输出 (Structured output)
- 中文编码修复 (Chinese encoding fix)
- 敏感信息过滤 (Sensitive info filtering)
- 智能分组 (Intelligent grouping)
- 颜色支持 (Color support)
"""

import re
import logging
from typing import Dict, Optional
from datetime import datetime
import sys


class LogLevel:
    """日志级别常量"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SUCCESS = "SUCCESS"  # 自定义成功级别


class ColorCode:
    """ANSI 颜色代码"""
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # 亮色前景色
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'


class LogFormatter:
    """日志格式化器"""

    # 敏感信息模式
    SENSITIVE_PATTERNS = [
        (r'sk-[A-Za-z0-9_-]{20,}', '[API_KEY]'),  # OpenAI API keys
        (r'Bearer\s+[A-Za-z0-9_\-\.]+', 'Bearer [TOKEN]'),  # Bearer tokens
        (r'api_key[=:]\s*["\']?[^"\'\s]+', 'api_key=[REDACTED]'),  # API key assignments
        (r'password[=:]\s*[^"\'\s]+', 'password=[REDACTED]'),  # Passwords (improved)
        (r'https?://[^\s]+', '[URL]'),  # URLs
        (r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '[IP]'),  # IP addresses (optional)
    ]

    # 忽略的重复警告
    IGNORED_WARNINGS = [
        'Model type could not be auto-mapped',
        'No device set',
        'No dtype set',
        'Using device cpu',
        'Using dtype torch.float32',
    ]

    # 日志级别颜色映射
    LEVEL_COLORS = {
        LogLevel.DEBUG: ColorCode.BRIGHT_BLACK,
        LogLevel.INFO: ColorCode.BRIGHT_BLUE,
        LogLevel.WARNING: ColorCode.BRIGHT_YELLOW,
        LogLevel.ERROR: ColorCode.BRIGHT_RED,
        LogLevel.CRITICAL: ColorCode.RED + ColorCode.BOLD,
        LogLevel.SUCCESS: ColorCode.BRIGHT_GREEN,
    }

    # 日志级别符号
    LEVEL_SYMBOLS = {
        LogLevel.DEBUG: '🔍',
        LogLevel.INFO: 'ℹ️',
        LogLevel.WARNING: '⚠️',
        LogLevel.ERROR: '❌',
        LogLevel.CRITICAL: '🚨',
        LogLevel.SUCCESS: '✅',
    }

    def __init__(self, use_colors: bool = True, filter_sensitive: bool = True):
        """
        initialized日志格式化器

        Args:
            use_colors: 是否使用颜色
            filter_sensitive: 是否过滤敏感信息
        """
        self.use_colors = use_colors and self._supports_color()
        self.filter_sensitive = filter_sensitive
        self.line_counter = 0
        self._warning_cache = set()  # 用于去重的警告缓存

    @staticmethod
    def _supports_color() -> bool:
        """检测终端是否支持颜色"""
        # Windows 10+ 支持 ANSI 颜色
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except:
                return False
        return True

    def _sanitize(self, message: str) -> str:
        """清理敏感信息"""
        if not self.filter_sensitive:
            return message

        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message)

        return message

    def _fix_encoding(self, message: str) -> str:
        """修复中文编码问题"""
        try:
            # 尝试检测并修复 Windows 控制台编码问题
            if sys.platform == 'win32':
                # 如果包含乱码字符，尝试重新编码
                if re.search(r'[��]+', message):
                    try:
                        # 尝试从 GBK 转到 UTF-8
                        message = message.encode('latin1').decode('gbk', errors='ignore')
                    except:
                        pass
        except:
            pass

        return message

    def _should_ignore(self, message: str) -> bool:
        """判断是否应该忽略此日志（去重）"""
        # 检查是否是重复的警告
        for ignored_pattern in self.IGNORED_WARNINGS:
            if ignored_pattern in message:
                if message in self._warning_cache:
                    return True  # 已经输出过，忽略
                else:
                    self._warning_cache.add(message)
                    return False

        return False

    def _colorize(self, text: str, color: str) -> str:
        """为文本添加颜色"""
        if not self.use_colors:
            return text
        return f"{color}{text}{ColorCode.RESET}"

    def _format_timestamp(self) -> str:
        """格式化时间戳"""
        return datetime.now().strftime('%H:%M:%S.%f')[:-3]  # 精确到毫seconds

    def format_log(
        self,
        level: str,
        message: str,
        module: Optional[str] = None,
        add_line_marker: bool = True
    ) -> str:
        """
        格式化日志消息

        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL, SUCCESS)
            message: 日志消息
            module: 模块名称
            add_line_marker: 是否添加行号标记

        Returns:
            格式化后的日志string
        """
        # 检查是否应忽略
        if self._should_ignore(message):
            return ""

        # 修复编码
        message = self._fix_encoding(message)

        # 清理敏感信息
        message = self._sanitize(message)

        # 获取时间戳
        timestamp = self._format_timestamp()

        # 行号标记（类似 UniLog）
        line_marker = ""
        if add_line_marker:
            self.line_counter += 1
            line_marker = f"<line{self.line_counter}> "

        # 级别符号和颜色
        level_symbol = self.LEVEL_SYMBOLS.get(level, '')
        level_color = self.LEVEL_COLORS.get(level, ColorCode.WHITE)

        # 格式化级别
        formatted_level = self._colorize(f"{level_symbol} {level:8}", level_color)

        # 格式化模块名
        module_part = f"[{module}] " if module else ""

        # 格式化时间戳
        timestamp_colored = self._colorize(timestamp, ColorCode.BRIGHT_BLACK)

        # 组装完整日志
        log_line = f"{line_marker}{timestamp_colored} {formatted_level} {module_part}{message}"

        return log_line

    def format_section_header(self, title: str, width: int = 60) -> str:
        """
        格式化章节标题

        Args:
            title: 标题文本
            width: 标题宽度

        Returns:
            格式化的标题
        """
        separator = "=" * width
        header = f"\n{separator}\n{title.center(width)}\n{separator}\n"
        return self._colorize(header, ColorCode.BRIGHT_CYAN + ColorCode.BOLD)

    def format_api_call(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: Optional[float] = None
    ) -> str:
        """
        格式化 API 调用日志

        Args:
            method: HTTP 方法
            endpoint: 端点路径
            status_code: 状态码
            duration_ms: 请求耗时（毫seconds）

        Returns:
            格式化的 API 调用日志
        """
        # 状态码颜色
        if 200 <= status_code < 300:
            status_color = ColorCode.BRIGHT_GREEN
        elif 300 <= status_code < 400:
            status_color = ColorCode.BRIGHT_CYAN
        elif 400 <= status_code < 500:
            status_color = ColorCode.BRIGHT_YELLOW
        else:
            status_color = ColorCode.BRIGHT_RED

        status_colored = self._colorize(str(status_code), status_color)
        method_colored = self._colorize(method, ColorCode.BRIGHT_MAGENTA)

        duration_part = ""
        if duration_ms is not None:
            duration_part = f" ({duration_ms:.0f}ms)"

        message = f"{method_colored} {endpoint} → {status_colored}{duration_part}"

        return self.format_log(LogLevel.INFO, message, module="API")

    def format_rag_search(
        self,
        conversation_id: int,
        query_preview: str,
        chunks_found: int,
        took_ms: Optional[float] = None
    ) -> str:
        """
        格式化 RAG 搜索日志

        Args:
            conversation_id: 会话 ID
            query_preview: 查询预览（前 30 字符）
            chunks_found: 找到的文档块数量
            took_ms: 搜索耗时

        Returns:
            格式化的搜索日志
        """
        query_short = query_preview[:30] + "..." if len(query_preview) > 30 else query_preview

        duration_part = ""
        if took_ms is not None:
            duration_part = f" in {took_ms:.0f}ms"

        message = f"🔍 Conv#{conversation_id} | Query: \"{query_short}\" | Found {chunks_found} chunks{duration_part}"

        return self.format_log(LogLevel.SUCCESS, message, module="RAG")

    def format_file_upload(
        self,
        filename: str,
        conversation_id: int,
        status: str = "processing"
    ) -> str:
        """
        格式化文件上传日志

        Args:
            filename: 文件名
            conversation_id: 会话 ID
            status: 状态 (processing, success, error)

        Returns:
            格式化的上传日志
        """
        # 修复文件名编码
        filename = self._fix_encoding(filename)

        status_symbols = {
            "processing": "📤",
            "success": "✅",
            "error": "❌"
        }

        symbol = status_symbols.get(status, "📄")
        level = LogLevel.SUCCESS if status == "success" else LogLevel.INFO

        message = f"{symbol} {filename} → Conv#{conversation_id}"

        return self.format_log(level, message, module="Upload")

    def reset_line_counter(self):
        """重置行号计数器"""
        self.line_counter = 0

    def clear_warning_cache(self):
        """清空警告缓存（用于新会话）"""
        self._warning_cache.clear()


# 创建全局格式化器实例
log_formatter = LogFormatter(use_colors=True, filter_sensitive=True)


class StructuredLogHandler(logging.Handler):
    """结构化日志处理器（集成到 Python logging）"""

    def __init__(self, formatter: LogFormatter):
        super().__init__()
        self.formatter_instance = formatter

    def emit(self, record: logging.LogRecord):
        try:
            # 提取日志级别
            level_name = record.levelname

            # 映射到自定义级别
            level_map = {
                'DEBUG': LogLevel.DEBUG,
                'INFO': LogLevel.INFO,
                'WARNING': LogLevel.WARNING,
                'ERROR': LogLevel.ERROR,
                'CRITICAL': LogLevel.CRITICAL,
            }

            level = level_map.get(level_name, LogLevel.INFO)

            # 格式化消息
            message = self.format(record)
            module = record.name

            formatted = self.formatter_instance.format_log(
                level=level,
                message=message,
                module=module,
                add_line_marker=True
            )

            if formatted:  # 如果没有被过滤掉
                print(formatted, file=sys.stderr)

        except Exception:
            self.handleError(record)


# usage examples
if __name__ == "__main__":
    # 演示用法
    formatter = LogFormatter()

    print(formatter.format_section_header("日志格式优化演示"))

    # 普通日志
    print(formatter.format_log(LogLevel.INFO, "应用启动成功", module="main"))
    print(formatter.format_log(LogLevel.SUCCESS, "✓ 配置加载完成", module="config"))
    print(formatter.format_log(LogLevel.WARNING, "API 密钥未设置，使用default值", module="security"))
    print(formatter.format_log(LogLevel.ERROR, "数据库连接失败", module="database"))

    # API 调用日志
    print(formatter.format_api_call("POST", "/api/chat/message", 200, 1250.5))
    print(formatter.format_api_call("GET", "/api/auth/me", 401, 45.2))

    # RAG 搜索日志
    print(formatter.format_rag_search(
        conversation_id=123,
        query_preview="这篇文章讲述了什么内容",
        chunks_found=10,
        took_ms=89.3
    ))

    # 文件上传日志
    print(formatter.format_file_upload(
        filename="学术论文.pdf",
        conversation_id=456,
        status="success"
    ))

    # 敏感信息过滤演示
    print(formatter.format_log(
        LogLevel.INFO,
        "API key: sk-abcd1234efgh5678 被成功加载",
        module="security"
    ))

    print(formatter.format_section_header("演示结束"))
