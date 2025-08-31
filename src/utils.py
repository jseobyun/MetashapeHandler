import numpy as np
import open3d as o3d

def apply_T(T, points):
    if len(T.shape) != 2 or len(points.shape) != 2:
        raise Exception("ERROR : the dimensions of transformation matrix and points are wrong.")

    points_ = np.matmul(T[:3, :3], points.transpose(1, 0)).transpose(1, 0) + T[:3, -1].reshape(-1, 3)
    return points_

def make_origin(T_gk=np.eye(4), scale=1):
    points = np.array([[0, 0, 0],
                       [1, 0, 0],
                       [0, 1, 0],
                       [0, 0, 1]]).astype(np.float32)
    if isinstance(scale, list):
        points[:, 0] *= scale[0]
        points[:, 1] *= scale[1]
        points[:, 2] *= scale[2]
    else:
        points = points * scale


    points = apply_T(T_gk, points)
    origin_line = [[0, 1], [0, 2], [0, 3]]
    origin_color = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]

    origin = o3d.geometry.LineSet(
        points=o3d.utility.Vector3dVector(points),
        lines=o3d.utility.Vector2iVector(origin_line),
    )
    origin.colors = o3d.utility.Vector3dVector(origin_color)
    return origin


def make_cam(T_gk, scale=0.05):
    camera_line = [[0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [2, 3], [3, 4], [4, 1]]

    green = (0, 1, 0)
    red = (1, 0, 0)
    camera_colors = [green for _ in range(8)]
    camera_colors[4] = red

    T = T_gk
    k = scale / 40
    camera_points = np.array([[0, 0, 0],
                              [-17 * k, -10 * k, 40 * k],
                              [17 * k, -10 * k, 40 * k],
                              [17 * k, 10 * k, 40 * k],
                              [-17 * k, 10 * k, 40 * k],
                              ])
    camera_points = apply_T(T, camera_points)
    camera = o3d.geometry.LineSet(
        points=o3d.utility.Vector3dVector(camera_points),
        lines=o3d.utility.Vector2iVector(camera_line),
    )

    camera.colors = o3d.utility.Vector3dVector(camera_colors)
    return camera
