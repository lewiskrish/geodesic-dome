try:
    from geo_dome.neighbourhood_search import *
    from geo_dome.tessellation import *
except:
    from neighbourhood_search import *
    from tessellation import *


import numpy as np


class GeodesicDome:
    """Class wrapper to create and interact with a Geodesic Dome"""

    def __init__(self, freq=0) -> None:
        """Creates a given geodesic dome with a given frequency.

        Args:
            freq (int, optional): The frequency of the geodesic dome. Defaults to 0.
        """

        # Input checking
        if freq < 0:
            raise ValueError("Invalid frequency")

        self.vertices, self.triangles, self.adj_list = create_geodesic_dome(
            freq)

        self.neighbours = np.zeros(0, dtype=np.int64)
        self.storage = {}
        pass

    def store(self, index: np.int64, value):
        """Store a value at a vertex

        Args:
            index (np.int64): index of the vertex
            value (any): value to store

        Raises:
            ValueError: if index given is invalid
        """
        if index < 0 or index >= len(self.vertices):
            raise ValueError("Invalid index")

        self.storage[str(index)] = value

    def retrieve(self, index: np.int64):
        """Retrieve stored information at a given vertex

        Args:
            index (np.int64): index of the vertex to retrieve 

        Raises:
            ValueError: if index given is invalid

        Returns:
            [type]: [description]
        """
        if index < 0 or index >= len(self.vertices):
            raise ValueError("Invalid index")

        return self.storage.get(str(index))

    def tessellate(self, freq=1) -> None:
        """Tessellates the geodesic dome a given number of times (tessellates once if no arguments provided)

        Args:
            freq (int, optional): The number of times to tessellate. Defaults to 1.
        """

        # Perform input checking
        if freq < 1:
            raise ValueError("Invalid tessellation frequency")

        for _ in range(freq):
            self.vertices, self.triangles, self.adj_list = tessellate_geodesic_dome(
                self.vertices, self.triangles
            )

    def partial_tessellate_vertex(self, index: np.int64, depth=0) -> None:
        """Main entrypoint to tessellate dome based on selected vertex

        Args:
            index (np.int64): index of root vertex
            depth (int, optional): tessellation depth. Defaults to 0.

        Raises:
            ValueError: Raised when depth is negative
            ValueError: Raised when vertex is out of bounds
        """
        if depth < 0:
            raise ValueError("Invalid depth")
        if index < 0 or index > len(self.vertices):
            raise ValueError("Invalid vertex index")
        neighbours = self.find_neighbours_vertex(index, depth)
        self.custom_partial_tessellate_vertex(neighbours)

    def partial_tessellate_triangle(self, index: np.int64, depth=0) -> None:
        """Main entrypoint to tessellate dome based on selected triangle

        Args:
            index (np.int64): index of root triangle
            depth (int, optional): tessellation depth. Defaults to 0.

        Raises:
            ValueError: Raised when depth is negative
            ValueError: Raised when triangle is out of bounds
        """
        if depth < 0:
            raise ValueError("Invalid depth")
        if index < 0 or index > len(self.triangles):
            raise ValueError("Invalid triangle index")

        if depth == 0:
            triangles = np.full(1, index, dtype=np.int64)
            self.custom_partial_tessellate_triangle(triangles)
        else:
            neighbours = self.find_neighbours_triangle(index, depth - 1)
            self.custom_partial_tessellate_vertex(neighbours)

    def find_neighbours_vertex(self, index: np.int64, depth=0) -> np.ndarray:
        """Finds the neighbours of a given vertex on the geodesic dome to a certain depth (defaults to 0 if not provided)

        Args:
            index (np.int64): The index of the vertex to search from
            depth (int, optional): The depth of neighbours to return. Defaults to 1.

        Raises:
            ValueError: Raised when depth is negative
            ValueError: Raised when vertex is out of bounds

        Returns:
            np.ndarray: An array containing the indices of all the vertex's
            neighbours
        """
        if depth < 0:
            raise ValueError("Invalid depth")

        if index >= len(self.vertices) or index < 0:
            raise ValueError("Invalid index")

        self.neighbours = find_neighbours_vertex(
            self.vertices, self.adj_list, index, depth
        )

        return self.neighbours

    def find_neighbours_triangle(self, index: np.int64, depth=0) -> np.ndarray:
        """Finds the neighbours of a given triangle's vertices on the geodesic
        dome to a certain depth (defaults to 0 if not provided)

        Args:
            index (np.int64): index of root triangle
            depth (int, optional): tessellation depth. Defaults to 0.

        Raises:
            ValueError: Raised when depth is negative
            ValueError: Raised when triangle is out of bounds

        Returns:
            np.ndarray: An array containing the indices of all the triangle's neighbouring vertices
        """

        if depth < 0:
            raise ValueError("Invalid depth")

        if index >= len(self.vertices) or index < 0:
            raise ValueError("Invalid index")

        start_vertices = np.zeros(3, dtype=np.int64)
        triangle = self.triangles[index]
        for i in range(len(triangle)):
            start_vertices[i] = triangle[i]

        self.neighbours = find_neighbours_triangle(
            self.vertices, self.adj_list, start_vertices, depth
        )

        return self.neighbours

    def custom_partial_tessellate_vertex(
        self, neighbours=np.zeros(0, dtype=np.int64)
    ) -> None:
        """Tessellates all adjacent triangles to a given set of vertices. If not vertices are given,
        it will attempt to tessellate from the most recent neighbourhood search results

        Args:
            neighours (np.ndarray, optional): The set of vertices to tessellate
            around (provided as indices). Defaults to an empty array.
        """
        if len(neighbours) == 0:
            # If no neighbours, tessellate from history
            neighbours = self.neighbours

            # Raise error if no stored neighbours
            if len(self.neighbours) == 0:
                raise ValueError(
                    "No neighbours provided and no stored neighbours")

        target_triangles = find_adjacent_triangles(self.triangles, neighbours)

        self.custom_partial_tessellate_triangle(target_triangles)

    def custom_partial_tessellate_triangle(self, target_triangles: np.ndarray) -> None:
        """Selectively tessellate certain triangles in the Geodesic Dome

        Args:
            target_triangles (np.ndarray): indices of triangles to tessellate

        Raises:
            ValueError: Target triangles not provided
        """
        if len(target_triangles) == 0:
            raise ValueError("Please provide at least one target triangle")

        self.vertices, self.triangles, self.adj_list = tessellate_geodesic_dome(
            self.vertices, self.triangles, target_triangles
        )

    def get_vertices(self) -> np.ndarray:
        """Getter function for vertices

        Returns:
            np.ndarray: the vertices of the geodesic dome
        """
        return self.vertices

    def get_triangles(self) -> np.ndarray:
        """Getter function for triangles

        Returns:
            np.ndarray: the triangles of the geodesic dome
        """
        return self.triangles
