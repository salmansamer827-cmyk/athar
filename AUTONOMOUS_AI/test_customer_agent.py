from growth.customer_agent import CustomerAgent


def main():

    agent = CustomerAgent()

    agent.find_customers(
        niche="small businesses",
        limit=10
    )


if __name__ == "__main__":
    main()
