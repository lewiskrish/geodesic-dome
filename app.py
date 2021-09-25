from flask import Flask, request, send_from_directory, jsonify
import script
import neighbours

from whitenoise import WhiteNoise

app = Flask(__name__)
app.wsgi_app = WhiteNoise(app.wsgi_app, root="static/")

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
    neighbourslist = neighbours.find_neighbours(vertices, adj_list, int(vertex), int(distance))
    true_neighbourslist = neighbourslist.tolist()[:-1]
    return jsonify(
        vertices=true_neighbourslist,
    )
