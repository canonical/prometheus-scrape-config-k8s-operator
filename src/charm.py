#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Prometheus Scrape Configuration
"""

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class PrometheusScrapeConfigCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.show_config_action, self._on_show_config_action)

    def _on_config_changed(self, _):
        """Update scrape configuration jobs.
        """
        self.unit.status = ActiveStatus()

    def _on_show_config_action(self, event):
        """Show current set of configured options.
        """
        event.set_results(self._config)

    @property
    def _config(self):
        return {key: value for key, value in self.model.config.items()}


if __name__ == "__main__":
    main(PrometheusScrapeConfigCharm)
