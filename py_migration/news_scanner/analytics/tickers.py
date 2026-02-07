"""
Ticker Extraction

Extracts stock symbols and cryptocurrency tickers from text.
"""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass
class TickerMatch:
    """A matched ticker."""
    symbol: str
    ticker_type: str  # "stock", "crypto", "index"
    context: str = ""  # Surrounding text


# Known crypto tickers (to avoid false positives)
KNOWN_CRYPTO = {
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "AVAX",
    "MATIC", "LINK", "UNI", "ATOM", "LTC", "BCH", "XLM", "ALGO",
    "VET", "FIL", "THETA", "AAVE", "EOS", "XTZ", "MKR", "COMP",
}

# Known indices
KNOWN_INDICES = {
    "SPX", "DJI", "NDX", "RUT", "VIX", "DXY",
}

# Common false positives to exclude
EXCLUDED_WORDS = {
    "A", "I", "AM", "PM", "CEO", "CFO", "CTO", "COO", "AI", "US",
    "UK", "EU", "UN", "IT", "TV", "PC", "PR", "HR", "VP", "MD",
    "OF", "OR", "ON", "BY", "TO", "AT", "IS", "IN", "IF", "AS",
    "AN", "THE", "AND", "FOR", "NOT", "BUT", "NEW", "OLD", "TOP",
    "IPO", "CEO", "FDA", "SEC", "FBI", "CIA", "NSA", "DOJ", "EPA",
    "IRS", "GDP", "CPI", "PMI", "IMF", "WTO", "WHO",
}


class TickerExtractor:
    """
    Extracts stock and crypto tickers from text.

    Example usage:
        extractor = TickerExtractor()
        tickers = extractor.extract("$AAPL and $GOOGL are up. Bitcoin (BTC) rising.")
        # Returns: ["AAPL", "GOOGL", "BTC"]

        # With types:
        matches = extractor.extract_with_types("$AAPL up, BTC surging")
        # Returns: [TickerMatch("AAPL", "stock"), TickerMatch("BTC", "crypto")]

        # Add custom patterns:
        extractor.add_crypto("PEPE")
    """

    def __init__(
        self,
        known_crypto: Optional[set[str]] = None,
        known_indices: Optional[set[str]] = None,
        excluded_words: Optional[set[str]] = None,
    ):
        """
        Initialize ticker extractor.

        Args:
            known_crypto: Set of known crypto symbols.
            known_indices: Set of known index symbols.
            excluded_words: Words to exclude from matching.
        """
        self.known_crypto = known_crypto if known_crypto is not None else KNOWN_CRYPTO.copy()
        self.known_indices = known_indices if known_indices is not None else KNOWN_INDICES.copy()
        self.excluded_words = excluded_words if excluded_words is not None else EXCLUDED_WORDS.copy()

        # Compile regex patterns
        self._patterns = [
            # $AAPL style
            (re.compile(r'\$([A-Z]{1,5})\b'), "stock"),
            # Explicit stock mentions: "AAPL stock", "shares of AAPL"
            (re.compile(r'\b([A-Z]{2,5})\s+(?:stock|shares|inc|corp|ltd)', re.IGNORECASE), "stock"),
            # Crypto: known symbols as words
            (re.compile(r'\b(' + '|'.join(self.known_crypto) + r')\b'), "crypto"),
            # Parenthetical: "(AAPL)" often used for tickers
            (re.compile(r'\(([A-Z]{2,5})\)'), "stock"),
        ]

    def extract(self, text: str) -> list[str]:
        """
        Extract all tickers from text.

        Args:
            text: Text to analyze.

        Returns:
            List of unique ticker symbols.
        """
        if not text:
            return []

        tickers = set()

        for pattern, _ in self._patterns:
            for match in pattern.finditer(text):
                symbol = match.group(1).upper()
                if symbol not in self.excluded_words:
                    tickers.add(symbol)

        return sorted(tickers)

    def extract_with_types(self, text: str) -> list[TickerMatch]:
        """
        Extract tickers with their types.

        Args:
            text: Text to analyze.

        Returns:
            List of TickerMatch objects.
        """
        if not text:
            return []

        matches = []
        seen = set()

        for pattern, default_type in self._patterns:
            for match in pattern.finditer(text):
                symbol = match.group(1).upper()
                if symbol in self.excluded_words or symbol in seen:
                    continue

                seen.add(symbol)

                # Determine type
                if symbol in self.known_crypto:
                    ticker_type = "crypto"
                elif symbol in self.known_indices:
                    ticker_type = "index"
                else:
                    ticker_type = default_type

                # Get context (surrounding 20 chars)
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                context = text[start:end].strip()

                matches.append(TickerMatch(symbol, ticker_type, context))

        return matches

    def add_crypto(self, symbol: str):
        """Add a known crypto symbol."""
        self.known_crypto.add(symbol.upper())
        self._rebuild_patterns()

    def add_excluded(self, word: str):
        """Add a word to exclude list."""
        self.excluded_words.add(word.upper())

    def _rebuild_patterns(self):
        """Rebuild regex patterns after modifying known symbols."""
        self._patterns[2] = (
            re.compile(r'\b(' + '|'.join(self.known_crypto) + r')\b'),
            "crypto"
        )

    def is_ticker(self, symbol: str) -> bool:
        """Check if a symbol looks like a valid ticker."""
        symbol = symbol.upper()
        if symbol in self.excluded_words:
            return False
        if len(symbol) < 1 or len(symbol) > 5:
            return False
        if not symbol.isalpha():
            return False
        return True
