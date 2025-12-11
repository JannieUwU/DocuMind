"""
Complete Translation Script - Chinese to English
Handles all Chinese text in the codebase
"""

import os
import re
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Comprehensive translation dictionary
TRANSLATIONS = {
    # Email templates
    "RAG 智能助手 - 注册验证码": "RAG AI Assistant - Registration Verification Code",
    "RAG 智能助手 - 密码重置验证码": "RAG AI Assistant - Password Reset Code",
    "RAG 智能助手": "RAG AI Assistant",
    "您好，": "Hello,",
    "您好": "Hello",
    "您的注册验证码是：": "Your registration verification code is:",
    "您的注册验证码是": "Your registration verification code is",
    "您的密码重置验证码是：": "Your password reset verification code is:",
    "您的密码重置验证码是": "Your password reset verification code is",
    "验证码有效期为 10 分钟，请尽快完成注册。": "This code is valid for 10 minutes. Please complete your registration promptly.",
    "验证码有效期为 10 分钟，请尽快完成密码重置。": "This code is valid for 10 minutes. Please complete your password reset promptly.",
    "如果您没有请求此验证码，请忽略此邮件。": "If you didn't request this code, please ignore this email.",
    "如果这不是您的操作，请忽略此邮件。": "If you didn't request this, please ignore this email.",
    "此为系统自动发送邮件，请勿回复。": "This is an automated email, please do not reply.",

    # HTTP Exception messages
    "配置未初始化。请先配置 API 密钥": "Configuration not initialized. Please configure API keys first",
    "配置未初始化": "Configuration not initialized",
    "请先配置 API 密钥": "Please configure API keys first",
    "请求验证码": "Request verification code first",
    "验证码已过期": "Verification code has expired",
    "验证码无效": "Invalid verification code",
    "验证码无效或已过期": "Invalid or expired verification code",
    "用户注册成功": "User registered successfully",
    "邮箱已注册": "Email already registered",
    "用户名已存在": "Username already exists",
    "邮箱未找到": "Email not found",
    "用户未找到": "User not found",
    "密码必须至少 6 个字符": "Password must be at least 6 characters",
    "密码必须包含至少一个大写字母": "Password must contain at least one uppercase letter",
    "密码必须包含至少一个小写字母": "Password must contain at least one lowercase letter",
    "密码必须包含至少一个数字": "Password must contain at least one number",
    "文档上传成功": "Document uploaded successfully",
    "文档删除成功": "Document deleted successfully",
    "会话已更新": "Session updated",
    "密码更新成功": "Password updated successfully",
    "验证码发送成功": "Verification code sent successfully",
    "登录成功": "Login successful",
    "用户名或密码错误": "Invalid username or password",

    # Logger messages
    "用户注册": "User registered",
    "用户登录": "User logged in",
    "配置已保存": "Configuration saved",
    "配置已设置": "Config set for user",
    "配置已删除": "Config deleted for user",
    "会话已设置": "Session set for user",
    "会话已创建": "Session created for user",
    "会话已更新": "Session updated for user",
    "会话已删除": "Session deleted for user",
    "验证码已设置": "Verification code set for email",
    "验证码已过期": "Verification code expired for email",
    "验证成功": "Verification successful",
    "验证失败": "Verification failed",
    "所有配置数据已清空": "All config data cleared",
    "文档上传": "Document uploaded",
    "文档删除": "Document deleted",
    "初始化": "initialized",

    # Comments and docstrings
    "线程安全的配置管理器": "Thread-safe configuration manager",
    "替代全局字典": "Replaces global dictionaries",
    "线程安全的读写操作": "Thread-safe read/write operations",
    "自动过期清理": "Automatic expiration cleanup",
    "类型安全的数据结构": "Type-safe data structures",
    "可扩展的持久化接口": "Extensible persistence interface",
    "用户配置数据结构": "User configuration data structure",
    "用户会话数据结构": "User session data structure",
    "验证码数据结构": "Verification code data structure",

    # Function/variable descriptions
    "功能": "Features",
    "用户 API 配置管理": "User API configuration management",
    "用户会话数据管理": "User session data management",
    "邮箱验证码管理": "Email verification code management",
    "带过期清理": "with expiration cleanup",
    "线程安全保证": "Thread safety guarantee",
    "所有读写操作使用": "All read/write operations use",
    "返回数据的深拷贝，防止外部修改": "Returns deep copy of data to prevent external modification",
    "初始化配置管理器": "Initialize configuration manager",
    "验证码过期时间": "Verification code TTL",
    "秒": "seconds",
    "默认": "default",
    "分钟": "minutes",
    "用户配置存储": "User configuration storage",
    "用户会话存储": "User session storage",
    "验证码存储": "Verification code storage",

    # Args/Returns documentation
    "用户名": "username",
    "邮箱地址": "email address",
    "配置字典": "configuration dictionary",
    "会话数据": "session data",
    "验证码": "verification code",
    "字符串": "string",
    "用户输入的验证码": "user input code",
    "要更新的字段": "fields to update",
    "是否存在配置": "whether configuration exists",
    "是否成功删除": "whether deletion was successful",
    "是否验证成功": "whether verification succeeded",
    "用户名列表": "list of usernames",
    "统计数据字典": "statistics dictionary",
    "清理的验证码数量": "number of codes cleaned",
    "如果不存在返回": "returns None if not exists",
    "如果不存在或已过期返回": "returns None if not exists or expired",

    # Method descriptions
    "设置用户配置": "Set user configuration",
    "获取用户配置": "Get user configuration",
    "检查用户是否有配置": "Check if user has configuration",
    "删除用户配置": "Delete user configuration",
    "获取所有已配置的用户名": "Get all configured usernames",
    "设置用户会话数据": "Set user session data",
    "获取用户会话数据": "Get user session data",
    "确保用户会话存在": "Ensure user session exists",
    "不存在则创建": "create if not exists",
    "更新用户会话数据": "Update user session data",
    "删除用户会话": "Delete user session",
    "设置邮箱验证码": "Set email verification code",
    "获取邮箱验证码": "Get email verification code",
    "验证邮箱验证码": "Verify email verification code",
    "清理过期验证码": "Clean expired verification codes",
    "获取统计信息": "Get statistics",
    "清空所有数据": "Clear all data",

    # Additional context
    "线程安全": "thread-safe",
    "带自动清理": "with auto-cleanup",
    "验证后自动删除": "auto-delete after verification",
    "先清理过期验证码": "clean expired codes first",
    "设置新验证码": "set new verification code",
    "检查过期": "check expiration",
    "检查是否过期": "check if expired",
    "验证码匹配": "code matches",
    "内部方法，不加锁": "internal method, no lock",
    "公开接口": "public interface",
    "调试和监控": "debugging and monitoring",
    "仅用于测试": "for testing only",
    "全局单例实例": "global singleton instance",
    "兼容性辅助函数": "compatibility helper functions",
    "兼容旧代码的辅助函数": "helper function for backward compatibility",
    "使用示例": "usage examples",
    "测试配置管理": "test configuration management",
    "测试会话管理": "test session management",
    "测试验证码管理": "test verification code management",
    "测试过期清理": "test expiration cleanup",
    "统计信息": "statistics",
    "模拟过期": "simulate expiration",
    "需要修改时间戳": "need to modify timestamp",
    "已清理": "cleaned",
    "个过期代码": "expired codes",
    "个过期验证码": "expired verification codes",
    "检索到的代码": "retrieved code",
    "验证结果": "verification result",
    "验证后应该被删除": "should be deleted after verification",

    # Numbers
    "位验证码": "digit code",
    "个字符": "characters",
}

def translate_text(text):
    """Translate Chinese text to English"""
    result = text
    # Sort by length (descending) to replace longer phrases first
    for zh, en in sorted(TRANSLATIONS.items(), key=lambda x: len(x[0]), reverse=True):
        result = result.replace(zh, en)
    return result

def process_file(file_path):
    """Process a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        content = translate_text(content)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function"""
    backend_dir = Path(__file__).parent

    # Find all Python files (excluding venv and __pycache__)
    python_files = []
    for root, dirs, files in os.walk(backend_dir):
        # Skip venv and __pycache__
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'node_modules']]

        for file in files:
            if file.endswith('.py') and not file.startswith('translate_'):
                python_files.append(os.path.join(root, file))

    print(f"Found {len(python_files)} Python files to process...\n")

    updated_count = 0
    for file_path in python_files:
        rel_path = os.path.relpath(file_path, backend_dir)
        if process_file(file_path):
            print(f"  ✓ Updated: {rel_path}")
            updated_count += 1

    print(f"\n{'='*60}")
    print(f"Translation complete:")
    print(f"  {updated_count}/{len(python_files)} files updated")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
