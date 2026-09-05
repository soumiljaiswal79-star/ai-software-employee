import unittest
from pathlib import Path


class DemoProjectTest(unittest.TestCase):
    def test_demo_script_exists(self) -> None:
        hello_path = Path(__file__).parent / "demo-project" / "hello.py"
        self.assertTrue(hello_path.is_file())


if __name__ == "__main__":
    unittest.main()