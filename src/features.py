from __future__ import annotations
import pandas as pd
import numpy as np


NUM_COLS = ["steps", "resting_hr", "sleep_hours", "sleep_efficiency", "hrv_proxy", "wear_time_hours"]


def load_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure expected columns exist and coerce types.
    """
    required = ["date"] + NUM_COLS
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    if out["date"].isna().any():
        raise ValueError("Some 'date' values could not be parsed.")

    for c in NUM_COLS:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    if "notes" not in out.columns:
        out["notes"] = ""

    out = out.sort_values("date").reset_index(drop=True)
    return out


def _rolling_median(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window=window, min_periods=max(3, window // 3)).median()


def compute_features(df: pd.DataFrame) -> dict:
    """
    Compute compact, LLM-friendly feature summary.
    Uses:
      - baseline: rolling median over previous 14 days (excluding current 7-day window)
      - last7: average over last 7 days
      - change: delta and percent where relevant
      - data coverage: missingness + wear time adequacy
    """
    df = df.copy()
    df["date_str"] = df["date"].dt.date.astype(str)

    if len(df) < 10:
        raise ValueError("Need at least ~10 days of data for meaningful baseline vs last7 comparison.")

    last7 = df.iloc[-7:].copy()
    prev = df.iloc[:-7].copy()
    if len(prev) < 5:
        # if dataset is short, fallback to earlier slice
        prev = df.iloc[:-3].copy()

    # Coverage / quality
    days_present = int(last7["date"].nunique())
    wear_ok_days = int((last7["wear_time_hours"] >= 12).sum())
    missing_sleep_days = int(last7["sleep_hours"].isna().sum())
    missing_any = int(last7[["steps", "resting_hr", "wear_time_hours"]].isna().any(axis=1).sum())

    def summarize_metric(col: str, kind: str) -> dict:
        base = float(prev[col].median(skipna=True))
        last7_avg = float(last7[col].mean(skipna=True))
        delta = last7_avg - base
        out = {"baseline_median": round(base, 2), "last7_avg": round(last7_avg, 2), "delta": round(delta, 2)}
        if kind in ("ratio", "count"):
            if abs(base) > 1e-9:
                out["delta_pct"] = round((delta / base) * 100.0, 1)
        return out

    trends = {
        "steps": summarize_metric("steps", "count"),
        "resting_hr": summarize_metric("resting_hr", "ratio"),
        "sleep_hours": summarize_metric("sleep_hours", "ratio"),
        "sleep_efficiency": summarize_metric("sleep_efficiency", "ratio"),
        "hrv_proxy": summarize_metric("hrv_proxy", "ratio"),
    }

    # Simple anomaly markers using last7 vs prev median and MAD scale
    flags = []
    def add_flag(flag_type: str, severity: str, rationale: str):
        flags.append({"type": flag_type, "severity": severity, "rationale": rationale})

    # Compute robust scale from prev using MAD
    def mad_scale(x: pd.Series) -> float:
        x = x.dropna()
        if len(x) < 5:
            return float("nan")
        med = float(x.median())
        mad = float(np.median(np.abs(x - med)))
        return mad * 1.4826  # approx std

    # RHR elevated
    rhr_base = trends["resting_hr"]["baseline_median"]
    rhr_last7 = trends["resting_hr"]["last7_avg"]
    rhr_scale = mad_scale(prev["resting_hr"])
    if not np.isnan(rhr_scale) and rhr_last7 > rhr_base + max(3.0, 1.0 * rhr_scale):
        sev = "moderate" if rhr_last7 < rhr_base + 7 else "high"
        add_flag("RHR_ELEVATED", sev, f"Last-7 avg {rhr_last7} vs baseline {rhr_base} bpm.")

    # Sleep reduced
    sl_base = trends["sleep_hours"]["baseline_median"]
    sl_last7 = trends["sleep_hours"]["last7_avg"]
    if not np.isnan(sl_last7) and sl_last7 < sl_base - 0.8:
        sev = "moderate" if sl_last7 > sl_base - 1.3 else "high"
        add_flag("SLEEP_REDUCED", sev, f"Last-7 avg {sl_last7}h vs baseline {sl_base}h.")

    # Steps down
    st_base = trends["steps"]["baseline_median"]
    st_last7 = trends["steps"]["last7_avg"]
    if not np.isnan(st_last7) and st_last7 < st_base * 0.7:
        sev = "moderate" if st_last7 > st_base * 0.55 else "high"
        add_flag("ACTIVITY_DOWN", sev, f"Last-7 avg {int(st_last7)} vs baseline {int(st_base)} steps.")

    # Low wear / missingness
    if wear_ok_days < 4:
        add_flag("LOW_WEAR_TIME", "moderate", f"Wear-time ≥12h on {wear_ok_days}/7 days.")
    if missing_sleep_days >= 2:
        add_flag("MISSING_SLEEP", "moderate", f"Missing sleep values on {missing_sleep_days}/7 days.")
    if missing_any >= 2:
        add_flag("MISSING_CORE_SIGNALS", "moderate", f"Missing core signals on {missing_any}/7 days.")

    # Pull notes from last7
    last7_notes = [n for n in last7.get("notes", "").fillna("").tolist() if str(n).strip()]

    feature_summary = {
        "window": {
            "start": str(last7["date"].iloc[0].date()),
            "end": str(last7["date"].iloc[-1].date()),
        },
        "coverage": {
            "days_present": days_present,
            "wear_ok_days": wear_ok_days,
            "missing_sleep_days": missing_sleep_days,
            "missing_any_core_days": missing_any,
        },
        "trends": trends,
        "flags": flags,
        "last7_notes": last7_notes[:5],
    }
    return feature_summary
