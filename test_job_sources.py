import unittest
from unittest.mock import patch
from job_sources import fetch_configured_sources

class JobSourceConfigTests(unittest.TestCase):
    @patch("job_sources.fetch_greenhouse", return_value=[{"title": "SRE"}])
    @patch("job_sources.fetch_lever", return_value=[{"title": "DevOps"}])
    def test_parses_both_public_source_types(self, lever, greenhouse):
        jobs, errors = fetch_configured_sources("# comment\ngreenhouse:acme\nlever:acme")
        self.assertEqual(len(jobs), 2)
        self.assertEqual(errors, [])
        greenhouse.assert_called_once_with("acme")
        lever.assert_called_once_with("acme")

    def test_reports_invalid_source_without_crashing(self):
        jobs, errors = fetch_configured_sources("unknown:board")
        self.assertEqual(jobs, [])
        self.assertEqual(len(errors), 1)

if __name__ == "__main__":
    unittest.main()
