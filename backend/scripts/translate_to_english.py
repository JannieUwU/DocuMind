"""
Batch Translation Script - Chinese to English
Converts all Chinese comments and strings in Python files to English
"""

import os
import re
from pathlib import Path

# Translation dictionary for common terms
TRANSLATIONS = {
    # Comments and docstrings
    "线程安全的配置管理器": "Thread-safe Configuration Manager",
    "替代全局字典": "Replaces global dictionaries",
    "线程安全的读写操作": "Thread-safe read/write operations",
    "自动过期清理": "Automatic expiration cleanup",
    "类型安全的数据结构": "Type-safe data structures",
    "可扩展的持久化接口": "Extensible persistence interface",
    "用户配置数据结构": "User configuration data structure",
    "用户会话数据结构": "User session data structure",
    "验证码数据结构": "Verification code data structure",
    "线程安全的配置管理器": "Thread-safe configuration manager",
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
    "设置用户配置": "Set user configuration",
    "线程安全": "thread-safe",
    "用户名": "username",
    "配置字典": "configuration dictionary",
    "获取用户配置": "Get user configuration",
    "如果不存在返回": "Returns None if not exists",
    "检查用户是否有配置": "Check if user has configuration",
    "是否存在配置": "Whether configuration exists",
    "删除用户配置": "Delete user configuration",
    "是否成功删除": "Whether deletion was successful",
    "获取所有已配置的用户名": "Get all configured usernames",
    "用户名列表": "List of usernames",
    "设置用户会话数据": "Set user session data",
    "会话数据": "Session data",
    "获取用户会话数据": "Get user session data",
    "如果不存在返回 None": "Returns None if not exists",
    "确保用户会话存在": "Ensure user session exists",
    "不存在则创建": "Create if not exists",
    "更新用户会话数据": "Update user session data",
    "要更新的字段": "Fields to update",
    "删除用户会话": "Delete user session",
    "设置邮箱验证码": "Set email verification code",
    "带自动清理": "with auto-cleanup",
    "邮箱地址": "Email address",
    "位验证码": "digit code",
    "先清理过期验证码": "Clean expired codes first",
    "设置新验证码": "Set new verification code",
    "获取邮箱验证码": "Get email verification code",
    "检查过期": "Check expiration",
    "验证码": "Verification code",
    "字符串": "string",
    "如果不存在或已过期返回": "Returns None if not exists or expired",
    "检查是否过期": "Check if expired",
    "验证邮箱验证码": "Verify email verification code",
    "验证后自动删除": "Auto-delete after verification",
    "用户输入的验证码": "User input code",
    "是否验证成功": "Whether verification succeeded",
    "验证成功": "Verification successful",
    "验证失败": "Verification failed",
    "验证码匹配": "Code matches",
    "清理过期验证码": "Clean expired verification codes",
    "内部方法，不加锁": "Internal method, no lock",
    "清理的验证码数量": "Number of codes cleaned",
    "公开接口": "Public interface",
    "调试和监控": "Debugging and monitoring",
    "获取统计信息": "Get statistics",
    "统计数据字典": "Statistics dictionary",
    "清空所有数据": "Clear all data",
    "仅用于测试": "For testing only",
    "全局单例实例": "Global singleton instance",
    "过期": "expiration",
    "兼容性辅助函数": "Compatibility helper functions",
    "获取用户配置": "Get user configuration",
    "兼容旧代码的辅助函数": "Helper function for backward compatibility",
    "注意：这里不能直接抛出": "Note: Cannot throw directly here",
    "调用者需要自行处理": "Caller needs to handle",
    "的情况": "case",
    "使用示例": "Usage examples",
    "配置日志": "Configure logging",
    "测试配置管理": "Test configuration management",
    "测试会话管理": "Test session management",
    "测试验证码管理": "Test verification code management",
    "检索到的代码": "Retrieved code",
    "验证结果": "Verification result",
    "验证后应该被删除": "Should be deleted after verification",
    "测试过期清理": "Test expiration cleanup",
    "模拟过期": "Simulate expiration",
    "需要修改时间戳": "Need to modify timestamp",
    "已清理": "Cleaned",
    "个过期代码": "expired codes",
    "统计信息": "Statistics",

    # Email related
    "智能助手": "AI Assistant",
    "注册验证码": "Registration Verification Code",
    "您好": "Hello",
    "您的注册验证码是": "Your registration verification code is",
    "请在": "Please complete registration within",
    "分钟内完成注册": "minutes",
    "如果这不是您的操作，请忽略此邮件": "If you didn't request this, please ignore this email",
    "此为系统自动发送邮件，请勿回复": "This is an automated email, please do not reply",
    "密码重置验证码": "Password Reset Verification Code",
    "您正在重置密码": "You are resetting your password",
    "您的密码重置验证码是": "Your password reset verification code is",

    # UI messages
    "配置未初始化。请先配置 API 密钥": "Configuration not initialized. Please configure API keys first",
    "请求验证码": "Request verification code first",
    "验证码已过期": "Verification code has expired",
    "验证码无效": "Invalid verification code",
    "用户注册成功": "User registered successfully",
    "邮箱已注册": "Email already registered",
    "用户名已存在": "Username already exists",
    "邮箱未找到": "Email not found",
    "密码必须至少": "Password must be at least",
    "个字符": "characters",
    "密码必须包含至少一个大写字母": "Password must contain at least one uppercase letter",
    "密码必须包含至少一个小写字母": "Password must contain at least one lowercase letter",
    "密码必须包含至少一个数字": "Password must contain at least one number",
    "文档上传成功": "Document uploaded successfully",
    "会话已更新": "Session updated",
    "文档已加载": "Documents loaded",

    # Log messages
    "已初始化": "initialized",
    "配置已设置": "Config set for user",
    "配置已删除": "Config deleted for user",
    "会话已设置": "Session set for user",
    "会话已创建": "Session created for user",
    "会话已更新": "Session updated for user",
    "会话已删除": "Session deleted for user",
    "验证码已设置": "Verification code set for email",
    "验证码已过期": "Verification code expired for email",
    "已清理": "Cleaned",
    "个过期验证码": "expired verification codes",
    "所有配置数据已清空": "All config data cleared",
}

def translate_text(text):
    """Translate Chinese text to English"""
    result = text
    for zh, en in TRANSLATIONS.items():
        result = result.replace(zh, en)
    return result

def process_file(file_path):
    """Process a single Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Translate docstrings and comments
        content = translate_text(content)

        # Only write if changed
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

    # Find all Python files (excluding venv)
    python_files = []
    for root, dirs, files in os.walk(backend_dir):
        # Skip venv directory
        if 'venv' in root or '__pycache__' in root:
            continue

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    print(f"Found {len(python_files)} Python files to process...")

    updated_count = 0
    for file_path in python_files:
        file_name = os.path.basename(file_path)
        if process_file(file_path):
            print(f"  ✓ Updated: {file_name}")
            updated_count += 1
        else:
            print(f"  - Skipped: {file_name} (no changes)")

    print(f"\nTotal: {updated_count}/{len(python_files)} files updated")

if __name__ == "__main__":
    main()
