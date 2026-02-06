"""Context memory — sliding window + summary for long conversations."""

import logging

import anthropic

log = logging.getLogger(__name__)

SUMMARY_THRESHOLD = 20  # exchanges before summarization triggers
WINDOW_SIZE = 10  # exchanges to keep in full after summarization

_SUMMARY_PROMPT = (
    "Summarize the following trading analytics conversation. "
    "Focus on: what questions the user asked, what data insights were found, "
    "what patterns emerged, and any conclusions reached. "
    "Keep it concise — 3-5 sentences in the same language the user used."
)


def should_summarize(message_count: int, context: dict | None) -> bool:
    """Check if conversation needs summarization."""
    if message_count < SUMMARY_THRESHOLD:
        return False
    if context and context.get("summary_up_to"):
        # Re-summarize when enough new exchanges accumulated
        return (message_count - context["summary_up_to"]) >= SUMMARY_THRESHOLD
    return True


def build_history_with_context(
    context: dict | None, messages: list[dict],
) -> list[dict]:
    """Build history: summary + recent messages, or full history if no context."""
    if not context or not context.get("summary"):
        return messages

    summary_up_to = context.get("summary_up_to", 0)
    # Each exchange = 2 rows (user + assistant)
    recent = messages[summary_up_to * 2 :]

    summary_msg = {
        "role": "assistant",
        "text": f"[Previous context]\n{context['summary']}",
    }
    return [summary_msg] + recent


def summarize(
    client: anthropic.Anthropic, model_id: str, old_summary: str | None, messages: list[dict],
) -> str:
    """Summarize conversation history via direct Anthropic call (no tools)."""
    parts = []
    if old_summary:
        parts.append(f"Previous summary:\n{old_summary}\n\nNew messages:\n")

    for msg in messages:
        role = msg.get("role", "user")
        text = msg.get("text", "")
        parts.append(f"{role}: {text}")

    conversation_text = "\n".join(parts)

    response = client.messages.create(
        model=model_id,
        max_tokens=1024,
        messages=[
            {"role": "user", "content": f"{_SUMMARY_PROMPT}\n\n{conversation_text}"},
        ],
    )

    if response.content and response.content[0].type == "text":
        return response.content[0].text
    return ""
