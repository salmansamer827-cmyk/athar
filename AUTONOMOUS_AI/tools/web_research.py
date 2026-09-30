import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


def clean_url(url: str) -> str:
    """Extract the original URL from DuckDuckGo redirect URLs."""

    if not url:
        return ""

    if url.startswith("//"):
        url = "https:" + url

    parsed = urlparse(url)

    if "duckduckgo.com" in parsed.netloc:
        params = parse_qs(parsed.query)
        original_url = params.get("uddg")

        if original_url:
            return original_url[0]

    return url


class WebResearch:

    def __init__(self):
        self.base_url = "https://html.duckduckgo.com/html/"

    def search(self, query: str, limit: int = 10):

        print()
        print("=" * 60)
        print("WEB RESEARCH")
        print("=" * 60)
        print(f"Query: {query}")
        print(f"Limit: {limit}")
        print()

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 14) "
                "AppleWebKit/537.36 "
                "Chrome/120.0 Mobile Safari/537.36"
            )
        }

        try:
            response = requests.get(
                self.base_url,
                params={"q": query},
                headers=headers,
                timeout=15
            )

            response.raise_for_status()

        except requests.RequestException as e:

            print(f"[ERROR] Web search failed: {e}")
            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []

        for result in soup.select(".result"):

            title_element = result.select_one(
                ".result__title"
            )

            link_element = result.select_one(
                ".result__a"
            )

            snippet_element = result.select_one(
                ".result__snippet"
            )

            if not link_element:
                continue

            title = (
                title_element.get_text(
                    " ",
                    strip=True
                )
                if title_element
                else link_element.get_text(
                    " ",
                    strip=True
                )
            )

            url = link_element.get(
                "href",
                ""
            )

            url = clean_url(url)

            snippet = (
                snippet_element.get_text(
                    " ",
                    strip=True
                )
                if snippet_element
                else ""
            )

            results.append({
                "title": title,
                "url": url,
                "snippet": snippet
            })

            if len(results) >= limit:
                break

        print(
            f"[INFO] Search results found: "
            f"{len(results)}"
        )

        for index, result in enumerate(
            results,
            start=1
        ):

            print()
            print(
                f"[RESULT {index}] "
                f"{result['title']}"
            )

            print(
                f"URL: {result['url']}"
            )

            print(
                f"Description: "
                f"{result['snippet']}"
            )

        return results
