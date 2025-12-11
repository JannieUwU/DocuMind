"""
Rate Limiting and Anti-Abuse System
限流和防滥用系统

Features:
1. 基于滑动窗口的限流
2. 多级限流策略
3. 用户级和IP级限流
4. 自动黑名单
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    限流器

    使用滑动窗口算法实现速率限制
    """

    def __init__(self):
        """initialized限流器"""
        # 存储请求时间戳 {user_id:operation -> [timestamps]}
        self.request_counts = defaultdict(list)

        # 限流规则 {operation: (max_requests, time_window_seconds)}
        self.limits = {
            "chat": (20, 60),           # 20次/minutes
            "upload": (10, 60),         # 10次/minutes
            "voice": (5, 60),           # 5次/minutes
            "login": (5, 300),          # 5次/5minutes
            "register": (3, 3600),      # 3次/小时
            "config_update": (10, 60),  # 10次/minutes
            "search": (30, 60),         # 30次/minutes
            "api_default": (100, 60)    # default限制
        }

        # 黑名单 {user_id -> (blocked_until, reason)}
        self.blacklist: Dict[str, Tuple[datetime, str]] = {}

        # 警告阈值 (达到限制的80%时警告)
        self.warning_threshold = 0.8

        logger.info("✓ RateLimiter initialized")

    def check_rate_limit(
        self,
        user_id: str,
        operation: str,
        cost: int = 1
    ) -> Tuple[bool, Optional[str]]:
        """
        检查是否超过速率限制

        Args:
            user_id: 用户ID或IP地址
            operation: 操作类型 (chat/upload/voice等)
            cost: 请求成本 (default1, 可以设置更高的值)

        Returns:
            (is_allowed, error_message)
            - is_allowed: True if allowed, False if rate limited
            - error_message: Error message if rate limited
        """
        # 1. 检查黑名单
        if user_id in self.blacklist:
            blocked_until, reason = self.blacklist[user_id]
            if datetime.now() < blocked_until:
                remaining = (blocked_until - datetime.now()).seconds
                logger.warning(
                    f"Blocked request from blacklisted user {user_id}: {reason}"
                )
                return False, f"Temporarily blocked: {reason}. Retry after {remaining}s"
            else:
                # 黑名单已过期,移除
                del self.blacklist[user_id]
                logger.info(f"Removed {user_id} from blacklist")

        # 2. 获取限流规则
        limit_count, limit_seconds = self.limits.get(
            operation,
            self.limits["api_default"]
        )

        # 3. 生成键
        key = f"{user_id}:{operation}"

        # 4. 清理过期记录 (滑动窗口)
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=limit_seconds)

        self.request_counts[key] = [
            ts for ts in self.request_counts[key]
            if ts > cutoff_time
        ]

        # 5. 检查是否超限
        current_count = len(self.request_counts[key])

        if current_count + cost > limit_count:
            # 超限
            retry_after = limit_seconds - (now - self.request_counts[key][0]).seconds
            logger.warning(
                f"Rate limit exceeded for {user_id} on {operation}: "
                f"{current_count}/{limit_count} in {limit_seconds}s"
            )

            # 检查是否需要加入黑名单 (频繁触发限流)
            self._check_blacklist_trigger(user_id, operation)

            return False, (
                f"Rate limit exceeded. Max {limit_count} requests per "
                f"{limit_seconds}s. Retry after {retry_after}s."
            )

        # 6. 警告检查
        if current_count >= limit_count * self.warning_threshold:
            logger.info(
                f"Rate limit warning for {user_id} on {operation}: "
                f"{current_count}/{limit_count}"
            )

        # 7. 记录请求
        for _ in range(cost):
            self.request_counts[key].append(now)

        return True, None

    def _check_blacklist_trigger(self, user_id: str, operation: str):
        """检查是否需要临时加入黑名单"""
        # 统计最近10minutes的限流触发次数
        violation_key = f"{user_id}:violations"
        now = datetime.now()
        cutoff = now - timedelta(minutes=10)

        # 清理旧记录
        self.request_counts[violation_key] = [
            ts for ts in self.request_counts[violation_key]
            if ts > cutoff
        ]

        # 记录本次违规
        self.request_counts[violation_key].append(now)

        # 检查违规次数
        violation_count = len(self.request_counts[violation_key])

        if violation_count >= 5:  # 10minutes内5次限流触发
            # 加入黑名单30minutes
            blocked_until = now + timedelta(minutes=30)
            reason = f"Excessive rate limit violations ({violation_count} times)"

            self.blacklist[user_id] = (blocked_until, reason)

            logger.error(
                f"Added {user_id} to blacklist for 30 minutes: {reason}"
            )

    def get_remaining_quota(
        self,
        user_id: str,
        operation: str
    ) -> Dict[str, any]:
        """
        获取剩余配额

        Args:
            user_id: 用户ID
            operation: 操作类型

        Returns:
            {
                "limit": int,
                "used": int,
                "remaining": int,
                "reset_in": int (seconds)
            }
        """
        limit_count, limit_seconds = self.limits.get(
            operation,
            self.limits["api_default"]
        )

        key = f"{user_id}:{operation}"
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=limit_seconds)

        # 清理过期记录
        self.request_counts[key] = [
            ts for ts in self.request_counts[key]
            if ts > cutoff_time
        ]

        used = len(self.request_counts[key])
        remaining = max(0, limit_count - used)

        # 计算重置时间
        if self.request_counts[key]:
            oldest_request = self.request_counts[key][0]
            reset_in = limit_seconds - (now - oldest_request).seconds
        else:
            reset_in = 0

        return {
            "limit": limit_count,
            "used": used,
            "remaining": remaining,
            "reset_in": reset_in,
            "window_seconds": limit_seconds
        }

    def reset_user_limits(self, user_id: str):
        """重置用户的所有限流计数"""
        # 移除所有相关键
        keys_to_remove = [
            key for key in self.request_counts.keys()
            if key.startswith(f"{user_id}:")
        ]

        for key in keys_to_remove:
            del self.request_counts[key]

        logger.info(f"Reset rate limits for user {user_id}")

    def add_to_blacklist(
        self,
        user_id: str,
        duration_minutes: int,
        reason: str
    ):
        """手动添加到黑名单"""
        blocked_until = datetime.now() + timedelta(minutes=duration_minutes)
        self.blacklist[user_id] = (blocked_until, reason)

        logger.warning(
            f"Manually added {user_id} to blacklist for {duration_minutes} min: {reason}"
        )

    def remove_from_blacklist(self, user_id: str):
        """从黑名单移除"""
        if user_id in self.blacklist:
            del self.blacklist[user_id]
            logger.info(f"Removed {user_id} from blacklist")
            return True
        return False

    def get_stats(self) -> Dict[str, any]:
        """获取限流器statistics"""
        # 统计活跃用户
        active_users = set()
        for key in self.request_counts.keys():
            if ':' in key:
                user_id = key.split(':')[0]
                active_users.add(user_id)

        # 统计总请求数
        total_requests = sum(len(timestamps) for timestamps in self.request_counts.values())

        return {
            "active_users": len(active_users),
            "total_requests_tracked": total_requests,
            "blacklisted_users": len(self.blacklist),
            "blacklist": {
                user_id: {
                    "blocked_until": blocked_until.isoformat(),
                    "reason": reason
                }
                for user_id, (blocked_until, reason) in self.blacklist.items()
            }
        }

    def update_limits(self, operation: str, max_requests: int, window_seconds: int):
        """更新限流规则"""
        self.limits[operation] = (max_requests, window_seconds)
        logger.info(
            f"Updated rate limit for {operation}: "
            f"{max_requests} requests per {window_seconds}s"
        )


