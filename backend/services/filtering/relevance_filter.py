import re

STOPWORDS = {
    "a", "an", "the", "is", "are", "of", "for", "and", "or", "to", "in",
    "on", "with", "review", "reviews", "vs", "versus",
}

def extract_query_tokens(query: str) -> set[str]:
    """
    Extract meaningful tokens from a search query.
    e.g. "iphone 16 review" -> {"iphone", "16"}
    """
    tokens = re.findall(r"[a-z0-9]+", query.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 1}


def build_variant_patterns(tokens: set[str]) -> set[str]:
    """
    Expand tokens into acceptable variants.
    e.g. "iphone" + "16" -> also accept "iphone16", 
    """
    variants = set(tokens)

    # if there's a brand-like token directly followed/preceded by a number in the query,
    # also accept the concatenated form: "iphone" + "16" -> "iphone16"
    numeric_tokens = {t for t in tokens if t.isdigit()}
    word_tokens = tokens - numeric_tokens

    for word in word_tokens:
        for num in numeric_tokens:
            variants.add(f"{word}{num}")   # iphone16
            variants.add(f"{word} {num}")  # iphone 16 (already covered by individual tokens, but explicit)

    return variants


def is_relevant(text: str, query_tokens: set[str]) -> bool:
    """
    Returns True if the tweet contains at least one query token or variant.
    """
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # direct token match (handles "iphone", "16", "iphone16" as substrings too)
    for token in query_tokens:
        if token.isdigit():
            if re.search(rf"\b{re.escape(token)}\b", normalized):
                return True
        elif token in normalized:
            return True


    return False


def filter_relevant_tweets(tweets: list, query: str) -> list:
    """
    Filters a list of tweet objects, keeping only those with at least
    one keyword/variant from the query.
    """
    base_tokens = extract_query_tokens(query)
    all_tokens = build_variant_patterns(base_tokens)

    return [t for t in tweets if is_relevant(t.text, all_tokens)]