function setUpWebSocket() {
    // get current room_id
    var current_url = new URL(window.location.href);
    var room_id = current_url.searchParams.get("room_id");
    var url = "ws://localhost:8000/ws/" + room_id;
    websocket = new WebSocket(url);
    websocket.onopen = function (ev) { onOpen(ev) };
    websocket.onmessage = function (ev) { onMessage(ev) };
}

function onOpen(ev) {
    console.log("Open websocket");
}

function onMessage(ev) {

    var data = JSON.parse(ev.data);

    if (data.message) {
        console.log(data.message);
    } else {
        plotUserStates(data);
    }

}

function plotUserStates (data) {

   new Morris.Donut({

    element: 'user-states',
    data: data

   });


}