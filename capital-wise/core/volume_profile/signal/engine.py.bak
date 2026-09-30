from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProfileSignalConfig:
    """
    Quantitative signal configuration.

    The engine uses only:
        - POC
        - VAH
        - VAL
        - Value Location
        - POC Velocity
        - Value Area Dynamics
        - Probability
        - Probability uncertainty
        - Expected Value
    """

    min_probability: float = 0.55
    min_adjusted_probability: float = 0.55

    min_ev_r: float = 0.0

    value_location_long: float = 0.60
    value_location_short: float = 0.40

    min_poc_velocity: float = 0.0

    require_expansion: bool = True

    # ======================================================
    # QUANTITATIVE SCORE
    # ======================================================

    min_score: float = 80.0

    weight_probability: float = 25.0
    weight_value_location: float = 20.0
    weight_poc_velocity: float = 20.0
    weight_value_area: float = 15.0
    weight_expected_value: float = 15.0
    weight_uncertainty: float = 5.0

    reward_risk: float = 3.0

    transaction_cost_r: float = 0.05

    uncertainty_penalty: float = 0.50


class VolumeProfileSignalEngine:
    """
    CAPITAL WISE
    ==============================

    Pure quantitative Volume Profile
    signal engine.

    No:
        EMA
        RSI
        MACD
        SMC

    Core mathematical variables:
        POC
        VAH
        VAL
        Value Location
        POC Velocity
        Value Area Dynamics
        Historical Probability
        Adjusted Probability
        Uncertainty
        Expected Value
    """

    def __init__(
        self,
        config: ProfileSignalConfig | None = None,
    ) -> None:

        self.config = (
            config
            if config is not None
            else ProfileSignalConfig()
        )

        self._validate_config()

    # ==========================================================
    # CONFIG VALIDATION
    # ==========================================================

    def _validate_config(self) -> None:

        c = self.config

        if not 0.0 <= c.min_probability <= 1.0:
            raise ValueError(
                "min_probability must be between 0 and 1"
            )

        if not 0.0 <= c.min_adjusted_probability <= 1.0:
            raise ValueError(
                "min_adjusted_probability must be between 0 and 1"
            )

        if not 0.0 <= c.value_location_short <= 1.0:
            raise ValueError(
                "value_location_short must be between 0 and 1"
            )

        if not 0.0 <= c.value_location_long <= 1.0:
            raise ValueError(
                "value_location_long must be between 0 and 1"
            )

        if c.value_location_short >= c.value_location_long:
            raise ValueError(
                "short value location must be below long value location"
            )

        if c.reward_risk <= 0:
            raise ValueError(
                "reward_risk must be > 0"
            )

        if c.transaction_cost_r < 0:
            raise ValueError(
                "transaction_cost_r must be >= 0"
            )

        if not 0.0 <= c.uncertainty_penalty <= 1.0:
            raise ValueError(
                "uncertainty_penalty must be between 0 and 1"
            )

    # ==========================================================
    # NUMERIC VALIDATION
    # ==========================================================

    @staticmethod
    def _finite(value: float, name: str) -> float:

        value = float(value)

        if not value == value:
            raise ValueError(
                f"{name} cannot be NaN"
            )

        if value in (
            float("inf"),
            float("-inf"),
        ):
            raise ValueError(
                f"{name} must be finite"
            )

        return value

    # ==========================================================
    # EVALUATION
    # ==========================================================

    def evaluate(
        self,
        profile: dict,
        dynamics: dict,
        probability: float,
        ev_r: float,
        entry: float,
        adjusted_probability: float | None = None,
        uncertainty: float = 0.0,
    ) -> Optional[dict]:

        entry = self._finite(
            entry,
            "entry",
        )

        probability = self._finite(
            probability,
            "probability",
        )

        ev_r = self._finite(
            ev_r,
            "ev_r",
        )

        uncertainty = self._finite(
            uncertainty,
            "uncertainty",
        )

        if entry <= 0:
            raise ValueError(
                "entry must be > 0"
            )

        if not 0.0 <= probability <= 1.0:
            raise ValueError(
                "probability must be between 0 and 1"
            )

        if adjusted_probability is None:
            adjusted_probability = probability

        adjusted_probability = self._finite(
            adjusted_probability,
            "adjusted_probability",
        )

        if not 0.0 <= adjusted_probability <= 1.0:
            raise ValueError(
                "adjusted_probability must be between 0 and 1"
            )

        if not 0.0 <= uncertainty <= 1.0:
            raise ValueError(
                "uncertainty must be between 0 and 1"
            )

        # ======================================================
        # PROFILE
        # ======================================================

        try:
            poc = self._finite(
                profile["poc"],
                "poc",
            )

            vah = self._finite(
                profile["vah"],
                "vah",
            )

            val = self._finite(
                profile["val"],
                "val",
            )

        except KeyError as exc:
            raise ValueError(
                f"Missing profile field: {exc}"
            ) from exc

        if not (
            val < poc < vah
        ):
            raise ValueError(
                "Invalid Value Area: expected VAL < POC < VAH"
            )

        # ======================================================
        # DYNAMICS
        # ======================================================

        try:
            value_location = self._finite(
                dynamics["value_location"],
                "value_location",
            )

            poc_velocity = self._finite(
                dynamics["poc_velocity"],
                "poc_velocity",
            )

            value_area_state = str(
                dynamics["value_area_state"]
            )

        except KeyError as exc:
            raise ValueError(
                f"Missing dynamics field: {exc}"
            ) from exc

        if not 0.0 <= value_location <= 1.0:
            raise ValueError(
                "value_location must be between 0 and 1"
            )

        # ======================================================
        # PROBABILITY FILTER
        # ======================================================

        if probability < self.config.min_probability:
            return None

        if (
            adjusted_probability
            < self.config.min_adjusted_probability
        ):
            return None

        # ======================================================
        # UNCERTAINTY ADJUSTMENT
        # ======================================================

        uncertainty_discount = (
            self.config.uncertainty_penalty
            * uncertainty
        )

        effective_probability = (
            adjusted_probability
            * (
                1.0
                - uncertainty_discount
            )
        )

        effective_probability = max(
            0.0,
            min(
                1.0,
                effective_probability,
            ),
        )

        # ======================================================
        # CONSERVATIVE EXPECTED VALUE
        #
        # EV = pR - (1-p) + costs
        # ======================================================

        reward_r = self.config.reward_risk
        risk_r = 1.0

        conservative_ev = (
            effective_probability
            * reward_r
            - (
                1.0
                - effective_probability
            )
            * risk_r
            - self.config.transaction_cost_r
        )

        # Use supplied EV only as an additional validation
        # signal, never as a substitute for probability math.
        if ev_r <= self.config.min_ev_r:
            return None

        if conservative_ev <= self.config.min_ev_r:
            return None

        # ======================================================
        # DIRECTIONAL QUANTITATIVE SCORE
        # ======================================================

        # ------------------------------------------------------
        # Probability strength
        # ------------------------------------------------------

        # ------------------------------------------------------
        # Probability normalization
        #
        # Maps effective probability into [0, 1]
        # relative to the minimum admissible probability.
        #
        # The normalization is intentionally nonlinear:
        # higher probabilities receive progressively more weight.
        # ------------------------------------------------------

        probability_floor = (
            self.config.min_adjusted_probability
        )

        probability_base = max(
            1e-12,
            1.0 - probability_floor,
        )

        probability_ratio = max(
            0.0,
            min(
                1.0,
                (
                    effective_probability
                    - probability_floor
                )
                / probability_base,
            ),
        )

        probability_strength = (
            probability_ratio ** 0.50
        )

        probability_score = (
            probability_strength
            * self.config.weight_probability
        )

        # ------------------------------------------------------
        # LONG directional components
        # ------------------------------------------------------

        long_value_strength = max(
            0.0,
            min(
                1.0,
                (
                    value_location
                    - self.config.value_location_long
                )
                / max(
                    1e-12,
                    1.0
                    - self.config.value_location_long,
                ),
            ),
        )

        # ------------------------------------------------------
        # SHORT directional components
        # ------------------------------------------------------

        short_value_strength = max(
            0.0,
            min(
                1.0,
                (
                    self.config.value_location_short
                    - value_location
                )
                / max(
                    1e-12,
                    self.config.value_location_short,
                ),
            ),
        )

        # ------------------------------------------------------
        # POC velocity normalization
        # ------------------------------------------------------

        velocity_scale = max(
            abs(poc_velocity),
            abs(self.config.min_poc_velocity),
            1e-12,
        )

        velocity_strength = max(
            0.0,
            min(
                1.0,
                abs(poc_velocity)
                / velocity_scale,
            ),
        )

        long_velocity_strength = (
            velocity_strength
            if poc_velocity > 0
            else 0.0
        )

        short_velocity_strength = (
            velocity_strength
            if poc_velocity < 0
            else 0.0
        )

        # ------------------------------------------------------
        # Value Area expansion
        # ------------------------------------------------------

        value_area_strength = (
            1.0
            if value_area_state == "EXPANDING"
            else 0.0
        )

        value_area_score = (
            value_area_strength
            * self.config.weight_value_area
        )

        # ------------------------------------------------------
        # Conservative EV strength
        # ------------------------------------------------------

        # ------------------------------------------------------
        # Expected-value normalization
        #
        # EV is normalized against the maximum theoretical
        # reward and compressed with sqrt so strong positive
        # expectancy receives meaningful quantitative weight
        # without allowing EV alone to dominate the model.
        # ------------------------------------------------------

        ev_ratio = (
            conservative_ev
            / max(
                self.config.reward_risk,
                1e-12,
            )
        )

        ev_strength = max(
            0.0,
            min(
                1.0,
                ev_ratio,
            ),
        )

        ev_strength = (
            ev_strength ** 0.50
        )

        expected_value_score = (
            ev_strength
            * self.config.weight_expected_value
        )

        # ------------------------------------------------------
        # Uncertainty quality
        # ------------------------------------------------------

        uncertainty_quality = max(
            0.0,
            min(
                1.0,
                1.0 - uncertainty,
            ),
        )

        uncertainty_score = (
            uncertainty_quality
            * self.config.weight_uncertainty
        )

        # ------------------------------------------------------
        # Directional scores
        # ------------------------------------------------------

        long_value_score = (
            long_value_strength
            * self.config.weight_value_location
        )

        short_value_score = (
            short_value_strength
            * self.config.weight_value_location
        )

        long_velocity_score = (
            long_velocity_strength
            * self.config.weight_poc_velocity
        )

        short_velocity_score = (
            short_velocity_strength
            * self.config.weight_poc_velocity
        )

        long_score = (
            probability_score
            + long_value_score
            + long_velocity_score
            + value_area_score
            + expected_value_score
            + uncertainty_score
        )

        short_score = (
            probability_score
            + short_value_score
            + short_velocity_score
            + value_area_score
            + expected_value_score
            + uncertainty_score
        )

        long_score = max(
            0.0,
            min(100.0, long_score),
        )

        short_score = max(
            0.0,
            min(100.0, short_score),
        )

        # ------------------------------------------------------
        # Direction selection
        # ------------------------------------------------------

        if long_score >= short_score:
            directional_score = long_score
            dominant_direction = "LONG"
        else:
            directional_score = short_score
            dominant_direction = "SHORT"

        # ------------------------------------------------------
        # Minimum quantitative quality
        # ------------------------------------------------------

        if directional_score < self.config.min_score:
            return None

        # ======================================================
        # LONG
        # ======================================================

        if (
            value_location
            >= self.config.value_location_long
            and poc_velocity
            > self.config.min_poc_velocity
        ):

            if (
                self.config.require_expansion
                and value_area_state != "EXPANDING"
            ):
                return None

            stop_loss = val

            price_risk = abs(
                entry - stop_loss
            )

            if price_risk <= 0:
                return None

            take_profit = (
                entry
                + reward_r * price_risk
            )

            return {
                "direction": "LONG",

                "quant_score": round(
                    directional_score,
                    4,
                ),

                "long_score": round(
                    long_score,
                    4,
                ),

                "short_score": round(
                    short_score,
                    4,
                ),

                "effective_probability": round(
                    effective_probability,
                    6,
                ),

                "uncertainty": round(
                    uncertainty,
                    6,
                ),

                "conservative_ev_r": round(
                    conservative_ev,
                    6,
                ),

                "entry": entry,

                "stop_loss": stop_loss,

                "take_profit": take_profit,

                "reward_risk": reward_r,

                "price_risk": price_risk,

                "probability": probability,

                "adjusted_probability":
                    adjusted_probability,

                "uncertainty": uncertainty,

                "effective_probability":
                    effective_probability,

                "ev_r": ev_r,

                "conservative_ev_r":
                    conservative_ev,

                "market_state":
                    "VALUE_MIGRATION_UP",

                "poc_velocity":
                    poc_velocity,

                "value_location":
                    value_location,

                "value_area_state":
                    value_area_state,

                "transaction_cost_r":
                    self.config.transaction_cost_r,
            }

        # ======================================================
        # SHORT
        # ======================================================

        if (
            value_location
            <= self.config.value_location_short
            and poc_velocity
            < -self.config.min_poc_velocity
        ):

            if (
                self.config.require_expansion
                and value_area_state != "EXPANDING"
            ):
                return None

            stop_loss = vah

            price_risk = abs(
                stop_loss - entry
            )

            if price_risk <= 0:
                return None

            take_profit = (
                entry
                - reward_risk
                * price_risk
            )

            return {
                "direction": "SHORT",

                "quant_score": round(
                    directional_score,
                    4,
                ),

                "long_score": round(
                    long_score,
                    4,
                ),

                "short_score": round(
                    short_score,
                    4,
                ),

                "effective_probability": round(
                    effective_probability,
                    6,
                ),

                "uncertainty": round(
                    uncertainty,
                    6,
                ),

                "conservative_ev_r": round(
                    conservative_ev,
                    6,
                ),

                "entry": entry,

                "stop_loss": stop_loss,

                "take_profit": take_profit,

                "reward_risk": reward_risk,

                "price_risk": price_risk,

                "probability": probability,

                "adjusted_probability":
                    adjusted_probability,

                "uncertainty": uncertainty,

                "effective_probability":
                    effective_probability,

                "ev_r": ev_r,

                "conservative_ev_r":
                    conservative_ev,

                "market_state":
                    "VALUE_MIGRATION_DOWN",

                "poc_velocity":
                    poc_velocity,

                "value_location":
                    value_location,

                "value_area_state":
                    value_area_state,

                "transaction_cost_r":
                    self.config.transaction_cost_r,
            }

        return None
