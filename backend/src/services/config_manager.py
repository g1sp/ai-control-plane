"""Configuration management service."""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import PolicyConfiguration
from ..config import settings


class ConfigManager:
    """Manage policy configuration with database persistence."""

    def __init__(self, db: Session):
        self.db = db
        self._defaults = {
            "models_whitelist": {
                "value": json.dumps(settings.models_whitelist),
                "data_type": "list",
            },
            "users_whitelist": {
                "value": json.dumps(settings.users_whitelist),
                "data_type": "list",
            },
            "budget_per_request": {
                "value": str(settings.budget_per_request_usd),
                "data_type": "float",
            },
            "budget_per_user_per_day": {
                "value": str(settings.budget_per_user_per_day_usd),
                "data_type": "float",
            },
            "rate_limit_req_per_minute": {
                "value": str(settings.rate_limit_req_per_minute),
                "data_type": "int",
            },
            "injection_patterns": {
                "value": json.dumps(settings.injection_patterns),
                "data_type": "list",
            },
        }

    def get_all_configs(self) -> dict:
        """Get all configuration values (latest version of each key)."""
        from sqlalchemy import func

        latest_configs = (
            self.db.query(PolicyConfiguration)
            .distinct(PolicyConfiguration.key)
            .order_by(PolicyConfiguration.key, desc(PolicyConfiguration.last_modified))
            .all()
        )

        result = {}
        existing_keys = {cfg.key for cfg in latest_configs}

        for cfg in latest_configs:
            result[cfg.key] = self._deserialize_value(cfg.value, cfg.data_type)

        # Initialize missing configs with defaults
        for key, default_val in self._defaults.items():
            if key not in existing_keys:
                self._initialize_config(key, default_val)
                result[key] = self._deserialize_value(default_val["value"], default_val["data_type"])

        return result

    def get_config(self, key: str):
        """Get single configuration value (latest version)."""
        cfg = (
            self.db.query(PolicyConfiguration)
            .filter(PolicyConfiguration.key == key)
            .order_by(desc(PolicyConfiguration.last_modified))
            .first()
        )

        if not cfg:
            if key in self._defaults:
                default = self._defaults[key]
                self._initialize_config(key, default)
                return self._deserialize_value(default["value"], default["data_type"])
            else:
                raise KeyError(f"Configuration key not found: {key}")

        return self._deserialize_value(cfg.value, cfg.data_type)

    def update_config(self, key: str, value, modified_by: str = "system") -> dict:
        """Update configuration value with validation and history tracking."""
        if key not in self._defaults:
            raise KeyError(f"Unknown configuration key: {key}")

        # Validate the value
        self._validate_config(key, value)

        # Serialize value
        data_type = self._defaults[key]["data_type"]
        serialized_value = self._serialize_value(value, data_type)

        cfg = PolicyConfiguration(
            key=key,
            value=serialized_value,
            data_type=data_type,
            modified_by=modified_by,
        )
        self.db.add(cfg)
        self.db.commit()
        self.db.refresh(cfg)

        return {
            "key": cfg.key,
            "value": self._deserialize_value(cfg.value, cfg.data_type),
            "last_modified": cfg.last_modified,
            "modified_by": cfg.modified_by,
        }

    def get_config_history(self, limit: int = 20) -> list:
        """Get configuration change history with previous values for diffs."""
        configs = (
            self.db.query(PolicyConfiguration)
            .order_by(desc(PolicyConfiguration.last_modified))
            .limit(limit * 2)  # Fetch extra to compute diffs
            .all()
        )

        history = []
        for i, cfg in enumerate(configs):
            current_value = self._deserialize_value(cfg.value, cfg.data_type)
            previous_value = None

            if i + 1 < len(configs) and configs[i + 1].key == cfg.key:
                previous_value = self._deserialize_value(configs[i + 1].value, configs[i + 1].data_type)

            history.append({
                "key": cfg.key,
                "previousValue": previous_value,
                "currentValue": current_value,
                "timestamp": cfg.last_modified,
                "modified_by": cfg.modified_by,
            })

            if len(history) >= limit:
                break

        return history

    def _initialize_config(self, key: str, config_spec: dict):
        """Initialize a configuration with default values."""
        cfg = PolicyConfiguration(
            key=key,
            value=config_spec["value"],
            data_type=config_spec["data_type"],
            modified_by="system",
        )
        self.db.add(cfg)
        self.db.commit()

    def _serialize_value(self, value, data_type: str) -> str:
        """Serialize value for database storage."""
        if data_type == "list":
            return json.dumps(value)
        elif data_type == "float":
            return str(float(value))
        elif data_type == "int":
            return str(int(value))
        else:
            return str(value)

    def _deserialize_value(self, value: str, data_type: str):
        """Deserialize value from database storage."""
        if data_type == "list":
            return json.loads(value)
        elif data_type == "float":
            return float(value)
        elif data_type == "int":
            return int(value)
        else:
            return value

    def rollback_config(self, key: str, target_timestamp, modified_by: str = "system-rollback") -> dict:
        """Rollback config to value it had at or before given timestamp."""
        if key not in self._defaults:
            raise KeyError(f"Unknown configuration key: {key}")

        configs = (
            self.db.query(PolicyConfiguration)
            .filter(PolicyConfiguration.key == key)
            .order_by(desc(PolicyConfiguration.last_modified))
            .all()
        )

        if not configs:
            raise KeyError(f"No history found for key: {key}")

        target_config = None
        for cfg in configs:
            if cfg.last_modified < target_timestamp:
                target_config = cfg
                break

        if not target_config:
            if len(configs) > 1:
                target_config = configs[-1]
            else:
                raise ValueError(f"Cannot rollback: only one version exists")

        previous_value = self._deserialize_value(target_config.value, target_config.data_type)
        return self.update_config(key, previous_value, modified_by=modified_by)

    def _validate_config(self, key: str, value):
        """Validate configuration value before update."""
        if key == "models_whitelist":
            if not isinstance(value, list) or len(value) == 0:
                raise ValueError("models_whitelist must be a non-empty list")
            if not all(isinstance(m, str) for m in value):
                raise ValueError("all models must be strings")

        elif key == "users_whitelist":
            if not isinstance(value, list) or len(value) == 0:
                raise ValueError("users_whitelist must be a non-empty list")
            if not all(isinstance(u, str) for u in value):
                raise ValueError("all users must be strings")

        elif key == "budget_per_request":
            try:
                f = float(value)
                if f <= 0 or f > 100:
                    raise ValueError("budget_per_request must be > 0 and <= 100")
            except (TypeError, ValueError):
                raise ValueError("budget_per_request must be a positive number")

        elif key == "budget_per_user_per_day":
            try:
                f = float(value)
                if f <= 0 or f > 1000:
                    raise ValueError("budget_per_user_per_day must be > 0 and <= 1000")
            except (TypeError, ValueError):
                raise ValueError("budget_per_user_per_day must be a positive number")

        elif key == "rate_limit_req_per_minute":
            try:
                i = int(value)
                if i <= 0 or i > 10000:
                    raise ValueError("rate_limit_req_per_minute must be > 0 and <= 10000")
            except (TypeError, ValueError):
                raise ValueError("rate_limit_req_per_minute must be a positive integer")
