"""Configuration loader - environment-aware, YAML-driven."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_CONFIG_DIR = _PROJECT_ROOT / "config"


def _resolve_env_vars(value: Any) -> Any:
    """Recursively resolve ${ENV_VAR} references in config values."""
    if isinstance(value, str) and "${" in value:
        for match in _ENV_PATTERN.finditer(value):
            env_key = match.group(1)
            env_val = os.environ.get(env_key, "")
            value = value.replace(match.group(0), env_val)
        return value
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


import re

_ENV_PATTERN = re.compile(r"\$\{(\w+)}")


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@lru_cache(maxsize=1)
def load_platform_config() -> dict[str, Any]:
    """Load the platform-level configuration."""
    config_path = _CONFIG_DIR / "platform.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=4)
def load_environment_config(environment: str | None = None) -> dict[str, Any]:
    """Load environment-specific configuration with env var resolution."""
    env = environment or os.environ.get("ENVIRONMENT", "dev")
    config_path = _CONFIG_DIR / "environments" / f"{env}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration not found: {config_path}")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    return _resolve_env_vars(config)


def load_prompt_templates() -> dict[str, Any]:
    """Load prompt template configuration."""
    config_path = _CONFIG_DIR / "prompts" / "templates.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_guardrails_config() -> dict[str, Any]:
    """Load guardrails validator configuration."""
    config_path = _CONFIG_DIR / "guardrails" / "validators.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_config(environment: str | None = None) -> dict[str, Any]:
    """Get merged platform + environment configuration."""
    platform = load_platform_config()
    env_config = load_environment_config(environment)
    return _deep_merge(platform, env_config)
