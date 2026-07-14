"""
Buffer GraphQL client for adding posts to your personal queue.

Docs: https://developers.buffer.com/guides/getting-started.html
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

BUFFER_API_URL = "https://api.buffer.com"
# Prefer X/Twitter when several channels exist; fall back to first channel.
PREFERRED_CHANNEL_SERVICES = ("twitter", "x")


@dataclass
class BufferQueueResult:
    ok: bool
    message: str
    post_id: str = ""
    due_at: str = ""


class BufferClient:
    """Thin GraphQL helper for Buffer createPost → addToQueue."""

    def __init__(
        self,
        api_key: str,
        channel_id: str = "",
        organization_id: str = "",
        timeout: int = 30,
    ):
        self.api_key = (api_key or "").strip()
        self.channel_id = (channel_id or "").strip()
        self.organization_id = (organization_id or "").strip()
        self.timeout = timeout
        self._resolved = False

    @classmethod
    def from_env(cls) -> Optional["BufferClient"]:
        api_key = (os.getenv("BUFFER_API_KEY") or "").strip()
        if not api_key:
            return None
        return cls(
            api_key=api_key,
            channel_id=(os.getenv("BUFFER_CHANNEL_ID") or "").strip(),
            organization_id=(os.getenv("BUFFER_ORGANIZATION_ID") or "").strip(),
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _graphql(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"query": query}
        if variables is not None:
            payload["variables"] = variables
        response = requests.post(
            BUFFER_API_URL,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("errors"):
            messages = "; ".join(
                str(err.get("message") or err) for err in data["errors"]
            )
            raise RuntimeError(messages or "Buffer GraphQL error")
        return data.get("data") or {}

    def ensure_ready(self) -> None:
        """Resolve organization + channel IDs once per session when missing."""
        if self._resolved and self.channel_id:
            return

        if not self.organization_id:
            orgs = self._graphql(
                """
                query GetOrganizations {
                  account {
                    organizations {
                      id
                      name
                    }
                  }
                }
                """
            )
            organizations = (
                ((orgs.get("account") or {}).get("organizations")) or []
            )
            if not organizations:
                raise RuntimeError("No Buffer organizations found for this API key.")
            self.organization_id = str(organizations[0].get("id") or "").strip()
            if not self.organization_id:
                raise RuntimeError("Buffer organization id was empty.")

        if not self.channel_id:
            channels_data = self._graphql(
                """
                query GetChannels($organizationId: OrganizationId!) {
                  channels(input: { organizationId: $organizationId }) {
                    id
                    name
                    service
                  }
                }
                """,
                {"organizationId": self.organization_id},
            )
            channels: List[Dict[str, Any]] = channels_data.get("channels") or []
            if not channels:
                raise RuntimeError(
                    "No Buffer channels found. Connect X/Twitter in Buffer first."
                )

            preferred = None
            for channel in channels:
                service = str(channel.get("service") or "").strip().lower()
                if service in PREFERRED_CHANNEL_SERVICES:
                    preferred = channel
                    break
            chosen = preferred or channels[0]
            self.channel_id = str(chosen.get("id") or "").strip()
            if not self.channel_id:
                raise RuntimeError("Buffer channel id was empty.")

        self._resolved = True

    def add_text_to_queue(self, text: str) -> BufferQueueResult:
        """Add a text post to the next free Buffer queue slot."""
        text = (text or "").strip()
        if not text:
            return BufferQueueResult(ok=False, message="Tweet text is empty.")

        try:
            self.ensure_ready()
            data = self._graphql(
                """
                mutation CreatePost($text: String!, $channelId: ChannelId!) {
                  createPost(input: {
                    text: $text
                    channelId: $channelId
                    schedulingType: automatic
                    mode: addToQueue
                  }) {
                    ... on PostActionSuccess {
                      post {
                        id
                        text
                        dueAt
                      }
                    }
                    ... on MutationError {
                      message
                    }
                  }
                }
                """,
                {"text": text, "channelId": self.channel_id},
            )
        except requests.RequestException as exc:
            return BufferQueueResult(
                ok=False,
                message=f"Buffer request failed: {exc}",
            )
        except Exception as exc:
            return BufferQueueResult(ok=False, message=str(exc))

        result = data.get("createPost") or {}
        post = result.get("post")
        if post and post.get("id"):
            due_at = str(post.get("dueAt") or "").strip()
            due_note = f" (scheduled {due_at})" if due_at else ""
            return BufferQueueResult(
                ok=True,
                message=f"Added to Buffer queue{due_note}.",
                post_id=str(post.get("id") or ""),
                due_at=due_at,
            )

        error_message = str(result.get("message") or "").strip()
        if not error_message:
            error_message = "Buffer did not confirm the post (unknown error)."
        return BufferQueueResult(ok=False, message=error_message)
