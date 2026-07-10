import math
import unittest
from unittest.mock import patch

from modes.pomodoro import PomodoroMode


class DummyConfig:
    def get_section(self, name):
        return {}


class PomodoroModeTests(unittest.TestCase):
    def test_running_snapshot_does_not_double_subtract_elapsed_time(self):
        clock = [1000.0]
        mode = PomodoroMode(DummyConfig())

        with patch('modes.pomodoro.time.time', lambda: clock[0]):
            mode.update_timer({
                'event': 'start',
                'state': 'running',
                'timeLeftMs': 10000,
                'totalTimeMs': 10000,
            })

            clock[0] = 1001.0
            first = mode._snapshot()

            clock[0] = 1002.0
            second = mode._snapshot()

        self.assertEqual(first['time_left_ms'], 9000)
        self.assertEqual(second['time_left_ms'], 8000)
        self.assertTrue(math.isclose(first['progress'], 0.1))
        self.assertTrue(math.isclose(second['progress'], 0.2))


if __name__ == '__main__':
    unittest.main()
