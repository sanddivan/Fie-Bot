# File: fielearning.py

import json
import random
import re

from pathlib import Path

MARKOV_FILE = Path("markov_data.json")

# Minimum / maximum number of words Fie will produce in a generated phrase.
MIN_WORDS = 4
MAX_WORDS = 20

# How many words must be in a message before we bother learning from it.
# Filters out one-word reactions, emoji-only messages, etc.
MIN_LEARN_LENGTH = 3
MAX_LEARN_LENGTH = 30


# --------------------------------------------------------------------------- #
# Internal helpers                                                             #
# --------------------------------------------------------------------------- #

def _load() -> dict:
    if MARKOV_FILE.exists():
        with open(MARKOV_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"chain": {}, "starters": {}}


def _save(data: dict) -> None:
    with open(MARKOV_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _clean(text: str) -> str:
    """Lowercase and strip out anything that isn't a letter, digit, or space."""
    text = text.lower()
    # Remove Discord mentions, URLs, and custom emotes before splitting.
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^a-z0-9áéíóúàãõâêôüçñ' ]", " ", text)
    return text.strip()


def _weighted_choice(options: dict) -> str:
    """Pick a key from {word: count} weighted by count."""
    words = list(options.keys())
    weights = list(options.values())
    return random.choices(words, weights=weights, k=1)[0]


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #

def learn(message_text: str) -> None:
    """
    Read a human message and update the Markov chain with the word transitions
    found in it. Call this once per non-bot message inside handle_message().
    """
    cleaned = _clean(message_text)
    words = cleaned.split()

    if MAX_LEARN_LENGTH < len(words) < MIN_LEARN_LENGTH:
        return

    data = _load()
    chain: dict = data["chain"]
    starters: dict = data["starters"]

    # Record the first word as a valid sentence starter.
    starters[words[0]] = starters.get(words[0], 0) + 1

    # Walk every consecutive pair and record the transition.
    for i in range(len(words) - 1):
        current = words[i]
        next_word = words[i + 1]

        if current not in chain:
            chain[current] = {}

        chain[current][next_word] = chain[current].get(next_word, 0) + 1

    data["chain"] = chain
    data["starters"] = starters
    _save(data)


def generate_phrase() -> str:
    """
    Walk the Markov chain to produce a new phrase. Returns a fallback string
    if the chain is still too small to generate anything sensible.
    """
    data = _load()
    chain: dict = data["chain"]
    starters: dict = data["starters"]

    if not starters or not chain:
        return "I haven't learned enough to say anything yet... talk more!"

    # Pick a starting word weighted by how often it actually started a sentence.
    current = _weighted_choice(starters)
    phrase = [current]

    for _ in range(MAX_WORDS - 1):
        if current not in chain or not chain[current]:
            # Dead end — stop here.
            break

        current = _weighted_choice(chain[current])
        phrase.append(current)

        if len(phrase) >= MIN_WORDS and random.random() < 0.15:
            # Small chance to stop early so phrases don't always hit MAX_WORDS.
            break

    if len(phrase) < MIN_WORDS:
        # The chain led us to a dead end too quickly; just return what we have.
        pass

    return " ".join(phrase).capitalize()


def chain_stats() -> str:
    """Return a small human-readable summary of how much Fie has learned."""
    data = _load()
    chain = data["chain"]
    starters = data["starters"]

    total_words = len(chain)
    total_transitions = sum(sum(v.values()) for v in chain.values())
    total_starters = len(starters)

    return (f"I've learned **{total_words}** unique words, "
            f"**{total_transitions}** word transitions, "
            f"and **{total_starters}** sentence starters so far!")