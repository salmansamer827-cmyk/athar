import requests


def fetch_url(url):
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "ATHAR-AI/1.0"
        }
    )

    response.raise_for_status()

    return response.text
