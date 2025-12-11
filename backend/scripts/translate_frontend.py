"""
Vue Frontend Translation Script - Chinese to English
Translates all Chinese text in Vue components
"""

import os
import re
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Comprehensive translation dictionary for Vue components
VUE_TRANSLATIONS = {
    # Authentication & User
    "登录": "Login",
    "注册": "Register",
    "退出登录": "Logout",
    "用户名": "Username",
    "密码": "Password",
    "确认密码": "Confirm Password",
    "邮箱": "Email",
    "验证码": "Verification Code",
    "发送验证码": "Send Code",
    "重新发送": "Resend",
    "获取验证码": "Get Code",
    "请输入用户名": "Please enter username",
    "请输入密码": "Please enter password",
    "请输入邮箱": "Please enter email",
    "请输入验证码": "Please enter verification code",
    "密码不一致": "Passwords do not match",
    "登录成功": "Login successful",
    "注册成功": "Registration successful",
    "退出成功": "Logout successful",
    "忘记密码": "Forgot Password",
    "重置密码": "Reset Password",
    "返回登录": "Back to Login",
    "立即注册": "Register Now",
    "已有账号？": "Already have an account?",
    "还没有账号？": "Don't have an account?",

    # Dashboard & Chat
    "对话": "Chat",
    "聊天": "Chat",
    "发送": "Send",
    "发送消息": "Send Message",
    "停止生成": "Stop Generation",
    "继续生成": "Continue",
    "重新生成": "Regenerate",
    "复制": "Copy",
    "删除": "Delete",
    "编辑": "Edit",
    "保存": "Save",
    "取消": "Cancel",
    "确认": "Confirm",
    "关闭": "Close",
    "清空": "Clear",
    "清空对话": "Clear Chat",
    "新建对话": "New Chat",
    "对话历史": "Chat History",
    "历史记录": "History",
    "搜索对话": "Search Chats",
    "请输入消息": "Please enter a message",
    "请输入问题": "Please enter your question",
    "输入你的问题": "Enter your question",
    "正在输入": "Typing...",
    "正在生成": "Generating...",
    "生成中": "Generating",
    "思考中": "Thinking...",
    "加载中": "Loading...",
    "复制成功": "Copied successfully",
    "删除成功": "Deleted successfully",
    "保存成功": "Saved successfully",
    "操作成功": "Operation successful",
    "操作失败": "Operation failed",

    # File Upload
    "上传文件": "Upload File",
    "上传文档": "Upload Document",
    "选择文件": "Select File",
    "拖拽文件到此处": "Drag files here",
    "或点击选择": "or click to select",
    "支持的格式": "Supported formats",
    "文件大小限制": "File size limit",
    "上传成功": "Upload successful",
    "上传失败": "Upload failed",
    "正在上传": "Uploading",
    "文件列表": "File List",
    "删除文件": "Delete File",
    "查看文件": "View File",
    "文件名": "Filename",
    "文件大小": "File Size",
    "上传时间": "Upload Time",
    "文件类型": "File Type",

    # Configuration
    "配置": "Configuration",
    "设置": "Settings",
    "API 配置": "API Configuration",
    "API 密钥": "API Key",
    "基础 URL": "Base URL",
    "模型选择": "Model Selection",
    "模型名称": "Model Name",
    "保存配置": "Save Configuration",
    "重置配置": "Reset Configuration",
    "配置成功": "Configuration successful",
    "配置失败": "Configuration failed",

    # Messages & Notifications
    "成功": "Success",
    "失败": "Failed",
    "错误": "Error",
    "警告": "Warning",
    "提示": "Tips",
    "信息": "Information",
    "确认删除吗？": "Confirm deletion?",
    "确认清空吗？": "Confirm clear?",
    "此操作不可撤销": "This action cannot be undone",
    "请先登录": "Please login first",
    "请先配置 API": "Please configure API first",
    "网络错误": "Network error",
    "请求超时": "Request timeout",
    "服务器错误": "Server error",
    "未知错误": "Unknown error",

    # Time & Date
    "刚刚": "Just now",
    "分钟前": "minutes ago",
    "小时前": "hours ago",
    "天前": "days ago",
    "今天": "Today",
    "昨天": "Yesterday",
    "上午": "AM",
    "下午": "PM",

    # Common Actions
    "搜索": "Search",
    "过滤": "Filter",
    "排序": "Sort",
    "导出": "Export",
    "导入": "Import",
    "下载": "Download",
    "刷新": "Refresh",
    "更多": "More",
    "展开": "Expand",
    "收起": "Collapse",
    "全选": "Select All",
    "反选": "Deselect All",

    # Status
    "在线": "Online",
    "离线": "Offline",
    "连接中": "Connecting",
    "已连接": "Connected",
    "断开连接": "Disconnected",
    "空闲": "Idle",
    "忙碌": "Busy",

    # Validation Messages
    "必填项": "Required field",
    "格式不正确": "Invalid format",
    "长度不符合要求": "Invalid length",
    "请填写完整": "Please fill in completely",
    "邮箱格式不正确": "Invalid email format",
    "密码长度至少6位": "Password must be at least 6 characters",
    "用户名已存在": "Username already exists",
    "邮箱已注册": "Email already registered",

    # Features
    "语音输入": "Voice Input",
    "停止录音": "Stop Recording",
    "开始录音": "Start Recording",
    "识别中": "Recognizing...",
    "语音识别": "Speech Recognition",
    "文字转语音": "Text to Speech",
    "主题切换": "Theme Toggle",
    "深色模式": "Dark Mode",
    "浅色模式": "Light Mode",
    "自动模式": "Auto Mode",

    # Conversation Management
    "对话管理": "Conversation Management",
    "重命名对话": "Rename Conversation",
    "删除对话": "Delete Conversation",
    "导出对话": "Export Conversation",
    "分享对话": "Share Conversation",
    "固定对话": "Pin Conversation",
    "归档对话": "Archive Conversation",

    # Document Management
    "文档管理": "Document Management",
    "知识库": "Knowledge Base",
    "我的文档": "My Documents",
    "最近使用": "Recently Used",
    "全部文档": "All Documents",
    "未分类": "Uncategorized",

    # Storage & Quota
    "存储空间": "Storage",
    "已使用": "Used",
    "剩余": "Remaining",
    "总容量": "Total Capacity",
    "清理空间": "Clean Storage",
    "升级套餐": "Upgrade Plan",

    # Academic Terms (if applicable)
    "学术术语": "Academic Terms",
    "术语解释": "Term Explanation",
    "专业术语库": "Term Database",
    "添加术语": "Add Term",
    "编辑术语": "Edit Term",

    # Instruction Assistant
    "指令助手": "Instruction Assistant",
    "优化指令": "Optimize Instruction",
    "分析指令": "Analyze Instruction",
    "生成指令": "Generate Instruction",
    "指令模板": "Instruction Template",

    # Welcome Page
    "欢迎": "Welcome",
    "开始使用": "Get Started",
    "产品介绍": "Product Introduction",
    "功能特性": "Features",
    "快速入门": "Quick Start",

    # Error Pages
    "页面未找到": "Page Not Found",
    "返回首页": "Back to Home",
    "出错了": "Something went wrong",

    # Placeholders
    "请输入": "Please enter",
    "请选择": "Please select",
    "暂无数据": "No data",
    "暂无内容": "No content",
    "加载失败": "Load failed",

    # Labels & Headers
    "标题": "Title",
    "内容": "Content",
    "描述": "Description",
    "作者": "Author",
    "创建时间": "Created At",
    "更新时间": "Updated At",
    "操作": "Actions",
    "状态": "Status",
    "类型": "Type",
    "大小": "Size",
    "数量": "Count",
    "总计": "Total",

    # CSS Comments & Demo
    "暗色模式样式": "Dark mode styles",
    "大屏幕优化": "Large screen optimization",
    "顶部控制栏": "Top control bar",
    "功能说明": "Feature description",
    "回复交互系统演示": "Reply Interaction System Demo",
    "AI回复交互系统演示": "AI Reply Interaction System Demo",

    # Buttons & Links
    "提交": "Submit",
    "重置": "Reset",
    "应用": "Apply",
    "查看详情": "View Details",
    "了解更多": "Learn More",
    "立即体验": "Try Now",
    "下一步": "Next",
    "上一步": "Previous",
    "完成": "Done",
    "跳过": "Skip",
}

