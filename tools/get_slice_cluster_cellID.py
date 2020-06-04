from aisynphys.database import default_db as db
from sqlalchemy import and_
import numpy as np
import matplotlib.pyplot as plt
import pprint
from aisynphys import lims
import os
help(os.system)

expts = db.query(db.Experiment).join(db.Cell).join(db.Morphology).filter(db.Experiment.project_name.in_(['mouse V1 pre-production', 'mouse V1 coarse matrix'])).filter(db.Morphology.cortical_layer != None).all()

slices = list(set([e.slice.lims_specimen_name for e in expts]))

record={}
list_of_cell_ids_by_cluster_and_specimen=[]
for s in slices:
    record['specimen_id'] = s
    images = lims.specimen_images(s)
    for image in images:
        if image.get('treatment') =='DAPI':
            record['image_series'] = image.get('image_series')
    cluster_ids = lims.cell_cluster_ids(s)
    for cluster in cluster_ids:
        record['cluster_id'] = cluster
        cell_ids = lims.cluster_cells(int(cluster))
        cell_id_list=[]
        record['cell_ids'] = [x[0] for x in cell_ids if x[5] == 'pass']
        list_of_cell_ids_by_cluster_and_specimen.append(record.copy())
print(list_of_cell_ids_by_cluster_and_specimen[8:12])