# ==================== 全局限流器 ====================

rate_limiter = RateLimiter()


# ==================== 便捷函数 ====================

def check_rate_limit(
    user_id: str,
    operation: str,
    cost: int = 1
) -> Tuple[bool, Optional[str]]:
    """检查限流 (便捷函数)"""
    return rate_limiter.check_rate_limit(user_id, operation, cost)


def get_remaining_quota(user_id: str, operation: str) -> Dict:
    """获取剩余配额 (便捷函数)"""
    return rate_limiter.get_remaining_quota(user_id, operation)


# ==================== 装饰器 ====================

def rate_limit(operation: str, cost: int = 1):
    """
    限流装饰器

    用法:
        @rate_limit("chat")
        def my_function(user_id: str):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 尝试从参数中提取user_id
            user_id = kwargs.get('user_id') or kwargs.get('username')

            if not user_id and args:
                user_id = args[0] if isinstance(args[0], str) else None

            if not user_id:
                raise ValueError("Cannot apply rate limit: user_id not found")

            # 检查限流
            is_allowed, error_msg = rate_limiter.check_rate_limit(
                user_id, operation, cost
            )

            if not is_allowed:
                from fastapi import HTTPException
                raise HTTPException(status_code=429, detail=error_msg)

            # 执行原函数
            return func(*args, **kwargs)

        return wrapper
    return decorator


# ==================== usage examples ====================

def example_usage():
    """usage examples"""
    print("="*70)
    print("限流器 - usage examples")
    print("="*70)

    # 1. 基础限流检查
    print("\n1. 基础限流检查:")
    user_id = "user123"

    for i in range(25):
        is_allowed, error = rate_limiter.check_rate_limit(user_id, "chat")

        if not is_allowed:
            print(f"  请求 {i+1}: ✗ 被限流 - {error}")
            break
        else:
            print(f"  请求 {i+1}: ✓ 允许")

    # 2. 查询剩余配额
    print("\n2. 剩余配额:")
    quota = rate_limiter.get_remaining_quota(user_id, "chat")
    print(f"  限制: {quota['limit']} 请求/{quota['window_seconds']}seconds")
    print(f"  已使用: {quota['used']}")
    print(f"  剩余: {quota['remaining']}")
    print(f"  重置倒计时: {quota['reset_in']}seconds")

    # 3. 不同操作类型
    print("\n3. 不同操作类型:")
    operations = ["chat", "upload", "voice"]

    for op in operations:
        is_allowed, _ = rate_limiter.check_rate_limit(user_id, op)
        quota = rate_limiter.get_remaining_quota(user_id, op)
        print(f"  {op}: {quota['remaining']}/{quota['limit']} 剩余")

    # 4. 黑名单测试
    print("\n4. 黑名单:")
    rate_limiter.add_to_blacklist("abuser123", 5, "Manual ban for testing")

    is_allowed, error = rate_limiter.check_rate_limit("abuser123", "chat")
    print(f"  黑名单用户请求: {'✓ 允许' if is_allowed else '✗ 拒绝'}")
    if error:
        print(f"  原因: {error}")

    # 5. statistics
    print("\n5. statistics:")
    stats = rate_limiter.get_stats()
    print(f"  活跃用户: {stats['active_users']}")
    print(f"  总请求数: {stats['total_requests_tracked']}")
    print(f"  黑名单用户: {stats['blacklisted_users']}")


if __name__ == "__main__":
    example_usage()
