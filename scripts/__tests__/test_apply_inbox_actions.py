import datetime
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from apply_inbox_actions import allowed, apply  # noqa: E402

TODAY = datetime.date(2026, 10, 15)


class TestApplyInboxActions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.apps = os.path.join(self.root, "applications", "01.10.26")
        os.makedirs(self.apps)
        self.job("01 - Acme - Backend Engineer", "interview")
        self.job("02 - Globex - Product Engineer", "ready")

    def tearDown(self):
        self.tmp.cleanup()

    def job(self, name, status):
        d = os.path.join(self.apps, name)
        os.makedirs(d)
        with open(os.path.join(d, "JOB-URL.txt"), "w") as fh:
            fh.write(f"{name}\n\nStatus: {status}\nApplied on: ____________\n")

    def read(self, name):
        with open(os.path.join(self.apps, name, "JOB-URL.txt")) as fh:
            return fh.read()

    def test_never_downgrades(self):
        apply([{"action": "set_status", "number": 1, "status": "applied", "evidence": "e1"}],
              root=self.root, today=TODAY)
        self.assertIn("Status: interview", self.read("01 - Acme - Backend Engineer"))

    def test_rejection_lands_and_follow_up_set_on_apply(self):
        apply([{"action": "set_status", "number": 2, "status": "applied",
                "applied_on": "28.09.26", "evidence": "e2"}], root=self.root, today=TODAY)
        t = self.read("02 - Globex - Product Engineer")
        self.assertIn("Status: applied", t)
        self.assertIn("Follow up: 12.10.26", t)
        apply([{"action": "set_status", "number": 2, "status": "rejected", "evidence": "e3"}],
              root=self.root, today=TODAY)
        self.assertIn("Status: rejected", self.read("02 - Globex - Product Engineer"))

    def test_idempotent(self):
        acts = [{"action": "set_status", "number": 2, "status": "applied", "evidence": "same"}]
        apply(acts, root=self.root, today=TODAY)
        first = self.read("02 - Globex - Product Engineer")
        apply(acts, root=self.root, today=TODAY)
        self.assertEqual(first, self.read("02 - Globex - Product Engineer"))

    def test_create_and_no_duplicate_company(self):
        rep = apply([{"action": "create", "company": "Initech", "role": "SRE [Remote]",
                      "status": "applied", "applied_on": "14.10.26", "evidence": "e4"},
                     {"action": "create", "company": "acme", "role": "Data Engineer",
                      "status": "applied", "evidence": "e5"}], root=self.root, today=TODAY)
        kinds = [k for k, _, _ in rep]
        self.assertEqual(kinds, ["created", "note"])
        created = os.listdir(os.path.join(self.root, "applications", "15.10.26"))
        self.assertEqual(created, ["03 - Initech - SRE  Remote"])
        self.assertIn("Another role at this company: Data Engineer", self.read("01 - Acme - Backend Engineer"))

    def test_dry_run_writes_nothing(self):
        apply([{"action": "create", "company": "Hooli", "status": "applied", "evidence": "e6"}],
              root=self.root, dry_run=True, today=TODAY)
        self.assertFalse(os.path.exists(os.path.join(self.root, "applications", "15.10.26")))

    def test_allowed_rules(self):
        self.assertFalse(allowed("rejected", "applied"))
        self.assertTrue(allowed("rejected", "applied", reapplied=True))
        self.assertTrue(allowed("rejected", "interview"))
        self.assertFalse(allowed("offer", "rejected"))
        self.assertFalse(allowed("applied", "skipped"))


if __name__ == "__main__":
    unittest.main()
