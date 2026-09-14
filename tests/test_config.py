"""Config validation: missing/wrong-typed keys must fail fast."""
import pytest
import yaml

from config.config_schema import load_config


def _write_broken_config(tmp_path, mutate):
    raw = yaml.safe_load(open("config/config.yaml", encoding="utf-8"))
    mutate(raw)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return str(path)


def test_missing_required_key_fails(tmp_path):
    def _drop(raw):
        del raw["suggestion_engine"]["cibil_good_threshold"]

    with pytest.raises(ValueError, match="Config validation failed"):
        load_config(_write_broken_config(tmp_path, _drop))


def test_wrong_type_fails(tmp_path):
    def _break(raw):
        raw["suggestion_engine"]["cibil_good_threshold"] = ["not", "a", "number"]

    with pytest.raises(ValueError, match="Config validation failed"):
        load_config(_write_broken_config(tmp_path, _break))


def test_valid_config_loads():
    cfg = load_config("config/config.yaml")
    assert cfg.suggestion_engine.cibil_good_threshold == 700
