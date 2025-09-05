import os
import sys
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(ROOT)
from src.reconstructor import Reconstructor




if __name__ == "__main__":

    recon = Reconstructor(
        calibration_level=0,  # [High 0 1 2 3 4 Low], image resolution control
        mesh_level=0,  # [High 0 1 2 3 4 Low], MVS reoslution control
        texture_size=4096,
        bbox_dim=[5, 5, 5],  # width height depth, height is updirection
    )

    img_dir = "/media/jseob/SSD_HEAD/ava256/20210817--0900--NRE683/decoder/image_jpg/043131"
    save_dir = "/media/jseob/SSD_HEAD/ava256/20210817--0900--NRE683/decoder/results"
    init_dir = "/media/jseob/SSD_HEAD/ava256/20210817--0900--NRE683/decoder"

    img_names = sorted(os.listdir(img_dir))
    img_paths = [os.path.join(img_dir, img_name) for img_name in img_names]

    # recon.run(img_paths, save_dir, init_dir="/media/jseob/SSD_HEAD/renderme360/processed/0039/e0/")
    recon.run(img_paths, save_dir, init_dir=init_dir, share_intrinsic=False, format="ava256", vis=True)

    


