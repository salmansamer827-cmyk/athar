from core.console import log
from tools.customer_research import CustomerResearch


class CustomerAgent:

    def __init__(self):

        self.researcher = CustomerResearch()

    def find_customers(self, niche: str, limit: int = 10):

        log("Customer Agent started")

        log(
            f"Searching potential customers "
            f"for niche: {niche}"
        )

        prospects = self.researcher.search(
            niche=niche,
            limit=limit
        )

        log(
            f"Customer research completed: "
            f"{len(prospects)} prospects"
        )

        return prospects
