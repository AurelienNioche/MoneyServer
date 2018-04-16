function showModal(room_id) {
        $("#roomToDelete").val(room_id);
        $('#myModal').modal();
        $("div [class='modal-body']").html(
            "<p> Do you want to delete room <strong>" + room_id  +"</strong>? </p>"
        );
}



function deleteRoom(room_id) {
    document.getElementById("delete-room-" + room_id).submit()
}

function setTabActive(){
    document.getElementById("room_management_tab").setAttribute("class", "active")
}