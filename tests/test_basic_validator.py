import unittest

from datetime import datetime

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.validators.basic_validator import BasicValidator
from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer


class BasicValidatorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        with self.store.session_scope():
            # Create a platform, a sensor, a datafile and finally a state object respectively
            nationality = self.store.add_to_nationalities("test_nationality").name
            platform_type = self.store.add_to_platform_types("test_platform_type").name
            sensor_type = self.store.add_to_sensor_types("test_sensor_type")
            privacy = self.store.add_to_privacies("test_privacy").name

            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
            )
            self.sensor = platform.get_sensor(self.store, "gps", sensor_type)
            self.current_time = datetime.utcnow()
            self.file = self.store.get_datafile("test_file", "csv")

            self.store.session.expunge(self.sensor)
            self.store.session.expunge(self.file)

        self.errors = list()

        class TestParser(Importer):
            def __init__(
                self,
                name="Test Importer",
                validation_level=constants.NONE_LEVEL,
                short_name="Test Importer",
                separator=" ",
            ):
                super().__init__(name, validation_level, short_name)
                self.separator = separator
                self.text_label = None
                self.depth = 0.0
                self.errors = list()

            def can_load_this_header(self, header) -> bool:
                return True

            def can_load_this_filename(self, filename):
                return True

            def can_load_this_type(self, suffix):
                return True

            def can_load_this_file(self, file_contents):
                return True

            def load_this_file(self, data_store, path, file_contents, datafile):
                pass

        self.parser = TestParser()
        self.file.measurements[self.parser.short_name] = list()

    def tearDown(self) -> None:
        pass

    def test_validate_longitude(self):
        state = self.file.create_state(
            self.sensor, self.current_time, parser_name=self.parser.short_name
        )
        state.location = "POINT(180.0 25.0)"
        BasicValidator(state, self.errors, "Test Parser")
        assert len(self.errors) == 1
        assert "Longitude is not between -90 and 90 degrees!" in str(self.errors[0])

    def test_validate_latitude(self):
        state = self.file.create_state(
            self.sensor, self.current_time, parser_name=self.parser.short_name
        )
        state.location = "POINT(25.0 300.0)"
        BasicValidator(state, self.errors, "Test Parser")
        assert len(self.errors) == 1
        assert "Latitude is not between -180 and 180 degrees!" in str(self.errors[0])

    def test_validate_heading(self):
        state = self.file.create_state(
            self.sensor, self.current_time, parser_name=self.parser.short_name
        )
        state.heading = 10.0  # 10 radians is approximately 572 degrees
        BasicValidator(state, self.errors, "Test Parser")
        assert len(self.errors) == 1
        assert "Heading is not between 0 and 360 degrees!" in str(self.errors[0])

    def test_validate_course(self):
        state = self.file.create_state(
            self.sensor, self.current_time, parser_name=self.parser.short_name
        )
        state.course = 10.0  # 10 radians is approximately 572 degrees
        BasicValidator(state, self.errors, "Test Parser")
        assert len(self.errors) == 1
        assert "Course is not between 0 and 360 degrees!" in str(self.errors[0])


if __name__ == "__main__":
    unittest.main()