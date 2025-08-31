import os
import cv2
import trimesh
import logging
import numpy as np
import open3d as o3d
from src.utils import apply_T, make_cam, make_origin

logging.basicConfig(
    format = '%(levelname)s:%(message)s',
    level=logging.INFO
)

class Visualizer():
    def __init__(self, width=None, height=None):
        pass

    def load_mesh(self, obj_path, mesh_coord_changer_path, compute_normals=False, enable_post_processing=False):
        obj = o3d.io.read_triangle_mesh(obj_path, enable_post_processing=enable_post_processing)
        mesh_coord_changer = np.load(mesh_coord_changer_path).reshape(4, 4)

        vertices = np.asarray(obj.vertices)
        vertices = apply_T(mesh_coord_changer, vertices)
        obj.vertices = o3d.utility.Vector3dVector(vertices)

        if compute_normals:
            obj.compute_vertex_normals()
        return obj

    def load_cameras(self, extrinsic_dir, scale=0.1):

        extrinsic_names = sorted(os.listdir(extrinsic_dir))
        cameras = []
        for extrinsic_name in extrinsic_names:
            T_gk = np.load(os.path.join(extrinsic_dir, extrinsic_name))
            cameras.append(make_cam(T_gk, scale=0.1))
        return cameras






    def run(self, save_dir, only_mesh=False, render=False):
        obj_path = os.path.join(save_dir, "mesh.obj")
        mesh_coord_changer_path = os.path.join(save_dir, "mesh_coord_changer.npy")
        mesh = self.load_mesh(obj_path, mesh_coord_changer_path, compute_normals=True)

        cameras = self.load_cameras(os.path.join(save_dir, "extrinsics"), scale=0.1)
        origin = make_origin(np.eye(4), scale=1)

        if only_mesh:
            o3d.visualization.draw_geometries([mesh])
        else:
            o3d.visualization.draw_geometries(cameras + [mesh, origin])