"""
Fits a prompt into the model's context before it is sent, so nothing is
cut where no one sees it. When too long, the oldest past turns go first,
in pairs, and the system text says how many; the instructions, the
project background, and the new message are never cut (TODO.md 71.7).

No tokenizer: sizes are estimated from characters, on the large side.
"""

# About 4 characters make a token in English; 3 overestimates on purpose.
CHARS_PER_TOKEN = 3
# Role markers and separators around each message.
TOKENS_PER_MESSAGE = 4


def estimate_tokens(messages: list[dict]) -> int:
    """An upper estimate of the prompt's size in tokens."""
    return sum(
        -(-len(m.get("content") or "") // CHARS_PER_TOKEN) + TOKENS_PER_MESSAGE
        for m in messages
    )


def fit_to_budget(messages: list[dict], budget: int) -> list[dict]:
    """`messages` ([system, past turns..., new message]) cut to `budget`
    tokens by leaving out the oldest past turns."""
    if estimate_tokens(messages) <= budget or len(messages) < 3:
        return messages
    system, turns, new = messages[0], messages[1:-1], messages[-1]
    dropped = 0
    while True:
        dropped += 2
        kept = turns[dropped:]
        left_out = len(turns) - len(kept)
        note = (
            f"\n\nThe first {left_out // 2} turns of this conversation are left "
            "out here; only the most recent ones are included."
        )
        fitted = [
            {**system, "content": system["content"] + note},
            *kept,
            new,
        ]
        if not kept or estimate_tokens(fitted) <= budget:
            return fitted
