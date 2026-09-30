from tools.web_research import WebResearch
from tools.lead_qualification import LeadQualificationEngine


def main():

    researcher = WebResearch()

    results = researcher.search(
        query="small business AI automation company",
        limit=20
    )

    engine = LeadQualificationEngine()

    leads = engine.qualify(results)

    print()
    print("=" * 60)
    print("FINAL LEADS")
    print("=" * 60)

    for index, lead in enumerate(
        leads,
        start=1
    ):

        print()
        print(
            f"Lead #{index}"
        )

        print(
            f"Business: "
            f"{lead['business']}"
        )

        print(
            f"Website: "
            f"{lead['website']}"
        )

        print(
            f"Fit: "
            f"{lead['fit']}"
        )

        print(
            f"Status: "
            f"{lead['status']}"
        )


if __name__ == "__main__":
    main()
