"""
외부 서비스 연동 - Slack, Discord, Notion
일정 알림을 다양한 협업 툴로 전송
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

import httpx
from dotenv import load_dotenv

load_dotenv()


class IntegrationType(str, Enum):
    """연동 서비스 타입"""
    SLACK = "slack"
    DISCORD = "discord"
    NOTION = "notion"


@dataclass
class IntegrationConfig:
    """연동 설정"""
    type: IntegrationType
    webhook_url: Optional[str] = None
    api_key: Optional[str] = None
    channel_id: Optional[str] = None
    database_id: Optional[str] = None  # Notion용
    enabled: bool = True
    
    def to_dict(self):
        return {
            "type": self.type.value,
            "enabled": self.enabled,
            "configured": bool(self.webhook_url or self.api_key)
        }


@dataclass
class NotificationPayload:
    """알림 페이로드"""
    title: str
    message: str
    url: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"  # high, medium, low
    category: Optional[str] = None
    
    def to_dict(self):
        return {
            "title": self.title,
            "message": self.message,
            "url": self.url,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority,
            "category": self.category
        }


class SlackIntegration:
    """Slack Webhook 연동"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient()
    
    async def send_notification(self, payload: NotificationPayload) -> bool:
        """Slack으로 알림 전송"""
        
        # 우선순위별 이모지
        priority_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }
        emoji = priority_emoji.get(payload.priority, "📢")
        
        # Slack Block Kit 메시지 구성
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {payload.title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": payload.message
                }
            }
        ]
        
        # 마감일이 있으면 추가
        if payload.due_date:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 마감: {payload.due_date.strftime('%Y-%m-%d %H:%M')}"
                    }
                ]
            })
        
        # URL이 있으면 버튼 추가
        if payload.url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "상세 보기",
                            "emoji": True
                        },
                        "url": payload.url
                    }
                ]
            })
        
        slack_payload = {"blocks": blocks}
        
        try:
            response = await self.client.post(
                self.webhook_url,
                json=slack_payload
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Slack send error: {e}")
            return False
    
    async def send_daily_summary(
        self, 
        schedules: List[Dict], 
        tasks: List[Dict]
    ) -> bool:
        """일일 요약 전송"""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📋 오늘의 일정 ({datetime.now().strftime('%m월 %d일')})",
                    "emoji": True
                }
            },
            {"type": "divider"}
        ]
        
        # 일정
        if schedules:
            schedule_text = "\n".join([
                f"• {s.get('title', '일정')} ({s.get('end_at', '')[:10]})"
                for s in schedules[:5]
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📅 오늘 일정 ({len(schedules)}건)*\n{schedule_text}"
                }
            })
        
        # 할 일
        if tasks:
            task_text = "\n".join([
                f"• {'✅' if t.get('is_done') else '⬜'} {t.get('title', '할 일')}"
                for t in tasks[:5]
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*✅ 오늘 할 일 ({len(tasks)}건)*\n{task_text}"
                }
            })
        
        if not schedules and not tasks:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "오늘은 등록된 일정이 없습니다. 여유로운 하루 되세요! 🎉"
                }
            })
        
        try:
            response = await self.client.post(
                self.webhook_url,
                json={"blocks": blocks}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Slack daily summary error: {e}")
            return False
    
    async def close(self):
        await self.client.aclose()


class DiscordIntegration:
    """Discord Webhook 연동"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient()
    
    async def send_notification(self, payload: NotificationPayload) -> bool:
        """Discord로 알림 전송"""
        
        # 우선순위별 색상 (Embed color)
        priority_colors = {
            "high": 0xFF0000,    # 빨강
            "medium": 0xFFFF00,  # 노랑
            "low": 0x00FF00      # 초록
        }
        color = priority_colors.get(payload.priority, 0x7289DA)
        
        # Discord Embed 구성
        embed = {
            "title": payload.title,
            "description": payload.message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if payload.due_date:
            embed["fields"] = [
                {
                    "name": "📅 마감",
                    "value": payload.due_date.strftime("%Y-%m-%d %H:%M"),
                    "inline": True
                }
            ]
        
        if payload.category:
            if "fields" not in embed:
                embed["fields"] = []
            embed["fields"].append({
                "name": "📁 카테고리",
                "value": payload.category,
                "inline": True
            })
        
        if payload.url:
            embed["url"] = payload.url
        
        discord_payload = {
            "embeds": [embed],
            "username": "5늘의 일정",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/2693/2693507.png"
        }
        
        try:
            response = await self.client.post(
                self.webhook_url,
                json=discord_payload
            )
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Discord send error: {e}")
            return False
    
    async def send_daily_summary(
        self, 
        schedules: List[Dict], 
        tasks: List[Dict]
    ) -> bool:
        """일일 요약 전송"""
        
        # 일정 필드
        schedule_value = "\n".join([
            f"• {s.get('title', '일정')}"
            for s in schedules[:5]
        ]) if schedules else "없음"
        
        # 할 일 필드
        task_value = "\n".join([
            f"{'✅' if t.get('is_done') else '⬜'} {t.get('title', '할 일')}"
            for t in tasks[:5]
        ]) if tasks else "없음"
        
        embed = {
            "title": f"📋 오늘의 일정 ({datetime.now().strftime('%m월 %d일')})",
            "color": 0x5865F2,
            "fields": [
                {
                    "name": f"📅 일정 ({len(schedules)}건)",
                    "value": schedule_value,
                    "inline": False
                },
                {
                    "name": f"✅ 할 일 ({len(tasks)}건)",
                    "value": task_value,
                    "inline": False
                }
            ],
            "footer": {
                "text": "5늘의 일정 | 오늘도 화이팅! 💪"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            response = await self.client.post(
                self.webhook_url,
                json={
                    "embeds": [embed],
                    "username": "5늘의 일정",
                }
            )
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Discord daily summary error: {e}")
            return False
    
    async def close(self):
        await self.client.aclose()


class NotionIntegration:
    """Notion API 연동"""
    
    def __init__(self, api_key: str, database_id: str):
        self.api_key = api_key
        self.database_id = database_id
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
        )
    
    async def add_schedule_to_database(self, payload: NotificationPayload) -> bool:
        """Notion 데이터베이스에 일정 추가"""
        
        # Notion 페이지 속성
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": payload.title
                        }
                    }
                ]
            },
            "Description": {
                "rich_text": [
                    {
                        "text": {
                            "content": payload.message[:2000]
                        }
                    }
                ]
            }
        }
        
        # 마감일
        if payload.due_date:
            properties["Due Date"] = {
                "date": {
                    "start": payload.due_date.strftime("%Y-%m-%d")
                }
            }
        
        # 우선순위
        properties["Priority"] = {
            "select": {
                "name": payload.priority.capitalize()
            }
        }
        
        # 카테고리
        if payload.category:
            properties["Category"] = {
                "select": {
                    "name": payload.category
                }
            }
        
        notion_payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }
        
        try:
            response = await self.client.post(
                "https://api.notion.com/v1/pages",
                json=notion_payload
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Notion add error: {e}")
            return False
    
    async def sync_schedules(self, schedules: List[Dict]) -> Dict:
        """일정 일괄 동기화"""
        results = {"success": 0, "failed": 0}
        
        for schedule in schedules:
            payload = NotificationPayload(
                title=schedule.get("title", "일정"),
                message=schedule.get("original_text", ""),
                due_date=datetime.fromisoformat(schedule["end_at"]) if schedule.get("end_at") else None,
                priority="high" if schedule.get("priority_score", 5) >= 7 else "medium",
                category=schedule.get("category")
            )
            
            success = await self.add_schedule_to_database(payload)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    async def close(self):
        await self.client.aclose()


class IntegrationManager:
    """연동 통합 관리자"""
    
    def __init__(self):
        self.integrations: Dict[IntegrationType, object] = {}
    
    def configure_slack(self, webhook_url: str):
        """Slack 연동 설정"""
        self.integrations[IntegrationType.SLACK] = SlackIntegration(webhook_url)
    
    def configure_discord(self, webhook_url: str):
        """Discord 연동 설정"""
        self.integrations[IntegrationType.DISCORD] = DiscordIntegration(webhook_url)
    
    def configure_notion(self, api_key: str, database_id: str):
        """Notion 연동 설정"""
        self.integrations[IntegrationType.NOTION] = NotionIntegration(api_key, database_id)
    
    async def send_notification(
        self, 
        payload: NotificationPayload,
        targets: List[IntegrationType] = None
    ) -> Dict[str, bool]:
        """알림 전송 (다중 채널)"""
        
        if targets is None:
            targets = list(self.integrations.keys())
        
        results = {}
        
        for target in targets:
            if target in self.integrations:
                integration = self.integrations[target]
                
                if hasattr(integration, 'send_notification'):
                    results[target.value] = await integration.send_notification(payload)
                elif target == IntegrationType.NOTION:
                    results[target.value] = await integration.add_schedule_to_database(payload)
        
        return results
    
    async def send_daily_summary(
        self,
        schedules: List[Dict],
        tasks: List[Dict],
        targets: List[IntegrationType] = None
    ) -> Dict[str, bool]:
        """일일 요약 전송"""
        
        if targets is None:
            targets = [IntegrationType.SLACK, IntegrationType.DISCORD]
        
        results = {}
        
        for target in targets:
            if target in self.integrations:
                integration = self.integrations[target]
                
                if hasattr(integration, 'send_daily_summary'):
                    results[target.value] = await integration.send_daily_summary(
                        schedules, tasks
                    )
        
        return results
    
    def get_configured_integrations(self) -> List[str]:
        """설정된 연동 목록"""
        return [t.value for t in self.integrations.keys()]
    
    async def close_all(self):
        """모든 연결 종료"""
        for integration in self.integrations.values():
            if hasattr(integration, 'close'):
                await integration.close()


# 환경변수에서 기본 설정 로드
def get_default_integration_manager() -> IntegrationManager:
    """환경변수 기반 기본 연동 관리자"""
    manager = IntegrationManager()
    
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if slack_webhook:
        manager.configure_slack(slack_webhook)
    
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if discord_webhook:
        manager.configure_discord(discord_webhook)
    
    notion_key = os.getenv("NOTION_API_KEY")
    notion_db = os.getenv("NOTION_DATABASE_ID")
    if notion_key and notion_db:
        manager.configure_notion(notion_key, notion_db)
    
    return manager
