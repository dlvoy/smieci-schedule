"""Constants for the smieci_wroclaw integration."""

DOMAIN = "smieci_wroclaw"

CONF_BASE_URL = "base_url"
CONF_TOKEN = "token"

DEFAULT_BASE_URL = "https://smieci.example.com"

UPDATE_INTERVAL_MINUTES = 30

FRACTIONS = [
    {"key": "plastics", "label_pl": "Tworzywa", "color": "#F2C200"},
    {"key": "mixed", "label_pl": "Zmieszane", "color": "#4B4B4B"},
    {"key": "bio", "label_pl": "BIO", "color": "#B5835A"},
    {"key": "paper", "label_pl": "Papier", "color": "#1565C0"},
    {"key": "glass", "label_pl": "Szklo", "color": "#2E7D32"},
]
FRACTION_KEYS = [f["key"] for f in FRACTIONS]

STATUS_PL = {
    "unknown": "nieznany",
    "scheduled": "zaplanowany",
    "tomorrow": "jutro",
    "today": "dzisiaj",
}

# --- Notification targets (stored in the config entry's options) ---
OPT_TARGETS = "notification_targets"

TARGET_ID = "id"
TARGET_NOTIFY_SERVICE = "notify_service"
TARGET_HOUR = "hour"
TARGET_MINUTE = "minute"
TARGET_EVENTS = "events"  # subset of ["tomorrow", "today"]
TARGET_FRACTIONS = "fractions"  # subset of FRACTION_KEYS, empty/absent = all
TARGET_ENABLED = "enabled"

EVENT_CHOICES = ["tomorrow", "today"]
EVENT_LABELS_PL = {"tomorrow": "Jutro", "today": "Dzisiaj"}
