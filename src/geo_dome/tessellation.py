import numpy as np
from numba import njit
from numba.typed import Dict
from typing import Union
import math

try:
    from geo_dome.neighbourhood_search import *
except:
    from neighbourhood_search import *

SCALE = 1


@njit
def find_adjacent_triangles(triangles: np.ndarray, vertices: np.ndarray) -> np.ndarray:
    """Finds adjacent triangles for a given point

    Args:
        triangles (np.ndarray): The list of triangles in the dome
        vertices (np.ndarray): The vertices (index) to find the adjacent triangles for

    Returns:
        np.ndarray: List of indices for triangles in the array
    """
    found_triangles = np.zeros((len(triangles)), dtype=np.int64)
    found_index = 0

    for i in range(len(triangles)):
        t = triangles[i]
        if t[0] in vertices or t[1] in vertices or t[2] in vertices:
            found_triangles[found_index] = i
            found_index += 1

    resized = np.zeros(found_index, dtype=np.int64)
    for i in range(found_index):
        resized[i] = found_triangles[i]

    return resized


@njit
def is_zero(coord, message="") -> None:
    """Debug method, checks if a coord is at origin

    Args:
        coord (np array): coordinate to check
        message (str, optional): descriptive message when triggered. Defaults to "".
    """
    if (coord == np.array([0, 0, 0])).all():
        print("Something is zero that shouldn't be: " + message)


@njit
def normalise_length(coords: np.ndarray) -> np.ndarray:
    """Normalises the distance from origin of a coord. Multiplies by the
    frequency the icosphere to avoid floating point precision errors

    Args:
        coords (np.ndarray): coordinate to normalise

    Returns:
        np.ndarray: normalised coordinate
    """
    length = math.sqrt(
        math.pow(coords[0], 2) + math.pow(coords[1], 2) + math.pow(coords[2], 2)
    )

    is_zero(coords, "normalise")

    return np.array(
        [
            (coords[0] / length) * SCALE,
            (coords[1] / length) * SCALE,
            (coords[2] / length) * SCALE,
        ]
    )


