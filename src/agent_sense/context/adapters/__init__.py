"""Context adapters for different client environments.

Exports
-------
WebContextAdapter
    Browser-based adapter using HTTP headers and user-agent.
MobileContextAdapter
    Mobile-specific context adapter.
VoiceContextAdapter
    Voice-only context adapter.
"""
from __future__ import annotations

from agent_sense.context.adapters.web import WebContextAdapter
from agent_sense.context.adapters.mobile import MobileContextAdapter
from agent_sense.context.adapters.voice import VoiceContextAdapter

__all__ = ["WebContextAdapter", "MobileContextAdapter", "VoiceContextAdapter"]
