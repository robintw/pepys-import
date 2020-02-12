import csv
import os
from pathlib import Path

from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.event import listen
from sqlalchemy.schema import CreateSchema
from sqlalchemy.sql import select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from importlib import import_module
from contextlib import contextmanager

from pepys_import.resolvers.default_resolver import DefaultResolver
from pepys_import.utils.data_store_utils import import_from_csv
from pepys_import.utils.geoalchemy_utils import load_spatialite
from .db_base import BasePostGIS, BaseSpatiaLite
from .db_status import TableTypes
from pepys_import.core.formats import unit_registry

from pepys_import import __version__
from pepys_import.utils.branding_util import (
    show_welcome_banner,
    show_software_meta_info,
)
from .table_summary import TableSummary, TableSummarySet

MAIN_DIRECTORY_PATH = Path(__file__).parent.parent.parent  # pepys_import/pepys_import
DEFAULT_DATA_PATH = os.path.join(MAIN_DIRECTORY_PATH, "database", "default_data")


class DataStore(object):
    """ Representation of database

    :returns: :class:`DataStore`
    """

    # Valid options for db_type are 'postgres' and 'sqlite'
    def __init__(
        self,
        db_username,
        db_password,
        db_host,
        db_port,
        db_name,
        db_type="postgres",
        missing_data_resolver=DefaultResolver(),
        show_welcome=True,
        show_status=True,
    ):
        if db_type == "postgres":
            self.db_classes = import_module("pepys_import.core.store.postgres_db")
            driver = "postgresql+psycopg2"
        elif db_type == "sqlite":
            self.db_classes = import_module("pepys_import.core.store.sqlite_db")
            driver = "sqlite+pysqlite"
        else:
            raise Exception(
                f"Unknown db_type {db_type} supplied, if specified should be one of 'postgres' or 'sqlite'"
            )

        # setup meta_class data
        self.meta_classes = {}
        self.setup_table_type_mapping()

        connection_string = "{}://{}:{}@{}:{}/{}".format(
            driver, db_username, db_password, db_host, db_port, db_name
        )
        self.engine = create_engine(connection_string, echo=False)

        if db_type == "postgres":
            BasePostGIS.metadata.bind = self.engine
        elif db_type == "sqlite":
            listen(self.engine, "connect", load_spatialite)
            BaseSpatiaLite.metadata.bind = self.engine

        self.missing_data_resolver = missing_data_resolver
        self.show_welcome = show_welcome
        self.show_status = show_status

        # caches of known data
        self.table_types = {}
        self.privacies = {}
        self.nationalities = {}
        self.datafile_types = {}
        self.datafiles = {}
        self.platform_types = {}
        self.platforms = {}
        self.sensor_types = {}
        self.sensors = {}
        self.comment_types = {}

        # TEMP list of values for defaulted IDs, to be replaced by missing info lookup mechanism
        self.default_user_id = 1  # DevUser

        # Instance attributes which are necessary for initialise method
        self.db_name = db_name
        self.db_type = db_type

        # use session_scope() to create a new session
        self.session = None

        # Branding Text
        if self.show_welcome:
            show_welcome_banner()
        if self.show_status:
            show_software_meta_info(__version__, self.db_type, self.db_name, db_host)
            print("---------------------------------")

    def initialise(self):
        """Create schemas for the database
        """

        if self.db_type == "sqlite":
            try:
                # Create geometry_columns and spatial_ref_sys metadata table
                with self.engine.connect() as conn:
                    conn.execute(select([func.InitSpatialMetaData()]))
                # Attempt to create schema if not present, to cope with fresh DB file
                BaseSpatiaLite.metadata.create_all(self.engine)
            except OperationalError:
                print(
                    "Error creating database schema, possible invalid path? ('"
                    + self.db_name
                    + "'). Quitting"
                )
                exit()
        elif self.db_type == "postgres":
            try:
                # Create extension for PostGIS first
                with self.engine.connect() as conn:
                    conn.execute("CREATE EXTENSION postgis;")
                #  ensure that create schema scripts created before create table scripts
                event.listen(
                    BasePostGIS.metadata,
                    "before_create",
                    CreateSchema("datastore_schema"),
                )
                BasePostGIS.metadata.create_all(self.engine)
            except OperationalError:
                print(f"Error creating database({self.db_name})! Quitting")
                exit()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        db_session = sessionmaker(bind=self.engine)
        self.session = db_session()
        try:
            yield self
            self.session.commit()
        except:
            self.session.rollback()
            raise
        finally:
            self.session.close()

    #############################################################
    # Other DataStore Methods

    def setup_table_type_mapping(self):
        """Setup a map of tables keyed by :class:`TableType`"""
        db_classes = dict(
            [
                (name, cls)
                for name, cls in self.db_classes.__dict__.items()
                if isinstance(cls, type)
                and (issubclass(cls, BasePostGIS) or issubclass(cls, BaseSpatiaLite))
                and cls.__name__ != "Base"
            ]
        )
        for table_type in TableTypes:
            self.meta_classes[table_type] = [
                cls
                for name, cls in db_classes.items()
                if db_classes[name].table_type == table_type
            ]

    def populate_reference(self, reference_data_folder=None):
        """Import given CSV file to the given reference table"""
        if reference_data_folder is None:
            reference_data_folder = os.path.join(DEFAULT_DATA_PATH)

        files = os.listdir(reference_data_folder)

        reference_tables = []
        # Create reference table list
        with self.session_scope() as session:
            self.setup_table_type_mapping()
            reference_table_objects = self.meta_classes[TableTypes.REFERENCE]
            for table_object in list(reference_table_objects):
                reference_tables.append(table_object.__tablename__)

        reference_files = [
            file
            for file in files
            if os.path.splitext(file)[0].replace(" ", "") in reference_tables
        ]
        for file in reference_files:
            # split file into filename and extension
            table_name, _ = os.path.splitext(file)
            possible_method = "add_to_" + table_name.lower().replace(" ", "_")
            method_to_call = getattr(self, possible_method, None)
            if method_to_call:
                with open(os.path.join(reference_data_folder, file), "r") as f:
                    reader = csv.reader(f)
                    # skip header
                    _ = next(reader)
                    with self.session_scope() as session:
                        for row in reader:
                            method_to_call(*row)
            else:
                print(f"Method({possible_method}) not found!")

    def populate_metadata(self, sample_data_folder=None):
        """Import CSV files from the given folder to the related Metadata Tables"""
        if sample_data_folder is None:
            sample_data_folder = os.path.join(DEFAULT_DATA_PATH)

        files = os.listdir(sample_data_folder)

        metadata_tables = []
        # Create metadata table list
        with self.session_scope() as session:
            self.setup_table_type_mapping()
            metadata_table_objects = self.meta_classes[TableTypes.METADATA]
            for table_object in list(metadata_table_objects):
                metadata_tables.append(table_object.__tablename__)

        metadata_files = [
            file for file in files if os.path.splitext(file)[0] in metadata_tables
        ]
        for file in sorted(metadata_files):
            # split file into filename and extension
            table_name, _ = os.path.splitext(file)
            possible_method = "add_to_" + table_name.lower().replace(" ", "_")
            method_to_call = getattr(self, possible_method, None)
            if method_to_call:
                with open(os.path.join(sample_data_folder, file), "r") as f:
                    reader = csv.reader(f)
                    # skip header
                    _ = next(reader)
                    with self.session_scope() as session:
                        for row in reader:
                            method_to_call(*row)
            else:
                print(f"Method({possible_method}) not found!")

    def populate_measurement(self, sample_data_folder=None):
        """Import CSV files from the given folder to the related Measurement Tables"""
        if sample_data_folder is None:
            sample_data_folder = DEFAULT_DATA_PATH

        files = os.listdir(sample_data_folder)

        measurement_tables = []
        # Create measurement table list
        measurement_table_objects = self.meta_classes[TableTypes.MEASUREMENT]
        for table_object in list(measurement_table_objects):
            measurement_tables.append(table_object.__tablename__)

        measurement_files = [
            file for file in files if os.path.splitext(file)[0] in measurement_tables
        ]
        import_from_csv(self, sample_data_folder, measurement_files)

    # End of Data Store methods
    #############################################################

    def add_to_entries(self, table_type_id, table_name):
        """
        Adds the specified entry to the :class:`Entry` table if not already present.

        :param table_type_id: Table Type ID
        :type table_type_id: Integer
        :param table_name: Name of table
        :type table_name: String
        :return: Created :class:`Entry` entity's entry_id
        :rtype: UUID
        """
        # ensure table type exists to satisfy foreign key constraint
        self.add_to_table_types(table_type_id, table_name)

        # No cache for entries, just add new one when called
        entry_obj = self.db_classes.Entry(
            table_type_id=table_type_id, created_user=self.default_user_id
        )

        self.session.add(entry_obj)
        self.session.flush()

        return entry_obj.entry_id

    def add_to_states(
        self,
        time,
        sensor,
        datafile,
        location=None,
        heading=None,
        course=None,
        speed=None,
        privacy=None,
    ):
        """
        Adds the specified state to the :class:`States` table if not already present.

        :param time: Timestamp of :class:`States`
        :type time: datetime
        :param sensor: Sensor of :class:`States`
        :type sensor: Sensor
        :param datafile: Datafile of :class:`States`
        :type datafile: Datafiles
        :param location: Location of :class:`States`
        :type location: Point
        :param heading: Heading of :class:`States` (Which converted to radians)
        :type heading: String
        :param course: Course of :class:`States`
        :type course:
        :param speed: Speed of :class:`States` (Which converted to m/sec)
        :type speed: String
        :param privacy: :class:`Privacies` of :class:`States`
        :type privacy: Privacies
        :return: Created :class:`States` entity
        :rtype: States
        """
        time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")

        sensor = self.search_sensor(sensor)
        datafile = self.search_datafile(datafile)
        privacy = self.search_privacy(privacy)

        if sensor is None or datafile is None:
            print(f"There is missing value(s) in '{sensor}, {datafile}'!")
            return

        heading_rads = None
        if heading:
            # heading is a string, turn into quantity. Convert to radians
            heading_quantity = float(heading) * unit_registry.knot
            heading_rads = heading_quantity.to(unit_registry.radians).magnitude

        speed_m_sec = None
        if speed:
            # speed is a string, turn into quantity. Convert to m/sec
            speed_quantity = float(speed) * unit_registry.knot
            speed_m_sec = speed_quantity.to(
                unit_registry.meter / unit_registry.second
            ).magnitude

        entry_id = self.add_to_entries(
            self.db_classes.States.table_type_id, self.db_classes.States.__tablename__
        )
        state_obj = self.db_classes.States(
            state_id=entry_id,
            time=time,
            sensor_id=sensor.sensor_id,
            location=location,
            heading=heading_rads,
            # course=course,
            speed=speed_m_sec,
            source_id=datafile.datafile_id,
            privacy_id=privacy.privacy_id,
        )
        self.session.add(state_obj)
        self.session.flush()

        return state_obj

    def add_to_sensors(self, name, sensor_type, host):
        """
        Adds the specified sensor to the :class:`Sensors` table if not already present.

        :param name: Name of sensor
        :type name: String
        :param sensor_type: Type of sensor
        :type sensor_type: :class:`SensorTypes`
        :param host: Platform of sensor
        :type host: Platforms
        :return: Created Sensors entity
        """
        sensor_type = self.search_sensor_type(sensor_type)
        host = self.search_platform(host)

        if sensor_type is None or host is None:
            print(f"There is missing value(s) in '{sensor_type}, {host}'!")
            return

        entry_id = self.add_to_entries(
            self.db_classes.Sensors.table_type_id, self.db_classes.Sensors.__tablename__
        )

        sensor_obj = self.db_classes.Sensors(
            sensor_id=entry_id,
            name=name,
            sensor_type_id=sensor_type.sensor_type_id,
            platform_id=host.platform_id,
        )
        self.session.add(sensor_obj)
        self.session.flush()

        return sensor_obj

    def add_to_datafiles(self, simulated, privacy, file_type, reference=None, url=None):
        """
        Adds the specified datafile to the Datafiles table if not already present.

        :param simulated: :class:`Datafiles` is simulated or not
        :type simulated: Boolean
        :param privacy: :class:`Privacies` of :class:`Datafiles`
        :type privacy: Privacies
        :param file_type: Type of :class:`Datafiles`
        :type file_type: String
        :param reference: Reference of :class:`Datafiles`
        :type reference: String
        :param url: URL of datafile
        :type url: String
        :return: Created :class:`Datafiles` entity
        :rtype: Datafiles
        """
        privacy = self.search_privacy(privacy)
        datafile_type = self.search_datafile_type(file_type)

        if privacy is None or datafile_type is None:
            print("There is missing value(s) in the data!")
            return

        entry_id = self.add_to_entries(
            self.db_classes.Datafiles.table_type_id,
            self.db_classes.Datafiles.__tablename__,
        )

        datafile_obj = self.db_classes.Datafiles(
            datafile_id=entry_id,
            simulated=bool(simulated),
            privacy_id=privacy.privacy_id,
            datafile_type_id=datafile_type.datafile_type_id,
            reference=reference,
            url=url,
        )

        self.session.add(datafile_obj)
        self.session.flush()

        return datafile_obj

    def add_to_platforms(self, name, nationality, platform_type, privacy):
        """
        Adds the specified platform to the Platforms table if not already present.

        :param name: Name of :class:`Platform`
        :type name: String
        :param nationality: Nationality of :class:`Platform`
        :type nationality: Nationalities
        :param platform_type: Type of :class:`Platform`
        :type platform_type: PlatformTypes
        :param privacy: :class:`Privacies` of :class:`Platform`
        :type privacy: Privacies
        :return: Created Platform entity
        :rtype: Platforms
        """
        nationality = self.search_nationality(nationality)
        platform_type = self.search_platform_type(platform_type)
        privacy = self.search_privacy(privacy)

        if nationality is None or platform_type is None or privacy is None:
            print("There is missing value(s) in the data!")
            return

        entry_id = self.add_to_entries(
            self.db_classes.Platforms.table_type_id,
            self.db_classes.Platforms.__tablename__,
        )

        platform_obj = self.db_classes.Platforms(
            platform_id=entry_id,
            name=name,
            nationality_id=nationality.nationality_id,
            platform_type_id=platform_type.platform_type_id,
            privacy_id=privacy.privacy_id,
        )

        self.session.add(platform_obj)
        self.session.flush()

        # add to cache and return created platform
        self.platforms[name] = platform_obj
        # should return DB type or something else decoupled from DB?
        return platform_obj

    #############################################################
    # Search/lookup functions

    def search_datafile_type(self, name):
        """Search for any datafile type with this name"""
        return (
            self.session.query(self.db_classes.DatafileTypes)
            .filter(self.db_classes.DatafileTypes.name == name)
            .first()
        )

    def search_datafile(self, name):
        """Search for any datafile with this name"""
        return (
            self.session.query(self.db_classes.Datafiles)
            .filter(self.db_classes.Datafiles.reference == name)
            .first()
        )

    # def search_datafile_by_id(self, id):
    #     # search for any datafile with this id
    #     return (
    #         self.session.query(self.db_classes.Datafile)
    #         .filter(self.db_classes.Datafile.datafile_id == str(id))
    #         .first()
    #     )

    def search_platform(self, name):
        """Search for any platform with this name"""
        return (
            self.session.query(self.db_classes.Platforms)
            .filter(self.db_classes.Platforms.name == name)
            .first()
        )

    def search_platform_type(self, name):
        """Search for any platform type with this name"""
        return (
            self.session.query(self.db_classes.PlatformTypes)
            .filter(self.db_classes.PlatformTypes.name == name)
            .first()
        )

    def search_nationality(self, name):
        """Search for any nationality with this name"""
        return (
            self.session.query(self.db_classes.Nationalities)
            .filter(self.db_classes.Nationalities.name == name)
            .first()
        )

    def search_sensor(self, name):
        """Search for any sensor type featuring this name"""
        return (
            self.session.query(self.db_classes.Sensors)
            .filter(self.db_classes.Sensors.name == name)
            .first()
        )

    def search_sensor_type(self, name):
        """Search for any sensor type featuring this name"""
        return (
            self.session.query(self.db_classes.SensorTypes)
            .filter(self.db_classes.SensorTypes.name == name)
            .first()
        )

    def search_privacy(self, name):
        """Search for any privacy with this name"""
        return (
            self.session.query(self.db_classes.Privacies)
            .filter(self.db_classes.Privacies.name == name)
            .first()
        )

    def search_table_type(self, table_type_id):
        """Search for any table type with this id"""
        return (
            self.session.query(self.db_classes.TableType)
            .filter(self.db_classes.TableType.table_type_id == table_type_id)
            .first()
        )

    #############################################################
    # New methods

    def get_datafile(self, datafile_name, datafile_type):
        """
        Adds an entry to the datafiles table of the specified name (path)
        and type if not already present.

        :param datafile_name:  Name of Datafile
        :type datafile_name: String
        :param datafile_type: Type of Datafile
        :type datafile_type: DatafileTypes
        :return:  Created Datafile entity
        :rtype: Datafiles
        """

        # return True if provided datafile exists
        def check_datafile(datafile):
            all_datafiles = self.session.query(self.db_classes.Datafiles).all()
            if next(
                (file for file in all_datafiles if file.reference == datafile), None,
            ):
                # A datafile already exists with that name
                return False

            return True

        self.add_to_datafile_types(datafile_type)
        self.add_to_privacies("NEW")

        if len(datafile_name) == 0:
            raise Exception("Datafile name can't be empty!")
        elif check_datafile(datafile_name):
            return self.add_to_datafiles(
                simulated=True,
                privacy="NEW",
                file_type=datafile_type,
                reference=datafile_name,
            )
        else:
            return (
                self.session.query(self.db_classes.Datafiles)
                .filter(self.db_classes.Datafiles.reference == datafile_name)
                .first()
            )

    def get_platform(
        self, platform_name, nationality=None, platform_type=None, privacy=None
    ):
        """
        Adds an entry to the platforms table for the specified platform
        if not already present.

        :param platform_name: Name of :class:`Platform`
        :type platform_name: String
        :param nationality: Name of :class:`Nationalities`
        :type nationality: Nationalities
        :param platform_type: Name of :class:`PlatformTypes`
        :type platform_type: PlatformTypes
        :param privacy: Name of :class:`Privacies`
        :type privacy: Privacies
        :return: Created Platforms entity
        """

        # return True if provided platform exists
        def check_platform(name):
            all_platforms = self.session.query(self.db_classes.Platforms).all()
            if next(
                (platform for platform in all_platforms if platform.name == name), None,
            ):
                # A platform already exists with that name
                return False

            return True

        if len(platform_name) == 0:
            raise Exception("Platform name can't be empty!")
        elif check_platform(platform_name):
            return self.add_to_platforms(
                name=platform_name,
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
            )
        else:
            return (
                self.session.query(self.db_classes.Platforms)
                .filter(self.db_classes.Platforms.name == platform_name)
                .first()
            )

    def get_status(
        self,
        report_measurement: bool = False,
        report_metadata: bool = False,
        report_reference: bool = False,
    ):
        """
        Provides a summary of the contents of the :class:`DataStore`.

        :param report_measurement: Boolean flag includes Metadata Tables
        :type report_measurement: Boolean
        :param report_metadata: Boolean flag includes Metadata Tables
        :type report_metadata: Boolean
        :param report_reference: Boolean flag includes Metadata Tables
        :type report_reference: Boolean
        :return: The summary of the contents of the :class:`DataStore`
        :rtype: TableSummarySet
        """

        table_summaries = []
        if report_measurement:
            # Create measurement table list
            measurement_table_objects = self.meta_classes[TableTypes.MEASUREMENT]
            for table_object in list(measurement_table_objects):
                ts = TableSummary(self.session, table_object)
                table_summaries.append(ts)

        if report_metadata:
            # Create metadata table list
            metadata_table_objects = self.meta_classes[TableTypes.METADATA]
            for table_object in list(metadata_table_objects):
                ts = TableSummary(self.session, table_object)
                table_summaries.append(ts)

        if report_reference:
            # Create reference table list
            reference_table_objects = self.meta_classes[TableTypes.REFERENCE]
            for table_object in list(reference_table_objects):
                ts = TableSummary(self.session, table_object)
                table_summaries.append(ts)

        table_summaries_set = TableSummarySet(table_summaries)

        return table_summaries_set

    def search_comment_type(self, name):
        """Search for any comment type featuring this name"""
        return (
            self.session.query(self.db_classes.CommentTypes)
            .filter(self.db_classes.CommentTypes.name == name)
            .first()
        )

    def add_to_comment_types(self, name):
        """
        Adds the specified comment type to the CommentTypes table if not already present

        :param name: Name of :class:`CommentTypes`
        :type name: String
        :return: Created entity of :class:`CommentTypes` table
        :rtype: CommentTypes
        """

        # check in cache for comment type
        if name in self.comment_types:
            return self.comment_types[name]

        # doesn't exist in cache, try to lookup in DB
        comment_types = self.search_comment_type(name)
        if comment_types:
            # add to cache and return looked up platform type
            self.comment_types[name] = comment_types
            return comment_types

        entry_id = self.add_to_entries(
            self.db_classes.CommentTypes.table_type_id,
            self.db_classes.CommentTypes.__tablename__,
        )
        # enough info to proceed and create entry
        comment_type = self.db_classes.CommentTypes(comment_type_id=entry_id, name=name)
        self.session.add(comment_type)
        self.session.flush()

        # add to cache and return created platform type
        self.comment_types[name] = comment_type
        # should return DB type or something else decoupled from DB?
        return comment_type

    # End of Measurements
    #############################################################
    # Reference Type Maintenance

    def add_to_table_types(self, table_type_id, table_name):
        """
        Adds the specified table type and name to the table types table if not already
        present.

        Returns:
            Created table type entity

        :param table_type_id: ID of :class:`TableType`
        :type table_type_id: Integer
        :param table_name: Name of :class:`TableType`
        :type table_name: String
        :return: Created :class:`TableType` entity
        :rtype: TableType
        """
        # check in cache for table type
        if table_type_id in self.table_types:
            return self.table_types[table_type_id]

        # doesn't exist in cache, try to lookup in DB
        table_types = self.search_table_type(table_type_id)
        if table_types:
            # add to cache and return
            self.table_types[table_type_id] = table_types
            return table_types

        # enough info to proceed and create entry
        table_type = self.db_classes.TableType(
            table_type_id=table_type_id, name=table_name
        )
        self.session.add(table_type)
        self.session.flush()

        # add to cache and return created table type
        self.table_types[table_type_id] = table_type
        # should return DB type or something else decoupled from DB?
        return table_type

    def add_to_platform_types(self, platform_type_name):
        """
        Adds the specified platform type to the platform types table if not already
        present.

        :param platform_type_name: Name of :class:`PlatformTypes`
        :type platform_type_name: String
        :return: Created :class:`PlatformTypes` entity
        :rtype: PlatformTypes
        """
        # check in cache for nationality
        if platform_type_name in self.platform_types:
            return self.platform_types[platform_type_name]

        # doesn't exist in cache, try to lookup in DB
        platform_types = self.search_platform_type(platform_type_name)
        if platform_types:
            # add to cache and return looked up platform type
            self.platform_types[platform_type_name] = platform_types
            return platform_types

        entry_id = self.add_to_entries(
            self.db_classes.PlatformTypes.table_type_id,
            self.db_classes.PlatformTypes.__tablename__,
        )
        # enough info to proceed and create entry
        platform_type = self.db_classes.PlatformTypes(
            platform_type_id=entry_id, name=platform_type_name
        )
        self.session.add(platform_type)
        self.session.flush()

        # add to cache and return created platform type
        self.platform_types[platform_type_name] = platform_type
        # should return DB type or something else decoupled from DB?
        return platform_type

    def add_to_nationalities(self, nationality_name):
        """
        Adds the specified nationality to the nationalities table if not already present

        :param nationality_name: Name of :class:`Nationalities`
        :type nationality_name: String
        :return: Created :class:`Nationalities` entity
        :rtype: Nationalities
        """
        # check in cache for nationality
        if nationality_name in self.nationalities:
            return self.nationalities[nationality_name]

        # doesn't exist in cache, try to lookup in DB
        nationalities = self.search_nationality(nationality_name)
        if nationalities:
            # add to cache and return looked up nationality
            self.nationalities[nationality_name] = nationalities
            return nationalities

        entry_id = self.add_to_entries(
            self.db_classes.Nationalities.table_type_id,
            self.db_classes.Nationalities.__tablename__,
        )
        # enough info to proceed and create entry
        nationality = self.db_classes.Nationalities(
            nationality_id=entry_id, name=nationality_name
        )
        self.session.add(nationality)
        self.session.flush()

        # add to cache and return created platform
        self.nationalities[nationality_name] = nationality
        # should return DB type or something else decoupled from DB?
        return nationality

    def add_to_privacies(self, privacy_name):
        """
        Adds the specified privacy entry to the :class:`Privacies` table if not already present.

        :param privacy_name: Name of :class:`Privacies`
        :type privacy_name: String
        :return: Created :class:`Privacies` entity
        :rtype: Privacies
        """
        # check in cache for privacy
        if privacy_name in self.privacies:
            return self.privacies[privacy_name]

        # doesn't exist in cache, try to lookup in DB
        privacies = self.search_privacy(privacy_name)
        if privacies:
            # add to cache and return looked up platform
            self.privacies[privacy_name] = privacies
            return privacies

        entry_id = self.add_to_entries(
            self.db_classes.Privacies.table_type_id,
            self.db_classes.Privacies.__tablename__,
        )
        # enough info to proceed and create entry
        privacy = self.db_classes.Privacies(privacy_id=entry_id, name=privacy_name)
        self.session.add(privacy)
        self.session.flush()

        # add to cache and return created platform
        self.privacies[privacy_name] = privacy
        # should return DB type or something else decoupled from DB?
        return privacy

    def add_to_datafile_types(self, datafile_type):
        """
        Adds the specified datafile type to the datafile types table if not already
        present.

        :param datafile_type: Name of :class:`DatafileTypes`
        :type datafile_type: String
        :return: Wrapped database entity for :class:`DatafileTypes`
        :rtype: DatafileTypes
        """
        # check in cache for datafile type
        if datafile_type in self.datafile_types:
            return self.datafile_types[datafile_type]

        # doesn't exist in cache, try to lookup in DB
        datafile_types = self.search_datafile_type(datafile_type)
        if datafile_types:
            # add to cache and return looked up datafile type
            self.datafile_types[datafile_type] = datafile_types
            return datafile_types

        entry_id = self.add_to_entries(
            self.db_classes.DatafileTypes.table_type_id,
            self.db_classes.DatafileTypes.__tablename__,
        )
        # proceed and create entry
        datafile_type_obj = self.db_classes.DatafileTypes(
            datafile_type_id=entry_id, name=datafile_type
        )

        self.session.add(datafile_type_obj)
        self.session.flush()

        # add to cache and return created datafile type
        self.datafile_types[datafile_type] = datafile_type_obj
        # should return DB type or something else decoupled from DB?
        return datafile_type_obj

    def add_to_sensor_types(self, sensor_type_name):
        """
        Adds the specified sensor type to the :class:`SensorTypes` table if not already present.

        :param sensor_type_name: Name of :class:`SensorTypes`
        :type sensor_type_name: String
        :return: Created :class:`SensorTypes` entity
        :rtype: SensorTypes
        """
        # check in cache for sensor type
        if sensor_type_name in self.sensor_types:
            return self.sensor_types[sensor_type_name]

        # doesn't exist in cache, try to lookup in DB
        sensor_types = self.search_sensor_type(sensor_type_name)
        if sensor_types:
            # add to cache and return looked up sensor type
            self.sensor_types[sensor_type_name] = sensor_types
            return sensor_types

        # enough info to proceed and create entry
        sensor_type = self.db_classes.SensorTypes(name=sensor_type_name)
        self.session.add(sensor_type)
        self.session.flush()

        # add to cache and return created sensor type
        self.sensor_types[sensor_type_name] = sensor_type
        # should return DB type or something else decoupled from DB?
        return sensor_type
