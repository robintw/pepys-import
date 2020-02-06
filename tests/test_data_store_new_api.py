import unittest
import os

from pepys_import.core.store.data_store import DataStore
from unittest import TestCase

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")


class TestDataStore(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        with self.store.session_scope() as session:
            self.nationality = self.store.add_to_nationalities("test_nationality").name
            self.platform_type = self.store.add_to_platform_types(
                "test_platform_type"
            ).name
            self.privacy = self.store.add_to_privacies("test_privacy").name

    def tearDown(self):
        pass

    def test_new_datafile_added_successfully(self):
        """Test whether a new datafile is created successfully or not"""

        with self.store.session_scope() as session:
            datafiles = self.store.get_datafiles()

        # there must be no entry at the beginning
        self.assertEqual(len(datafiles), 0)

        with self.store.session_scope() as session:
            created_datafile = self.store.get_datafile("test_file.csv", "csv")

        # there must be one entry
        with self.store.session_scope() as session:
            datafiles = self.store.get_datafiles()
        self.assertEqual(len(datafiles), 1)

    def test_present_datafile_not_added(self):
        """Test whether present datafile is not created"""

        with self.store.session_scope() as session:
            datafiles = self.store.get_datafiles()

        # there must be no entry at the beginning
        self.assertEqual(len(datafiles), 0)

        with self.store.session_scope() as session:
            created_datafile = self.store.get_datafile("test_file.csv", "csv")
            created_datafile_2 = self.store.get_datafile("test_file.csv", "csv")

        # there must be one entry
        with self.store.session_scope() as session:
            datafiles = self.store.get_datafiles()
        self.assertEqual(len(datafiles), 1)

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_datafile(self):
        pass

    def test_new_platform_added_successfully(self):
        """Test whether a new platform is created successfully or not"""

        with self.store.session_scope() as session:
            platforms = self.store.get_platforms()

        # there must be no entry at the beginning
        self.assertEqual(len(platforms), 0)

        with self.store.session_scope() as session:
            created_platform = self.store.get_platform(
                "Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
            )

        # there must be one entry
        with self.store.session_scope() as session:
            platforms = self.store.get_platforms()
        self.assertEqual(len(platforms), 1)

    def test_present_platform_not_added(self):
        """Test whether present platform is not created"""

        with self.store.session_scope() as session:
            platforms = self.store.get_platforms()

        # there must be no entry at the beginning
        self.assertEqual(len(platforms), 0)

        with self.store.session_scope() as session:
            created_platform = self.store.get_platform(
                "Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
            )
            created_platform_2 = self.store.get_platform(
                "Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
            )

        # there must be one entry
        with self.store.session_scope() as session:
            platforms = self.store.get_platforms()
        self.assertEqual(len(platforms), 1)

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_platform(self):
        pass


class TestDataStoreStatus(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        self.store.populate_reference(TEST_DATA_PATH)
        self.store.populate_metadata(TEST_DATA_PATH)
        self.store.populate_measurement(TEST_DATA_PATH)

    def tearDown(self):
        pass

    def test_get_status_of_measurement(self):
        """Test whether summary contents correct for measurement tables"""

        # get_status returns dictionary for measurement, metadata, and reference tables
        # respectively. Therefore, the first return is import in this case.
        table_summary, _, _ = self.store.get_status(report_measurement=True)
        self.assertNotEqual(table_summary, {})
        self.assertIn("States", table_summary.keys())
        self.assertIn("Contacts", table_summary.keys())
        self.assertIn("Activations", table_summary.keys())

    def test_get_status_of_metadata(self):
        """Test whether summary contents correct for metadata tables"""

        # get_status returns dictionary for measurement, metadata, and reference tables
        # respectively. Therefore, the second return is import in this case
        _, table_summary, _ = self.store.get_status(report_metadata=True)
        self.assertNotEqual(table_summary, {})
        self.assertIn("Sensors", table_summary.keys())
        self.assertIn("Platforms", table_summary.keys())
        self.assertIn("Datafiles", table_summary.keys())

    def test_get_status_of_reference(self):
        """Test whether summary contents correct for reference tables"""

        # get_status returns dictionary for measurement, metadata, and reference tables
        # respectively. Therefore, the third return is import in this case.
        _, _, table_summary = self.store.get_status(report_reference=True)
        self.assertNotEqual(table_summary, {})
        self.assertIn("Nationalities", table_summary.keys())
        self.assertIn("Privacies", table_summary.keys())
        self.assertIn("PlatformTypes", table_summary.keys())


class TestSensor(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    # TODO: not implemented yet
    def test_new_sensor_added_successfully(self):
        """Test whether a new sensor is created"""

        pass

    def test_present_sensor_not_added(self):
        """Test whether present sensor is not created"""

        pass

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_sensor(self):
        pass


class TestMeasurements(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    # TODO: not implemented yet
    def test_new_state_added_successfully(self):
        """Test whether a new state is created"""

        pass

    def test_present_state_not_added(self):
        """Test whether present state is not created"""

        pass

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_state(self):
        pass

    def test_new_contact_added_successfully(self):
        """Test whether a new contact is created"""

        pass

    def test_present_contact_not_added(self):
        """Test whether present contact is not created"""

        pass

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_contact(self):
        pass

    def test_new_comment_added_successfully(self):
        """Test whether a new comment is created"""

        pass

    def test_present_comment_not_added(self):
        """Test whether present comment is not created"""

        pass

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_comment(self):
        pass


if __name__ == "__main__":
    unittest.main()