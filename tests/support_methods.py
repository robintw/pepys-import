from sqlalchemy.orm import sessionmaker
from tabulate import tabulate

from pepys_import.core.store.sqlite_db import State, Platform, Sensor

class Support_Methods():
    def count_states(self, data_store):
        '''
        return the number of State records present in the database
        '''
        engine = data_store.engine
        Session = sessionmaker(bind = engine)
        session = Session()
        numStates = session.query(State).count()
        return numStates

    def list_states(self, data_store):
        '''
        return the number of State records present in the database
        '''
        engine = data_store.engine
        Session = sessionmaker(bind = engine)
        session = Session()
        result = session.query(State).all()

        headers = "Id", "Time", "Sensor", "Location", "heading", "Speed", "datafile", "privacy"

        rows = []
        for row in result:
            rows.append([row.state_id,row.time,row.sensor_id, row.location, row.heading,
            row.speed, row.datafile_id, row.privacy_id])
        res = tabulate(rows, headers=headers)

        return res

    def list_platforms(self, data_store):
        '''
        return the number of State records present in the database
        '''
        engine = data_store.engine
        Session = sessionmaker(bind = engine)
        session = Session()
        result = session.query(Platform).all()

        headers = "Id", "Name", "Platform-Type", "Nationality"

        rows = []
        for row in result:
            rows.append([row.platform_id,row.name,row.platform_type_id, row.nationality_id,])
        res = tabulate(rows, headers=headers)

        return res


    def list_sensors(self, data_store):
        '''
        return the number of State records present in the database
        '''
        engine = data_store.engine
        Session = sessionmaker(bind = engine)
        session = Session()
        result = session.query(Sensor).all()

        headers = "Id", "Name", "Sensor-Type", "Platform-id"

        rows = []
        for row in result:
            rows.append([row.sensor_id,row.name,row.sensor_type_id, row.platform_id,])
        res = tabulate(rows, headers=headers)

        return res
