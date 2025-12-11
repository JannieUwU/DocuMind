"""
API Key Encryption Manager
API密钥加密管理器

Features:
1. 主密钥管理
2. API密钥加密/解密
3. 安全存储
4. 密钥轮换支持
"""
import os
import logging
from cryptography.fernet import Fernet
from typing import Optional, Dict
import base64
import hashlib

logger = logging.getLogger(__name__)


class KeyManager:
    """
    密钥管理器

    使用Fernet对称加密保护API密钥
    """

    def __init__(self, master_key: Optional[str] = None):
        """
        Args:
            master_key: 主加密密钥 (可选)
                       如果未提供,从环境变量 MASTER_ENCRYPTION_KEY 读取
                       如果环境变量也不存在,则生成新密钥
        """
        if master_key:
            self.master_key = master_key.encode()
        else:
            # 尝试从环境变量读取
            master_key_env = os.environ.get("MASTER_ENCRYPTION_KEY")

            if master_key_env:
                logger.info("Using master key from environment variable")
                self.master_key = master_key_env.encode()
            else:
                # 生成新密钥 (仅开发环境)
                logger.warning(
                    "⚠️  No master key found! Generating new key. "
                    "IMPORTANT: Save this key securely!"
                )
                self.master_key = Fernet.generate_key()
                logger.warning(
                    f"Generated master key: {self.master_key.decode()}"
                )
                logger.warning(
                    "⚠️  Set MASTER_ENCRYPTION_KEY environment variable "
                    "with this key for production!"
                )

        # initialized加密器
        try:
            self.cipher = Fernet(self.master_key)
            logger.info("✓ Encryption cipher initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize cipher: {e}")
            raise ValueError("Invalid master key format")

    def encrypt_api_key(self, api_key: str) -> str:
        """
        加密API密钥

        Args:
            api_key: 明文API密钥

        Returns:
            加密后的密钥 (base64编码string)
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        try:
            encrypted = self.cipher.encrypt(api_key.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {e}")
            raise ValueError("Encryption failed")

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        解密API密钥

        Args:
            encrypted_key: 加密的API密钥

        Returns:
            明文API密钥
        """
        if not encrypted_key:
            raise ValueError("Encrypted key cannot be empty")

        try:
            decrypted = self.cipher.decrypt(encrypted_key.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            raise ValueError("Decryption failed - key may be corrupted or invalid")

    def hash_api_key(self, api_key: str) -> str:
        """
        生成API密钥的哈希值 (用于验证或日志)

        Args:
            api_key: API密钥

        Returns:
            SHA256哈希值 (前8位)
        """
        hash_obj = hashlib.sha256(api_key.encode())
        return hash_obj.hexdigest()[:8]

    def encrypt_config(self, config: Dict[str, str]) -> Dict[str, str]:
        """
        加密整个configuration dictionary

        Args:
            config: configuration dictionary {"openai": "sk-xxx", "gemini": "..."}

        Returns:
            加密后的configuration dictionary
        """
        encrypted_config = {}

        for key, value in config.items():
            if value and isinstance(value, str):
                try:
                    encrypted_config[key] = self.encrypt_api_key(value)
                    logger.debug(f"Encrypted {key} API key")
                except Exception as e:
                    logger.error(f"Failed to encrypt {key}: {e}")
                    encrypted_config[key] = value  # 保持原值
            else:
                encrypted_config[key] = value

        return encrypted_config

    def decrypt_config(self, encrypted_config: Dict[str, str]) -> Dict[str, str]:
        """
        解密整个configuration dictionary

        Args:
            encrypted_config: 加密的configuration dictionary

        Returns:
            明文configuration dictionary
        """
        decrypted_config = {}

        for key, value in encrypted_config.items():
            if value and isinstance(value, str):
                try:
                    decrypted_config[key] = self.decrypt_api_key(value)
                    logger.debug(f"Decrypted {key} API key")
                except:
                    # 如果解密失败,可能是未加密的值,保持原样
                    decrypted_config[key] = value
            else:
                decrypted_config[key] = value

        return decrypted_config

    def validate_api_key_format(self, api_key: str, service: str) -> bool:
        """
        验证API密钥格式是否正确

        Args:
            api_key: API密钥
            service: 服务名称 (openai/gemini/etc)

        Returns:
            是否有效
        """
        if not api_key:
            return False

        # OpenAI格式验证
        if service == "openai":
            return api_key.startswith("sk-") and len(api_key) > 20

        # Gemini格式验证
        elif service == "gemini":
            return len(api_key) > 20

        # 其他服务
        else:
            return len(api_key) > 10

    @staticmethod
    def generate_master_key() -> str:
        """
        生成新的主密钥

        Returns:
            Base64编码的主密钥
        """
        return Fernet.generate_key().decode()

    def rotate_keys(
        self,
        old_encrypted_config: Dict[str, str],
        new_key_manager: 'KeyManager'
    ) -> Dict[str, str]:
        """
        密钥轮换 - 用新密钥重新加密

        Args:
            old_encrypted_config: 使用旧密钥加密的配置
            new_key_manager: 新的密钥管理器

        Returns:
            使用新密钥加密的配置
        """
        # 1. 用旧密钥解密
        decrypted = self.decrypt_config(old_encrypted_config)

        # 2. 用新密钥加密
        re_encrypted = new_key_manager.encrypt_config(decrypted)

        logger.info("✓ Key rotation completed successfully")
        return re_encrypted


# ==================== 全局密钥管理器 ====================

# initialized全局密钥管理器
try:
    key_manager = KeyManager()
    logger.info("✓ Global KeyManager initialized")
except Exception as e:
    logger.error(f"Failed to initialize KeyManager: {e}")
    # 如果initialized失败,创建临时密钥管理器 (仅用于开发)
    logger.warning("Using temporary KeyManager - NOT FOR PRODUCTION!")
    key_manager = KeyManager(master_key=Fernet.generate_key().decode())


# ==================== 便捷函数 ====================

def encrypt_api_key(api_key: str) -> str:
    """加密API密钥 (便捷函数)"""
    return key_manager.encrypt_api_key(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """解密API密钥 (便捷函数)"""
    return key_manager.decrypt_api_key(encrypted_key)


def encrypt_config(config: Dict[str, str]) -> Dict[str, str]:
    """加密配置 (便捷函数)"""
    return key_manager.encrypt_config(config)


def decrypt_config(encrypted_config: Dict[str, str]) -> Dict[str, str]:
    """解密配置 (便捷函数)"""
    return key_manager.decrypt_config(encrypted_config)


# ==================== usage examples ====================

def example_usage():
    """usage examples"""
    print("="*70)
    print("密钥加密管理器 - usage examples")
    print("="*70)

    # 1. 加密单个API密钥
    print("\n1. 加密单个API密钥:")
    api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
    encrypted = key_manager.encrypt_api_key(api_key)

    print(f"原始密钥: {api_key[:10]}...")
    print(f"加密后: {encrypted[:50]}...")

    # 2. 解密
    print("\n2. 解密:")
    decrypted = key_manager.decrypt_api_key(encrypted)
    print(f"解密后: {decrypted[:10]}...")
    print(f"匹配: {decrypted == api_key}")

    # 3. 加密整个配置
    print("\n3. 加密配置:")
    config = {
        "openai": "sk-openai-key-12345",
        "gemini": "gemini-key-67890",
        "jina": "jina-key-abcde"
    }

    encrypted_config = key_manager.encrypt_config(config)
    print("加密的配置:")
    for key, value in encrypted_config.items():
        print(f"  {key}: {value[:30]}...")

    # 4. 解密配置
    print("\n4. 解密配置:")
    decrypted_config = key_manager.decrypt_config(encrypted_config)
    print("解密的配置:")
    for key, value in decrypted_config.items():
        print(f"  {key}: {value[:15]}...")

    # 5. 密钥哈希
    print("\n5. 密钥哈希 (用于日志):")
    key_hash = key_manager.hash_api_key(api_key)
    print(f"密钥哈希: {key_hash}")

    # 6. 格式验证
    print("\n6. 格式验证:")
    print(f"OpenAI格式: {key_manager.validate_api_key_format('sk-test123', 'openai')}")
    print(f"Gemini格式: {key_manager.validate_api_key_format('gemini-test123456789', 'gemini')}")


if __name__ == "__main__":
    example_usage()
