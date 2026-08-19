"""Manage daily submission CSVs and auto-archiving."""
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta


def get_submissions_dir():
    """Get submissions directory, create if needed."""
    base_dir = Path(__file__).parent.parent
    submissions_dir = base_dir / "data" / "submissions"
    (submissions_dir / "recent").mkdir(parents=True, exist_ok=True)
    (submissions_dir / "older").mkdir(parents=True, exist_ok=True)
    return submissions_dir


def get_today_file():
    """Get today's submission CSV path."""
    submissions_dir = get_submissions_dir()
    today = datetime.now().strftime("%Y-%m-%d")
    return submissions_dir / "recent" / f"applications_{today}.csv"


def save_submission(app_data):
    """Save application to today's CSV."""
    today_file = get_today_file()

    if today_file.exists():
        df_existing = pd.read_csv(today_file)
        df_new = pd.DataFrame([app_data])
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = pd.DataFrame([app_data])

    df_combined.to_csv(today_file, index=False)


def auto_archive():
    """Move CSVs older than 30 days from recent/ to older/."""
    submissions_dir = get_submissions_dir()
    recent_dir = submissions_dir / "recent"
    older_dir = submissions_dir / "older"

    now = datetime.now()
    cutoff_date = now - timedelta(days=30)

    for file in recent_dir.glob("applications_*.csv"):
        # Extract date from filename (applications_YYYY-MM-DD.csv)
        try:
            date_str = file.stem.replace("applications_", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d")

            if file_date < cutoff_date:
                file.rename(older_dir / file.name)
        except Exception:
            pass


def load_submissions(include_recent=True, include_older=False, specific_date=None):
    """Load submission CSVs based on filters.

    Args:
        include_recent: Load files from recent/ (last 30 days)
        include_older: Load files from older/ (30+ days)
        specific_date: Load specific date (YYYY-MM-DD format)

    Returns:
        DataFrame of combined submissions
    """
    auto_archive()
    submissions_dir = get_submissions_dir()
    dfs = []

    if specific_date:
        # Load specific date
        for folder in ["recent", "older"]:
            file = submissions_dir / folder / f"applications_{specific_date}.csv"
            if file.exists():
                dfs.append(pd.read_csv(file))
    else:
        # Load by timeframe
        if include_recent:
            for file in (submissions_dir / "recent").glob("applications_*.csv"):
                dfs.append(pd.read_csv(file))

        if include_older:
            for file in (submissions_dir / "older").glob("applications_*.csv"):
                dfs.append(pd.read_csv(file))

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


def get_available_dates():
    """Get list of all available submission dates."""
    submissions_dir = get_submissions_dir()
    dates = []

    for folder in ["recent", "older"]:
        for file in (submissions_dir / folder).glob("applications_*.csv"):
            try:
                date_str = file.stem.replace("applications_", "")
                dates.append(date_str)
            except Exception:
                pass

    return sorted(dates, reverse=True)


def get_recent_submission_count():
    """Get count of submissions in recent/ folder."""
    submissions_dir = get_submissions_dir()
    count = 0

    for file in (submissions_dir / "recent").glob("applications_*.csv"):
        df = pd.read_csv(file)
        count += len(df)

    return count
