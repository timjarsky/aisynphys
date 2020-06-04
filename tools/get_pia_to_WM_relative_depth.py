import sys, argparse
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from shapely.geometry import Polygon, Point, LineString, LinearRing
from functools import partial
from allensdk.internal.core import lims_utilities as lu
from neuron_morphology.lims_apical_queries import get_data
import os
from neuron_morphology.transforms.pia_wm_streamlines.calculate_pia_wm_streamlines import run_streamlines
from neuron_morphology.vis import morphovis as mvis
from neuron_morphology.layered_point_depths.__main__ import setup_interpolator, step_from_node, tuplize
import shapely.affinity

#Copied from neuron_morphology since my argschema doesn't match theirs
from typing import Callable, List, Dict, Tuple, Union, Optional
from neuron_morphology.snap_polygons.types import (
    NicePathType, PathType, PathsType, ensure_path
)

QueryEngineType = Callable[[str], List[Dict]]

def query_for_layer_polygons(
    query_engine: QueryEngineType, 
    focal_plane_image_series_id: int
    ) -> List[Dict[str, Union[NicePathType, str]]]:
    """ Get all layer polygons for this image series
    """

    query = f"""
        select
            st.acronym as name,
            polygon.path as path
        from specimens sp
        join specimens spp on spp.id = sp.parent_id
        join image_series imser on imser.specimen_id = spp.id
        join sub_images si on si.image_series_id = imser.id
        join images im on im.id = si.image_id
        join treatments tm on tm.id = im.treatment_id
        join avg_graphic_objects layer on layer.sub_image_id = si.id
        join avg_group_labels label on label.id = layer.group_label_id
        join avg_graphic_objects polygon on polygon.parent_id = layer.id
        join structures st on st.id = polygon.cortex_layer_id
        where 
            imser.id = {focal_plane_image_series_id}
            and label.name in ('Cortical Layers')
            and tm.name = 'Biocytin' -- the polys are duplicated between 'Biocytin' and 'DAPI' images. Need only one of these
        """
    return [
        {
            "name": layer["name"],
            "path": ensure_path(layer["path"])
        }
        for layer in query_engine(query)
    ]

def distant_edge(poly, from_poly):
    cent_line = LineString([poly.centroid, from_poly.centroid])
    rect = poly.minimum_rotated_rectangle
    ref_pt = cent_line.intersection(rect.exterior)
    
    # Identify the nearest-neighbor points on the exterior rectangle
    # to the intersection with a line drawn between the two centroids
    # The other two points will be the farther set of corners
    #neighbor_rect_inds = []
    proj_ref = rect.exterior.project(ref_pt)
    post_dist = np.inf
    pre_dist = np.inf
    pre_ind = None
    post_ind = None
    for i, c in enumerate(rect.exterior.coords):
        c_dist = rect.exterior.project(Point(c))
        if c_dist < proj_ref:
            if np.abs(c_dist - proj_ref) < pre_dist:
                pre_dist = np.abs(c_dist - proj_ref)
                pre_ind = i
        else:
            if np.abs(c_dist - proj_ref) < post_dist:
                post_dist = np.abs(c_dist - proj_ref)
                post_ind = i

    farthest = []
    pre_pt = list(rect.exterior.coords)[pre_ind]
    post_pt = list(rect.exterior.coords)[post_ind]
    for c in rect.exterior.coords[:-1]:
        if c != pre_pt and c != post_pt:
            farthest.append(c)
            
    # Get the points on the polygon closest 
    corners = corners_for_farthest(poly, farthest)
    
    orig_ring = poly.exterior
    rev_ring = LinearRing(poly.exterior.coords[::-1])

    l_orig = line_between_corners(orig_ring, corners)
    l_rev = line_between_corners(rev_ring, corners)

    if l_orig.length > l_rev.length:
        return l_rev
    else:
        return l_orig

def corners_for_farthest(poly, farthest):
    corners = []
    for f in farthest:
        out_p = Point(f)
        d_to_poly = [out_p.distance(Point(c)) for c in poly.exterior.coords]
        min_d = np.argmin(d_to_poly)
        corner = list(poly.exterior.coords)[min_d]
        corners.append(corner)
    return corners

