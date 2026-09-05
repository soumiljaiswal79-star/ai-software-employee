import unittest
from pathlib import Path


class HelloScriptTest(unittest.TestCase):
    def test_hello_script_contains_expected_message(self) -> None:
        hello_path = Path(__file__).with_name("hello.py")
        self.assertEqual(
            hello_path.read_text(encoding="utf-8").strip(),
            'print("Hello from the demo project!")',
        )


if __name__ == "__main__":
    unittest.main()