from spidermon.contrib.monitors.mixins import StatsMonitorMixin
from spidermon import Monitor, MonitorSuite, monitors
from spidermon.contrib.actions.discord.notifiers import (
    SendDiscordMessageSpiderFinished,
)


@monitors.name("Item validation")
class ItemValidationMonitor(Monitor, StatsMonitorMixin):

    @monitors.name("No item validation errors")
    def test_no_item_validation_errors(self):
        validation_errors = getattr(self.stats, "spidermon/validation/fields/errors", 0)
        self.assertEqual(
            validation_errors,
            0,
            msg="Found validation errors in {} fields".format(validation_errors),
        )


class SpiderCloseMonitorSuite(MonitorSuite):
    monitors = [
        ItemValidationMonitor,
    ]

    monitors_failed_actions = [
        SendDiscordMessageSpiderFinished,
    ]
