// ----------------------------------------------------------------------------
// index.js
// ----------------------------------------------------------------------------


// Global variables.

// The chart object.
var chart = null;

// Sliding windows over the most recent chart data values.
var chart_data_raw = [];
var chart_data_agd = [];

// The websocket.
var socket = null;

// Number of log messages we're displaying.
var log_count = 0;

// The DOM element containing the log messages.
var log = null;



// Two objects used to setup the sensor readings chart.
// Full docs at http://www.chartjs.org

const _data = {
    datasets: [{
        fill: false,
        label: 'RAW',
        data: chart_data_raw,
        borderColor: '#0080f0',
        backgroundColor: '#0080f0',
        pointRadius: 0,
        lineTension: 0,
        yAxisID: 'left_axis',
    }, {
        fill: false,
        label: 'AGD',
        data: chart_data_agd,
        borderColor: '#00a040',
        backgroundColor: '#00a040',
        pointRadius: 0,
        lineTension: 0,
        yAxisID: 'right_axis',
    }]
}

const _options = {
//  Visibility becomes useful with >1 dataset; bonus: clicking hides/shows datasets.
//    legend: {
//        display: false
//    },
    maintainAspectRatio: false,
    scales: {
        xAxes: [{
            type: 'time',
            time: {
                minUnit: 'year',
                displayFormats: {
                    minute: 'HH:mm:ss'
                }
            },
            ticks: {
                maxRotation: 0,
                minRotation: 0,
            },
        }],
        yAxes: [{
            id: 'left_axis',
            position: 'left',
            afterDataLimits: function(axis) {
                // Force axis range to be slighly larger than the data range.
                axis.min -= 5;
                axis.max += 5;
            }
        }, {
            id: 'right_axis',
            position: 'right',
            afterDataLimits: function(axis) {
                // This is somewhat of a hack, read on.
                // Ideally, we could just extend the axis range; however, the
                // threshold annotation values are accounted for there (not sure
                // if this is a chartjs/chart-annotations limitation of it's
                // just my lack of understanding).
                // The hack:
                // - Get out of here if !chart (we're being called too early).
                // - Grab the chart.options.annotation.annotations array and:
                //   - Collect valid (non-null) annotations.
                //   - If no annotations found, just extend the axis.
                //   - If annotations are found, extend the axis taking into
                //     account not only the chart data, already accounted for
                //     when we are called, but also the min/max values for the
                //     existing annotations.
                if ( !chart ) {
                    return;
                }
                var chart_annotations = chart.options.annotation.annotations;
                var threshold_values = chart_annotations.map(item => item.value);
                threshold_values = threshold_values.filter(item => item !== null);
                if ( !threshold_values.length ) {
                    axis.min -= 5;
                    axis.max += 5;
                } else {
                    axis.min = Math.min(axis.min, Math.min(...threshold_values)) - 5;
                    axis.max = Math.max(axis.max, Math.max(...threshold_values)) + 5;
                }
            }
        }]
    },
    animation: {
        duration: 0
    },
// Depends on https://github.com/chartjs/chartjs-plugin-annotation
    annotation: {
        events: ["click"],
        annotations: [{
            drawTime: "afterDatasetsDraw",
            type: "line",
            mode: "horizontal",
            scaleID: "right_axis",
            value: null,
            borderColor: "rgba(0, 0, 0, 0.3)",
            borderWidth: 28,
            label: {
                content: "Level 1",
                position: 'left',
                xAdjust: 10,
                backgroundColor: "rgba(0, 0, 0, 0)",
                enabled: true
            },
            onClick: function(e) {
                // console.log("Annotation", e.type, this);
                _prompt_level_threshold(1);
            }
        }, {
            drawTime: "afterDatasetsDraw",
            type: "line",
            mode: "horizontal",
            scaleID: "right_axis",
            value: null,
            borderColor: "rgba(0, 0, 0, 0.3)",
            borderWidth: 28,
            label: {
                content: "Level 2",
                position: 'left',
                xAdjust: 10,
                backgroundColor: "rgba(0, 0, 0, 0)",
                enabled: true
            },
            onClick: function(e) {
                // console.log("Annotation", e.type, this);
                _prompt_level_threshold(2);
            }
        }, {
            drawTime: "afterDatasetsDraw",
            type: "line",
            mode: "horizontal",
            scaleID: "right_axis",
            value: null,
            borderColor: "rgba(0, 0, 0, 0.3)",
            borderWidth: 28,
            label: {
                content: "Level 3",
                position: 'left',
                xAdjust: 10,
                backgroundColor: "rgba(0, 0, 0, 0)",
                enabled: true
            },
            onClick: function(e) {
                // console.log("Annotation", e.type, this);
                _prompt_level_threshold(3);
            }
        }]
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
    var url = "ws://" + location.hostname + ":" + location.port + "/ws";
    var ws = new WebSocket(url);

    ws.onopen = socket_open;
    ws.onmessage = socket_message;
    ws.onclose = socket_close;

    return ws;
}



// Websocket event handler: called when the connection is ready.

function socket_open() {
    console.log('socket open');
    update_log('-- CONNECTION UP --');
}



// Websocket event handler: called when a message is received.
// Should be a JSON payload.

function socket_message(msg) {
    var obj = JSON.parse(msg.data);
    switch ( obj.type ) {
        case 'chart-data':
            _update_chart_data(obj);
            break;
        case 'chart-threshold':
            _update_chart_threshold(obj);
            break;
        case 'log-message':
            update_log(obj.message);
            break;
        default:
            console.log('bad message: "'+msg.data+'"');
            break;
    }
}



// Updates the chart from an object with .ts, .raw and .agd values.

function _update_chart_data(data_object) {
    var ts = new Date(data_object.ts);
    chart_data_raw.push({t: ts, y: data_object.raw});
    chart_data_agd.push({t: ts, y: data_object.agd});
    if ( chart_data_raw.length > 100 ) {
        chart_data_raw.shift();
        chart_data_agd.shift();
    }
    chart.update();
}



// Updates chart thresholds from an object with .level and .value values.

function _update_chart_threshold(data_object) {
    chart.options.annotation.annotations[data_object.level-1].value = data_object.value;
    // We could skip chart.update():
    // Motive: data keeps coming in, this is superfluous.
    chart.update();
}



// Asks the user for a new threshold value and notifies the server about it.

function _prompt_level_threshold(level) {
    var new_value_str = prompt('New level '+level+' threshold:');
    var new_value = parseInt(new_value_str, 10);
    if ( isNaN(new_value) ) {
        return;
    }
    set_threshold(level, new_value);
}



// Appends the `s` text message to the `log` DOM element's innerText.
// Truncates initial `log` inner text if it holds more than a certain amount
// of messages (for now hardcoded at 40).

function update_log(s) {
    log.innerText += s + "\n";
    log_count++;
    if ( log_count > 45 ) {
        pos = log.innerText.indexOf("\n"); 
        log.innerText = log.innerText.substring(pos+1);
    }
}



// Appends a marker line to the log.

function mark_log() {
    if ( log.innerText.endsWith('-- MARK --\n') ) {
        clear_log();
    } else {
        update_log('-- MARK --');
    }
}



// Clear log.

function clear_log() {
    log.innerText = "";
    log_count = 0;
    update_log('-- LOG CLEARED --');
}



// Websocket event handler: called when the connection is closed.

function socket_close(e) {
    console.log('socket close');
    update_log('-- CONNECTION LOST --');
    socket = null;
}



// Initialize global objects.

window.onload = function() {
    chart = create_chart();
    socket = create_websocket();
    log = document.getElementById("log");
}



// threshold change request handler

function set_threshold(level, value) {
    _socket_send({
        action: "set_threshold",
        level: level,
        value: value
    });
}



// level button click handler.

function change_play_level(level) {
    _socket_send({
        action: "change_play_level",
        level: level
    });
}



// Log level change click handler.

function set_log_level() {
    var e = document.getElementById("logger_namespace");
    var namespace = e.options[e.selectedIndex].value;
    e = document.getElementById("logger_level");
    var level = e.options[e.selectedIndex].value;
    _socket_send({
        action: "set_log_level",
        namespace: namespace,
        level: level
    });
}



// Send an JSONified object over the websocket.

function _socket_send(obj) {
    if ( !socket ) {
        update_log('-- NOT CONNECTED --');
        return;
    }
    socket.send(JSON.stringify(obj));
}


// ----------------------------------------------------------------------------
// index.js
// ----------------------------------------------------------------------------

