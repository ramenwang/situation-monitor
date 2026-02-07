"""
Region Detection

Detects geographic regions mentioned in news text.
"""

from typing import Optional


# Default region keywords
DEFAULT_REGIONS: dict[str, list[str]] = {
    "EUROPE": [
        "nato", "eu", "european", "ukraine", "russia", "germany", "france",
        "uk", "britain", "poland", "italy", "spain", "netherlands", "belgium",
        "sweden", "norway", "finland", "denmark", "austria", "switzerland",
        "greece", "portugal", "ireland", "czech", "romania", "hungary",
    ],
    "MENA": [  # Middle East & North Africa
        "iran", "israel", "saudi", "syria", "iraq", "gaza", "lebanon",
        "yemen", "houthi", "middle east", "dubai", "uae", "qatar", "kuwait",
        "bahrain", "oman", "jordan", "egypt", "libya", "tunisia", "morocco",
        "algeria", "turkey", "ankara", "tehran", "riyadh", "tel aviv",
    ],
    "APAC": [  # Asia-Pacific
        "china", "taiwan", "japan", "korea", "indo-pacific", "south china sea",
        "asean", "philippines", "vietnam", "thailand", "indonesia", "malaysia",
        "singapore", "australia", "new zealand", "india", "pakistan",
        "beijing", "tokyo", "seoul", "taipei", "hong kong", "shanghai",
    ],
    "AMERICAS": [
        "us", "usa", "america", "united states", "canada", "mexico", "brazil",
        "venezuela", "argentina", "chile", "colombia", "peru", "latin america",
        "washington", "new york", "california", "texas", "florida",
    ],
    "AFRICA": [
        "africa", "sahel", "niger", "sudan", "ethiopia", "somalia", "kenya",
        "nigeria", "south africa", "congo", "mali", "burkina faso", "chad",
        "cameroon", "ghana", "senegal", "tanzania", "uganda", "rwanda",
    ],
    "RUSSIA_CIS": [  # Russia & former Soviet states
        "russia", "moscow", "kremlin", "putin", "belarus", "kazakhstan",
        "uzbekistan", "turkmenistan", "kyrgyzstan", "tajikistan", "armenia",
        "azerbaijan", "georgia", "moldova", "siberia",
    ],
}


class RegionDetector:
    """
    Detects geographic regions in text.

    Example usage:
        detector = RegionDetector()
        region = detector.detect("Tensions rise in Taiwan Strait")
        # Returns: "APAC"

        # Get all regions:
        regions = detector.detect_all("US sanctions on Russia over Ukraine")
        # Returns: ["AMERICAS", "EUROPE", "RUSSIA_CIS"]

        # Add custom region:
        detector.add_region("ARCTIC", ["arctic", "greenland", "svalbard"])
    """

    def __init__(
        self,
        regions: Optional[dict[str, list[str]]] = None,
        case_sensitive: bool = False,
    ):
        """
        Initialize region detector.

        Args:
            regions: Custom region definitions. If None, uses defaults.
            case_sensitive: Whether to match case-sensitively.
        """
        self.regions = regions if regions is not None else DEFAULT_REGIONS.copy()
        self.case_sensitive = case_sensitive

    def detect(self, text: str) -> Optional[str]:
        """
        Detect the primary region mentioned in text.

        Returns the first region found (by definition order).

        Args:
            text: Text to analyze.

        Returns:
            Region name or None if no region detected.
        """
        if not text:
            return None

        search_text = text if self.case_sensitive else text.lower()

        for region, keywords in self.regions.items():
            for keyword in keywords:
                kw = keyword if self.case_sensitive else keyword.lower()
                if kw in search_text:
                    return region

        return None

    def detect_all(self, text: str) -> list[str]:
        """
        Detect all regions mentioned in text.

        Args:
            text: Text to analyze.

        Returns:
            List of region names.
        """
        if not text:
            return []

        search_text = text if self.case_sensitive else text.lower()
        detected = []

        for region, keywords in self.regions.items():
            for keyword in keywords:
                kw = keyword if self.case_sensitive else keyword.lower()
                if kw in search_text:
                    detected.append(region)
                    break

        return detected

    def detect_with_keywords(self, text: str) -> dict[str, list[str]]:
        """
        Detect regions and return the matching keywords.

        Args:
            text: Text to analyze.

        Returns:
            Dict of region -> list of matched keywords.
        """
        if not text:
            return {}

        search_text = text if self.case_sensitive else text.lower()
        results = {}

        for region, keywords in self.regions.items():
            matches = []
            for keyword in keywords:
                kw = keyword if self.case_sensitive else keyword.lower()
                if kw in search_text:
                    matches.append(keyword)
            if matches:
                results[region] = matches

        return results

    def add_region(self, name: str, keywords: list[str]):
        """Add a new region."""
        self.regions[name] = keywords

    def remove_region(self, name: str):
        """Remove a region."""
        self.regions.pop(name, None)

    def add_keyword(self, region: str, keyword: str):
        """Add a keyword to an existing region."""
        if region in self.regions:
            self.regions[region].append(keyword)

    def get_regions(self) -> list[str]:
        """Get list of all region names."""
        return list(self.regions.keys())
