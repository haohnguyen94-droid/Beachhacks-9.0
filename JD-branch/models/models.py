from uagents import Model


class ScraperOutput(Model):
    ticker: str
    text: str
    source_name: str
    source_type: str
    credibility_weight: float
    scraped_at: str
    post_id: str = ""
    title: str = ""
    url: str = ""
    published_at: str = ""
    raw_payload: dict = {}