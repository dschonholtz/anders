import unittest

from anders.adapters.linkedin import classify_linkedin_signal, normalize_linkedin_notifications


class LinkedInAdapterTests(unittest.TestCase):
    def test_normalize_linkedin_message_notification(self):
        items = [
            {
                "source": "gmail",
                "source_id": "abc",
                "title": "Jane sent you a message on LinkedIn",
                "person": "LinkedIn <messages-noreply@linkedin.com>",
                "summary": "Jane sent you a message: hello https://www.linkedin.com/messaging/",
                "occurred_at": "Sat, 16 May 2026 09:00:00 -0400",
            },
            {"source": "gmail", "source_id": "def", "title": "Bank receipt", "summary": "ordinary email"},
        ]
        out = normalize_linkedin_notifications(items)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].metadata["signal"], "message")
        self.assertEqual(out[0].url, "https://www.linkedin.com/messaging/")

    def test_classify_connection(self):
        self.assertEqual(
            classify_linkedin_signal({"title": "You have a new connection request", "summary": ""}),
            "connection",
        )


if __name__ == "__main__":
    unittest.main()
