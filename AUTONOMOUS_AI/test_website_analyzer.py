from tools.website_analyzer import WebsiteAnalyzer


def main():

    analyzer = WebsiteAnalyzer()

    analyzer.analyze(
        "https://automatenexus.com/"
    )


if __name__ == "__main__":
    main()
