from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import numpy as np
import pandas as pd


@dataclass
class SimConfig:
    days: int = 30
    seed: int = 7
    profile: str = "normal"  # normal | flu_like | stressed | missing_wear


def _clip(x, lo, hi):
    return np.minimum(np.maximum(x, lo), hi)


def generate_simulated_user(cfg: SimConfig) -> pd.DataFrame:
    """
    Prototype-friendly wearable daily aggregates.
    This is simulated data for demo purposes (not physiological truth).
    """
    rng = np.random.default_rng(cfg.seed)
    end = date.today()
    start = end - timedelta(days=cfg.days - 1)
    dates = pd.date_range(start=start, end=end, freq="D")

    # Baselines
    steps_base = int(rng.integers(6500, 9500))
    rhr_base = int(rng.integers(52, 66))
    sleep_base = float(rng.uniform(6.7, 7.9))
    eff_base = float(rng.uniform(0.84, 0.93))
    hrv_base = float(rng.uniform(35, 70))
    wear_base = float(rng.uniform(14, 22))

    n = len(dates)
    steps = steps_base + rng.normal(0, 1200, size=n)
    rhr = rhr_base + rng.normal(0, 2.3, size=n)
    sleep = sleep_base + rng.normal(0, 0.55, size=n)
    eff = eff_base + rng.normal(0, 0.04, size=n)
    hrv = hrv_base + rng.normal(0, 6.0, size=n)
    wear = wear_base + rng.normal(0, 2.0, size=n)

    # Apply profiles in last 7 days
    last7_idx = np.arange(max(0, n - 7), n)

    notes = [""] * n
    if cfg.profile == "flu_like":
        steps[last7_idx] -= rng.uniform(1800, 3800, size=len(last7_idx))
        rhr[last7_idx] += rng.uniform(4, 9, size=len(last7_idx))
        sleep[last7_idx] -= rng.uniform(0.4, 1.2, size=len(last7_idx))
        hrv[last7_idx] -= rng.uniform(4, 10, size=len(last7_idx))
        notes[last7_idx[0]] = "simulated: flu-like week"
    elif cfg.profile == "stressed":
        sleep[last7_idx] -= rng.uniform(0.5, 1.4, size=len(last7_idx))
        eff[last7_idx] -= rng.uniform(0.05, 0.10, size=len(last7_idx))
        rhr[last7_idx] += rng.uniform(2, 5, size=len(last7_idx))
        steps[last7_idx] += rng.uniform(-600, 600, size=len(last7_idx))
        notes[last7_idx[0]] = "simulated: stress-like week"
    elif cfg.profile == "missing_wear":
        # Reduce wear time and create missingness
        wear[last7_idx] -= rng.uniform(6, 12, size=len(last7_idx))
        missing_days = rng.choice(last7_idx, size=min(3, len(last7_idx)), replace=False)
        for i in missing_days:
            sleep[i] = np.nan
            eff[i] = np.nan
        notes[last7_idx[0]] = "simulated: low adherence / missing data"

    # Clip to plausible ranges
    steps = _clip(steps, 0, 25000)
    rhr = _clip(rhr, 40, 110)
    sleep = _clip(sleep, 0, 12)
    eff = _clip(eff, 0.5, 0.99)
    hrv = _clip(hrv, 10, 130)
    wear = _clip(wear, 0, 24)

    df = pd.DataFrame(
        {
            "date": dates.date.astype(str),
            "steps": np.round(steps).astype(int),
            "resting_hr": np.round(rhr, 1),
            "sleep_hours": np.round(sleep, 2),
            "sleep_efficiency": np.round(eff, 2),
            "hrv_proxy": np.round(hrv, 1),
            "wear_time_hours": np.round(wear, 1),
            "notes": notes,
        }
    )
    return df
