from unittest import TestCase
import os
from src.zfspace.zfspace import size2human


os.chdir(os.path.dirname(__file__) + '/..')


class TestZfspace(TestCase):
    def test_size2human(self):
        self.assertTrue(size2human(123) == '123 B')
        # print(size2human(2_000_000_000_000_000_000_000))
        self.assertTrue(size2human(1_234) == '1.21 kiB')
        self.assertTrue(size2human(1_001) == '1001 B')
        self.assertTrue(size2human(1_002_000) == '979 kiB')
        self.assertTrue(size2human(2_000_000_000) == '1.86 GiB')
        self.assertTrue(size2human(2_000_000_000_000) == '1.82 TiB')
        self.assertTrue(size2human(2_000_000_000_000_000) == '1.78 PiB')
        self.assertTrue(size2human(1_150_000_000_000_000_000) == '1021 PiB')
        self.assertTrue(size2human(2_000_000_000_000_000_000_000) == '1.69 ZiB')

        try:
            size2human(2_000_000_000_000_000_000_000, format='bad')
        except ValueError:
            pass

        self.assertTrue(size2human(123, format='short') == '123B')
        self.assertTrue(size2human(1_234, format='short') == '1k')
        self.assertTrue(size2human(1_001, format='short') == '1001B')
        self.assertTrue(size2human(1_002_000, format='short') == '979k')
        self.assertTrue(size2human(2_000_000_000, format='short') == '2G')
        self.assertTrue(size2human(2_000_000_000_000, format='short') == '2T')
        self.assertTrue(size2human(2_000_000_000_000_000, format='short') == '2P')
        self.assertTrue(size2human(1_150_000_000_000_000_000, format='short') == '1021P')
        self.assertTrue(size2human(2_000_000_000_000_000_000_000, format='short') == '2Z')
