"""
Mainlayer payment verification for Jupyter notebooks.
"""

from __future__ import annotations

import os
import json
import time
from pathlib import Path
from typing import Optional

try:
    from mainlayer import MainlayerClient
except ImportError:
    MainlayerClient = None  # type: ignore

CACHE_DIR = Path.home() / ".mainlayer"
CACHE_TTL = 12 * 3600  # 12 hours


class PaywallError(Exception):
    """Raised when a paywalled cell is executed without a valid license."""
    pass


class PaymentVerifier:
    """Verifies Mainlayer licenses with local caching."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("MAINLAYER_API_KEY") or self._read_config()

    def _read_config(self) -> Optional[str]:
        config_file = CACHE_DIR / "config.json"
        try:
            with open(config_file) as f:
                data = json.load(f)
                return data.get("api_key")
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _cache_path(self, key: str) -> Path:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        safe = key[:16].replace("/", "_")
        return CACHE_DIR / f"cache_{safe}.json"

    def _read_cache(self, key: str) -> Optional[bool]:
        try:
            with open(self._cache_path(key)) as f:
                data = json.load(f)
            if time.time() - data["cached_at"] < CACHE_TTL:
                return data["valid"]
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            pass
        return None

    def _write_cache(self, key: str, valid: bool) -> None:
        try:
            with open(self._cache_path(key), "w") as f:
                json.dump({"valid": valid, "cached_at": time.time()}, f)
        except OSError:
            pass

    def verify(self, license_key: Optional[str] = None) -> bool:
        """
        Verify a license key. Returns True if valid.

        Priority: explicit key > MAINLAYER_LICENSE env > stored api_key
        """
        key = (
            license_key
            or os.environ.get("MAINLAYER_LICENSE")
            or self.api_key
        )

        if not key:
            return False

        cached = self._read_cache(key)
        if cached is not None:
            return cached

        if MainlayerClient is None:
            raise PaywallError(
                "mainlayer package not installed. Run: pip install mainlayer"
            )

        try:
            client = MainlayerClient(api_key=key)
            result = client.licenses.verify(license_key=key)
            valid = bool(result.valid)
            self._write_cache(key, valid)
            return valid
        except Exception:
            return False

    def require(self, license_key: Optional[str] = None) -> None:
        """
        Assert that a valid license exists. Raises PaywallError if not.
        """
        if not self.verify(license_key):
            raise PaywallError(
                "\n"
                "╔══════════════════════════════════════════════════════╗\n"
                "║           PREMIUM CONTENT — LICENSE REQUIRED         ║\n"
                "╠══════════════════════════════════════════════════════╣\n"
                "║  This notebook cell requires a Mainlayer license.    ║\n"
                "║                                                      ║\n"
                "║  Get your license at: https://mainlayer.fr           ║\n"
                "║                                                      ║\n"
                "║  Then set:                                           ║\n"
                "║    export MAINLAYER_LICENSE=<your-license-key>       ║\n"
                "║  or pass it to the magic:                            ║\n"
                "║    %%mainlayer_paid --key <your-license-key>         ║\n"
                "╚══════════════════════════════════════════════════════╝\n"
            )


# Module-level singleton
_verifier: Optional[PaymentVerifier] = None


def get_verifier() -> PaymentVerifier:
    global _verifier
    if _verifier is None:
        _verifier = PaymentVerifier()
    return _verifier


def verify_license(license_key: Optional[str] = None) -> bool:
    return get_verifier().verify(license_key)


def require_license(license_key: Optional[str] = None) -> None:
    get_verifier().require(license_key)
