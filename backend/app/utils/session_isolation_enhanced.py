"""
Session Isolation Enhancement
会话隔离机制强化模块

Features:
1. 会话有效性验证
2. 会话过期检测
3. 会话所有权严格验证
4. 会话活动追踪
5. 防御性安全检查
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import database

logger = logging.getLogger(__name__)


class SessionValidator:
    """
    会话验证器

    提供严格的会话验证和安全检查
    """

    def __init__(self, expiry_days: int = 30):
        """
        Args:
            expiry_days: 会话过期天数 (default30天未活动)
        """
        self.expiry_days = expiry_days

    def validate_conversation_access(
        self,
        conversation_id: int,
        user_id: int,
        require_active: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        验证用户对会话的访问权限

        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            require_active: 是否要求会话处于活跃状态

        Returns:
            (is_valid, error_message)
            - is_valid: True if valid, False otherwise
            - error_message: Error description if invalid, None otherwise
        """
        # 1. 检查会话是否存在
        conversation = database.get_conversation_by_id(conversation_id, user_id)

        if not conversation:
            logger.warning(
                f"Conversation {conversation_id} not found for user {user_id}"
            )
            return False, "Conversation not found or access denied"

        # 2. 验证所有权
        if conversation['user_id'] != user_id:
            logger.error(
                f"Ownership violation: User {user_id} attempted to access "
                f"conversation {conversation_id} owned by user {conversation['user_id']}"
            )
            return False, "Access denied: You don't own this conversation"

        # 3. check if expired (如果要求活跃状态)
        if require_active:
            is_expired, expiry_msg = self.is_conversation_expired(conversation)
            if is_expired:
                logger.warning(
                    f"Conversation {conversation_id} has expired: {expiry_msg}"
                )
                return False, expiry_msg

        logger.debug(
            f"Conversation {conversation_id} validated for user {user_id}"
        )
        return True, None

    def is_conversation_expired(
        self,
        conversation: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        检查会话是否过期

        Args:
            conversation: 会话对象 (from database)

        Returns:
            (is_expired, message)
        """
        if not conversation:
            return True, "Conversation does not exist"

        updated_at_str = conversation.get('updated_at')

        if not updated_at_str:
            # 如果没有更新时间,使用创建时间
            updated_at_str = conversation.get('created_at')

        if not updated_at_str:
            logger.warning(f"Conversation {conversation['id']} has no timestamp")
            return True, "Invalid conversation timestamp"

        try:
            # 解析时间戳 (SQLite格式: YYYY-MM-DD HH:MM:SS)
            updated_at = datetime.strptime(updated_at_str, '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.error(f"Failed to parse timestamp '{updated_at_str}': {e}")
            return True, "Invalid conversation timestamp format"

        # 计算时间差
        now = datetime.now()
        age = now - updated_at

        # 检查是否超过过期时间
        if age > timedelta(days=self.expiry_days):
            days_ago = age.days
            return True, (
                f"Conversation expired: Last activity was {days_ago} days ago "
                f"(max: {self.expiry_days} days)"
            )

        return False, None

    def validate_conversation_for_upload(
        self,
        conversation_id: Optional[int],
        user_id: int
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        验证会话是否可用于Document uploaded

        Args:
            conversation_id: 会话ID (可选)
            user_id: 用户ID

        Returns:
            (is_valid, validated_conversation_id, error_message)
        """
        # 如果没有conversation_id,创建新的
        if not conversation_id:
            logger.info(f"No conversation_id provided, will create new conversation")
            return True, None, None

        # 验证现有会话
        is_valid, error_msg = self.validate_conversation_access(
            conversation_id=conversation_id,
            user_id=user_id,
            require_active=True
        )

        if not is_valid:
            return False, None, error_msg

        return True, conversation_id, None

    def validate_conversation_for_chat(
        self,
        conversation_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        验证会话是否可用于聊天

        Args:
            conversation_id: 会话ID
            user_id: 用户ID

        Returns:
            (is_valid, error_message)
        """
        return self.validate_conversation_access(
            conversation_id=conversation_id,
            user_id=user_id,
            require_active=True
        )

    def check_conversation_health(
        self,
        conversation_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        检查会话健康状态

        Args:
            conversation_id: 会话ID
            user_id: 用户ID

        Returns:
            {
                "exists": bool,
                "owned_by_user": bool,
                "is_expired": bool,
                "message_count": int,
                "document_count": int,
                "last_activity": str,
                "age_days": int,
                "health_status": "healthy" | "expiring" | "expired" | "invalid"
            }
        """
        # 获取会话
        conversation = database.get_conversation_by_id(conversation_id, user_id)

        if not conversation:
            return {
                "exists": False,
                "owned_by_user": False,
                "is_expired": True,
                "message_count": 0,
                "document_count": 0,
                "last_activity": None,
                "age_days": 0,
                "health_status": "invalid"
            }

        # 检查所有权
        owned = conversation['user_id'] == user_id

        # check expiration
        is_expired, _ = self.is_conversation_expired(conversation)

        # 获取消息数量
        messages = database.get_conversation_messages(conversation_id, limit=1)
        message_count = conversation.get('message_count', len(messages))

        # 获取文档数量
        has_docs = database.has_user_documents(user_id, conversation_id)
        # 注意: 这只是boolean,需要实际计数可以扩展database.py

        # 计算年龄
        updated_at_str = conversation.get('updated_at') or conversation.get('created_at')
        age_days = 0
        if updated_at_str:
            try:
                updated_at = datetime.strptime(updated_at_str, '%Y-%m-%d %H:%M:%S')
                age_days = (datetime.now() - updated_at).days
            except:
                pass

        # 判断健康状态
        if not owned:
            health_status = "invalid"
        elif is_expired:
            health_status = "expired"
        elif age_days > self.expiry_days * 0.8:  # 超过80%时间
            health_status = "expiring"
        else:
            health_status = "healthy"

        return {
            "exists": True,
            "owned_by_user": owned,
            "is_expired": is_expired,
            "message_count": message_count,
            "document_count": 1 if has_docs else 0,  # 简化版本
            "last_activity": updated_at_str,
            "age_days": age_days,
            "health_status": health_status
        }

    def cleanup_expired_conversations(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        清理用户的过期会话

        Args:
            user_id: 用户ID

        Returns:
            {
                "total_conversations": int,
                "expired_count": int,
                "deleted_count": int,
                "deleted_ids": List[int]
            }
        """
        # 获取用户所有会话
        conversations = database.get_user_conversations(user_id)

        total = len(conversations)
        expired = []

        for conv in conversations:
            is_exp, _ = self.is_conversation_expired(conv)
            if is_exp:
                expired.append(conv['id'])

        # 删除过期会话
        deleted = []
        for conv_id in expired:
            try:
                success = database.delete_conversation(conv_id, user_id)
                if success:
                    deleted.append(conv_id)
                    logger.info(f"Deleted expired conversation {conv_id} for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to delete conversation {conv_id}: {e}")

        return {
            "total_conversations": total,
            "expired_count": len(expired),
            "deleted_count": len(deleted),
            "deleted_ids": deleted
        }


# ==================== 全局验证器实例 ====================

# default30天过期
session_validator = SessionValidator(expiry_days=30)


# ==================== 便捷函数 ====================

def validate_conversation_access(
    conversation_id: int,
    user_id: int,
    require_active: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    验证会话访问权限 (便捷函数)

    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        require_active: 是否要求活跃状态

    Returns:
        (is_valid, error_message)
    """
    return session_validator.validate_conversation_access(
        conversation_id=conversation_id,
        user_id=user_id,
        require_active=require_active
    )


def is_conversation_expired(conversation_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
    """
    检查会话是否过期 (便捷函数)

    Args:
        conversation_id: 会话ID
        user_id: 用户ID

    Returns:
        (is_expired, message)
    """
    conversation = database.get_conversation_by_id(conversation_id, user_id)
    if not conversation:
        return True, "Conversation not found"

    return session_validator.is_conversation_expired(conversation)


def check_conversation_health(conversation_id: int, user_id: int) -> Dict[str, Any]:
    """
    检查会话健康状态 (便捷函数)

    Returns:
        Health status dictionary
    """
    return session_validator.check_conversation_health(conversation_id, user_id)


# ==================== usage examples ====================

def example_usage():
    """usage examples"""
    # 假设用户ID和会话ID
    user_id = 1
    conversation_id = 123

    # 1. 验证会话访问
    is_valid, error = validate_conversation_access(conversation_id, user_id)

    if not is_valid:
        print(f"❌ 访问被拒绝: {error}")
        return

    print("✅ 会话访问验证通过")

    # 2. 检查会话健康
    health = check_conversation_health(conversation_id, user_id)

    print(f"会话健康状态: {health['health_status']}")
    print(f"  - 消息数: {health['message_count']}")
    print(f"  - 年龄: {health['age_days']} 天")
    print(f"  - 最后活动: {health['last_activity']}")

    # 3. check if expired
    is_exp, msg = is_conversation_expired(conversation_id, user_id)

    if is_exp:
        print(f"⚠️  会话已过期: {msg}")
    else:
        print("✅ 会话处于活跃状态")


if __name__ == "__main__":
    print("="*70)
    print("会话隔离增强模块 - 测试")
    print("="*70)
    example_usage()
