const express = require('express');
const path = require('path');

const app = express();
const port = process.env.PORT || 8000;
app.use(express.static('public'));
app.use(express.text());

let { PythonShell } = require('python-shell')

app.get('/', function (req, res) {
    res.sendFile(path.join(__dirname, '/index.html'));
});

app.post('/face', function (req, res) {
    let pyshell = new PythonShell('script.py')
    var id = req.body;
    console.log(req.body);
    pyshell.send(id);
    pyshell.on('message', function (message) {
        var data = JSON.parse(message)
        res.json(data)
    });
    pyshell.end(function (err,code,signal) {
        if (err) throw err;
        console.log('The exit code was: ' + code);
        console.log('The exit signal was: ' + signal);
        console.log('finished');
    });
});

app.post('/search', function (req, res) {
    let pyshell = new PythonShell('neighbours.py');
    var indices = req.body;
    console.log(req.body);
    pyshell.send(indices);
    pyshell.on('message', function (message) {
        var data = JSON.parse(message)
        res.json(data)
    });
    pyshell.end(function (err,code,signal) {
        if (err) throw err;
        console.log('The exit code was: ' + code);
        console.log('The exit signal was: ' + signal);
        console.log('finished');
    });
});

app.listen(port);
console.log('Server started at http://localhost:' + port);