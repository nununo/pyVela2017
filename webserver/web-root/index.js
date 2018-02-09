// ----------------------------------------------------------------------------
// index.js
// ----------------------------------------------------------------------------


// Global variables.

// The chart object.
var chart = null;

// Sliding window over the most recent chart data values.
var chart_data = [];

// The websocket.
var socket = null;

// Number of log messages we're displaying.
var log_count = 0;

// The DOM element containing the log messages.
var log = null;



// Two objects used to setup the arduino readings chart.
// Full docs at http://www.chartjs.org

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



// Called by window.onload to create the chart object.

function create_chart() {
    var canvas = document.getElementById('chart');
    var ctx = canvas.getContext('2d');

    return new Chart(ctx, {
        type: 'line',
        data: _data,
        options: _options
    });
}



// Called by window.onload to create the websocket.

function create_websocket() {
    var ws = new WebSocket("ws://" + location.hostname + ":8081");

    ws.onopen = socket_open;
    ws.onmessage = socket_message;
    ws.onclose = socket_close;

    return ws;
}



// Websocket event handler: called when the connection is ready.

function socket_open() {
    console.log('socket open');
}



// Websocket event handler: called when a message is received.

function socket_message(msg) {
    var obj = JSON.parse(msg.data);
    if ( obj.hasOwnProperty("y") ) {
        obj.t = new Date(obj.t);
        chart_data.push(obj);
        if ( chart_data.length > 600 ) {
            chart_data.shift();
        }
        chart.update();
    } else {
        update_log(obj.text);
    }
}



// Appends the `s` text message to the `log` DOM element's innerText.
// Truncates initial `log` inner text if it holds more than a certain amount
// of messages (for now hardcoded at 20).

function update_log(s) {
    log.innerText += s + "\n";
    log_count++;
    if (log_count > 20) {
        pos = log.innerText.indexOf("\n"); 
        log.innerText = log.innerText.substring(pos+1);
    }
}



// Websocket event handler: called when the connection is closed.

function socket_close(e) {
    console.log('socket close');
}



// Initialize global objects.

window.onload = function() {
    chart = create_chart();
    socket = create_websocket();
    log = document.getElementById("log");
}



// Dummy input button click handler: sends `arg` via the connected websocket.

function button_click(arg) {
    socket.send(arg);
}


// ----------------------------------------------------------------------------
// index.js
// ----------------------------------------------------------------------------

