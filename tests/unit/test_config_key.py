# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest
from pathlib import Path

import yaml


class TestConfigKeys(unittest.TestCase):
    def test_config_keys_were_mindfully_added(self):
        # In charm.py, all config keys, unless explicitly excluded, would be used as part of a scrape config.
        # For this reason, any newly added key should be either a valid scrape config key or explicitly excluded.
        metadata = yaml.safe_load(Path("./charmcraft.yaml").read_text())
        config_keys = set(metadata["config"]["options"].keys())

        # WARNING: Update this test only after confirming the new config key is valid or explicitly excluded.
        assert config_keys == {
            "scrape_interval",
            "scrape_timeout",
            "proxy_url",
            "relabel_configs",  # Special treatment: from yaml
            "metric_relabel_configs",  # Special treatment: from yaml
            "sample_limit",
            "label_limit",
            "label_name_length_limit",
            "label_value_length_limit",
            "forward_alert_rules",  # Excluded (non scrape config keys)
        }
