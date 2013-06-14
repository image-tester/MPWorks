import json
import logging
import os
import sys
from pymongo import MongoClient
from mpworks.drones.mp_vaspdrone import MPVaspDrone

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Jun 13, 2013'


if __name__ == '__main__':
    # get the directory containing the db file
    db_dir = os.environ['DB_LOC']
    db_path = os.path.join(db_dir, 'tasks_db.json')

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('MPVaspDrone')
    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setLevel(getattr(logging, 'INFO'))
    logger.addHandler(sh)

    with open(db_path) as f:
        db_creds = json.load(f)
        conn = MongoClient(db_creds['host'], db_creds['port'])
        db = conn[db_creds['database']]
        db.authenticate(db_creds['admin_user'], db_creds['admin_password'])
        coll = db[db_creds['collection']]

        print coll.count()

        """
        drone = MPVaspDrone(
            host=db_creds['host'], port=db_creds['port'],
            database=db_creds['database'], user=db_creds['admin_user'],
            password=db_creds['admin_password'],
            collection=db_creds['collection'], parse_dos=True,
            additional_fields={},
            update_duplicates=True)
        t_id, d = drone.assimilate(prev_dir, launches_coll=LaunchPad.auto_load().launches)
        """