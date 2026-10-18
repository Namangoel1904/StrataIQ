"""
StrataIQ Google Cloud Firestore Synchronization Service

Syncs real-time employee session events and executive decision matrix approvals
to Google Cloud Firestore collections:
  - strataiq_sessions
  - strataiq_decisions

Built with robust local/offline fallback so pytest suites and local offline dev
never fail when GCP credentials or ADC are not configured.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import get_settings

logger = logging.getLogger("strataiq.firestore")
settings = get_settings()


class FirestoreSyncService:
    """
    Syncs StrataIQ events and high-stakes executive decisions to Google Cloud Firestore.
    Operates with graceful offline / no-op fallback so local tests and offline dev
    never crash if Google Cloud credentials / ADC are absent.
    """

    def __init__(self) -> None:
        self._client = None
        self._initialized = False
        self._available = False

    def _get_client(self):
        if self._initialized:
            return self._client
        self._initialized = True
        try:
            from google.cloud import firestore  # noqa: PLC0415

            project = settings.GOOGLE_CLOUD_PROJECT or None
            self._client = firestore.Client(project=project)
            self._available = True
            logger.info("Google Cloud Firestore client connected (project=%s)", project)
        except Exception as exc:
            self._client = None
            self._available = False
            logger.info("Firestore running in local fallback mode: %s", exc)
        return self._client

    @property
    def is_available(self) -> bool:
        return self._get_client() is not None

    def sync_user_session_event(
        self,
        user_id: str,
        layer_code: str,
        action: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Writes an audit event to the 'strataiq_sessions' Firestore collection.
        """
        client = self._get_client()
        if not client:
            logger.debug("[Local Fallback] Firestore session event: %s - %s", user_id, action)
            return None
        try:
            doc_ref = client.collection("strataiq_sessions").document()
            payload = {
                "event_id": doc_ref.id,
                "user_id": user_id,
                "layer_code": layer_code,
                "action": action,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "strataiq_cloud_run",
            }
            doc_ref.set(payload)
            logger.info("Synced session event to Firestore: %s (%s)", doc_ref.id, action)
            return doc_ref.id
        except Exception as exc:
            logger.warning("Failed to sync session event to Firestore: %s", exc)
            return None

    def sync_executive_decision(
        self,
        decision_id: str,
        selected_option: str,
        approver_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Writes an executive decision record to the 'strataiq_decisions' Firestore collection.
        """
        client = self._get_client()
        if not client:
            logger.debug(
                "[Local Fallback] Firestore decision: %s approved by %s",
                decision_id,
                approver_id,
            )
            return None
        try:
            doc_ref = client.collection("strataiq_decisions").document(decision_id)
            payload = {
                "decision_id": decision_id,
                "selected_option": selected_option,
                "approver_id": approver_id,
                "metadata": metadata or {},
                "status": "APPROVED",
                "decided_at": datetime.now(timezone.utc).isoformat(),
                "source": "strataiq_cloud_run",
            }
            doc_ref.set(payload, merge=True)
            logger.info("Synced executive decision to Firestore: %s", decision_id)
            return decision_id
        except Exception as exc:
            logger.warning("Failed to sync executive decision to Firestore: %s", exc)
            return None


firestore_service = FirestoreSyncService()
