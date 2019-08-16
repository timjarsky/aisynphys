"""
A database holding results of manual analyses
"""

from multipatch_analysis.database.database import declarative_base, make_table
from multipatch_analysis.database import Database
from multipatch_analysis import config

DataNotesORMBase = declarative_base()


PairNotes = make_table(
    name='pair_notes',
    comment="Manually verified fits to average synaptic responses",
    columns=[
        ('expt_id', 'str', 'Unique experiment identifier (acq_timestamp)', {'index': True}),
        ('pre_cell_id', 'str', 'external id of presynaptic cell'),
        ('post_cell_id', 'str', 'external id of postsynaptic cell'),
        ('notes','object', 'pair data dict which includes synapse call, initial fit parameters, output fit parameters, comments, etc'),
    ],
    ormbase=DataNotesORMBase,
)


db = Database(config.synphys_db_host, config.synphys_db_host_rw, "data_notes", DataNotesORMBase)

db.create_tables()


def get_pair_notes(expt_id, pre_cell_id, post_cell_id, session=None):
    if session is None:
        session = db.session()

    q = db.query(PairNotes.notes)
    q = q.filter(PairNotes.expt_id==expt_id)
    q = q.filter(PairNotes.pre_cell_id==pre_cell_id)
    q = q.filter(PairNotes.post_cell_id==post_cell_id)
    
    recs = q.all()
    if len(recs) == 0:
        return None
    elif len(recs) > 1:
        raise Exception("Multiple records found in pair_notes for pair %s %s %s!" % (expt_id, pre_cell_id, post_cell_id))
    return recs[0]
