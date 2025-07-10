"""
告警规则同步服务
"""
import os
import yaml
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger

from ..core.config import settings


@dataclass
class PrometheusRule:
    """Prometheus告警规则"""
    alert: str
    expr: str
    for_: str
    labels: Dict[str, str]
    annotations: Dict[str, str]


@dataclass
class RuleGroup:
    """告警规则组"""
    name: str
    interval: str
    rules: List[PrometheusRule]


@dataclass
class AlertRuleFile:
    """告警规则文件"""
    groups: List[RuleGroup]


class AlertRulesManager:
    """告警规则管理器"""
    
    def __init__(self, rules_dir: str = "monitoring/rules"):
        self.rules_dir = Path(rules_dir)
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        self.rules_cache: Dict[str, AlertRuleFile] = {}
    
    def generate_default_rules(self) -> AlertRuleFile:
        """生成默认告警规则"""
        
        # CTP连接告警规则
        ctp_rules = [
            PrometheusRule(
                alert="CTPConnectionDown",
                expr="quant_platform_ctp_connection_status == 0",
                for_="1m",
                labels={
                    "severity": "critical",
                    "component": "ctp",
                    "category": "connection"
                },
                annotations={
                    "summary": "CTP连接断开",
                    "description": "CTP {{ $labels.connection_type }} 连接已断开超过1分钟",
                    "runbook_url": "https://docs.quant-platform.com/runbooks/ctp-connection"
                }
            ),
            PrometheusRule(
                alert="CTPHighReconnectRate",
                expr="rate(quant_platform_ctp_reconnect_total[5m]) > 0.1",
                for_="2m",
                labels={
                    "severity": "warning",
                    "component": "ctp",
                    "category": "connection"
                },
                annotations={
                    "summary": "CTP重连频率过高",
                    "description": "CTP {{ $labels.connection_type }} 在过去5分钟内重连频率超过0.1次/秒",
                    "runbook_url": "https://docs.quant-platform.com/runbooks/ctp-reconnect"
                }
            )
        ]
        
        # 系统资源告警规则
        system_rules = [
            PrometheusRule(
                alert="HighCPUUsage",
                expr="quant_platform_cpu_usage_percent > 80",
                for_="5m",
                labels={
                    "severity": "warning",
                    "component": "system",
                    "category": "resource"
                },
                annotations={
                    "summary": "CPU使用率过高",
                    "description": "系统CPU使用率已超过80%持续5分钟",
                    "runbook_url": "https://docs.quant-platform.com/runbooks/high-cpu"
                }
            ),
            PrometheusRule(
                alert="HighMemoryUsage",
                expr="(quant_platform_memory_usage_bytes / quant_platform_memory_total_bytes) * 100 > 85",
                for_="5m",
                labels={
                    "severity": "warning",
                    "component": "system",
                    "category": "resource"
                },
                annotations={
                    "summary": "内存使用率过高",
                    "description": "系统内存使用率已超过85%持续5分钟",
                    "runbook_url": "https://docs.quant-platform.com/runbooks/high-memory"
                }
            ),
            PrometheusRule(
                alert="SystemDown",
                expr="up{job=\"ctp-backend\"} == 0",
                for_="1m",
                labels={
                    "severity": "critical",
                    "component": "system",
                    "category": "availability"
                },
                annotations={
                    "summary": "系统服务不可用",
                    "description": "量化交易平台后端服务已停止响应超过1分钟",
                    "runbook_url": "https://docs.quant-platform.com/runbooks/system-down"
                }
            )
        ]
        
        # 交易告警规则
        trading_rules = [
            PrometheusRule(
                alert="HighOrderErrorRate",
                expr="(rate(quant_platform_orders_total{status=\"rejected\"}[5m]) / rate(quant_platform_orders_total[5m])) * 100 > 10",
                for_="2m",
                labels={
                    "severity": "warning",
                    "component": "trading",
                    "category": "error_rate"
                },
                annotations={
                    "summary": "订单错误率过高",
                    "description": "过去5分钟内订单错误率超过10%",
                    "runbook_url": "https://docs.quant-platform.com/runbooks/high-order-error-rate"
                }
            ),
            PrometheusRule(
                alert="SlowOrderResponse",
                expr="histogram_quantile(0.95, rate(quant_platform_order_response_time_seconds_bucket[5m])) > 2",
                for_="3m",
                labels={
                    "severity": "warning",
                    "component": "trading",
                    "category": "performance"
                },
                annotations={
                    "summary": "订单响应时间过慢",
                    "description": "95%的订单响应时间超过2秒",
                    "runbook_url": "https://docs.quant-platform.com/runbooks/slow-order-response"
                }
            ),
            PrometheusRule(
                alert="NoTradingActivity",
                expr="rate(quant_platform_trades_total[1h]) == 0",
                for_="30m",
                labels={
                    "severity": "info",
                    "component": "trading",
                    "category": "activity"
                },
                annotations={
                    "summary": "无交易活动",
                    "description": "过去1小时内没有任何交易活动",
                    "runbook_url": "https://docs.quant-platform.com/runbooks/no-trading-activity"
                }
            )
        ]
        
        # 行情数据告警规则
        market_data_rules = [
            PrometheusRule(
                alert="HighMarketDataLatency",
                expr="histogram_quantile(0.95, rate(quant_platform_market_data_latency_seconds_bucket[5m])) > 1",
                for_="2m",
                labels={
                    "severity": "warning",
                    "component": "market_data",
                    "category": "latency"
                },
                annotations={
                    "summary": "行情数据延迟过高",
                    "description": "95%的行情数据延迟超过1秒",
                    "runbook_url": "https://docs.quant-platform.com/runbooks/high-market-data-latency"
                }
            ),
            PrometheusRule(
                alert="NoMarketDataReceived",
                expr="rate(quant_platform_market_data_received_total[5m]) == 0",
                for_="2m",
                labels={
                    "severity": "critical",
                    "component": "market_data",
                    "category": "data_flow"
                },
                annotations={
                    "summary": "未接收到行情数据",
                    "description": "过去5分钟内未接收到任何行情数据",
                    "runbook_url": "https://docs.quant-platform.com/runbooks/no-market-data"
                }
            )
        ]
        
        # HTTP API告警规则
        api_rules = [
            PrometheusRule(
                alert="HighHTTPErrorRate",
                expr="(rate(quant_platform_http_requests_total{status_code=~\"5..\"}[5m]) / rate(quant_platform_http_requests_total[5m])) * 100 > 5",
                for_="2m",
                labels={
                    "severity": "warning",
                    "component": "api",
                    "category": "error_rate"
                },
                annotations={
                    "summary": "HTTP错误率过高",
                    "description": "过去5分钟内HTTP 5xx错误率超过5%",
                    "runbook_url": "https://docs.quant-platform.com/runbooks/high-http-error-rate"
                }
            ),
            PrometheusRule(
                alert="SlowHTTPResponse",
                expr="histogram_quantile(0.95, rate(quant_platform_http_request_duration_seconds_bucket[5m])) > 5",
                for_="3m",
                labels={
                    "severity": "warning",
                    "component": "api",
                    "category": "performance"
                },
                annotations={
                    "summary": "HTTP响应时间过慢",
                    "description": "95%的HTTP请求响应时间超过5秒",
                    "runbook_url": "https://docs.quant-platform.com/runbooks/slow-http-response"
                }
            )
        ]
        
        # 创建规则组
        groups = [
            RuleGroup(
                name="ctp_alerts",
                interval="30s",
                rules=ctp_rules
            ),
            RuleGroup(
                name="system_alerts",
                interval="30s",
                rules=system_rules
            ),
            RuleGroup(
                name="trading_alerts",
                interval="30s",
                rules=trading_rules
            ),
            RuleGroup(
                name="market_data_alerts",
                interval="30s",
                rules=market_data_rules
            ),
            RuleGroup(
                name="api_alerts",
                interval="30s",
                rules=api_rules
            )
        ]
        
        return AlertRuleFile(groups=groups)
    
    def save_rules_to_file(self, rules: AlertRuleFile, filename: str = "quant_platform_alerts.yml"):
        """保存告警规则到文件"""
        file_path = self.rules_dir / filename
        
        # 转换为Prometheus格式
        prometheus_format = {
            "groups": []
        }
        
        for group in rules.groups:
            group_dict = {
                "name": group.name,
                "interval": group.interval,
                "rules": []
            }
            
            for rule in group.rules:
                rule_dict = {
                    "alert": rule.alert,
                    "expr": rule.expr,
                    "for": rule.for_,
                    "labels": rule.labels,
                    "annotations": rule.annotations
                }
                group_dict["rules"].append(rule_dict)
            
            prometheus_format["groups"].append(group_dict)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(prometheus_format, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Alert rules saved to {file_path}")
        return file_path
    
    def load_rules_from_file(self, filename: str) -> Optional[AlertRuleFile]:
        """从文件加载告警规则"""
        file_path = self.rules_dir / filename
        
        if not file_path.exists():
            logger.warning(f"Alert rules file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            groups = []
            for group_data in data.get("groups", []):
                rules = []
                for rule_data in group_data.get("rules", []):
                    rule = PrometheusRule(
                        alert=rule_data["alert"],
                        expr=rule_data["expr"],
                        for_=rule_data["for"],
                        labels=rule_data.get("labels", {}),
                        annotations=rule_data.get("annotations", {})
                    )
                    rules.append(rule)
                
                group = RuleGroup(
                    name=group_data["name"],
                    interval=group_data.get("interval", "30s"),
                    rules=rules
                )
                groups.append(group)
            
            return AlertRuleFile(groups=groups)
            
        except Exception as e:
            logger.error(f"Error loading alert rules from {file_path}: {e}")
            return None
    
    async def sync_rules_to_prometheus(self, prometheus_config_dir: str = "monitoring"):
        """同步告警规则到Prometheus配置目录"""
        try:
            # 生成默认规则
            default_rules = self.generate_default_rules()
            
            # 保存到本地
            local_file = self.save_rules_to_file(default_rules)
            
            # 复制到Prometheus配置目录
            prometheus_rules_dir = Path(prometheus_config_dir) / "rules"
            prometheus_rules_dir.mkdir(parents=True, exist_ok=True)
            
            target_file = prometheus_rules_dir / "quant_platform_alerts.yml"
            
            import shutil
            shutil.copy2(local_file, target_file)
            
            logger.info(f"Alert rules synced to Prometheus: {target_file}")
            
            return target_file
            
        except Exception as e:
            logger.error(f"Error syncing alert rules to Prometheus: {e}")
            raise
    
    async def validate_rules(self, rules: AlertRuleFile) -> List[str]:
        """验证告警规则"""
        errors = []
        
        for group in rules.groups:
            for rule in group.rules:
                # 检查必需字段
                if not rule.alert:
                    errors.append(f"Rule in group {group.name} missing alert name")
                
                if not rule.expr:
                    errors.append(f"Rule {rule.alert} missing expression")
                
                # 检查表达式语法（简单检查）
                if rule.expr and not any(metric in rule.expr for metric in ["quant_platform_", "up", "rate", "histogram_quantile"]):
                    errors.append(f"Rule {rule.alert} expression may be invalid")
        
        return errors


# 全局告警规则管理器实例
alert_rules_manager = AlertRulesManager()


async def setup_alert_rules():
    """设置告警规则"""
    try:
        # 同步规则到Prometheus
        await alert_rules_manager.sync_rules_to_prometheus()
        
        logger.info("Alert rules setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup alert rules: {e}")
        raise
