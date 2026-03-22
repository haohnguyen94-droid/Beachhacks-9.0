from uagents import Model


class SharedAgentState(Model):
    chat_session_id: str
    query: str                      # ticker symbol (e.g. "AAPL") or free text
    user_sender_address: str
    result: str = ""
    source_agent: str = ""          # which agent produced this result
    posts_sent: int = 0             # how many ScraperOutputs were sent to sentiment agent
