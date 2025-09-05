import os
import sys
from tqdm import tqdm
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.preprocessor import Preprocessor


if __name__ == "__main__":
    # preprocessor= Preprocessor(format="renderme360")
    # root = "/media/jseob/SSD_HEAD/renderme360/processed/0039/e0"
    # preprocessor.run(calib_path = os.path.join(root, "calibration.json"), save_dir=root)

    preprocessor= Preprocessor()
    root = "/media/jseob/SSD_HEAD/ava256"

    subj_names = sorted(os.listdir(root))
    for subj_name in tqdm(subj_names):
        subj_dir = os.path.join(root, subj_name, "decoder")
        preprocessor.run(
            calib_path = os.path.join(subj_dir, "camera_calibration.json"), 
            save_dir=subj_dir, 
            format="ava256")


