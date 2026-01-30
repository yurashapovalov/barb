#!/usr/bin/env python3
"""Export a conversation with messages and tool calls to JSON.

Usage:
    python scripts/export_conversation.py <conversation_id>
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Load .env
_env_file = ROOT / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

from supabase import create_client


def export_conversation(conversation_id: str) -> dict:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    db = create_client(url, key)

    # Conversation
    conv = (
        db.table("conversations")
        .select("*")
        .eq("id", conversation_id)
        .execute()
    )
    if not conv.data:
        print(f"Conversation {conversation_id} not found", file=sys.stderr)
        sys.exit(1)

    # Messages
    messages = (
        db.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    ).data

    # Tool calls for all messages in one query
    message_ids = [m["id"] for m in messages]
    tool_calls = []
    if message_ids:
        tool_calls = (
            db.table("tool_calls")
            .select("*")
            .in_("message_id", message_ids)
            .order("created_at", desc=False)
            .execute()
        ).data

    # Group tool calls by message_id
    tc_by_msg: dict[str, list] = {}
    for tc in tool_calls:
        tc_by_msg.setdefault(tc["message_id"], []).append(tc)

    # Nest tool calls into messages
    for msg in messages:
        msg["tool_calls"] = tc_by_msg.get(msg["id"], [])

    return {
        "conversation": conv.data[0],
        "messages": messages,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/export_conversation.py <conversation_id>", file=sys.stderr)
        sys.exit(1)

    conversation_id = sys.argv[1]
    data = export_conversation(conversation_id)

    out_dir = ROOT / "results" / "conversations"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{conversation_id}.json"

    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    print(f"Exported to {out_file}")
    print(f"  Messages: {len(data['messages'])}")
    print(f"  Tool calls: {sum(len(m['tool_calls']) for m in data['messages'])}")


if __name__ == "__main__":
    main()
