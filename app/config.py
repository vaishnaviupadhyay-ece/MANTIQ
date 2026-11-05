"""
MANTIQ - central configuration.

"""

from pathlib import Path

# ----------------------------------------------------------------------------
# Identity and labels
# ----------------------------------------------------------------------------
APP_NAME = "MANTIQ"
TAGLINE = "Action Before Failure."

DATA_SOURCE_LABEL = "NASA IMS — Historical Bearing Experiment"
REPLAY_LABEL = "Experimental Data Replay"
DEMO_AUTH_NOTICE = (
    "Demo authentication for the hackathon prototype. "
)

# ----------------------------------------------------------------------------
# Paths (all relative to the project root, so the app runs from any machine)
# ----------------------------------------------------------------------------
# This file is MANTIQ/app/config.py, so the project root is two levels up.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
ASSETS_DIR = PROJECT_ROOT / "assets"

FEATURES_CSV = DATA_DIR / "processed" / "ims_features.csv"
TIMELINE_CSV = RESULTS_DIR / "bearing_timeline.csv"

DB_PATH = PROJECT_ROOT / "app" / "database" / "mantiq.db"
SCHEMA_PATH = PROJECT_ROOT / "app" / "database" / "schema.sql"

LOGO_SVG = ASSETS_DIR / "logo.svg"
FAVICON_SVG = ASSETS_DIR / "favicon.svg"

# ----------------------------------------------------------------------------
# Machine / model settings
# ----------------------------------------------------------------------------
BEARINGS = (1, 2, 3, 4)

# MIRRORS src/bearing_analysis.py: split = int(len(data) * 0.60)
TRAIN_FRACTION = 0.60

# MIRRORS src/condition_engine.py: recent = data.tail(50)
CONDITION_WINDOW = 50

# Replay warm-up: the first condition assessment at the start of the replay
# uses the 49 preceding recordings plus the first replayed one (= 50 total).
REPLAY_WARMUP_RECORDINGS = CONDITION_WINDOW - 1


def model_path(bearing: int) -> Path:
    """Path of the saved model artifact for one bearing."""
    return MODELS_DIR / f"bearing_{bearing}.joblib"


def bearing_channels(bearing: int) -> tuple:
    """Bearing N uses channels 2N-1 and 2N (same rule as bearing_analysis.py)."""
    return (bearing * 2 - 1, bearing * 2)


# ----------------------------------------------------------------------------
# Roles and DEMO users
# ----------------------------------------------------------------------------
ROLE_OPERATOR = "operator"
ROLE_HEAD = "maintenance_head"

ROLE_LABELS = {
    ROLE_OPERATOR: "Operator",
    ROLE_HEAD: "Maintenance Head",
}

# DEMO ONLY: plain-text passwords in source code are fine for a hackathon demo
# and completely unacceptable in a real product.
DEMO_USERS = {
    "operator": {
        "password": "operator456",
        "role": ROLE_OPERATOR,
        "display_name": "Demo Operator",
    },
    "maintenance": {
        "password": "head123",
        "role": ROLE_HEAD,
        "display_name": "Demo Maintenance Head",
    },
}

# ----------------------------------------------------------------------------
# Navigation (page names shown in the sidebar)
# ----------------------------------------------------------------------------
NAV_SHARED = ["Overview", "Machines", "Replay", "Alerts", "Maintenance", "History"]
NAV_HEAD_ONLY = ["Team / Assignments", "Analytics", "Configuration"]


def pages_for_role(role: str) -> list:
    """Page names a role may see."""
    if role == ROLE_HEAD:
        return [
            page
            for page in NAV_SHARED + NAV_HEAD_ONLY
            if page.strip().casefold() != "configuration"
        ]

    return list(NAV_SHARED)

# ----------------------------------------------------------------------------
# Theme
# ----------------------------------------------------------------------------
DEFAULT_THEME = "light"


SRC_DIR = PROJECT_ROOT / "src"

# Format of the timestamp column in both CSV files: 2003.11.17.19.42.30
TIMESTAMP_FORMAT = "%Y.%m.%d.%H.%M.%S"