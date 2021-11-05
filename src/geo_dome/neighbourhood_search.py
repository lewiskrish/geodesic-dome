import numpy as np
from numba import njit

MAX_POINTS = 12


@njit
def adj_insert(adj: np.ndarray, root: np.int64, neighbour: np.int64) -> None:
    """Function to insert a point into adjacency list of root vertex

    Args:
        adj (np.ndarray): array of arrays, representing adjacency list
        root (np.int64): index of root vertex
        neighbour (np.int64): index of neighbour vertex to add
    """
    root_list = adj[root]
    for i in range(MAX_POINTS):
        if root_list[i] == neighbour:
            break
        if root_list[i] == -1:
            root_list[i] = neighbour
            break


@njit
def create_adj_list(vertices: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    """Function to create adjacency list representation of vertices

    Args:
        vertices (np.ndarray): numpy array of vertices
        triangles (np.ndarray): numpy array of vertices

    Returns:
        np.ndarray: array of arrays representing adjacency list
    """
    adj = np.full((len(vertices), MAX_POINTS), -1, dtype=np.int64)

    for t in triangles:
        adj_insert(adj, t[0], t[1])
        adj_insert(adj, t[0], t[2])
        adj_insert(adj, t[1], t[0])
        adj_insert(adj, t[1], t[2])
        adj_insert(adj, t[2], t[0])
        adj_insert(adj, t[2], t[1])

    return adj


@njit
def find_neighbours_vertex(
    vertices: np.ndarray, adj_list: np.ndarray, index: np.int64, depth=1
) -> np.ndarray:
    """Function to find nearest neighbours to a specific point, up to a
    specified depth

    Args:
        vertices (np.ndarray): numpy array of vertices in the Dome
        adj (np.ndarray): adjacency list of the vertices
        index (np.int64): index of the root vertex
        depth (np.int64, optional): search depth. Defaults to 1.

    Returns:
        np.ndarray: Array of neighbours found, may include -1 representing empty entries
    """
    size = 1
    for i in range(depth):
        size += (i + 1) * MAX_POINTS

    if size > len(vertices):
        size = len(vertices)

    curr_depth = 1

    neighbours = np.full(size, -1, dtype=np.int64)
    neighbours[0] = index
    num_neighbours = 1
    queue = np.full(1, index, dtype=np.int64)
    visited = np.full(len(vertices), False, dtype=np.bool_)

    q_end = 1

    while curr_depth <= depth:
        temp = np.full(len(queue) * MAX_POINTS, -1, dtype=np.int64)
        temp_ptr = 0
        q_front = 0
        while q_front < q_end:
            v_index = queue[q_front]

            for neighbour in adj_list[v_index]:
                if neighbour != -1 and visited[neighbour] == False:
                    neighbours[num_neighbours] = neighbour
                    temp[temp_ptr] = neighbour

                    num_neighbours += 1
                    temp_ptr += 1
                    visited[neighbour] = True
            visited[v_index] = True
            q_front += 1

        # resize queue to contain all new neighbours, remove -1
        new_queue = np.zeros(temp_ptr, dtype=np.int64)
        for i in range(temp_ptr):
            new_queue[i] = temp[i]
        queue = new_queue
        q_end = temp_ptr
        curr_depth += 1
        if temp_ptr == 0:
            break
    return neighbours


@njit
def find_neighbours_triangle(
    vertices: np.ndarray, adj_list: np.ndarray, start_vertices: np.ndarray, depth=1
) -> np.ndarray:
    """Function to find nearest neighbours to a specific point, up to a
    specified depth

    Args:
        vertices (np.ndarray): numpy array of vertices in the Dome
        adj (np.ndarray): adjacency list of the vertices
        index (np.int64): index of the root triangle
        depth (np.int64, optional): search depth. Defaults to 1.

    Returns:
        np.ndarray: Array of neighbours found, may include -1 representing empty entries
    """
    START_LEN = 3
    if len(start_vertices) != START_LEN:
        raise Exception("Invalid starting vertices")

    # make space for initial 3 vertices
    size = START_LEN
    for i in range(depth):
        size += ((i + 1) * MAX_POINTS) + START_LEN

    if size > len(vertices):
        size = len(vertices)

    curr_depth = 1

    neighbours = np.full(size, -1, dtype=np.int64)
    queue = start_vertices
    visited = np.full(len(vertices), False, dtype=np.bool_)

    # add initial 3 triangle vertices to neighbour array
    for i in range(START_LEN):
        visited[queue[i]] = True
        neighbours[i] = queue[i]

    num_neighbours = START_LEN

    q_end = START_LEN

    while curr_depth <= depth:
        temp = np.full((len(queue) * MAX_POINTS) + START_LEN, -1, dtype=np.int64)
        temp_ptr = 0
        q_front = 0

        while q_front < q_end:
            v_index = queue[q_front]
            for neighbour in adj_list[v_index]:

                if neighbour != -1 and visited[neighbour] == False:
                    neighbours[num_neighbours] = neighbour
                    temp[temp_ptr] = neighbour

                    num_neighbours += 1
                    temp_ptr += 1
                    visited[neighbour] = True
            visited[v_index] = True
            q_front += 1
        new_queue = np.zeros(temp_ptr, dtype=np.int64)
        for i in range(temp_ptr):
            new_queue[i] = temp[i]
        queue = new_queue
        q_end = temp_ptr
        curr_depth += 1
        if temp_ptr == 0:
            break

    return neighbours
