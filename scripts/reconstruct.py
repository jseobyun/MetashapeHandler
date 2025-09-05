import os
import sys
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(ROOT)
from src.reconstructor import Reconstructor




if __name__ == "__main__":

    recon = Reconstructor(
        calibration_level=0,  # [High 0 1 2 3 4 Low], image resolution control
        mesh_level=1,  # [High 0 1 2 3 4 Low], MVS reoslution control
        texture_size=4096,
        bbox_dim=[2, 2, 2],  # width height depth, height is updirection
    )

    root = "/media/jseob/3D-PHOTO-03/k_hairstyle_raw/Training/masked"
    style_names = sorted(os.listdir(root))
    for style_name in style_names:
        subj_names = sorted(os.listdir(os.path.join(root, style_name)))
        for subj_name in subj_names:

            img_dir = os.path.join(root, style_name, subj_name)
            save_dir = img_dir.replace("masked", "results")            

            img_names = sorted(os.listdir(img_dir))
            img_paths = [os.path.join(img_dir, img_name) for img_name in img_names]

            # recon.run(img_paths, save_dir, init_dir="/media/jseob/SSD_HEAD/renderme360/processed/0039/e0/")
            recon.run(img_paths, save_dir, share_intrinsic=False)

    


