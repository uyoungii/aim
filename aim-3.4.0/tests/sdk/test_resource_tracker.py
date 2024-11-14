import time

from tests.base import TestBase
from tests.utils import remove_test_data

from aim.sdk import Run


class TestRunResourceTracker(TestBase):
    def tearDown(self):
        remove_test_data()

    def test_default_tracking_interval(self):
        run = Run()  # default tracking interval 10s
        run_hash = run.hash
        run.track(1, name='metric')
        time.sleep(.1)  # allow tracker to add resource usage metrics
        del run

        metrics = list(self.repo.query_metrics(f'run.hash == "{run_hash}" and metric.name.startswith("__")'))
        self.assertEqual(4, len(metrics))
        expected_metrics = {'__system__cpu', '__system__disk_percent',
                            '__system__memory_percent', '__system__p_memory_percent'}
        self.assertSetEqual(expected_metrics, set(m.name for m in metrics))

    def test_custom_tracking_interval(self):
        run = Run(system_tracking_interval=1)
        run_hash = run.hash
        run.track(1, name='metric')
        time.sleep(3)  # allow tracker to add resource usage metrics
        del run

        metrics = list(self.repo.query_metrics(f'run.hash == "{run_hash}" and metric.name.startswith("__")'))
        self.assertEqual(4, len(metrics))
        expected_metrics = {'__system__cpu', '__system__disk_percent',
                            '__system__memory_percent', '__system__p_memory_percent'}
        self.assertSetEqual(expected_metrics, set(m.name for m in metrics))
        for metric in metrics:
            # 3 sec. runtime, 1 sec. interval
            self.assertGreaterEqual(len(metric.values), 3)
            self.assertLessEqual(len(metric.values), 4)

    def test_disable_resource_tracking(self):
        run = Run(system_tracking_interval=None)
        run_hash = run.hash
        run.track(1, name='metric')
        time.sleep(.1)  # allow tracker to add resource usage metrics
        del run

        metrics = list(self.repo.query_metrics(f'run.hash == "{run_hash}" and metric.name.startswith("__")'))
        self.assertListEqual([], metrics)

    def test_resource_tracking_interval_limits(self):
        run = Run(system_tracking_interval=0)
        self.assertIsNone(run._system_resource_tracker)
        run = Run(system_tracking_interval=2 * 24 * 3600)  # two days
        self.assertIsNone(run._system_resource_tracker)
