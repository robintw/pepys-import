import os
import sqlite3
import unittest
from contextlib import redirect_stdout
from io import StringIO
from sqlite3 import OperationalError

import pg8000
import pytest
from testing.postgresql import Postgresql

from pepys_import.cli import process
from pepys_import.core.store.data_store import DataStore
from pepys_import.utils.geoalchemy_utils import load_spatialite

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/other_data")


class TestImportWithMissingDBFieldSQLite(unittest.TestCase):
    def setUp(self):
        ds = DataStore("", "", "", 0, "cli_import_test.db", db_type="sqlite")
        ds.initialise()

    def tearDown(self):
        os.remove("cli_import_test.db")

    def test_import_with_missing_db_field(self):
        conn = sqlite3.connect("cli_import_test.db")
        load_spatialite(conn, None)

        # We want to DROP a column from the States table, but SQLite doesn't support this
        # so we drop the table and create a new table instead
        conn.execute("DROP TABLE States")

        # SQL to create a States table without a heading column
        create_sql = """CREATE TABLE States (
        state_id INTEGER NOT NULL, 
        time TIMESTAMP NOT NULL, 
        sensor_id INTEGER NOT NULL, 
        elevation REAL, 
        course REAL, 
        speed REAL, 
        source_id INTEGER NOT NULL, 
        privacy_id INTEGER, 
        created_date DATETIME, "location" POINT, 
        PRIMARY KEY (state_id)
        )"""

        conn.execute(create_sql)
        conn.close()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            process(path=DATA_PATH, archive=False, db="cli_import_test.db", resolver="default")
        output = temp_output.getvalue()

        assert "ERROR: SQL error when communicating with database" in output


@pytest.mark.postgres
class TestImportWithMissingDBFieldPostgres(unittest.TestCase):
    def setUp(self):
        self.postgres = None
        self.store = None
        try:
            self.postgres = Postgresql(
                database="test", host="localhost", user="postgres", password="postgres", port=55527,
            )
        except RuntimeError:
            print("PostgreSQL database couldn't be created! Test is skipping.")
            return
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
            self.store.initialise()
        except OperationalError:
            print("Database schema and data population failed! Test is skipping.")

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_import_with_missing_db_field(self):
        conn = pg8000.connect(user="postgres", password="postgres", database="test", port=55527)
        cursor = conn.cursor()
        # Alter table to drop heading column
        cursor.execute('ALTER TABLE pepys."States" DROP COLUMN heading CASCADE;')

        conn.commit()
        conn.close()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            db_config = {
                "name": "test",
                "host": "localhost",
                "username": "postgres",
                "password": "postgres",
                "port": 55527,
                "type": "postgres",
            }

            process(path=DATA_PATH, archive=False, db=db_config, resolver="default")
        output = temp_output.getvalue()

        assert "ERROR: SQL error when communicating with database" in output


@pytest.mark.postgres
class TestImportWithWrongTypeDBFieldPostgres(unittest.TestCase):
    def setUp(self):
        self.postgres = None
        self.store = None
        try:
            self.postgres = Postgresql(
                database="test", host="localhost", user="postgres", password="postgres", port=55527,
            )
        except RuntimeError:
            print("PostgreSQL database couldn't be created! Test is skipping.")
            return
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
            self.store.initialise()
        except OperationalError:
            print("Database schema and data population failed! Test is skipping.")

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_import_with_wrong_type_db_field(self):
        conn = pg8000.connect(user="postgres", password="postgres", database="test", port=55527)
        cursor = conn.cursor()
        # Alter table to change heading column to be a timestamp
        cursor.execute(
            'ALTER TABLE pepys."States" ALTER COLUMN heading SET DATA TYPE character varying(150);'
        )

        conn.commit()
        conn.close()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            db_config = {
                "name": "test",
                "host": "localhost",
                "username": "postgres",
                "password": "postgres",
                "port": 55527,
                "type": "postgres",
            }

            process(path=DATA_PATH, archive=False, db=db_config, resolver="default")
        output = temp_output.getvalue()

        assert "ERROR: SQL error when communicating with database" in output