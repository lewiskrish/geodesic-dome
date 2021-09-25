from flask import Flask, request, send_from_directory, jsonify
import script
import neighbours

app = Flask(__name__)

@app.route("/")
def hello_world():
    return send_from_directory('static', "index.html")

@app.route("/tesselate", methods=["POST"])
def tesselate():
    index = request.get_data()
    vertices, triangles = script.create_icosphere(int(index))
    v = vertices.tolist()
    i = triangles.tolist()
    print(type(v[0][0]))
    return jsonify(
        vertices=v,
        indices=i,
    )

@app.route("/search", methods=["POST"])
def search():
    data = request.get_data().decode()
    data = data.split(",")
    factor = data[0]
    vertex = data[1]
    distance = data[2]
    vertices, triangles, adj_list = neighbours.create_icosphere(int(factor))
    neighbours_list = neighbours.find_neighbours(vertices, adj_list, int(vertex), int(distance)).tolist()
    true_neighbours = [item for item in neighbours_list if item >= 0]
    return jsonify(
        vertices=true_neighbours,
    )

if __name__ == "__main__":
    app.run()
