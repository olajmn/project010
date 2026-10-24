"""Checks for fitting a prompt into the model's context - no model call."""

from backend.model.brief.budget import estimate_tokens, fit_to_budget


def _prompt(turns: int, size: int = 300) -> list[dict]:
    messages = [{"role": "system", "content": "S" * 900}]
    for i in range(turns):
        messages.append({"role": "user", "content": f"q{i} " + "x" * size})
        messages.append({"role": "assistant", "content": f"a{i} " + "y" * size})
    messages.append({"role": "user", "content": "new message"})
    return messages


def test_estimate_errs_on_the_large_side() -> None:
    # About 4 characters make a token in English; counting 3 overestimates.
    assert estimate_tokens([{"role": "user", "content": "x" * 300}]) >= 100


def test_a_prompt_that_fits_is_left_alone() -> None:
    messages = _prompt(3)
    assert fit_to_budget(messages, 10_000) == messages


def test_oldest_turns_go_first_and_the_model_is_told() -> None:
    messages = _prompt(10)
    fitted = fit_to_budget(messages, estimate_tokens(messages) // 2)
    assert estimate_tokens(fitted) <= estimate_tokens(messages) // 2
    assert fitted[-1] == messages[-1]  # the new message stays
    assert fitted[1]["role"] == "user"  # turns stay in pairs
    kept = [m["content"][:3] for m in fitted[1:-1:2]]
    assert kept == [f"q{i} " for i in range(10 - len(kept), 10)]  # newest kept
    dropped = 10 - len(kept)
    assert fitted[0]["content"].startswith("S" * 900)  # instructions stay whole
    assert (
        f"The first {dropped} turns of this conversation are left out"
        in (fitted[0]["content"])
    )


def test_instructions_and_background_are_never_cut() -> None:
    # Even when nothing but them would fit, all turns go and they stay.
    messages = _prompt(5)
    fitted = fit_to_budget(messages, 10)
    assert [m["role"] for m in fitted] == ["system", "user"]
    assert fitted[0]["content"].startswith("S" * 900)


def test_a_prompt_too_large_even_alone_is_reported(capsys) -> None:
    fit_to_budget(_prompt(2), 10)
    assert "over the budget" in capsys.readouterr().out
