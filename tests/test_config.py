"""Tests for pyverity.config."""

import os

import pytest

from pyverity.config import ProviderConfig, RuntimeConfig, default_config


class TestProviderConfig:
    def test_defaults(self):
        cfg = ProviderConfig()
        assert cfg.api_base == "https://api.openai.com/v1"
        assert cfg.api_key == ""
        assert cfg.model == "gpt-4o-mini"

    def test_custom_values(self):
        cfg = ProviderConfig(api_key="sk-test", api_base="https://custom.api/v1", model="gpt-4o")
        assert cfg.api_key == "sk-test"
        assert cfg.api_base == "https://custom.api/v1"
        assert cfg.model == "gpt-4o"


class TestRuntimeConfig:
    def test_defaults(self):
        cfg = RuntimeConfig()
        assert cfg.default_retry == 2
        assert cfg.debug is False
        assert cfg.timeout_s == 30.0

    def test_custom_values(self):
        provider = ProviderConfig(api_key="sk-x")
        cfg = RuntimeConfig(provider=provider, debug=True, timeout_s=10.0)
        assert cfg.provider.api_key == "sk-x"
        assert cfg.debug is True
        assert cfg.timeout_s == 10.0


class TestDefaultConfig:
    def test_reads_env_vars(self, monkeypatch):
        monkeypatch.setenv("VERITY_API_KEY", "sk-env-key")
        monkeypatch.setenv("VERITY_API_BASE", "https://env.api/v1")
        monkeypatch.setenv("VERITY_MODEL", "gpt-4-turbo")
        monkeypatch.setenv("VERITY_DEBUG", "1")

        cfg = default_config()

        assert cfg.provider.api_key == "sk-env-key"
        assert cfg.provider.api_base == "https://env.api/v1"
        assert cfg.provider.model == "gpt-4-turbo"
        assert cfg.debug is True

    def test_defaults_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("VERITY_API_KEY", raising=False)
        monkeypatch.delenv("VERITY_API_BASE", raising=False)
        monkeypatch.delenv("VERITY_MODEL", raising=False)
        monkeypatch.delenv("VERITY_DEBUG", raising=False)

        cfg = default_config()

        assert cfg.provider.api_key == ""
        assert cfg.provider.api_base == "https://api.openai.com/v1"
        assert cfg.provider.model == "gpt-4o-mini"
        assert cfg.debug is False

    def test_debug_false_when_not_one(self, monkeypatch):
        monkeypatch.setenv("VERITY_DEBUG", "true")
        cfg = default_config()
        assert cfg.debug is False
