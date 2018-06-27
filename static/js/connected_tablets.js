function setUpWebSocket() {
    var url = "ws://127.0.0.1/ws/connection/";
    websocket = new WebSocket(url);
    websocket.onopen = function (ev) { onOpen(ev) };
    websocket.onmessage = function (ev) { onMessage(ev) };
}

function onOpen(ev) {
    console.log("Open websocket");
    websocket.send(JSON.stringify({ connect: "true" }));
}

function onMessage(ev) {

    console.log("Received msg.");
    var data = JSON.parse(ev.data);

    if (data.html) {
        $('#update').html(data.html)
    } else {
        alert('Error on updating data' + data.toString())
    }

}
