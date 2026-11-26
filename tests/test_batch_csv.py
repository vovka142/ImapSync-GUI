import csv
import tempfile
import unittest
from pathlib import Path

from app.modules.BatchMigration import load_jobs, write_template


class BatchCsvTests(unittest.TestCase):
    def write_csv(self, content: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "mailboxes.csv"
        path.write_text(content, encoding="utf-8-sig")
        return path

    def test_load_comma_delimited_csv(self):
        path = self.write_csv(
            "label,source_user,source_password,target_user,target_password\n"
            "Бухгалтерия,old@example.org,old pass,new@example.org,new pass\n"
        )
        jobs = load_jobs(path)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["label"], "Бухгалтерия")
        self.assertEqual(jobs[0]["source_password"], "old pass")

    def test_load_semicolon_delimited_csv(self):
        path = self.write_csv(
            "source_user;source_password;target_user;target_password\n"
            "old@example.org;pass1;new@example.org;pass2\n"
        )
        self.assertEqual(load_jobs(path)[0]["target_user"], "new@example.org")

    def test_missing_password_is_rejected_with_line_number(self):
        path = self.write_csv(
            "source_user,source_password,target_user,target_password\n"
            "old@example.org,,new@example.org,pass2\n"
        )
        with self.assertRaisesRegex(ValueError, "Строка 2"):
            load_jobs(path)

    def test_empty_csv_is_rejected(self):
        path = self.write_csv("source_user,source_password,target_user,target_password\n")
        with self.assertRaisesRegex(ValueError, "нет ни одного"):
            load_jobs(path)

    def test_template_has_expected_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "template.csv"
            write_template(path)
            with path.open(encoding="utf-8-sig", newline="") as stream:
                self.assertEqual(
                    next(csv.reader(stream)),
                    ["label", "source_user", "source_password", "target_user", "target_password"],
                )


if __name__ == "__main__":
    unittest.main()
