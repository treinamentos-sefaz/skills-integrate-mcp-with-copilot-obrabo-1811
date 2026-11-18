import unittest
from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException

from src import app as app_module


class SignupCapacityTests(unittest.TestCase):
    activity_name = "Capacity Test"

    def setUp(self):
        self.previous_activity = app_module.activities.get(self.activity_name)
        app_module.activities[self.activity_name] = {
            "max_participants": 2,
            "participants": [],
        }

    def tearDown(self):
        if self.previous_activity is None:
            del app_module.activities[self.activity_name]
        else:
            app_module.activities[self.activity_name] = self.previous_activity

    def test_rejects_signup_when_activity_is_full(self):
        app_module.activities[self.activity_name]["participants"] = [
            "first@mergington.edu",
            "second@mergington.edu",
        ]

        with self.assertRaises(HTTPException) as error:
            app_module.signup_for_activity(
                self.activity_name, "third@mergington.edu"
            )

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(error.exception.detail, "Activity is full")
        self.assertEqual(
            len(app_module.activities[self.activity_name]["participants"]), 2
        )

    def test_rejects_duplicate_signup(self):
        app_module.activities[self.activity_name]["participants"] = [
            "student@mergington.edu",
        ]

        with self.assertRaises(HTTPException) as error:
            app_module.signup_for_activity(
                self.activity_name, "student@mergington.edu"
            )

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(
            error.exception.detail, "Student is already signed up"
        )

    def test_concurrent_signups_do_not_exceed_capacity(self):
        emails = [
            f"student{index}@mergington.edu"
            for index in range(20)
        ]

        def signup(email):
            try:
                app_module.signup_for_activity(self.activity_name, email)
                return True
            except HTTPException:
                return False

        with ThreadPoolExecutor(max_workers=len(emails)) as executor:
            successful_signups = list(executor.map(signup, emails))

        participants = app_module.activities[self.activity_name]["participants"]
        self.assertEqual(sum(successful_signups), 2)
        self.assertEqual(len(participants), 2)


if __name__ == "__main__":
    unittest.main()
