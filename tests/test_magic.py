"""Tests for mainlayer_jupyter paywall."""

import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest

from src.paywall import PaymentVerifier, PaywallError, require_license, verify_license


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Remove license env vars before each test."""
    monkeypatch.delenv("MAINLAYER_LICENSE", raising=False)
    monkeypatch.delenv("MAINLAYER_API_KEY", raising=False)


@pytest.fixture
def verifier(tmp_path, monkeypatch):
    """Return a PaymentVerifier with isolated cache dir."""
    monkeypatch.setattr("src.paywall.CACHE_DIR", tmp_path)
    return PaymentVerifier()


class TestPaymentVerifier:
    def test_returns_false_with_no_key(self, verifier):
        assert verifier.verify() is False

    def test_returns_false_when_sdk_returns_invalid(self, verifier, monkeypatch):
        mock_client = MagicMock()
        mock_client.licenses.verify.return_value = MagicMock(valid=False)
        mock_cls = MagicMock(return_value=mock_client)
        monkeypatch.setattr("src.paywall.MainlayerClient", mock_cls)

        assert verifier.verify("invalid-key") is False

    def test_returns_true_when_sdk_returns_valid(self, verifier, monkeypatch):
        mock_client = MagicMock()
        mock_client.licenses.verify.return_value = MagicMock(valid=True)
        mock_cls = MagicMock(return_value=mock_client)
        monkeypatch.setattr("src.paywall.MainlayerClient", mock_cls)

        assert verifier.verify("valid-key") is True

    def test_caches_valid_result(self, verifier, monkeypatch):
        mock_client = MagicMock()
        mock_client.licenses.verify.return_value = MagicMock(valid=True)
        mock_cls = MagicMock(return_value=mock_client)
        monkeypatch.setattr("src.paywall.MainlayerClient", mock_cls)

        verifier.verify("cache-key")
        verifier.verify("cache-key")

        # SDK should only be called once due to cache
        assert mock_cls.call_count == 1

    def test_uses_env_variable(self, verifier, monkeypatch):
        monkeypatch.setenv("MAINLAYER_LICENSE", "env-key")
        mock_client = MagicMock()
        mock_client.licenses.verify.return_value = MagicMock(valid=True)
        mock_cls = MagicMock(return_value=mock_client)
        monkeypatch.setattr("src.paywall.MainlayerClient", mock_cls)

        result = verifier.verify()
        assert result is True
        mock_cls.assert_called_once_with(api_key="env-key")

    def test_explicit_key_takes_priority_over_env(self, verifier, monkeypatch):
        monkeypatch.setenv("MAINLAYER_LICENSE", "env-key")
        mock_client = MagicMock()
        mock_client.licenses.verify.return_value = MagicMock(valid=True)
        mock_cls = MagicMock(return_value=mock_client)
        monkeypatch.setattr("src.paywall.MainlayerClient", mock_cls)

        verifier.verify("explicit-key")
        mock_cls.assert_called_once_with(api_key="explicit-key")

    def test_returns_false_on_network_error(self, verifier, monkeypatch):
        mock_cls = MagicMock(side_effect=Exception("Network error"))
        monkeypatch.setattr("src.paywall.MainlayerClient", mock_cls)

        # Should not raise, just return False
        assert verifier.verify("key") is False

    def test_require_raises_paywall_error_when_invalid(self, verifier):
        with pytest.raises(PaywallError) as exc_info:
            verifier.require()
        assert "mainlayer.fr" in str(exc_info.value)

    def test_require_does_not_raise_when_valid(self, verifier, monkeypatch):
        mock_client = MagicMock()
        mock_client.licenses.verify.return_value = MagicMock(valid=True)
        mock_cls = MagicMock(return_value=mock_client)
        monkeypatch.setattr("src.paywall.MainlayerClient", mock_cls)

        # Should not raise
        verifier.require("valid-key")

    def test_expired_cache_is_not_used(self, verifier, monkeypatch, tmp_path):
        monkeypatch.setattr("src.paywall.CACHE_DIR", tmp_path)
        # Write an expired cache entry
        cache_file = tmp_path / "cache_valid-key-expir.json"
        expired_time = time.time() - (13 * 3600)  # 13 hours ago
        cache_file.write_text(json.dumps({"valid": True, "cached_at": expired_time}))

        mock_client = MagicMock()
        mock_client.licenses.verify.return_value = MagicMock(valid=False)
        mock_cls = MagicMock(return_value=mock_client)
        monkeypatch.setattr("src.paywall.MainlayerClient", mock_cls)

        result = verifier.verify("valid-key-expired")
        # Should have re-verified (not used cache) and returned False
        assert result is False
        assert mock_cls.call_count == 1
