#!/usr/bin/env python3

import os
import json
import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone
from src.utils import make_cam

def create_intrinsic_xml(output_path, projection="frame", width=6000, height=4000,
                         f=9000.0, cx=0.0, cy=0.0, k1=0.0, k2=0.0, k3=0.0,
                         p1=0.0, p2=0.0, date=None):
    """
    Create an XML file with camera intrinsic parameters.

    Parameters:
    -----------
    output_path : str
        Path where the XML file will be saved
    projection : str
        Projection type (default: "frame")
    width : int
        Image width in pixels
    height : int
        Image height in pixels
    f : float
        Focal length
    cx : float
        Principal point x-coordinate offset
    cy : float
        Principal point y-coordinate offset
    k1, k2, k3 : float
        Radial distortion coefficients
    p1, p2 : float
        Tangential distortion coefficients
    date : str
        Date string in ISO format (default: current datetime)
    """

    # Create root element
    root = ET.Element("calibration")

    # Add elements
    ET.SubElement(root, "projection").text = projection
    ET.SubElement(root, "width").text = str(width)
    ET.SubElement(root, "height").text = str(height)
    ET.SubElement(root, "f").text = str(f)
    ET.SubElement(root, "cx").text = str(cx)
    ET.SubElement(root, "cy").text = str(cy)
    ET.SubElement(root, "k1").text = str(k1)
    ET.SubElement(root, "k2").text = str(k2)
    ET.SubElement(root, "k3").text = str(k3)
    ET.SubElement(root, "p1").text = str(p1)
    ET.SubElement(root, "p2").text = str(p2)

    # Add date
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ET.SubElement(root, "date").text = date

    # Create pretty-printed XML string
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")

    # Write to file
    with open(output_path, 'w') as f:
        f.write(xml_str)

    print(f"Created XML file: {output_path}")

class Preprocessor():
    def __init__(self):
        pass

    def run(self, calib_path, save_dir, format="renderme360"):
        intr_dir = os.path.join(save_dir, "intrinsics")
        extr_dir = os.path.join(save_dir, "extrinsics")
        os.makedirs(intr_dir, exist_ok=True)
        os.makedirs(extr_dir, exist_ok=True)

        with open(calib_path, 'r') as json_file:
            calib = json.load(json_file)

        ### ava256 format
        if format=="ava256":
            calib = calib["KRT"]            
            for data in calib:
                img_id = data["cameraId"]
                K = np.asarray(data["K"]).reshape(3, 3).astype(np.float32).transpose().copy()
                K[:2, :] /= 4
                dist = np.asarray(data["distortion"])
                T_kg = np.asarray(data["T"]).reshape(4,4).astype(np.float32).transpose().copy()
                T_kg[:3, -1] /= 1000
                T_gk = np.linalg.inv(T_kg)
                img_w = 667
                img_h = 1024
                

                f = np.sqrt(K[0,0] * K[1,1])
                cx = K[0,2]-img_w/2 # Metashape uses principal point in offset shape.
                cy = K[1,2]-img_h/2 # Metashape uses principal point in offset shape.
                k1 = dist[0]
                k2 = dist[1]
                p1 = dist[2]
                p2 = dist[3]
                k3 = 0

                save_intr_path = os.path.join(intr_dir, f"cam{img_id}_intrinsic.xml")
                save_extr_path = os.path.join(extr_dir, f"cam{img_id}_extrinsic.npy")

                create_intrinsic_xml(save_intr_path,
                                    projection="frame",
                                    width=img_w,
                                    height=img_h,
                                    f=f,
                                    cx=cx,
                                    cy=cy,
                                    k1=k1,
                                    k2=k2,
                                    p1=p1,
                                    p2=p2,
                                    k3=k3)
                np.save(save_extr_path, T_gk)



        ### renderme360 format
        if format=="renderme360":
            img_ids = list(calib.keys())
            Ks = []
            T_gks = []
            for img_id in img_ids:
                K = np.asarray(calib[img_id]["K"]).reshape(3, 3).astype(np.float32)
                dist = np.asarray(calib[img_id]["dist"]).reshape(-1)
                T_gk = np.asarray(calib[img_id]["T_gk"]).reshape(4, 4).astype(np.float32)
                img_w = calib[img_id]["img_w"]
                img_h = calib[img_id]["img_h"]
                f = np.sqrt(K[0,0] * K[1,1])
                cx = K[0,2]-img_w/2 # Metashape uses principal point in offset shape.
                cy = K[1,2]-img_h/2 # Metashape uses principal point in offset shape.
                k1 = dist[0]
                k2 = dist[1]
                p1 = dist[2]
                p2 = dist[3]
                k3 = dist[4]

                save_intr_path = os.path.join(intr_dir, f"{img_id}_intrinsic.xml")
                save_extr_path = os.path.join(extr_dir, f"{img_id}_extrinsic.npy")

                create_intrinsic_xml(save_intr_path,
                                    projection="frame",
                                    width=img_w,
                                    height=img_h,
                                    f=f,
                                    cx=cx,
                                    cy=cy,
                                    k1=k1,
                                    k2=k2,
                                    p1=p1,
                                    p2=p2,
                                    k3=k3)
                np.save(save_extr_path, T_gk)


