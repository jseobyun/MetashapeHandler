import os
import sys
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(ROOT)
from src.visualizer import Visualizer




if __name__ == "__main__":

    vis = Visualizer()
    save_dir = "/media/jseob/SSD_HEAD/renderme360/processed/0131/e0/results/000_from_calibrated"

    vis.run(save_dir, only_mesh=False)


