"""Quick script to see FinBERT scores for sample sentences."""

import asyncio
import sys
sys.path.insert(0, "../fast")

import sentiment_agent as sa
from sentiment_agent import score_with_finbert, _direction_from_score

# Load FinBERT
from transformers import AutoModelForSequenceClassification, AutoTokenizer

sa.finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
sa.finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
sa.finbert_model.eval()

sentences = [
    "Tesla reported record-breaking revenue, beating all analyst expectations.",
    "The company announced massive layoffs and a 40% drop in revenue.",
    "Apple held its quarterly earnings call on Tuesday as scheduled.",
    "Bitcoin surged 20% after major institutional investors announced new positions.",
    "The bank is under federal investigation for fraud and money laundering.",
]

async def main():
    for text in sentences:
        result = await score_with_finbert(text)
        direction = _direction_from_score(result["score"])
        print(f"\n\"{text}\"")
        print(f"  Score: {result['score']:.4f}  |  Confidence: {result['confidence']:.4f}  |  Direction: {direction}")

asyncio.run(main())
