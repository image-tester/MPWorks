import gridfs
from fireworks import FireTaskBase
import json
import os
from pymongo import MongoClient
from fireworks.core.firework import FWAction
from fireworks.utilities.fw_serializers import FWSerializable
from monty.os.path import zpath
from monty.json import jsanitize
from mpworks.snl_utils.mpsnl import get_meta_from_structure
from mpworks.workflows.wf_utils import get_loc, get_block_part
from pymatgen import Structure
from pymatgen.electronic_structure.bandstructure import BandStructure
from pymatgen.electronic_structure.boltztrap import BoltztrapRunner, BoltztrapAnalyzer
from pymatgen.io.vaspio.vasp_output import Vasprun

__author__ = 'Geoffroy Hautier, Anubhav Jain'
__copyright__ = 'Copyright 2014, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 24, 2014'


class BoltztrapRunTask(FireTaskBase, FWSerializable):
    _fw_name = "Boltztrap Run Task"

    def run_task(self, fw_spec):

        # get the band structure and nelect from files
        """
        prev_dir = get_loc(fw_spec['prev_vasp_dir'])
        vasprun_loc = zpath(os.path.join(prev_dir, 'vasprun.xml'))
        kpoints_loc = zpath(os.path.join(prev_dir, 'KPOINTS'))

        vr = Vasprun(vasprun_loc)
        bs = vr.get_band_structure(kpoints_filename=kpoints_loc)
        """

        # get the band structure and nelect from DB
        block_part = get_block_part(fw_spec['prev_vasp_dir'])

        db_dir = os.environ['DB_LOC']
        assert isinstance(db_dir, object)
        db_path = os.path.join(db_dir, 'tasks_db.json')
        with open(db_path) as f:
            creds = json.load(f)
            connection = MongoClient(creds['host'], creds['port'])
            tdb = connection[creds['database']]
            tdb.authenticate(creds['admin_user'], creds['admin_password'])

            m_task = tdb.tasks.find_one({"dir_name": block_part}, {"calculations": 1, "task_id": 1})
            nelect = m_task['calculations'][0]['input']['parameters']['NELECT']
            bs_id = m_task['calculations'][0]['band_structure_fs_id']
            print bs_id, type(bs_id)
            fs = gridfs.GridFS(tdb, 'band_structure_fs')
            bs_dict = json.loads(fs.get(bs_id).read())
            bs_dict['structure'] = m_task['calculations'][0]['output']['crystal']
            bs = BandStructure.from_dict(bs_dict)
            print 'Band Structure found:', bool(bs)
            print nelect

            # run Boltztrap
            runner = BoltztrapRunner(bs, nelect)
            dir = runner.run(path_dir=os.getcwd())

            # put the data in the database
            bta = BoltztrapAnalyzer.from_files(dir)
            data = bta.as_dict()
            data.update(get_meta_from_structure(bs._structure))
            data['snlgroup_id'] = fw_spec['snlgroup_id']
            data['run_tags'] = fw_spec['run_tags']
            data['snl'] = fw_spec['mpsnl']
            data['dir_name_full'] = dir
            data['dir_name'] = get_block_part(dir)
            data['task_id'] = m_task['task_id']
            data['hall'] = {}  # remove because it is too large and not useful
            data['hall_doping'] = {}  # remove because it is too large and not useful
            tdb.boltztrap.insert(jsanitize(data))

        update_spec = {'prev_vasp_dir': fw_spec['prev_vasp_dir'],
                       'boltztrap_dir': os.getcwd(),
                       'prev_task_type': fw_spec['task_type'],
                       'mpsnl': fw_spec['mpsnl'],
                       'snlgroup_id': fw_spec['snlgroup_id'],
                       'run_tags': fw_spec['run_tags'], 'parameters': fw_spec.get('parameters')}

        return FWAction(update_spec=update_spec)