import os
import shutil
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import pytest

from pepys_admin.admin_cli import AdminShell
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/rep_data")


class AdminCLITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, self.store, False)

        self.admin_shell = AdminShell(self.store)

    @patch("pepys_admin.admin_cli.iterfzf", return_value="rep_test1.rep")
    @patch("pepys_admin.admin_cli.input", return_value="Y")
    def test_do_export(self, patched_iterfzf, patched_input):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export()
        output = temp_output.getvalue()
        assert "'rep_test1.rep' is going to be exported." in output
        assert "Datafile successfully exported to exported_rep_test1_rep.rep." in output

        file_path = os.path.join(CURRENT_DIR, "exported_rep_test1_rep.rep")
        assert os.path.exists(file_path) is True
        with open(file_path, "r") as file:
            data = file.read().splitlines()
        assert len(data) == 22  # 8 States, 7 Contacts, 7 Comments

    @patch("pepys_admin.admin_cli.input")
    def test_do_export_all(self, patched_input):
        patched_input.side_effect = ["Y", "export_test"]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export_all()
        output = temp_output.getvalue()
        assert "Datafiles are going to be exported to" in output
        assert "All datafiles are successfully exported!" in output

        folder_path = os.path.join(CURRENT_DIR, "export_test")
        assert os.path.exists(folder_path) is True

        shutil.rmtree(folder_path)

    def test_do_status(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_status()
        output = temp_output.getvalue()

        states_text = "| States       |              738 |"
        contacts_text = "| Contacts     |               15 |"
        comments_text = "| Comments     |                7 |"
        datafiles_text = "| Datafiles    |                7 |"
        assert states_text in output
        assert contacts_text in output
        assert comments_text in output
        assert datafiles_text in output

    def test_do_exit(self):
        temp_output = StringIO()
        with pytest.raises(SystemExit), redirect_stdout(temp_output):
            self.admin_shell.do_exit()
        output = temp_output.getvalue()
        assert "Thank you for using Pepys Admin" in output


if __name__ == "__main__":
    unittest.main()
