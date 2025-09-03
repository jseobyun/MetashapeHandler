import os
import sys
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(ROOT)
from src.visualizer import Visualizer




if __name__ == "__main__":

    vis = Visualizer()
    save_dir = "/home/jseob/Downloads/TEST/results/1115.CP790947"

    vis.run(save_dir, only_mesh=False)


