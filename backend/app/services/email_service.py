"""
邮件服务
提供邮件发送功能，包括欢迎邮件、密码重置邮件等
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
import asyncio
from datetime import datetime
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.smtp_server = self.settings.SMTP_SERVER
        self.smtp_port = self.settings.SMTP_PORT
        self.smtp_username = self.settings.SMTP_USERNAME
        self.smtp_password = self.settings.SMTP_PASSWORD
        self.use_tls = self.settings.SMTP_USE_TLS
        self.from_email = self.settings.FROM_EMAIL
        self.from_name = self.settings.FROM_NAME
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        发送邮件
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML内容
            text_content: 纯文本内容
            attachments: 附件列表
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 创建邮件对象
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # 添加纯文本内容
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)
            
            # 添加HTML内容
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    await self._add_attachment(message, file_path)
            
            # 发送邮件
            await self._send_message(message, to_email)
            
            logger.info(f"邮件发送成功: {to_email} - {subject}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {to_email} - {subject} - {str(e)}")
            return False
    
    async def _send_message(self, message: MIMEMultipart, to_email: str):
        """发送邮件消息"""
        def _send():
            # 创建SMTP连接
            if self.use_tls:
                context = ssl.create_default_context()
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            # 登录
            server.login(self.smtp_username, self.smtp_password)
            
            # 发送邮件
            server.sendmail(self.from_email, to_email, message.as_string())
            server.quit()
        
        # 在线程池中执行同步操作
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send)
    
    async def _add_attachment(self, message: MIMEMultipart, file_path: str):
        """添加附件"""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {file_path.split('/')[-1]}"
            )
            message.attach(part)
        except Exception as e:
            logger.error(f"添加附件失败: {file_path} - {str(e)}")
    
    async def send_welcome_email(self, to_email: str, username: str) -> bool:
        """
        发送欢迎邮件
        
        Args:
            to_email: 用户邮箱
            username: 用户名
            
        Returns:
            bool: 发送是否成功
        """
        subject = "欢迎加入量化投资平台"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>欢迎加入量化投资平台</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .feature {{ margin: 15px 0; padding: 15px; background: white; border-radius: 5px; border-left: 4px solid #667eea; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 欢迎加入量化投资平台！</h1>
                    <p>您的量化投资之旅从这里开始</p>
                </div>
                
                <div class="content">
                    <h2>亲爱的 {username}，</h2>
                    <p>感谢您注册我们的量化投资平台！我们很高兴您能成为我们社区的一员。</p>
                    
                    <h3>🚀 平台特色功能</h3>
                    <div class="feature">
                        <strong>📊 实时行情数据</strong><br>
                        获取全市场实时行情，支持多种金融产品
                    </div>
                    <div class="feature">
                        <strong>⚡ 高频交易支持</strong><br>
                        毫秒级订单执行，支持多种交易策略
                    </div>
                    <div class="feature">
                        <strong>🎛️ 专业回测引擎</strong><br>
                        强大的策略回测功能，支持复杂策略验证
                    </div>
                    <div class="feature">
                        <strong>📈 智能风控系统</strong><br>
                        多层级风险控制，保护您的投资安全
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{self.settings.FRONTEND_URL}/dashboard" class="button">
                            立即开始使用
                        </a>
                    </div>
                    
                    <p>如果您有任何问题或需要帮助，请随时联系我们的客服团队。</p>
                    
                    <p>祝您投资顺利！</p>
                    <p><strong>量化投资平台团队</strong></p>
                </div>
                
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复</p>
                    <p>© 2024 量化投资平台. 保留所有权利.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        欢迎加入量化投资平台！
        
        亲爱的 {username}，
        
        感谢您注册我们的量化投资平台！我们很高兴您能成为我们社区的一员。
        
        平台特色功能：
        - 📊 实时行情数据：获取全市场实时行情，支持多种金融产品
        - ⚡ 高频交易支持：毫秒级订单执行，支持多种交易策略
        - 🎛️ 专业回测引擎：强大的策略回测功能，支持复杂策略验证
        - 📈 智能风控系统：多层级风险控制，保护您的投资安全
        
        立即访问: {self.settings.FRONTEND_URL}/dashboard
        
        如果您有任何问题或需要帮助，请随时联系我们的客服团队。
        
        祝您投资顺利！
        
        量化投资平台团队
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """
        发送密码重置邮件
        
        Args:
            to_email: 用户邮箱
            reset_token: 重置令牌
            
        Returns:
            bool: 发送是否成功
        """
        subject = "密码重置请求 - 量化投资平台"
        reset_url = f"{self.settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>密码重置请求</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f44336; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .button {{ display: inline-block; background: #f44336; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                .token {{ background: #f5f5f5; padding: 10px; border-radius: 3px; font-family: monospace; word-break: break-all; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 密码重置请求</h1>
                    <p>我们收到了您的密码重置请求</p>
                </div>
                
                <div class="content">
                    <p>您好，</p>
                    <p>我们收到了重置您账户密码的请求。如果这是您本人的操作，请点击下面的按钮重置密码：</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">
                            重置密码
                        </a>
                    </div>
                    
                    <p>或者复制以下链接到浏览器地址栏：</p>
                    <div class="token">{reset_url}</div>
                    
                    <div class="warning">
                        <strong>⚠️ 安全提醒：</strong><br>
                        • 此链接将在 15 分钟后过期<br>
                        • 如果您没有请求重置密码，请忽略此邮件<br>
                        • 为了您的账户安全，请不要将此链接分享给他人
                    </div>
                    
                    <p>如果您没有请求重置密码，您的账户可能面临安全风险，建议您：</p>
                    <ul>
                        <li>立即登录检查账户状态</li>
                        <li>修改密码以确保安全</li>
                        <li>联系客服团队获得帮助</li>
                    </ul>
                    
                    <p>如有任何疑问，请联系我们的客服团队。</p>
                    
                    <p><strong>量化投资平台团队</strong></p>
                </div>
                
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复</p>
                    <p>© 2024 量化投资平台. 保留所有权利.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        密码重置请求 - 量化投资平台
        
        您好，
        
        我们收到了重置您账户密码的请求。如果这是您本人的操作，请访问以下链接重置密码：
        
        {reset_url}
        
        安全提醒：
        • 此链接将在 15 分钟后过期
        • 如果您没有请求重置密码，请忽略此邮件
        • 为了您的账户安全，请不要将此链接分享给他人
        
        如果您没有请求重置密码，您的账户可能面临安全风险，建议您：
        - 立即登录检查账户状态
        - 修改密码以确保安全
        - 联系客服团队获得帮助
        
        如有任何疑问，请联系我们的客服团队。
        
        量化投资平台团队
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_password_reset_success_email(self, to_email: str) -> bool:
        """
        发送密码重置成功通知邮件
        
        Args:
            to_email: 用户邮箱
            
        Returns:
            bool: 发送是否成功
        """
        subject = "密码重置成功 - 量化投资平台"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>密码重置成功</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4caf50; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .success {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .button {{ display: inline-block; background: #4caf50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ 密码重置成功</h1>
                    <p>您的密码已成功重置</p>
                </div>
                
                <div class="content">
                    <div class="success">
                        <strong>🎉 恭喜！</strong><br>
                        您的账户密码已于 {current_time} 成功重置。
                    </div>
                    
                    <p>您现在可以使用新密码登录您的账户。为了确保账户安全，我们建议您：</p>
                    
                    <ul>
                        <li>使用强密码，包含大小写字母、数字和特殊字符</li>
                        <li>不要在多个网站使用相同密码</li>
                        <li>定期更换密码</li>
                        <li>启用双重认证（如果可用）</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="{self.settings.FRONTEND_URL}/login" class="button">
                            立即登录
                        </a>
                    </div>
                    
                    <p><strong>如果这不是您本人的操作，请立即联系我们的客服团队。</strong></p>
                    
                    <p>感谢您使用量化投资平台！</p>
                    
                    <p><strong>量化投资平台团队</strong></p>
                </div>
                
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复</p>
                    <p>© 2024 量化投资平台. 保留所有权利.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        密码重置成功 - 量化投资平台
        
        恭喜！您的账户密码已于 {current_time} 成功重置。
        
        您现在可以使用新密码登录您的账户。为了确保账户安全，我们建议您：
        - 使用强密码，包含大小写字母、数字和特殊字符
        - 不要在多个网站使用相同密码
        - 定期更换密码
        - 启用双重认证（如果可用）
        
        立即登录: {self.settings.FRONTEND_URL}/login
        
        如果这不是您本人的操作，请立即联系我们的客服团队。
        
        感谢您使用量化投资平台！
        
        量化投资平台团队
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_login_alert_email(
        self, 
        to_email: str, 
        username: str, 
        ip_address: str, 
        user_agent: str,
        login_time: str
    ) -> bool:
        """
        发送登录提醒邮件
        
        Args:
            to_email: 用户邮箱
            username: 用户名
            ip_address: 登录IP地址
            user_agent: 用户代理
            login_time: 登录时间
            
        Returns:
            bool: 发送是否成功
        """
        subject = "账户登录提醒 - 量化投资平台"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>账户登录提醒</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2196f3; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .info {{ background: white; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #2196f3; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 账户登录提醒</h1>
                    <p>您的账户有新的登录活动</p>
                </div>
                
                <div class="content">
                    <p>亲爱的 {username}，</p>
                    <p>我们检测到您的账户有新的登录活动：</p>
                    
                    <div class="info">
                        <strong>登录详情：</strong><br>
                        📅 登录时间：{login_time}<br>
                        🌐 IP地址：{ip_address}<br>
                        💻 设备信息：{user_agent}
                    </div>
                    
                    <p>如果这是您本人的操作，您可以忽略此邮件。</p>
                    <p>如果这不是您本人的操作，请立即：</p>
                    <ul>
                        <li>修改您的账户密码</li>
                        <li>检查账户安全设置</li>
                        <li>联系我们的客服团队</li>
                    </ul>
                    
                    <p>账户安全是我们的首要任务，感谢您的理解与配合。</p>
                    
                    <p><strong>量化投资平台团队</strong></p>
                </div>
                
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复</p>
                    <p>© 2024 量化投资平台. 保留所有权利.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        账户登录提醒 - 量化投资平台
        
        亲爱的 {username}，
        
        我们检测到您的账户有新的登录活动：
        
        登录详情：
        📅 登录时间：{login_time}
        🌐 IP地址：{ip_address}
        💻 设备信息：{user_agent}
        
        如果这是您本人的操作，您可以忽略此邮件。
        如果这不是您本人的操作，请立即：
        - 修改您的账户密码
        - 检查账户安全设置
        - 联系我们的客服团队
        
        账户安全是我们的首要任务，感谢您的理解与配合。
        
        量化投资平台团队
        """
        
        return await self.send_email(to_email, subject, html_content, text_content) 