def translate_vue_text(text):
    """Translate Chinese text to English in Vue files"""
    result = text
    # Sort by length (descending) to replace longer phrases first
    for zh, en in sorted(VUE_TRANSLATIONS.items(), key=lambda x: len(x[0]), reverse=True):
        # Replace in various contexts
        # 1. Template strings: {{ text }}
        result = re.sub(rf'{re.escape(zh)}(?=\s*}})', en, result)
        # 2. String literals: "text" or 'text'
        result = re.sub(rf'(["\']){re.escape(zh)}(["\'])', rf'\1{en}\2', result)
        # 3. Attribute values: placeholder="text"
        result = re.sub(rf'(placeholder\s*=\s*["\']){re.escape(zh)}(["\'])', rf'\1{en}\2', result)
        result = re.sub(rf'(title\s*=\s*["\']){re.escape(zh)}(["\'])', rf'\1{en}\2', result)
        result = re.sub(rf'(label\s*=\s*["\']){re.escape(zh)}(["\'])', rf'\1{en}\2', result)
        # 4. Toast/message content
        result = re.sub(rf'(message:\s*["\']){re.escape(zh)}(["\'])', rf'\1{en}\2', result)
        result = re.sub(rf'(showMessage\(["\']){re.escape(zh)}(["\'])', rf'\1{en}\2', result)
        # 5. Plain replacement for remaining cases
        result = result.replace(zh, en)

    return result

def process_vue_file(file_path):
    """Process a single Vue file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        content = translate_vue_text(content)

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
    frontend_dir = Path(__file__).parent.parent  # Go up from backend to project root
    src_dir = frontend_dir / "src"

    if not src_dir.exists():
        print(f"Error: Frontend src directory not found: {src_dir}")
        return

    # Find all Vue, JS, TS files in src directory
    vue_files = []
    for ext in ['*.vue', '*.js', '*.ts']:
        vue_files.extend(src_dir.rglob(ext))

    # Exclude node_modules and dist
    vue_files = [f for f in vue_files if 'node_modules' not in str(f) and 'dist' not in str(f)]

    print(f"Found {len(vue_files)} frontend files to process...\n")

    updated_count = 0
    for file_path in vue_files:
        rel_path = file_path.relative_to(src_dir)
        if process_vue_file(file_path):
            print(f"  ✓ Updated: {rel_path}")
            updated_count += 1

    print(f"\n{'='*60}")
    print(f"Frontend translation complete:")
    print(f"  {updated_count}/{len(vue_files)} files updated")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
