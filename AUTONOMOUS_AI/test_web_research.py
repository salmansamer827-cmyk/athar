from tools.web_research import WebResearch


def main():

    researcher = WebResearch()

    researcher.search(
        query="small business AI automation",
        limit=10
    )


if __name__ == "__main__":
    main()
