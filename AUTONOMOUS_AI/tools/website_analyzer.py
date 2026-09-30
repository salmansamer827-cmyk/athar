import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class WebsiteAnalyzer:

    def __init__(self):

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Linux; Android 14) "
                "AppleWebKit/537.36 "
                "Chrome/120.0 Mobile Safari/537.36"
            )
        }

    def analyze(self, url: str):

        print()
        print("=" * 60)
        print("WEBSITE ANALYZER")
        print("=" * 60)
        print(f"URL: {url}")
        print()

        try:

            response = requests.get(
                url,
                headers=self.headers,
                timeout=15
            )

            response.raise_for_status()

        except requests.RequestException as e:

            print(
                f"[ERROR] Website request failed: {e}"
            )

            return None

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # إزالة العناصر غير المهمة
        for element in soup(
            ["script", "style", "noscript"]
        ):
            element.decompose()

        title = ""

        if soup.title:

            title = soup.title.get_text(
                " ",
                strip=True
            )

        text = soup.get_text(
            " ",
            strip=True
        )

        # تنظيف النص
        text = " ".join(
            text.split()
        )

        # نأخذ جزءًا محدودًا للتحليل
        text_sample = text[:10000]

        signals = {
            "contact": [
                "contact",
                "contact us",
                "get in touch"
            ],

            "services": [
                "services",
                "our services",
                "solutions"
            ],

            "booking": [
                "book",
                "booking",
                "appointment",
                "schedule"
            ],

            "sales": [
                "sales",
                "quote",
                "request a quote"
            ],

            "support": [
                "support",
                "customer service",
                "help"
            ],

            "marketing": [
                "marketing",
                "advertising",
                "social media"
            ],

            "business": [
                "company",
                "business",
                "agency",
                "firm",
                "studio"
            ]
        }

        detected = {}

        lower_text = text_sample.lower()

        for category, keywords in signals.items():

            matches = []

            for keyword in keywords:

                if keyword.lower() in lower_text:

                    matches.append(keyword)

            if matches:

                detected[category] = matches

        # استخراج الروابط
        links = []

        for link in soup.find_all("a", href=True):

            href = link.get("href")

            absolute_url = urljoin(
                url,
                href
            )

            links.append(
                absolute_url
            )

        # إزالة التكرار
        links = list(
            dict.fromkeys(links)
        )

        result = {

            "url": url,

            "title": title,

            "text": text_sample,

            "signals": detected,

            "links": links[:100]
        }

        print(
            f"Title: {title}"
        )

        print()

        print("Detected signals:")

        if detected:

            for category, matches in detected.items():

                print(
                    f"  {category}: "
                    f"{', '.join(matches)}"
                )

        else:

            print("  None")

        print()

        print(
            f"Links discovered: "
            f"{len(links)}"
        )

        return result
