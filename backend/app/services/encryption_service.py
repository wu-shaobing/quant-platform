"""
数据加密服务
提供CTP交易数据的加密和解密功能
"""
import base64
import secrets
import logging
from typing import Dict, List, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """数据加密服务"""
    
    # CTP敏感字段定义
    CTP_SENSITIVE_FIELDS = [
        "password",           # 密码
        "broker_id",         # 经纪商ID
        "user_id",           # 用户ID
        "investor_id",       # 投资者ID
        "auth_code",         # 认证码
        "app_id",            # 应用ID
        "trading_day",       # 交易日
        "front_address",     # 前置地址
        "md_address",        # 行情地址
        "account_id",        # 账户ID
        "bank_account",      # 银行账户
        "bank_password",     # 银行密码
        "currency_id",       # 货币代码
        "customer_name",     # 客户姓名
        "id_card_type",      # 证件类型
        "id_card_no",        # 证件号码
        "mobile",            # 手机号
        "email",             # 邮箱
        "address",           # 地址
    ]
    
    def __init__(self):
        self.master_key = self._get_master_key()
        self.key_length = 32
        self.salt_length = 16
        self.iterations = 100000
    
    def _get_master_key(self) -> str:
        """获取主密钥"""
        master_key = getattr(settings, 'ENCRYPTION_MASTER_KEY', None)
        if not master_key:
            # 生成临时密钥（生产环境应该从安全存储中获取）
            master_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
            logger.warning("Using generated master key. Set ENCRYPTION_MASTER_KEY in production.")
        return master_key
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """派生加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_length,
            salt=salt,
            iterations=self.iterations,
        )
        return kdf.derive(password.encode())
    
    def encrypt_data(self, data: str, password: str = None) -> str:
        """加密数据"""
        try:
            # 使用密码或主密钥
            key_source = password or self.master_key
            
            # 生成随机盐值
            salt = secrets.token_bytes(self.salt_length)
            
            # 派生密钥
            key = self._derive_key(key_source, salt)
            
            # 创建Fernet加密器
            fernet = Fernet(base64.urlsafe_b64encode(key))
            
            # 加密数据
            encrypted_data = fernet.encrypt(data.encode())
            
            # 组合盐值和加密数据
            combined = salt + encrypted_data
            
            # Base64编码返回
            return base64.urlsafe_b64encode(combined).decode()
            
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise ValueError(f"Failed to encrypt data: {e}")
    
    def decrypt_data(self, encrypted_data: str, password: str = None) -> str:
        """解密数据"""
        try:
            # Base64解码
            combined = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # 分离盐值和加密数据
            salt = combined[:self.salt_length]
            encrypted_bytes = combined[self.salt_length:]
            
            # 使用密码或主密钥
            key_source = password or self.master_key
            
            # 重新派生密钥
            key = self._derive_key(key_source, salt)
            
            # 创建Fernet解密器
            fernet = Fernet(base64.urlsafe_b64encode(key))
            
            # 解密数据
            decrypted_data = fernet.decrypt(encrypted_bytes)
            
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise ValueError(f"Failed to decrypt data: {e}")
    
    def encrypt_ctp_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """加密CTP订单数据"""
        encrypted_order = order_data.copy()
        
        # 加密敏感字段
        for field in self.CTP_SENSITIVE_FIELDS:
            if field in encrypted_order and encrypted_order[field]:
                encrypted_order[field] = self.encrypt_data(str(encrypted_order[field]))
        
        # 标记为已加密
        encrypted_order["_encrypted"] = True
        encrypted_order["_encryption_version"] = "1.0"
        
        return encrypted_order
    
    def decrypt_ctp_order(self, encrypted_order: Dict[str, Any]) -> Dict[str, Any]:
        """解密CTP订单数据"""
        if not encrypted_order.get("_encrypted"):
            return encrypted_order
        
        decrypted_order = encrypted_order.copy()
        
        # 解密敏感字段
        for field in self.CTP_SENSITIVE_FIELDS:
            if field in decrypted_order and decrypted_order[field]:
                try:
                    decrypted_order[field] = self.decrypt_data(decrypted_order[field])
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field}: {e}")
                    decrypted_order[field] = None
        
        # 移除加密标记
        decrypted_order.pop("_encrypted", None)
        decrypted_order.pop("_encryption_version", None)
        
        return decrypted_order
    
    def encrypt_ctp_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """加密CTP账户数据"""
        encrypted_account = account_data.copy()
        
        # 账户特定的敏感字段
        account_sensitive_fields = [
            "broker_id", "user_id", "investor_id", "password", 
            "auth_code", "app_id", "front_address", "md_address"
        ]
        
        for field in account_sensitive_fields:
            if field in encrypted_account and encrypted_account[field]:
                encrypted_account[field] = self.encrypt_data(str(encrypted_account[field]))
        
        encrypted_account["_encrypted"] = True
        return encrypted_account
    
    def decrypt_ctp_account(self, encrypted_account: Dict[str, Any]) -> Dict[str, Any]:
        """解密CTP账户数据"""
        if not encrypted_account.get("_encrypted"):
            return encrypted_account
        
        decrypted_account = encrypted_account.copy()
        
        account_sensitive_fields = [
            "broker_id", "user_id", "investor_id", "password", 
            "auth_code", "app_id", "front_address", "md_address"
        ]
        
        for field in account_sensitive_fields:
            if field in decrypted_account and decrypted_account[field]:
                try:
                    decrypted_account[field] = self.decrypt_data(decrypted_account[field])
                except Exception as e:
                    logger.error(f"Failed to decrypt account field {field}: {e}")
                    decrypted_account[field] = None
        
        decrypted_account.pop("_encrypted", None)
        return decrypted_account
    
    def encrypt_sensitive_fields(
        self, 
        data: Dict[str, Any], 
        sensitive_fields: List[str]
    ) -> Dict[str, Any]:
        """加密指定的敏感字段"""
        encrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt_data(str(encrypted_data[field]))
        
        encrypted_data["_encrypted_fields"] = sensitive_fields
        return encrypted_data
    
    def decrypt_sensitive_fields(
        self, 
        encrypted_data: Dict[str, Any], 
        sensitive_fields: List[str] = None
    ) -> Dict[str, Any]:
        """解密指定的敏感字段"""
        # 如果没有指定字段，从数据中获取
        if sensitive_fields is None:
            sensitive_fields = encrypted_data.get("_encrypted_fields", [])
        
        decrypted_data = encrypted_data.copy()
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt_data(decrypted_data[field])
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field}: {e}")
                    decrypted_data[field] = None
        
        decrypted_data.pop("_encrypted_fields", None)
        return decrypted_data
    
    def batch_encrypt(self, data_list: List[Dict[str, Any]], data_type: str = "order") -> List[Dict[str, Any]]:
        """批量加密数据"""
        encrypted_list = []
        
        for data in data_list:
            try:
                if data_type == "order":
                    encrypted_data = self.encrypt_ctp_order(data)
                elif data_type == "account":
                    encrypted_data = self.encrypt_ctp_account(data)
                else:
                    encrypted_data = self.encrypt_sensitive_fields(data, self.CTP_SENSITIVE_FIELDS)
                
                encrypted_list.append(encrypted_data)
                
            except Exception as e:
                logger.error(f"Failed to encrypt data item: {e}")
                encrypted_list.append(data)  # 保留原始数据
        
        return encrypted_list
    
    def batch_decrypt(self, encrypted_list: List[Dict[str, Any]], data_type: str = "order") -> List[Dict[str, Any]]:
        """批量解密数据"""
        decrypted_list = []
        
        for encrypted_data in encrypted_list:
            try:
                if data_type == "order":
                    decrypted_data = self.decrypt_ctp_order(encrypted_data)
                elif data_type == "account":
                    decrypted_data = self.decrypt_ctp_account(encrypted_data)
                else:
                    decrypted_data = self.decrypt_sensitive_fields(encrypted_data)
                
                decrypted_list.append(decrypted_data)
                
            except Exception as e:
                logger.error(f"Failed to decrypt data item: {e}")
                decrypted_list.append(encrypted_data)  # 保留加密数据
        
        return decrypted_list
    
    def generate_secure_token(self, length: int = 32) -> str:
        """生成安全令牌"""
        return secrets.token_urlsafe(length)
    
    def hash_data(self, data: str) -> str:
        """哈希数据（不可逆）"""
        import hashlib
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_data_integrity(self, data: str, hash_value: str) -> bool:
        """验证数据完整性"""
        return self.hash_data(data) == hash_value


# 全局加密服务实例
encryption_service = EncryptionService()


# 导出主要组件
__all__ = [
    "EncryptionService",
    "encryption_service",
]
