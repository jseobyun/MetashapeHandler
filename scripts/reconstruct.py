import os
import sys
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(ROOT)
from src.reconstructor import Reconstructor




if __name__ == "__main__":

    recon = Reconstructor(
        calibration_level=0,  # [High 0 1 2 3 4 Low], image resolution control
        mesh_level=1,  # [High 0 1 2 3 4 Low], MVS reoslution control
        texture_size=8192,
        bbox_dim=[1.5, 1.5, 1.5],  # width height depth, height is updirection
    )

    img_dir = "/home/jseob/Downloads/TEST/rgbas/1115.CP790947"
    save_dir = img_dir.replace("rgbas", "results")
    os.makedirs(save_dir, exist_ok=True)

    img_names = sorted(os.listdir(img_dir))
    img_paths = [os.path.join(img_dir, img_name) for img_name in img_names]

    # recon.run(img_paths, save_dir, init_dir="/media/jseob/SSD_HEAD/renderme360/processed/0039/e0/")
    recon.run(img_paths, save_dir, init_dir=None, share_intrinsic=True)

    # vis.run(save_dir)


