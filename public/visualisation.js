// Importing from CDN - can change to npm or local copy
import * as THREE from "https://cdn.skypack.dev/three";
import { TrackballControls } from "https://cdn.skypack.dev/three/examples/jsm/controls/TrackballControls";
import { GUI } from "https://cdn.skypack.dev/three/examples/jsm/libs/dat.gui.module";
import data from "./icojson.js";

// Setting up the scene and camera
const scene = new THREE.Scene();
scene.background = new THREE.Color("grey");
const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);
camera.position.z = 100;
scene.add(camera);

// Used for intersection detection
const mouse = new THREE.Vector2();
const raycaster = new THREE.Raycaster();
var intersectedFace;
var intersectedPoint;

// Creating renderer and adding to dom
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);
document.addEventListener("mousemove", onPointerMove, false);
document.addEventListener('click', onClick, false);

// Configuring controls
var controls = new TrackballControls(camera, renderer.domElement);
controls.rotateSpeed = 2.0;
controls.zoomSpeed = 1.2;
controls.panSpeed = 0.8;

// Adding some lighting
var spotLight = new THREE.SpotLight(
    new THREE.Color("rgb(255, 166, 77)"),
    1
);
camera.add(spotLight);

// Creating a material to use for the mesh
var pinkMat = new THREE.MeshPhongMaterial({
    color: new THREE.Color("white"),
    // emissive: new THREE.Color("red"),
    shininess: 1,
    flatShading: THREE.FlatShading,
    transparent: 1,
    opacity: 1,
    vertexColors: true,
});

// Creates the geometry of the dome
function createGeometry(data) {
    const geometry = new THREE.BufferGeometry();
    const indices = [];
    const vertices = [];
    const colors = [];
    const color = new THREE.Color("white");

    for (let i = 0; i < data.vertices.length; i += 3) {
        vertices.push(data.vertices[i] * 50, data.vertices[i + 1] * 50, data.vertices[i + 2] * 50);
        colors.push(color.r, color.g, color.b);
    }
    for (let i = 0; i < data.indices.length; i += 3) {
        indices.push(data.indices[i], data.indices[i + 1], data.indices[i + 2]);
    }

    geometry.setIndex(indices);
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))

    return geometry;
}

// Creates a mesh of the dome
function createMesh(data) {
    const geometry = createGeometry(data);
    const mesh = new THREE.Mesh(geometry, pinkMat);
    return mesh;
}

// Creating the mesh and adding it to the scene
var mesh = createMesh(data);
scene.add(mesh);

// Creates a mesh representing the wireframe of the dome
function createLine(mesh) {
    const wireframe = new THREE.WireframeGeometry(mesh.geometry);
    const line = new THREE.LineSegments(wireframe);
    line.material.depthTest = true;
    line.material.opacity = 0.75;
    line.material.transparent = true;
    line.material.color = new THREE.Color("blue");
    return line;
}

// Creating a wireframe to use for showing edges
var line = createLine(mesh);

const sprite = new THREE.TextureLoader().load("disc.png");

// Creates a points object representing the vertices of the dome
function createPoints(mesh) {

    const vertices = [];
    const positionAttribute = mesh.geometry.getAttribute("position");
    for (let i = 0; i < positionAttribute.count; i++) {
        const vertex = new THREE.Vector3();
        vertex.fromBufferAttribute(positionAttribute, i);
        vertices.push(vertex);
    }
    // Creating material for the points
    const pointsMaterial = new THREE.PointsMaterial({
        size: 2,
        alphaTest: 0.5,
        vertexColors: true,
        map: sprite,
    });
    const pointsGeometry = new THREE.BufferGeometry().setFromPoints(vertices)
    // Colouring points
    const colors = []
    const color = new THREE.Color(0x0080ff);
    for (let i = 0; i < vertices.length; i++) {
        colors.push(color.r, color.g, color.b);
    }
    pointsGeometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    const points = new THREE.Points(pointsGeometry, pointsMaterial);
    return points;
}

// Creating the points
var points = createPoints(mesh);

// Setting up GUI parameters
var params = {
    factor: 0,
    showEdges: false,
    showFaces: true,
    showPoints: false,
    domeColor: 0xffa64d,
    pointSize: 2,
    searchDistance: 1,
};

// GUI logic
const gui = new GUI();
gui
    .add(params, "factor", 0, 10, 1)
    .name("tesselation factor")
    .onFinishChange(function (value) {
        fetch("http://localhost:8000/face", {
            method: 'POST',
            body: value,
            headers: {
                'Content-Type': 'text/plain'
            },
        })
            .then(reponse => reponse.json())
            .then(data => {
                mesh.geometry.dispose();
                line.geometry.dispose();
                points.geometry.dispose();
                scene.remove(mesh);
                scene.remove(line);
                scene.remove(points);
                mesh = createMesh(data);
                line = createLine(mesh);
                points = createPoints(mesh);
                scene.add(mesh);
            });
    })
