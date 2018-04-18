function submitForm(e) {

    if (e.keyCode === 13) {
        $.post("/new_room/", $("form").serialize())
            .done(function( data ) { $("#form-div").html(data);});

    }

}