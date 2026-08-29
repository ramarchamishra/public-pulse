import html
import re


class RegexTextCleaner:
    """
    Light text cleaning for tweets before embeddings/topic modeling.

    Removes:
    - URLs
    - @mentions

    Converts:
    - HTML entities, e.g. &amp; -> &

    Preserves:
    - hashtag words, e.g. #NEET -> NEET
    - normal punctuation/content
    """

    URL_PATTERN = re.compile(r"https?://\S+")
    MENTION_PATTERN = re.compile(r"@\w+")
    HASHTAG_PATTERN = re.compile(r"#(\w+)")
    WHITESPACE_PATTERN = re.compile(r"\s+")

    def clean(self, text: str) -> str:
        if not text:
            return ""

        cleaned = html.unescape(text)

        cleaned = self.URL_PATTERN.sub("", cleaned)
        cleaned = self.MENTION_PATTERN.sub("", cleaned)

        # Keep hashtag text, remove only '#'
        cleaned = self.HASHTAG_PATTERN.sub(r"\1", cleaned)

        cleaned = self.WHITESPACE_PATTERN.sub(" ", cleaned).strip()

        return cleaned

    def clean_batch(self, texts: list[str]) -> list[str]:
        return [self.clean(text) for text in texts]