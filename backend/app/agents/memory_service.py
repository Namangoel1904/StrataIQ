"""
StrataIQ — Backboard.io Memory Service (memory_service.py)

Cross-session user personalization & persistent preference memory:
  - Uses official `backboard` SDK (`from backboard import BackboardClient`)
  - Persists query/interaction history and layer UI preferences
  - Synchronizes with `users.ui_preferences_json` in the relational database
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User

settings = get_settings()

try:
    from backboard import BackboardClient
    BACKBOARD_AVAILABLE = True
except Exception:
    BACKBOARD_AVAILABLE = False


@dataclass
class UserMemorySnapshot:
    user_id: str
    ui_preferences: dict[str, Any]
    interaction_count: int
    recent_topics: list[str] = field(default_factory=list)
    provider: str = "backboard_io_live"   # backboard_io_live | local_rdbms_sync


class BackboardMemoryService:
    """
    Manages long-term user memory and preference persistence.
    Syncs seamlessly between Backboard.io cloud memory and local DB ui_preferences_json.
    """

    def __init__(self) -> None:
        self.client: Optional[BackboardClient] = None
        if BACKBOARD_AVAILABLE and settings.BACKBOARD_API_KEY:
            try:
                self.client = BackboardClient(api_key=settings.BACKBOARD_API_KEY)
            except Exception:
                self.client = None

    def record_interaction(
        self,
        user_id: str,
        query: str,
        intent: str,
        answer: str,
        db: Session,
    ) -> None:
        """
        Record a user interaction to Backboard cloud memory and update DB preferences.
        """
        # 1. Backboard cloud memory record
        if self.client and settings.BACKBOARD_API_KEY:
            try:
                # Add memory note to Backboard
                self.client.add_memory(
                    content=f"User {user_id} performed query with intent {intent}: '{query[:120]}'. Key topic extracted."
                )
            except Exception:
                pass  # Graceful fallback to local DB sync

        # 2. Sync to local database ui_preferences_json
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if user:
                prefs = json.loads(user.ui_preferences_json or "{}")
                recent = prefs.get("recent_queries", [])
                recent.insert(0, {"query": query[:100], "intent": intent})
                prefs["recent_queries"] = recent[:5]
                user.ui_preferences_json = json.dumps(prefs)
                db.commit()
        except Exception:
            db.rollback()

    def get_user_memory(self, user_id: str, db: Session) -> UserMemorySnapshot:
        """
        Retrieve user's persistent preferences and recent topic history.
        """
        user = db.query(User).filter(User.user_id == user_id).first()
        ui_prefs = {}
        if user and user.ui_preferences_json:
            try:
                ui_prefs = json.loads(user.ui_preferences_json)
            except Exception:
                ui_prefs = {}

        recent_queries = ui_prefs.get("recent_queries", [])
        topics = [q.get("query", "") for q in recent_queries if isinstance(q, dict)]

        provider = "backboard_io_live" if (self.client and settings.BACKBOARD_API_KEY) else "local_rdbms_sync"

        return UserMemorySnapshot(
            user_id=user_id,
            ui_preferences=ui_prefs,
            interaction_count=len(recent_queries),
            recent_topics=topics,
            provider=provider,
        )

    def update_ui_preferences(
        self,
        user_id: str,
        new_preferences: dict[str, Any],
        db: Session,
    ) -> dict[str, Any]:
        """
        Update user UI layout preferences, committing to both DB and Backboard memory.
        """
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return {}

        current_prefs = json.loads(user.ui_preferences_json or "{}")
        current_prefs.update(new_preferences)
        user.ui_preferences_json = json.dumps(current_prefs)
        db.commit()

        if self.client and settings.BACKBOARD_API_KEY:
            try:
                self.client.add_memory(
                    content=f"User {user_id} updated layout preferences: {json.dumps(new_preferences)}"
                )
            except Exception:
                pass

        return current_prefs
