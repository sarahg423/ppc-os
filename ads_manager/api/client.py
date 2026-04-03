"""Google Ads API client initialization and authentication.

Handles loading credentials from config/credentials.yaml and creating
an authenticated GoogleAdsClient instance. All account-specific values
are read from config/account.yaml — nothing is hardcoded.
"""

import yaml
from pathlib import Path

try:
    from google.ads.googleads.client import GoogleAdsClient
    HAS_API = True
except ImportError:
    HAS_API = False


CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.yaml"
ACCOUNT_PATH = CONFIG_DIR / "account.yaml"


class AdsClientError(Exception):
    """Raised when the Google Ads API client can't be initialized."""
    pass


def load_account_config() -> dict:
    """Load account configuration from config/account.yaml.

    This is the single source of truth for account ID, brand name,
    benchmarks, ad copy rules, and everything else account-specific.
    """
    if not ACCOUNT_PATH.exists():
        raise FileNotFoundError(
            f"Account config not found at {ACCOUNT_PATH}. "
            f"Copy config/account.example.yaml to config/account.yaml "
            f"and customize for your account."
        )
    with open(ACCOUNT_PATH) as f:
        return yaml.safe_load(f)


def get_account_id(hyphenated: bool = True) -> str:
    """Return the Google Ads account ID from config."""
    config = load_account_config()
    if hyphenated:
        return config["account"]["id"]
    return config["account"]["id_numeric"]


def get_account_name() -> str:
    """Return the human-readable account name from config."""
    config = load_account_config()
    return config["account"].get("name", "Unknown Account")


def load_credentials() -> dict:
    """Load API credentials from config/credentials.yaml."""
    if not CREDENTIALS_PATH.exists():
        raise AdsClientError(
            f"Credentials file not found at {CREDENTIALS_PATH}. "
            f"Copy config/credentials.example.yaml to config/credentials.yaml "
            f"and fill in your values."
        )
    with open(CREDENTIALS_PATH) as f:
        config = yaml.safe_load(f)

    if not config or "google_ads" not in config:
        raise AdsClientError("credentials.yaml must contain a 'google_ads' section.")

    creds = config["google_ads"]
    required_fields = ["developer_token", "client_id", "client_secret", "refresh_token"]
    missing = [f for f in required_fields if not creds.get(f) or "YOUR_" in str(creds[f])]

    if missing:
        raise AdsClientError(
            f"Missing or placeholder credentials: {', '.join(missing)}. "
            f"Update config/credentials.yaml with real values."
        )
    return creds


def get_client() -> "GoogleAdsClient":
    """Create and return an authenticated GoogleAdsClient."""
    if not HAS_API:
        raise AdsClientError(
            "google-ads package is not installed. "
            "Install it with: pip install google-ads"
        )

    creds = load_credentials()
    config_dict = {
        "developer_token": creds["developer_token"],
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "use_proto_plus": True,
    }

    login_id = creds.get("login_customer_id") or get_account_id(hyphenated=False)
    if login_id:
        config_dict["login_customer_id"] = str(login_id)

    try:
        return GoogleAdsClient.load_from_dict(config_dict)
    except Exception as e:
        raise AdsClientError(f"Failed to create Google Ads client: {e}")


def is_api_available() -> bool:
    """Check whether the Google Ads API can be used.

    Returns True if the package is installed AND valid credentials exist.
    Does not make a network call.
    """
    if not HAS_API:
        return False
    try:
        load_credentials()
        return True
    except AdsClientError:
        return False
