"""Quick test: Haiku vs Gemini Flash on the same scenario."""

import anthropic
from assistant.prompt import build_system_prompt
from assistant.tools import get_declarations, run_tool, Workspace
from barb.data import load_data
from config.market.instruments import get_instrument

# Scenario: Inside Day
TURNS = [
    "сколько inside days было за 2024-2025?",
    "да, RTH",
    "какой средний range на следующий день после inside day?",
    "покажи топ-10 самых сильных движений после inside day",
]


def gemini_to_anthropic_tools(declarations: list[dict]) -> list[dict]:
    """Convert Gemini tool format to Anthropic format."""
    tools = []
    for decl in declarations:
        tool = {
            "name": decl["name"],
            "description": decl.get("description", ""),
            "input_schema": decl.get("parameters", {"type": "object", "properties": {}}),
        }
        tools.append(tool)
    return tools


def run_test():
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )

    # Load data
    instrument = "NQ"
    df = load_data(instrument)
    config = get_instrument(instrument)
    sessions = config["sessions"]

    # Build prompt and tools
    system_prompt = build_system_prompt(instrument)
    tools = gemini_to_anthropic_tools(get_declarations())

    messages = []
    workspace = Workspace(df, sessions)

    print("=" * 60)
    print("Testing Claude Haiku on Inside Day scenario")
    print("=" * 60)

    for turn_num, user_msg in enumerate(TURNS, 1):
        print(f"\n--- Turn {turn_num} ---")
        print(f"User: {user_msg}")

        messages.append({"role": "user", "content": user_msg})

        # May need multiple rounds for tool use
        for round_num in range(5):
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                system=system_prompt,
                tools=tools,
                messages=messages,
            )

            # Process response
            assistant_content = []
            tool_calls = []
            text_response = ""

            for block in response.content:
                if block.type == "text":
                    text_response += block.text
                    assistant_content.append(block)
                elif block.type == "tool_use":
                    tool_calls.append(block)
                    assistant_content.append(block)
                    print(f"  Tool: {block.name}({dict(block.input)})")

            messages.append({"role": "assistant", "content": assistant_content})

            if not tool_calls:
                # No more tool calls, we have final response
                print(f"Assistant: {text_response[:200]}...")
                break

            # Execute tools and add results
            tool_results = []
            for tool_call in tool_calls:
                result, data = run_tool(tool_call.name, dict(tool_call.input), workspace)
                print(f"    → {result[:100]}...")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})

        print(f"\nWorkspace rows: {len(workspace.df)}")

    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)


if __name__ == "__main__":
    run_test()
