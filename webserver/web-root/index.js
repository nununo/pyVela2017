// ----------------------------------------------------------------------------
// index.js
// ----------------------------------------------------------------------------

var chart = null;
var chart_data = [];
var socket = null;


const _data = {
    datasets: [{
        fill: false,
        label: 'Arduino raw',
        data: chart_data,
        borderColor: '#0080f0',
        backgroundColor: '#0080f0',
        pointRadius: 0,
        lineTension: 0,
    }]
}

const _options = {
    scales: {
        xAxes: [{
            type: 'time',
            time: {
                minUnit: 'minute',
                displayFormats: {
                    minute: 'MMM DD, HH:mm'
                }
            },
            ticks: {
                maxRotation: 0,
                minRotation: 0,
            },
        }],
        yAxes: [{
            ticks: {
//                beginAtZero: true,
            }
        }]
    },
    animation: {
        duration: 0
    },
}


function create_chart() {
    var canvas = document.getElementById('chart');
    var ctx = canvas.getContext('2d');

    return new Chart(ctx, {
        type: 'line',
        data: _data,
        options: _options
    });
}

function create_websocket() {
    var ws = new WebSocket("ws://" + location.hostname + ":8081");

    ws.onopen = socket_open;
    ws.onmessage = socket_message;
    ws.onclose = socket_close;

    return ws;
}

function socket_open() {
    console.log('socket open');
}

function socket_message(msg) {
    var obj = JSON.parse(msg.data);
    obj.t = new Date(obj.t);
    chart_data.push(obj);
    if ( chart_data.length > 600 ) {
        chart_data.shift();
    }
    chart.update();
}

function socket_close(e) {
    console.log('socket close');
}

window.onload = function() {
    chart = create_chart();
    socket = create_websocket();
}

function button_click(arg) {
    socket.send(arg);
}

// ----------------------------------------------------------------------------
// index.js
// ----------------------------------------------------------------------------

