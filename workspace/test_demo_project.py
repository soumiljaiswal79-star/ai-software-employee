import unittest
from pathlib import Path


class DemoProjectTest(unittest.TestCase):
    def test_demo_script_exists(self) -> None:
        self.assertTrue(Path("demo-project/hello.py").is_file())


if __name__ == "__main__":
    unittest.main()