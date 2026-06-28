from __future__ import annotations

from collections.abc import Iterable
from typing import Any


class UnsafeContextError(RuntimeError):
    pass


SECRET_KEY_NAMES = {
    "password",
    "passwd",
    "pwd",
    "token",
    "jwt",
    "service_role",
    "private_key",
    "apikey",
    "api_key",
    "access_key",
    "refresh_token",
    "client_secret",
    "password_path",
    "pem_path",
    "env_path",
}

SECRET_VALUE_MARKERS = (
    "-----BEGIN PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----",
    "eyJ",
    "sk-",
    "ghp_",
    "xoxb-",
    "AKIA",
    ".env",
    ".pem",
)

ALLOWED_SECRET_KEYS = {"configured", "readable_by_agent"}


def find_suspicious_keys(data: Any, prefix: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            lowered = key_text.lower()
            if lowered in SECRET_KEY_NAMES:
                findings.append(path)
            findings.extend(find_suspicious_keys(value, path))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            findings.extend(find_suspicious_keys(item, f"{prefix}[{index}]"))
    return findings


def find_suspicious_values(data: Any, prefix: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            findings.extend(find_suspicious_values(value, path))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            findings.extend(find_suspicious_values(item, f"{prefix}[{index}]"))
    elif isinstance(data, str):
        if any(marker in data for marker in SECRET_VALUE_MARKERS):
            findings.append(prefix)
    return findings


def assert_safe_output(data: Any) -> None:
    findings = find_suspicious_keys(data) + find_suspicious_values(data)
    if findings:
        joined = ", ".join(findings)
        raise UnsafeContextError(f"Refusing to render context containing secret-like data: {joined}")


def validate_device_secret_block(secrets: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for key, value in secrets.items():
        if key in ALLOWED_SECRET_KEYS or key.endswith("_ref"):
            continue
        warnings.append(f"device.secrets.{key}")
        if isinstance(value, (dict, list)):
            warnings.extend(find_suspicious_keys(value, f"device.secrets.{key}"))
    if secrets.get("readable_by_agent") is not False:
        warnings.append("device.secrets.readable_by_agent must be false")
    return warnings


def bool_value(value: Any) -> bool:
    return value is True or str(value).lower() in {"true", "yes", "1"}


def first_text(mapping: dict[str, Any], keys: Iterable[str]) -> str | None:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value:
            return value
    return None