gui
    .add(params, "pointSize", 0, 10)
    .name("point size")
    .onChange(function (value) {
        points.material.size = value;
    });
gui
    .add(params, "showPoints")
    .name("show points")
    .onChange(function (value) {
        value ? scene.add(points) : scene.remove(points);
    });
gui
    .add(params, "showEdges")
    .name("show edges")
    .onChange(function (value) {
        value ? scene.add(line) : scene.remove(line);
    });
gui
    .add(params, "showFaces")
    .name("show faces")
    .onChange(function (value) {
        value ? scene.add(mesh) : scene.remove(mesh);
    });
gui
    .addColor(params, "domeColor")
    .name("dome colour")
    .onChange(function () {
        spotLight.color.set(params.domeColor);
    });
gui
    .add(params, "searchDistance", 0, 100, 1)
    .name("search distance");
gui
    .add({
        reset: function () {
            const colorAttribute = points.geometry.getAttribute("color");
            const color = new THREE.Color(0x0080ff);
            for (let i = 0; i < colorAttribute.count; i++) {
                colorAttribute.setXYZ(i, color.r, color.g, color.b);
                colorAttribute.needsUpdate = true;
            }
        }
    }, "reset")
    .name("reset points");

// Animation function
const animate = function () {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
};

// Function to highlight faces with a given colour
const highlightFace = (color) => {
    const { face } = intersectedFace;
    const colorAttribute =
        intersectedFace.object.geometry.getAttribute("color");

    colorAttribute.setXYZ(face.a, color.r, color.g, color.b);
    colorAttribute.setXYZ(face.b, color.r, color.g, color.b);
    colorAttribute.setXYZ(face.c, color.r, color.g, color.b);

    colorAttribute.needsUpdate = true;
};

// Function to highlight intersected points with a given colour
const highlightPoint = (color) => {
    const { index } = intersectedPoint;
    const colorAttribute =
        intersectedPoint.object.geometry.getAttribute("color");

    colorAttribute.setXYZ(index, color.r, color.g, color.b);

    colorAttribute.needsUpdate = true;
};

// Function to highlight neighbour points with a given colour
const highlightPointNeighbour = (index, color) => {
    const colorAttribute =
        points.geometry.getAttribute("color");

    colorAttribute.setXYZ(index, color.r, color.g, color.b);

    colorAttribute.needsUpdate = true;
};

// Pointer intersection detection and handling
function onPointerMove(event) {
    event.preventDefault();

    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const objects = raycaster.intersectObjects(scene.children);

    if (objects.length > 0) {
        // If mouse is on a face
        if (objects[0].object.type === "Mesh") {
            if (intersectedFace != objects[0].object) {
                if (intersectedFace) {
                    highlightFace(new THREE.Color("white"));
                }
                if (intersectedPoint) {
                    highlightPoint(new THREE.Color(0x0080ff));
                }
                intersectedFace = objects[0];
                highlightFace(new THREE.Color("red"));
            }
            // If mouse is on a vertex
        } else if (objects[0].object.type === "Points") {
            if (intersectedPoint != objects[0].object) {
                if (intersectedPoint) {
                    highlightPoint(new THREE.Color(0x0080ff));
                }
                if (intersectedFace) {
                    highlightFace(new THREE.Color("white"));
                }
                intersectedPoint = objects[0];
                highlightPoint(new THREE.Color("red"));
            }
        }
        // Mouse isn't on face or point
    } else {
        if (intersectedFace) {
            highlightFace(new THREE.Color("white"));
        }
        if (intersectedPoint) {
            highlightPoint(new THREE.Color(0x0080ff));
        }
        intersectedFace = null;
        intersectedPoint = null;
    }
}

// Used for clicking on faces and vertices
function onClick(event) {
    event.preventDefault();
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const objects = raycaster.intersectObjects(scene.children);

    if (objects.length > 0) {
        // If mouse is on a face
        if (objects[0].object.type === "Mesh") {
            // alert(objects[0].faceIndex);
            // If mouse is on a vertex do neighbour search
        } else if (objects[0].object.type === "Points") {
            fetch("http://localhost:8000/search", {
                method: 'POST',
                body: params.factor + "," + objects[0].index + "," + params.searchDistance,
                headers: {
                    'Content-Type': 'text/plain'
                },
            })
                .then(reponse => reponse.json())
                .then(data => {
                    for (let i = 0; i < data.vertices.length; i++) {
                        highlightPointNeighbour(data.vertices[i], new THREE.Color("red"));
                    }
                });
        }
    }
};

animate();