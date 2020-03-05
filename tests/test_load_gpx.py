import os
import unittest
from sqlite3 import OperationalError

from pepys_import.file.gpx_importer import GPXImporter
from pepys_import.file.file_processor import FileProcessor
from pepys_import.core.store.data_store import DataStore

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/gpx")


class TestLoadGPX(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_process_gpx_data(self):
        processor = FileProcessor()
        processor.register_importer(GPXImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            states = self.store.session.query(self.store.db_classes.State).all()
            assert len(states) == 0

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 0

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 0

        # parse the folder
        processor.process(DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            assert len(states) == 36

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 3

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 7

            #
            # Test the actual values that are imported
            #

            # there should be 5 States with a speed of 4.5m/s
            # as the first <trkpt> element in gpx_1_0.gpx has been imported
            # 5 times based on the multiple modified versions of that file used
            # for testing
            speed_states = (
                self.store.session.query(self.store.db_classes.State)
                .filter(self.store.db_classes.State.speed == 4.5)
                .all()
            )
            assert len(speed_states) == 5

            # there should be one point with an elevation of 2372m
            elev_states = (
                self.store.session.query(self.store.db_classes.State)
                .filter(self.store.db_classes.State.elevation == 2372)
                .all()
            )
            assert len(elev_states) == 1


if __name__ == "__main__":
    unittest.main()