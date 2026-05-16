from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from anders.google_ingest import (
    DayPaths,
    normalize_gmail_message,
    sender_summary,
    triage_recommendation,
    write_gmail_artifacts,
)


class GoogleIngestTests(unittest.TestCase):
    def test_normalize_gmail_message_metadata(self) -> None:
        raw = {
            "id": "abc123",
            "threadId": "thr1",
            "labelIds": ["UNREAD", "INBOX"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "Sender <sender@example.com>"},
                    {"name": "Subject", "value": "Hello"},
                    {"name": "Date", "value": "Sat, 16 May 2026 12:00:00 -0400"},
                    {"name": "List-Unsubscribe", "value": "<mailto:unsubscribe@example.com>"},
                ]
            },
            "snippet": "Hi Doug",
        }
        msg = normalize_gmail_message(raw, include_body=False)
        self.assertEqual(msg["id"], "abc123")
        self.assertEqual(msg["from"], "Sender <sender@example.com>")
        self.assertEqual(msg["subject"], "Hello")
        self.assertEqual(msg["date"], "2026-05-16T12:00:00-04:00")

    def test_triage_recommendation_is_dry_run(self) -> None:
        rec = triage_recommendation(
            {
                "id": "m1",
                "thread_id": "t1",
                "label_ids": ["UNREAD", "CATEGORY_PROMOTIONS"],
                "from": "Deals <deals@example.com>",
                "subject": "Weekend sale newsletter",
                "list_unsubscribe": "<mailto:u@example.com>",
            }
        )
        self.assertTrue(rec["dry_run_only"])
        self.assertEqual(rec["recommended_action"], "unsubscribe_candidate")
        self.assertIn("has List-Unsubscribe header", rec["reasons"])

    def test_sender_summary_and_artifact_write(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            data_repo = Path(td)
            paths = DayPaths(data_repo, "2026-05-16")
            messages = [
                {
                    "id": "m1",
                    "thread_id": "t1",
                    "label_ids": ["UNREAD"],
                    "from": "A <a@example.com>",
                    "subject": "One",
                    "snippet": "one",
                    "body_text": "body",
                },
                {
                    "id": "m2",
                    "thread_id": "t2",
                    "label_ids": [],
                    "from": "B <b@example.com>",
                    "subject": "Two",
                    "snippet": "two",
                    "body_text": "body",
                },
            ]
            summary = sender_summary(messages)
            self.assertEqual(summary[0]["domain"], "example.com")
            self.assertEqual(summary[0]["count"], 2)
            manifest = write_gmail_artifacts(paths, messages, "unit", "test-query")
            manifest_path = data_repo / "briefings/days/2026-05-16/google/gmail-unit.manifest.json"
            self.assertTrue(manifest_path.exists())
            self.assertEqual(json.loads(manifest_path.read_text())["count"], 2)
            self.assertEqual(len(manifest["messages"]), 2)


if __name__ == "__main__":
    unittest.main()
