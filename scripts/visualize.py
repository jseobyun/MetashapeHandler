import os
import sys
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(ROOT)
from src.visualizer import Visualizer




if __name__ == "__main__":

    vis = Visualizer()
    save_dir = "/media/jseob/SSD_HEAD/ava256/20210817--0900--NRE683/decoder/results"

    vis.run(save_dir, only_mesh=False)


