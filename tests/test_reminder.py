import unittest
from unittest.mock import patch

from modes.reminder import ReminderMode


class DummyConfig:
    def get_section(self, name):
        return {}


class DummyCanvas:
    def SetPixel(self, x, y, r, g, b):
        pass


class ReminderModeTests(unittest.TestCase):
    def test_reminder_requests_return_mode_after_duration(self):
        clock = [2000.0]
        mode = ReminderMode(DummyConfig())
        canvas = DummyCanvas()

        with patch('modes.reminder.time.monotonic', lambda: clock[0]):
            mode.show({
                'text': 'STAND UP',
                'text_color': [255, 255, 255],
                'gradient_start': [0, 0, 0],
                'gradient_end': [40, 40, 40],
                'display_time_s': 2,
            }, 'spotify')

            mode.render(canvas)
            self.assertIsNone(mode.consume_requested_mode())

            clock[0] = 2002.1
            mode.render(canvas)
            self.assertEqual(mode.consume_requested_mode(), 'spotify')


if __name__ == '__main__':
    unittest.main()
