import unittest
import os

from datetime import datetime
from pepys_import.core.store.data_store import DataStore
from unittest import TestCase

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")


class DataStoreTestCase(TestCase):
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


class DataStoreStatusTestCase(TestCase):
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


class SensorTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        with self.store.session_scope() as session:
            self.nationality = self.store.add_to_nationalities("test_nationality").name
            self.platform_type = self.store.add_to_platform_types(
                "test_platform_type"
            ).name
            self.privacy = self.store.add_to_privacies("test_privacy").name

            self.platform = self.store.get_platform(
                "Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
            )

    def tearDown(self):
        pass

    # TODO: not working yet
    def test_new_sensor_added_successfully(self):
        """Test whether a new sensor is created"""
        with self.store.session_scope() as session:
            sensors = self.store.get_sensors()

        # there must be no entry at the beginning
        self.assertEqual(len(sensors), 0)

        self.platform.get_sensor(sensors, self.store.session, "gps")

        # there must be one entry
        with self.store.session_scope() as session:
            sensors = self.store.get_sensors()
        self.assertEqual(len(sensors), 1)
        self.assertEqual(sensors[0].name, "gps")

    def test_present_sensor_not_added(self):
        """Test whether present sensor is not created"""
        with self.store.session_scope() as session:
            sensors = self.store.get_sensors()

        # there must be no entry at the beginning
        self.assertEqual(len(sensors), 0)

        self.platform.get_sensor(sensors, self.store.session, "gps")
        self.platform.get_sensor(sensors, self.store.session, "gps")

        # there must be one entry
        with self.store.session_scope() as session:
            sensors = self.store.get_sensors()

        self.assertEqual(len(sensors), 1)

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_sensor(self):
        pass


class MeasurementsTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        with self.store.session_scope() as session:
            self.nationality = self.store.add_to_nationalities("test_nationality").name
            self.platform_type = self.store.add_to_platform_types(
                "test_platform_type"
            ).name
            self.privacy = self.store.add_to_privacies("test_privacy").name

            self.platform = self.store.get_platform(
                "Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
            )
            self.sensor = self.platform.get_sensor("gps")
            self.file = self.store.get_datafile("test_file", "csv")
            self.comment_type = self.store.add_to_comment_types("test_type").name

    def tearDown(self):
        pass

    # TODO: not completed yet
    def test_new_state_added_successfully(self):
        """Test whether a new state is created"""
        with self.store.session_scope() as session:
            states = self.store.get_states()

        # there must be no entry at the beginning
        self.assertEqual(len(states), 0)

        self.file.create_state(self.sensor, datetime.utcnow, "Comment", self.co)

        # there must be one entry
        with self.store.session_scope() as session:
            states = self.store.get_states()
        self.assertEqual(len(states), 1)

    def test_present_state_not_added(self):
        """Test whether present state is not created"""
        with self.store.session_scope() as session:
            states = self.store.get_states()

        # there must be no entry at the beginning
        self.assertEqual(len(states), 0)

        self.file.create_state(self.sensor, "2020-01-01")
        self.file.create_state(self.sensor, "2020-01-01")

        # there must be one entry
        with self.store.session_scope() as session:
            states = self.store.get_states()
        self.assertEqual(len(states), 1)

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_state(self):
        pass

    def test_new_contact_added_successfully(self):
        """Test whether a new contact is created"""

        with self.store.session_scope() as session:
            contacts = self.store.get_contacts()

        # there must be no entry at the beginning
        self.assertEqual(len(contacts), 0)

        self.file.create_contact(self.sensor, datetime.utcnow)

        # there must be one entry
        with self.store.session_scope() as session:
            contacts = self.store.get_contacts()
        self.assertEqual(len(contacts), 1)

    def test_present_contact_not_added(self):
        """Test whether present contact is not created"""
        with self.store.session_scope() as session:
            contacts = self.store.get_contacts()

        # there must be no entry at the beginning
        self.assertEqual(len(contacts), 0)

        self.file.create_contact(self.sensor, "2020-01-01")
        self.file.create_contact(self.sensor, "2020-01-01")

        # there must be one entry
        with self.store.session_scope() as session:
            contacts = self.store.get_contacts()
        self.assertEqual(len(contacts), 1)
        pass

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_contact(self):
        pass

    def test_new_comment_added_successfully(self):
        """Test whether a new comment is created"""

        with self.store.session_scope() as session:
            comments = self.store.get_comments()

        # there must be no entry at the beginning
        self.assertEqual(len(comments), 0)

        self.file.create_comment(
            self.sensor, datetime.utcnow, "Comment", self.comment_type
        )

        # there must be one entry
        with self.store.session_scope() as session:
            comments = self.store.get_comments()
        self.assertEqual(len(comments), 1)

    def test_present_comment_not_added(self):
        """Test whether present comment is not created"""
        with self.store.session_scope() as session:
            comments = self.store.get_comments()

        # there must be no entry at the beginning
        self.assertEqual(len(comments), 0)

        self.file.create_comment(
            self.sensor, datetime.utcnow, "Comment", self.comment_type
        )
        self.file.create_comment(
            self.sensor, datetime.utcnow, "Comment", self.comment_type
        )

        # there must be one entry
        with self.store.session_scope() as session:
            comments = self.store.get_comments()
        self.assertEqual(len(comments), 1)
        pass

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_comment(self):
        pass


if __name__ == "__main__":
    unittest.main()
