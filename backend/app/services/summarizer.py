import re

from .. import config

_STOPWORDS_FR = {
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "en", "à", "au", "aux",
    "ce", "ces", "cet", "cette", "il", "elle", "ils", "elles", "on", "nous", "vous",
    "je", "tu", "que", "qui", "quoi", "dont", "où", "est", "sont", "était", "être",
    "avoir", "a", "ont", "pour", "par", "sur", "sous", "dans", "avec", "sans", "plus",
    "mais", "ou", "donc", "or", "ni", "car", "se", "sa", "son", "ses", "leur", "leurs",
    "mon", "ma", "mes", "ton", "ta", "tes", "not", "d", "l", "s", "qu", "n", "y",
}


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _extractive_summary(text: str, max_sentences: int = 5) -> str:
    sentences = _split_sentences(text)
    if len(sentences) <= max_sentences:
        return text.strip()

    word_freq: dict[str, int] = {}
    for word in re.findall(r"\b\w+\b", text.lower()):
        if word in _STOPWORDS_FR or word.isdigit():
            continue
        word_freq[word] = word_freq.get(word, 0) + 1

    if not word_freq:
        return " ".join(sentences[:max_sentences])

    max_freq = max(word_freq.values())
    for word in word_freq:
        word_freq[word] /= max_freq

    scores = []
    for idx, sentence in enumerate(sentences):
        words = re.findall(r"\b\w+\b", sentence.lower())
        if not words:
            score = 0.0
        else:
            score = sum(word_freq.get(w, 0) for w in words) / len(words)
        position_bonus = 0.15 if idx == 0 else 0.0
        scores.append((score + position_bonus, idx, sentence))

    top = sorted(scores, key=lambda x: x[0], reverse=True)[:max_sentences]
    top_in_order = [s for _, _, s in sorted(top, key=lambda x: x[1])]
    return " ".join(top_in_order)


def _llm_summary(text: str, title: str | None) -> str | None:
    if not config.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
    except ImportError:
        return None

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        title_hint = f' du film "{title}"' if title else ""
        message = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=400,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Voici une transcription ou description{title_hint}. "
                        "Rédige un résumé clair et concis en français (5 à 8 phrases), "
                        "sans spoiler la toute fin si possible, sans préambule ni titre:\n\n"
                        f"{text[:15000]}"
                    ),
                }
            ],
        )
        return "".join(block.text for block in message.content if hasattr(block, "text")).strip()
    except Exception:
        return None


def generate_summary(text: str, title: str | None = None) -> tuple[str, str]:
    text = (text or "").strip()
    if not text:
        return "", "none"

    llm_result = _llm_summary(text, title)
    if llm_result:
        return llm_result, "llm"

    return _extractive_summary(text), "extractive"
