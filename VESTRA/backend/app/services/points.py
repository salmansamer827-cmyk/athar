USER_POINTS_PER_USD = 10_000
PROJECT_POINTS_PER_USD = 20_000


def usd_to_user_points(amount: float) -> int:
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    return int(amount * USER_POINTS_PER_USD)


def project_cost_to_points(amount: float) -> int:
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    return int(amount * PROJECT_POINTS_PER_USD)


def user_points_to_usd(points: int) -> float:
    if points < 0:
        raise ValueError("Points cannot be negative")

    return points / USER_POINTS_PER_USD


def project_points_to_usd(points: int) -> float:
    if points < 0:
        raise ValueError("Points cannot be negative")

    return points / PROJECT_POINTS_PER_USD
