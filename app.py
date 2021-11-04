from flask import Flask, json, request, send_from_directory, jsonify, session
from flask_session import Session
import secrets
import numpy as np
import sys
sys.path.append("src/geo_dome")
try:
    from geo_dome.geodesic_dome import GeodesicDome
    from geo_dome.neighbourhood_search import create_adj_list
except:
    from geodesic_dome import GeodesicDome
    from neighbourhood_search import create_adj_list

app = Flask(__name__)
app.secret_key = secrets.token_bytes(32)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def hello_world():
    session.clear()
    return send_from_directory('static', "index.html")

@app.route("/tesselate", methods=["POST"])
def tesselate():
    index = request.get_data()
    dome = GeodesicDome(0)
    if "vertices" and "indices" in session:
        dome.vertices = np.asarray(session["vertices"])
        dome.triangles = np.asarray(session["indices"])
    for i in range(int(index)):
        dome.tessellate(1)
    v = dome.get_vertices().tolist()
    i = dome.get_triangles().tolist()
    session["vertices"] = v
    session["indices"] = i
    return jsonify(
        vertices=v,
        indices=i,
    )

@app.route("/faceselective", methods=["POST"])
def faceselective():
    data = request.get_json()
    index = data["index"]
    dome = GeodesicDome(0)
    if "vertices" and "indices" in session:
        dome.vertices = np.asarray(session["vertices"])
        dome.triangles = np.asarray(session["indices"])
    target = np.array([index], dtype=np.int64)
    dome.partial_tessellate_triangle(target, 0)
    v = dome.get_vertices().tolist()
    i = dome.get_triangles().tolist()
    session["vertices"] = v
    session["indices"] = i
    return jsonify(
        vertices=v,
        indices=i,
    )

@app.route("/vertexselective", methods=["POST"])
def vertexselective():
    data = request.get_json()
    vertex = data["index"]
    distance = data["distance"]
    dome = GeodesicDome(0)
    if "vertices" and "indices" in session:
        dome.vertices = np.asarray(session["vertices"])
        dome.triangles = np.asarray(session["indices"])
    dome.partial_tessellate_vertex(int(vertex), int(distance))
    v = dome.get_vertices().tolist()
    i = dome.get_triangles().tolist()
    session["vertices"] = v
    session["indices"] = i
    return jsonify(
        vertices=v,
        indices=i,
    )

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    vertex = data["index"]
    distance = data["distance"]
    dome = GeodesicDome(0)
    if "vertices" and "indices" in session:
        dome.vertices = np.asarray(session["vertices"])
        dome.triangles = np.asarray(session["indices"])
    dome.adj_list = create_adj_list(dome.get_vertices(), dome.get_triangles())
    neighbours_list = dome.find_neighbours_vertex(int(vertex), int(distance))
    true_neighbours = [item for item in neighbours_list.tolist() if item >= 0]
    return jsonify(
        vertices=true_neighbours,
    )

@app.route("/store", methods=["POST"])
def store():
    data = request.get_json()
    vertex = data["index"]
    value = data["value"]
    if "storage" in session:
        s = session["storage"]
    else:
        s = {}
    s[str(vertex)] = value
    session["storage"] = s
    return jsonify(
        success="Success"
    )

@app.route("/retrieve", methods=["POST"])
def retrieve():
    data = request.get_json()
    vertex = data["index"]
    if "storage" in session:
        s = session["storage"]
    else:
        return jsonify(
            value=None
        )
    if str(vertex) not in s:
        return jsonify(
            value=None
        )
    return jsonify(
        value=s[str(vertex)]
    )

if __name__ == "__main__":
    app.run()
