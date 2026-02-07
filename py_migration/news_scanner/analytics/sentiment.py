"""
Sentiment Analysis

Basic sentiment analysis using keyword matching.
Can be extended with ML models (VADER, transformers, etc.)
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum


class Sentiment(str, Enum):
    """Sentiment categories."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    sentiment: Sentiment
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    positive_keywords: list[str]
    negative_keywords: list[str]


# Default sentiment keywords
POSITIVE_KEYWORDS = [
    "surge", "soar", "rally", "gain", "rise", "jump", "boom", "bull",
    "breakthrough", "success", "win", "growth", "profit", "beat",
    "optimistic", "bullish", "recovery", "strong", "record high",
    "upgrade", "outperform", "exceed", "positive", "improvement",
]

NEGATIVE_KEYWORDS = [
    "crash", "plunge", "drop", "fall", "decline", "slump", "bear",
    "crisis", "failure", "loss", "miss", "weak", "recession",
    "pessimistic", "bearish", "downgrade", "underperform", "warning",
    "concern", "fear", "risk", "threat", "negative", "deteriorate",
    "layoff", "bankruptcy", "default", "collapse",
]


class SentimentAnalyzer:
    """
    Analyzes sentiment of text.

    Basic implementation using keyword matching.
    For production, consider integrating:
    - NLTK VADER
    - TextBlob
    - Hugging Face transformers

    Example usage:
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("Stock surges on strong earnings")
        # Returns: SentimentResult(sentiment=POSITIVE, score=0.5, ...)

        # With custom keywords:
        analyzer = SentimentAnalyzer(
            positive=["bullish", "moon"],
            negative=["bearish", "dump"]
        )

        # Use external model:
        class MyMLAnalyzer(SentimentAnalyzer):
            def analyze(self, text):
                # Call your ML model here
                pass
    """

    def __init__(
        self,
        positive: Optional[list[str]] = None,
        negative: Optional[list[str]] = None,
        case_sensitive: bool = False,
    ):
        """
        Initialize sentiment analyzer.

        Args:
            positive: Positive sentiment keywords.
            negative: Negative sentiment keywords.
            case_sensitive: Whether to match case-sensitively.
        """
        self.positive = positive if positive is not None else POSITIVE_KEYWORDS.copy()
        self.negative = negative if negative is not None else NEGATIVE_KEYWORDS.copy()
        self.case_sensitive = case_sensitive

    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze.

        Returns:
            SentimentResult with sentiment, score, and matched keywords.
        """
        if not text:
            return SentimentResult(
                sentiment=Sentiment.NEUTRAL,
                score=0.0,
                confidence=0.0,
                positive_keywords=[],
                negative_keywords=[],
            )

        search_text = text if self.case_sensitive else text.lower()

        # Find matches
        pos_matches = []
        for kw in self.positive:
            k = kw if self.case_sensitive else kw.lower()
            if k in search_text:
                pos_matches.append(kw)

        neg_matches = []
        for kw in self.negative:
            k = kw if self.case_sensitive else kw.lower()
            if k in search_text:
                neg_matches.append(kw)

        # Calculate score
        pos_count = len(pos_matches)
        neg_count = len(neg_matches)
        total = pos_count + neg_count

        if total == 0:
            return SentimentResult(
                sentiment=Sentiment.NEUTRAL,
                score=0.0,
                confidence=0.0,
                positive_keywords=[],
                negative_keywords=[],
            )

        # Score from -1 to 1
        score = (pos_count - neg_count) / total

        # Confidence based on number of matches
        confidence = min(1.0, total / 5.0)  # Max confidence at 5+ matches

        # Determine sentiment
        if pos_count > 0 and neg_count > 0:
            sentiment = Sentiment.MIXED
        elif score > 0.1:
            sentiment = Sentiment.POSITIVE
        elif score < -0.1:
            sentiment = Sentiment.NEGATIVE
        else:
            sentiment = Sentiment.NEUTRAL

        return SentimentResult(
            sentiment=sentiment,
            score=score,
            confidence=confidence,
            positive_keywords=pos_matches,
            negative_keywords=neg_matches,
        )

    def is_positive(self, text: str) -> bool:
        """Check if text has positive sentiment."""
        result = self.analyze(text)
        return result.sentiment == Sentiment.POSITIVE

    def is_negative(self, text: str) -> bool:
        """Check if text has negative sentiment."""
        result = self.analyze(text)
        return result.sentiment == Sentiment.NEGATIVE

    def add_positive(self, keyword: str):
        """Add a positive keyword."""
        self.positive.append(keyword)

    def add_negative(self, keyword: str):
        """Add a negative keyword."""
        self.negative.append(keyword)
