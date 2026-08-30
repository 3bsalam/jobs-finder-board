import os
import sys
import unittest
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from filter_jobs import load_profile

class TestProfileParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file = os.path.join(self.temp_dir.name, "profile.yaml")

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_profile(self, content):
        with open(self.temp_file, "w", encoding="utf-8") as f:
            f.write(content)

    def test_load_valid_profile(self):
        self.write_profile("""
candidate:
  residence_country: "Brazil"
  primary_stack:
    - "React"
    - "Node.js"
  disallowed_technologies:
    - "PHP"
  disallowed_arrangements:
    - "hybrid"
""")
        profile = load_profile(self.temp_file)
        self.assertEqual(profile["residence"], "Brazil")
        self.assertEqual(profile["primary_stack"], ["React", "Node.js"])
        self.assertEqual(profile["disallowed_tech"], ["PHP"])
        self.assertEqual(profile["disallowed_arrangements"], ["hybrid"])

    def test_load_missing_file_throws(self):
        with self.assertRaises(FileNotFoundError):
            load_profile(os.path.join(self.temp_dir.name, "nonexistent.yaml"))

    def test_load_missing_residence_throws(self):
        self.write_profile("""
candidate:
  primary_stack:
    - "React"
""")
        with self.assertRaises(ValueError) as context:
            load_profile(self.temp_file)
        self.assertIn("residence_country", str(context.exception))

    def test_load_missing_primary_stack_throws(self):
        self.write_profile("""
candidate:
  residence_country: "Brazil"
""")
        with self.assertRaises(ValueError) as context:
            load_profile(self.temp_file)
        self.assertIn("primary_stack", str(context.exception))

if __name__ == "__main__":
    unittest.main()