@njit
def get_middle_coords(v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
    """Gets the midpoint between two coords

    Args:
        v1 (np.ndarray): coord 1
        v2 (np.ndarray): coord 2

    Returns:
        np.ndarray: the midpoint (not normalised)
    """
    ret = np.array(
        [(v2[0] + v1[0]) / 2, (v2[1] + v1[1]) / 2, (v2[2] + v1[2]) / 2],
        dtype=np.float64,
    )
    return ret


@njit
def old_add_middle_get_index(
    matrix: np.ndarray,
    new_vertices: np.ndarray,
    old_vertices: np.ndarray,
    v_index: np.int64,
    v1: np.int64,
    v2: np.int64,
) -> Union[np.int64, np.int64]:
    """Matrix based method for inserting new vertices with the guarantee of uniqueness

    Args:
        matrix (np.ndarray): (Nvertices x Nvertices) matrix
        new_vertices (np.ndarray): Array to store new vertices
        old_vertices (np.ndarray): Array of old vertices
        v_index (np.int64): Current index of new vertices
        v1 (np.int64): Index of outer vertex
        v2 (np.int64): Index of other outer vertex

    Returns:
        Union[np.int64, np.int64]: index of inserted vertex, new v_index
    """
    if matrix[v1][v2] == -1:
        matrix[v1][v2] = v_index
        matrix[v2][v1] = v_index
        new_vertices[v_index] = get_middle_coords(old_vertices[v1], old_vertices[v2])
        v_index += 1

    return matrix[v1][v2], v_index


@njit
def add_vertex_get_index(mid: np.ndarray, vertices: np.ndarray, v_dict: Dict):
    """Adds a given midpoint to a list of new vertices

    Args:
        mid (np.ndarray): the midpoint to add
        vertices (np.ndarray): an array of new vertices, to be concatenated with
        existing vertices
        v_index (Dict): dictionary containing the indexes of existing midpoints,
        to prevent duplicates

    Returns:
        int: the index of the midpoint that was added to vertices
    """
    # Creating (hopefully) unique key for each coordinate
    mid_sum = mid[0] * 100 + mid[1] * 10 + mid[2]
    # Adding key to dictionary of coords with index as value
    inserted = False

    while not inserted:
        if mid_sum not in v_dict:
            v_dict[mid_sum] = len(v_dict)
            inserted = True
        else:
            if (mid != vertices[v_dict[mid_sum]]).any():
                mid_sum += 100
            else:
                break

    index = v_dict[mid_sum]
    # Add new midpoint to new vertices array
    if (vertices[index] == np.array([0, 0, 0])).all():
        vertices[index] = mid

    return index


@njit
def calc_dist(points) -> list:
    """Calculates the distance of each point in the Dome from the origin

    Args:
        points (list): list of points

    Returns:
        list: List of distances of each point in the Dome
    """

    distances = []
    for p in points:
        dist = math.sqrt(p[0] * p[0] + p[1] * p[1] + p[2] * p[2])
        distances.append(round(dist, 2))

    return distances


@njit
def tessellate_geodesic_dome(
    vertices: np.ndarray,
    triangles: np.ndarray,
    target_triangles: np.ndarray = np.zeros(0, dtype=np.int64),
) -> Union[np.ndarray, np.ndarray]:
    """Tessellates the target triangles in the dome

    Args:
        vertices (np.ndarray): Array of vertices
        triangles (np.ndarray): Array of triangles
        target_triangles (np.ndarray): Target triangles to tessellate
                                        (optional: tessellates all triangles if not given)

    Returns:
        Union[np.ndarray, np.ndarray, np.ndarray]: Array of new vertices,
        triangles, and new adjacency list
    """

    # Fill target with all triangles if not given
    if len(target_triangles) == 0:
        target_triangles = np.arange(len(triangles))

    # First calculate the number of edges covered by the current triangles

    # create new array for new triangles
    n_new_triangles = len(triangles) + 3 * len(target_triangles)
    new_triangles = np.zeros((n_new_triangles, 3), dtype=np.int64)
    n_old_vertices = len(vertices)
    generous_edge_count = len(target_triangles) * 3 + n_old_vertices
    # create new array for new vertices
    new_vertices = np.zeros((generous_edge_count, 3), dtype=np.float64)
    v_dict = Dict.empty(key_type=np.float64, value_type=np.int64)

    i = 0

    hit_triangles = np.zeros((len(triangles)), dtype=np.int8)

    # Add all existing vertices to dictionary
    for v in vertices:
        add_vertex_get_index(v, new_vertices, v_dict)

    for t in target_triangles:
        tri = triangles[t]
        hit_triangles[t] = 1

        v0 = vertices[tri[0]]
        v1 = vertices[tri[1]]
        v2 = vertices[tri[2]]

        # Get midpoints for each edge of the triangle and normalise
        mid01 = normalise_length(get_middle_coords(v0, v1))
        mid12 = normalise_length(get_middle_coords(v1, v2))
        mid02 = normalise_length(get_middle_coords(v0, v2))

        index01 = add_vertex_get_index(mid01, new_vertices, v_dict)
        index12 = add_vertex_get_index(mid12, new_vertices, v_dict)
        index02 = add_vertex_get_index(mid02, new_vertices, v_dict)

        # Create new triangles
        new_triangles[i] = [tri[0], index01, index02]
        new_triangles[i + 1] = [tri[1], index12, index01]
        new_triangles[i + 2] = [tri[2], index02, index12]
        new_triangles[i + 3] = [index01, index12, index02]

        i += 4

    # Add all the untargeted triangles
    for j in range(len(triangles)):
        if hit_triangles[j] == 0:
            t = triangles[j]
            new_triangles[i] = t
            i += 1

    # Create array to concatenate old vertices with new midpoints
    vertices = np.zeros((len(v_dict), 3), dtype=np.float64)

    for i in range(len(v_dict)):
        vertices[i] = new_vertices[i]

    # i = 0
    # # Add old vertices
    # for v in old_vertices:
    #     vertices[i] = v
    #     i += 1
    # # Add new midpoints
    # for j in range(v_index):
    #     vertices[i] = new_vertices[j]
    #     i += 1

    new_adj_list = create_adj_list(vertices, new_triangles)
    return vertices, new_triangles, new_adj_list


@njit
def create_geodesic_dome(freq=0) -> Union[np.ndarray, np.ndarray, np.ndarray]:
    """Creates an geodesic dome of a given frequency

    Args:
        freq (int, optional): the frequency of the dome. Defaults to 0.

    Returns:
        Union[np.ndarray, np.ndarray]: the array of vertices, the array of
        triangles

        Vertices = [[x,y,z], ... , [x,y,z]]
        Triangles = [[v1, v2, v3], ...] where vx is the index of a vertex in the vertices array

        Adjacency list = [[v1, ..., v5, v6?], ...] where vx is the index of a vertex. v6 may not exist for some vertices
    """
    # Set normalised scaling
    if freq != 0:
        SCALE = freq

    g_ratio = (1 + math.sqrt(5)) / 2

    # creating initial icosahedron vertices
    icosa_vertices = np.array(
        [
            (-1, g_ratio, 0),
            (1, g_ratio, 0),
            (-1, -(g_ratio), 0),
            (1, -(g_ratio), 0),
            (0, -1, g_ratio),
            (0, 1, g_ratio),
            (0, -1, -(g_ratio)),
            (0, 1, -(g_ratio)),
            (g_ratio, 0, -1),
            (g_ratio, 0, 1),
            (-(g_ratio), 0, -1),
            (-(g_ratio), 0, 1),
        ],
        dtype=np.float64,
    )
    # creating initial icosahedron edges
    triangles = np.array(
        [
            (0, 11, 5),
            (0, 5, 1),
            (0, 1, 7),
            (0, 7, 10),
            (0, 10, 11),
            (1, 5, 9),
            (5, 11, 4),
            (11, 10, 2),
            (10, 7, 6),
            (7, 1, 8),
            (3, 9, 4),
            (3, 4, 2),
            (3, 2, 6),
            (3, 6, 8),
            (3, 8, 9),
            (4, 9, 5),
            (2, 4, 11),
            (6, 2, 10),
            (8, 6, 7),
            (9, 8, 1),
        ],
        dtype=np.int64,
    )

    # Array for normalised vertices
    vertices = np.zeros((len(icosa_vertices), 3), dtype=np.float64)

    # Normalise all icosahedron vertices
    for i in range(len(icosa_vertices)):
        vertices[i] = normalise_length(icosa_vertices[i])
    # Tessellate icosahedron
    adj_list = create_adj_list(vertices, triangles)
    for i in range(freq):
        vertices, triangles, adj_list = tessellate_geodesic_dome(vertices, triangles)
    return vertices, triangles, adj_list
