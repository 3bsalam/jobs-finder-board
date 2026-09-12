import os
import sys
import unittest
import tempfile
from unittest.mock import patch

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.dirname(TEST_DIR)
ROOT_DIR = os.path.dirname(DASHBOARD_DIR)
sys.path.insert(0, DASHBOARD_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

import build as board_build


class TestBoardBuild(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_job_sort_key(self):
        job1 = {"date": "12.09.26", "num": "5"}
        job2 = {"date": "2026-09-12", "num": "10"}
        job3 = {"date": "12.09.26", "num": "abc"}

        self.assertEqual(board_build.parse_job_sort_key(job1), ("2026-09-12", 5))
        self.assertEqual(board_build.parse_job_sort_key(job2), ("2026-09-12", 10))
        self.assertEqual(board_build.parse_job_sort_key(job3), ("2026-09-12", 0))

    def test_pay_of(self):
        self.assertEqual(board_build.pay_of("Salary: $120,000 / year"), "$120,000 / year")
        self.assertEqual(board_build.pay_of("Compensation: Not disclosed"), "")
        self.assertEqual(board_build.pay_of("Pay: €80k - €100k per year"), "€80k - €100k per year")

    def test_collect(self):
        apps_dir = os.path.join(self.temp_dir.name, "applications")
        
        # Day 1: 12.09.26
        job1_dir = os.path.join(apps_dir, "12.09.26", "01 - Acme - Backend Engineer")
        os.makedirs(job1_dir, exist_ok=True)
        with open(os.path.join(job1_dir, "JOB-URL.txt"), "w", encoding="utf-8") as f:
            f.write("https://acme.com/jobs/1\nLocation: Remote\nSalary: $150k")

        job2_dir = os.path.join(apps_dir, "12.09.26", "02 - TechCorp - Frontend Engineer")
        os.makedirs(job2_dir, exist_ok=True)
        with open(os.path.join(job2_dir, "JOB-URL.txt"), "w", encoding="utf-8") as f:
            f.write("https://techcorp.com/jobs/2\nStatus: ready")

        # Day 2: 13.09.26
        job3_dir = os.path.join(apps_dir, "13.09.26", "03 - BadFit - Fullstack - REJECTED")
        os.makedirs(job3_dir, exist_ok=True)
        with open(os.path.join(job3_dir, "JOB-URL.txt"), "w", encoding="utf-8") as f:
            f.write("https://badfit.com/jobs/3")

        job4_dir = os.path.join(apps_dir, "13.09.26", "04 - GoodFit - Dev")
        os.makedirs(job4_dir, exist_ok=True)
        with open(os.path.join(job4_dir, "JOB-URL.txt"), "w", encoding="utf-8") as f:
            f.write("https://goodfit.com/jobs/4\nApplied on: 13.09.26")

        with patch.object(board_build, "APPS", apps_dir):
            jobs = board_build.collect()

        self.assertEqual(len(jobs), 4)
        # Should be sorted reverse chronologically by (iso_date, num)
        # Order expected: job 4 (13.09.26 #4), job 3 (13.09.26 #3), job 2 (12.09.26 #2), job 1 (12.09.26 #1)
        self.assertEqual([j["num"] for j in jobs], ["04", "03", "02", "01"])
        self.assertEqual(jobs[0]["status"], "applied")
        self.assertEqual(jobs[1]["status"], "rejected")
        self.assertEqual(jobs[2]["status"], "ready")
        self.assertEqual(jobs[3]["status"], "to_prepare")
        self.assertEqual(jobs[3]["pay"], "$150k")

    def test_build_html_rendering(self):
        jobs = [
            {
                "num": "01",
                "company": "Acme",
                "role": "Backend",
                "date": "12.09.26",
                "status": "to_prepare",
                "url": "https://acme.com",
                "applied_on": "",
                "location": "Remote",
                "verdict": "",
                "followup": "",
                "salary": "",
                "pay": "",
                "folder": "/path/to/folder",
                "docs": [],
                "guides": [],
                "notes": "",
                "mynotes": "",
            }
        ]

        html = board_build.build(jobs)
        self.assertIn('"num": "01"', html)
        self.assertIn('"company": "Acme"', html)
        self.assertIn("1 roles", html)
        self.assertIn('id="searchbtn"', html)
        self.assertIn('id="searchmodal"', html)
        self.assertIn('id="search_start"', html)
        self.assertIn('parseJobDate', html)


if __name__ == "__main__":
    unittest.main()