def line_between_corners(ring, corners):
    ind_list = []
    for i, c in enumerate(ring.coords):
        if c == corners[0] or c == corners[1]:
            ind_list.append(i)
        
    return LineString(ring.coords[ind_list[0]:ind_list[1] + 1])

def get_pia_to_WM_relative_depth(focal_plane_image_series_id, cell_id_list):
    
    os.environ["DBHOST"] = "limsdb2"
    os.environ["DBNAME"] = "lims2"
    os.environ["DBREADER"] = "limsreader"
    os.environ["DBPASSWORD"] = "limsro"

    engine = partial(
        lu.query, 
        host=os.getenv("DBHOST"), 
        port=5432, 
        database=os.getenv("DBNAME"), 
        user=os.getenv("DBREADER"), 
        password=os.getenv("DBPASSWORD")
    )

    # Get layer drawings from LIMS
    focal_plane_image_series_id = 609213086
    layers = query_for_layer_polygons(engine, focal_plane_image_series_id)

    # Pull out the top and bottom layers
    for l in layers:
        if l["name"] == "Layer1":
            poly_L1 = Polygon(l["path"])
        elif l["name"] == "Layer6b":
            poly_L6b = Polygon(l["path"])

    # Find the top and bottom edges
    top_edge = distant_edge(poly_L1, from_poly=poly_L6b)
    bottom_edge = distant_edge(poly_L6b, from_poly=poly_L1)

    # based on query in lims_apical_queries but remove requirement of reconstruction
    # specimen_ids = [869623521, 869623551, 869623570, 869623500]
    ids_str = ', '.join([str(sid) for sid in cell_id_list])
    query_for_soma = f"""
            SELECT DISTINCT sp.id as specimen_id, 'null', layert.name as path_type, poly.path, sc.resolution, 'null', 'null'
            FROM specimens sp
            JOIN biospecimen_polygons AS bsp ON bsp.biospecimen_id=sp.id
            JOIN avg_graphic_objects poly ON poly.id=bsp.polygon_id
            JOIN avg_graphic_objects layer ON layer.id=poly.parent_id
            JOIN avg_group_labels layert ON layert.id=layer.group_label_id
            AND layert.prevent_missing_polygon_structure=false
            JOIN sub_images AS si ON si.id=layer.sub_image_id
            AND si.failed=false
            JOIN images AS im ON im.id=si.image_id
            JOIN slides AS s ON s.id=im.slide_id
            JOIN scans AS sc ON sc.slide_id=s.id
            AND sc.superseded=false
            JOIN treatments t ON t.id = im.treatment_id AND t.id = 300080909 --Why?
            WHERE sp.id IN ({ids_str})
            ORDER BY sp.id
            """

    _, data = get_data(query_for_soma)

    pia_path_str = ",".join(["{},{}".format(x, y) for x, y in list(top_edge.coords)])
    wm_path_str = ",".join(["{},{}".format(x, y) for x, y in list(bottom_edge.coords)])

    specimen = data[int(cell_id_list[1])]

    depth_field, gradient_field, translation = run_streamlines(
            pia_path_str,
            wm_path_str,
            specimen["resolution"],
            None,
        )

    # set up interpolator for getting value from depth field
    depth_interp = setup_interpolator(
        depth_field, None, method="linear", 
        bounds_error=False, fill_value=None)

    record={}
    for k in data:
        record[k]= 1 - depth_interp(data[k]["soma_center"])[0]
        print(k, 1 - depth_interp(data[k]["soma_center"])[0])

    return record

if __name__ == '__main__':

    if len(sys.argv) > 3:
        print('You have specified too many arguments')
        print(sys.argv)
        sys.exit()
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_series_id', type=int)
    parser.add_argument('--cell_id_list', type=str)

    args = parser.parse_args(sys.argv[1:])
    image_series_id=args.image_series_id
    cell_id_list=[]
    cell_id_list=args.cell_id_list.split(',')
    get_pia_to_WM_relative_depth(image_series_id, cell_id_list)

