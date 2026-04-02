"""
Sentiment Analysis Service using NLTK VADER.
Free, instant, no API key required.
"""

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Download VADER lexicon on first import (idempotent)
nltk.download("vader_lexicon", quiet=True)

_analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str) -> str:
    """
    Classify text as 'Positive', 'Negative', or 'Neutral'
    using VADER's compound polarity score.

    Thresholds (standard VADER recommendations):
        compound >= 0.05  → Positive
        compound <= -0.05 → Negative
        else              → Neutral
    """
    if not text or not isinstance(text, str):
        return "Neutral"

    scores = _analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.05:
        return "Positive"
    elif compound <= -0.05:
        return "Negative"
    else:
        return "Neutral"
