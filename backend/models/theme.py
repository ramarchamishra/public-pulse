from dataclasses import dataclass, field


@dataclass
class Theme:

    theme_id: int | None
    search_id: int

    name: str

    keywords: list[str] = field(default_factory=list)

    tweet_count: int = 0