import os
import math
import time
import logging
import trimesh
import numpy as np
import Metashape as ms
import open3d as o3d

from PIL import Image, ImageOps
from src.utils import make_cam, make_origin

logging.basicConfig(
    format='%(levelname)s:%(message)s',
    level=logging.INFO
)


class Reconstructor():
    def __init__(self,
                 calibration_level,
                 mesh_level,
                 texture_size=8192,  # 8k
                 bbox_dim=[1.5, 2, 1.5],  # bbox width x, height y, depth z
                 ):

        self.calibration_level = self.decode_level(calibration_level, isdepth=False)
        self.mesh_level = self.decode_level(mesh_level, isdepth=True)
        self.texture_size = texture_size
        self.bbox_dim = bbox_dim

    def decode_level(self, level, isdepth=False):
        ## sfm   0 1 2 4 8
        ## depth 1 2 4 8 16
        downscale = None
        if level == 0:  # highest
            downscale = 0 if not isdepth else 1
        elif level == 1:  # high
            downscale = 1 if not isdepth else 2
        elif level == 2:
            downscale = 2 if not isdepth else 4
        elif level == 3:
            downscale = 4 if not isdepth else 8
        elif level == 4:
            downscale = 8 if not isdepth else 16
        else:
            logging.error("Reconstruction level is out of range. Choose among  High-to-Low [0, 1, 2, 3, 4]")
            raise Exception("Reconstruction stops.")
        return downscale

    def inspect_inputs(self, img_inputs):
        img_paths = []
        if not isinstance(img_inputs, list):
            logging.error("Input should be a list of image paths")
            raise Exception("Reconstruction stops.")
        else:
            for img_input in img_inputs:
                if isinstance(img_input, str):
                    img_path = img_input
                    if not img_path.lower().endswith(".jpg") and not img_path.lower().endswith(".png"):
                        logging.error(f"{img_path} is not image file.")
                        raise Exception("Reconstruction stops.")

                    if not os.path.exists(img_path):
                        logging.error(f"{img_path} does not exists. Please check images.")
                        raise Exception("Reconstruction stops.")
                    else:
                        img_paths.append(img_path)
                else:
                    logging.error("Input type should be string for image path.")
                    raise Exception("Reconstruction stops.")

        logging.info(f"The number of images : {len(img_paths)}")
        return sorted(img_paths)

    def print_processing_time(self, start, end):
        elapsed_time = end - start
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        logging.info(f"Processing time : {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d} hmr")

    def run(self, img_inputs, save_dir, init_dir=None):
        start_time = time.time()
        '''
        Data inspection
        '''

        img_paths = self.inspect_inputs(img_inputs)

        '''
        Metashape preparation
        '''
        doc = ms.Document()
        chunk = doc.addChunk()

        chunk.addPhotos(img_paths)

        # initialization with precalibrated files
        if init_dir is not None:
            # Assign calibration settings to sensors
            init_intr_dir = os.path.join(init_dir, "intrinsics")

            for camera in chunk.cameras:
                # image_name works as camera ID
                image_name = os.path.splitext(os.path.basename(camera.photo.path))[0]

                # Create a new sensor
                sensor = chunk.addSensor()
                sensor.label = image_name
                sensor.type = ms.Sensor.Type.Frame

                # Get image dimensions using Pillow
                image_path = camera.photo.path
                with Image.open(image_path) as img:
                    sensor.width, sensor.height = img.size

                # Load calibration settings from the XML file
                calib_file = os.path.join(init_intr_dir, f"{image_name}_intrinsic.xml")
                calibration = ms.Calibration()
                calibration.load(calib_file)
                sensor.user_calib = calibration
                sensor.fixed = True  # make it True if you want to fix intrinsic parameters.

                # Assign the sensor to the camera
                camera.sensor = sensor
        # initialization from scratch
        else:
            for camera in chunk.cameras:
                # Extract image name without extension
                image_name = os.path.splitext(os.path.basename(camera.photo.path))[0]

                # Create a new sensor
                sensor = chunk.addSensor()
                sensor.label = image_name
                sensor.type = ms.Sensor.Type.Frame

                # Get image dimensions using Pillow
                image_path = camera.photo.path
                with Image.open(image_path) as img:
                    sensor.width, sensor.height = img.size

                # Assign the sensor to the camera
                camera.sensor = sensor

        '''
        Metashape run
        '''
        logging.info("Reconstruction starts...")

        # feature point extraction matching + building tracks.
        chunk.matchPhotos(downscale=self.calibration_level,
                          keypoint_limit=40000, # increase this if more feature points are required. Processing time will be increased together.
                          tiepoint_limit=10000, # increase this if more feature points are required. Processing time will be increased together.
                          filter_mask=False,
                          generic_preselection=True,
                          reference_preselection=True,
                          #reference_preselection_mode=ms.ReferencePreselectionMode.ReferencePreselectionSequential,
                          reference_preselection_mode=ms.ReferencePreselectionMode.ReferencePreselectionSource, # change it to above ...Sequential if your images are sorted by camera sequence.
                          )

        # initialize camera poses and parameters.
        chunk.alignCameras()

        if init_dir is not None:
            # refine intrinsic parameters
            chunk.optimizeCameras(adaptive_fitting=True)

        '''
        Heuristic trick for using pre-calibrated parameters.
        
        Based on my experience, there is no Metashape's official support for precalibrated extrinsic parameters.
        (Only precalibrated intrinsic parameters are supported. please see the line 122.)
        
        As as result, my following implementation uses simple trick.
        
        1) replace the camera poses to precalibrate extrinsic parameters.
        2) transform the (pre-calibrated) cameras into chunk.region coordinate system.
           -> Updating region to precalibrated setting is ideal but I've failed to find how to update region.            
        3) reconstruct the mesh
        4) transform back into original coordinate of precalibrated setting with mesh_coord_changer                  
        '''
        mesh_coord_changer = np.eye(4)
        if init_dir is not None:
            region = chunk.region # this is working volume of Metashape. it should cover the whole cameras.

            # load precalibrated camera pose : cam-to-world noted as T_gk
            init_extr_dir = os.path.join(init_dir, "extrinsics")
            center = np.asarray(region.center).reshape(-1) # the center of the region
            rot = np.asarray(region.rot).reshape(3, 3) # the coordinate axes of chunk.region
            size = np.asarray(region.size).reshape(3) # bounding box edge lengths in xyz order

            T_gk = np.eye(4) # cam-to-world
            T_gk[:3, :3] = rot
            T_gk[:3, -1] = center

            mesh_coord_changer = np.linalg.inv(T_gk)
            for cam_idx, camera in enumerate(chunk.cameras):
                # Extract image name without extension
                image_name = os.path.splitext(os.path.basename(camera.photo.path))[0]
                # extrinsic add
                m = np.load(os.path.join(init_extr_dir, image_name + "_extrinsic.npy")).reshape(4, 4)
                # transform pre-calibrated camera into chunk.region's coordinate system.
                m = T_gk @ m
                transform = ms.Matrix([[m[0, 0], m[0, 1], m[0, 2], m[0, 3]],
                                       [m[1, 0], m[1, 1], m[1, 2], m[1, 3]],
                                       [m[2, 0], m[2, 1], m[2, 2], m[2, 3]],
                                       [m[3, 0], m[3, 1], m[3, 2], m[3, 3]]])
                # update camera
                camera.transform = transform

            # update region.center and size to cover pre-calibrated camera system in chunk.region coordinate system.
            cam_center = 0
            for camera in chunk.cameras:
                cam_center += np.asarray(camera.transform).reshape(4, 4)[:3, -1]
            cam_center = cam_center / len(chunk.cameras)

            region.center = ms.Vector([cam_center[0], cam_center[1], cam_center[2]])
            region.size = ms.Vector([self.bbox_dim[0], self.bbox_dim[1], self.bbox_dim[2]])
            chunk.region = region
            chunk.updateTransform()

        ### feature matching and SfM
        chunk.buildDepthMaps(downscale=self.mesh_level, filter_mode=ms.MildFiltering)  # ms.AggressiveFiltering
        chunk.buildModel(source_data=ms.DepthMapsData)
        chunk.buildUV(texture_size=self.texture_size)
        chunk.buildTexture(texture_size=self.texture_size)
        # chunk.buildPointCloud()

        '''
        Save
        '''
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
            logging.info(f"{save_dir} is created.")

        intr_dir = os.path.join(save_dir, "intrinsics")
        extr_dir = os.path.join(save_dir, "extrinsics")
        os.makedirs(intr_dir, exist_ok=True)
        os.makedirs(extr_dir, exist_ok=True)

        for sensor in chunk.sensors:
            if sensor.label == "unknown":
                continue
            calib_path = os.path.join(intr_dir, f"{sensor.label}_intrinsic.xml")
            sensor.calibration.save(calib_path)

        for camera in chunk.cameras:
            transform_path = os.path.join(extr_dir, f"{camera.label}_extrinsic.npy")
            transform = mesh_coord_changer @ np.asarray(camera.transform).reshape(4, 4)
            np.save(transform_path, transform)

        mesh_path = os.path.join(save_dir, "mesh.obj")
        np.save(os.path.join(save_dir, "mesh_coord_changer.npy"), mesh_coord_changer)
        # pcd_path = os.path.join(save_dir, "sparse.ply")

        # chunk.exportPointCloud(pcd_path)
        chunk.exportModel(path=mesh_path, format=ms.ModelFormat.ModelFormatOBJ, crs=chunk.crs)

        end_time = time.time()
        self.print_processing_time(start_time, end_time)


