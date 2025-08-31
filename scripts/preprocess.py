import os
from src.preprocessor import Preprocessor


if __name__ == "__main__":
    preprocessor= Preprocessor()
    root = "/media/jseob/SSD_HEAD/renderme360/processed/0039/e0"
    preprocessor.run(calib_path = os.path.join(root, "calibration.json"),
                     save_dir=root)


