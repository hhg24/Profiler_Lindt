import unittest

import pandas as pd

from src.write import generate_profiler_interpretations


class TestGenerateProfilerInterpretations(unittest.TestCase):
    def test_generates_chapter_based_interpretations(self):
        profiler_df = pd.DataFrame(
            [
                ["x", "y", "Purchasing behavior", None, None, None, None, None, None, None, "z"],
                ["x", "y", "Average order value", 100, 120, 80, 90, 110, 105, None, "z"],
                ["x", "y", "Repeat purchase rate", "25%", "30%", "20%", "22%", "28%", "26%", None, "z"],
                ["x", "y", "Lifecycle", None, None, None, None, None, None, None, "z"],
                ["x", "y", "New customers", 10, 10, 10, 10, 10, 10, None, "z"],
            ],
            columns=[
                "A",
                "B",
                "Descriptive feature",
                "Total",
                "Dubai",
                "Non Dubai",
                "Only Offline",
                "Only Online",
                "Hybrid",
                "Comments",
                "Trailing",
            ],
        )

        result = generate_profiler_interpretations(profiler_df)

        self.assertIn("Within Purchasing behavior", result.loc[1, "Comments"])
        self.assertIn("strongest for Dubai", result.loc[1, "Comments"])
        self.assertIn("lowest for Non Dubai", result.loc[1, "Comments"])
        self.assertIn("30.0%", result.loc[2, "Comments"])
        self.assertIn("Within Lifecycle", result.loc[4, "Comments"])
        self.assertIn("broadly consistent", result.loc[4, "Comments"])

    def test_does_not_overwrite_existing_comments_when_disabled(self):
        profiler_df = pd.DataFrame(
            [
                ["Purchasing behavior", None, None, None, None, None, "existing comment"],
                ["Average order value", 100, 120, 80, 90, 110, None],
            ],
            columns=[
                "Descriptive feature",
                "Total",
                "Dubai",
                "Non Dubai",
                "Only Offline",
                "Only Online",
                "Comments",
            ],
        )

        result = generate_profiler_interpretations(profiler_df, overwrite_comments=False)

        self.assertEqual(result.loc[0, "Comments"], "existing comment")
        self.assertIn("Within Purchasing behavior", result.loc[1, "Comments"])


if __name__ == "__main__":
    unittest.main()
