from spidermon.contrib.monitors.mixins import StatsMonitorMixin
from spidermon import Monitor, MonitorSuite, monitors
from spidermon.contrib.actions.discord.notifiers import (
    SendDiscordMessageSpiderFinished,
)
from spidermon.contrib.scrapy.monitors import (
    UnwantedHTTPCodesMonitor,
    PeriodicExecutionTimeMonitor,
    PeriodicItemCountMonitor,
    ErrorCountMonitor,
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


@monitors.name("Periodic ERROR log count")
class PeriodicErrorLogCountMonitor(Monitor, StatsMonitorMixin):
    @monitors.name("Maximum number of errors reached")
    def test_number_of_errors(self):
        accepted_num_errors = self.data.crawler.settings.getint(
            "SPIDERMON_MAX_ERRORS_PERIODIC", 0
        )
        num_errors = self.data.stats.get("log_count/ERROR", 0)

        msg = f"The job has exceeded the maximum number ({accepted_num_errors = }) of errors"
        self.assertLessEqual(num_errors, accepted_num_errors, msg=msg)


class PeriodicMonitorSuite(MonitorSuite):

    monitors = [
        PeriodicErrorLogCountMonitor,  # SPIDERMON_MAX_ERRORS_PERIODIC
        PeriodicExecutionTimeMonitor,  # SPIDERMON_MAX_EXECUTION_TIME
        PeriodicItemCountMonitor,  # SPIDERMON_ITEM_COUNT_INCREASE
        UnwantedHTTPCodesMonitor,  # SPIDERMON_UNWANTED_HTTP_CODES
    ]

    monitors_failed_actions = [SendDiscordMessageSpiderFinished]


class SpiderCloseMonitorSuite(MonitorSuite):
    monitors = [
        ItemValidationMonitor,
        ErrorCountMonitor,
    ]

    monitors_failed_actions = [
        SendDiscordMessageSpiderFinished,
    ]

    monitors_passed_actions = [SendDiscordMessageSpiderFinished]
