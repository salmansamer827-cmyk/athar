from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileRiskLevels:
    direction: str

    entry: float
    stop_loss: float
    take_profit: float

    price_risk: float
    reward: float
    rr: float

    reference_level: float
    buffer: float


class ProfileRiskLevelEngine:
    """
    CAPITAL WISE

    Mathematical Volume Profile Risk Engine.

    Stop placement is derived from:
        - Value Area
        - HVN
        - LVN
        - Standard deviation

    The engine does NOT determine whether
    a trade should exist.

    It only calculates risk levels after
    a direction has been validated.
    """

    def __init__(
        self,
        volatility_buffer: float = 0.25,
        reward_risk: float = 3.0,
    ):

        if volatility_buffer < 0:
            raise ValueError(
                "volatility_buffer must be >= 0"
            )

        if reward_risk <= 0:
            raise ValueError(
                "reward_risk must be > 0"
            )

        self.volatility_buffer = (
            volatility_buffer
        )

        self.reward_risk = reward_risk

    def calculate(
        self,
        direction: str,
        entry: float,
        val: float,
        vah: float,
        std: float,
        nodes: list,
    ) -> ProfileRiskLevels:

        direction = direction.upper()

        if direction not in {
            "LONG",
            "SHORT",
        }:
            raise ValueError(
                "direction must be LONG or SHORT"
            )

        if entry <= 0:
            raise ValueError(
                "entry must be > 0"
            )

        if std < 0:
            raise ValueError(
                "std must be >= 0"
            )

        buffer = (
            std
            * self.volatility_buffer
        )

        if direction == "LONG":

            reference = self._long_reference(
                entry=entry,
                val=val,
                nodes=nodes,
            )

            stop = reference - buffer

            if stop >= entry:
                stop = (
                    entry - max(
                        buffer,
                        std * 0.25,
                        entry * 0.001,
                    )
                )

            price_risk = (
                entry - stop
            )

            target = (
                entry
                + price_risk
                * self.reward_risk
            )

        else:

            reference = self._short_reference(
                entry=entry,
                vah=vah,
                nodes=nodes,
            )

            stop = reference + buffer

            if stop <= entry:
                stop = (
                    entry + max(
                        buffer,
                        std * 0.25,
                        entry * 0.001,
                    )
                )

            price_risk = (
                stop - entry
            )

            target = (
                entry
                - price_risk
                * self.reward_risk
            )

        return ProfileRiskLevels(
            direction=direction,
            entry=entry,
            stop_loss=stop,
            take_profit=target,
            price_risk=price_risk,
            reward=(
                price_risk
                * self.reward_risk
            ),
            rr=self.reward_risk,
            reference_level=reference,
            buffer=buffer,
        )

    @staticmethod
    def _long_reference(
        entry: float,
        val: float,
        nodes: list,
    ) -> float:

        candidates = [val]

        for node in nodes:

            center = (
                node.center_price
            )

            if center < entry:
                candidates.append(
                    center
                )

        return max(candidates)

    @staticmethod
    def _short_reference(
        entry: float,
        vah: float,
        nodes: list,
    ) -> float:

        candidates = [vah]

        for node in nodes:

            center = (
                node.center_price
            )

            if center > entry:
                candidates.append(
                    center
                )

        return min(candidates)
