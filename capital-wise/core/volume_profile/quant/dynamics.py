from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileDynamics:
    poc_change: float
    poc_velocity: float

    vah_change: float
    val_change: float

    value_area_width: float
    value_area_width_change: float

    value_location: float

    poc_direction: str
    value_area_state: str


class ProfileDynamicsEngine:

    def calculate(
        self,
        current_poc: float,
        previous_poc: float,
        previous_poc_k: float,

        current_vah: float,
        previous_vah: float,

        current_val: float,
        previous_val: float,

        price_low: float,
        price_high: float,

        lookback: int = 1,
    ) -> ProfileDynamics:

        if lookback <= 0:
            raise ValueError(
                "lookback must be > 0"
            )

        if price_high <= price_low:
            raise ValueError(
                "price_high must be > price_low"
            )

        current_width = (
            current_vah - current_val
        )

        previous_width = (
            previous_vah - previous_val
        )

        poc_change = (
            current_poc
            - previous_poc
        )

        poc_velocity = (
            current_poc
            - previous_poc_k
        ) / lookback

        vah_change = (
            current_vah
            - previous_vah
        )

        val_change = (
            current_val
            - previous_val
        )

        width_change = (
            current_width
            - previous_width
        )

        value_location = (
            (current_poc - price_low)
            / (price_high - price_low)
        )

        epsilon = 1e-12

        if poc_change > epsilon:
            poc_direction = "UP"
        elif poc_change < -epsilon:
            poc_direction = "DOWN"
        else:
            poc_direction = "FLAT"

        width_epsilon = max(
            abs(previous_width) * 0.001,
            epsilon,
        )

        if width_change > width_epsilon:
            value_state = "EXPANDING"
        elif width_change < -width_epsilon:
            value_state = "CONTRACTING"
        else:
            value_state = "STABLE"

        return ProfileDynamics(
            poc_change=poc_change,
            poc_velocity=poc_velocity,

            vah_change=vah_change,
            val_change=val_change,

            value_area_width=current_width,
            value_area_width_change=width_change,

            value_location=value_location,

            poc_direction=poc_direction,
            value_area_state=value_state,
        )
