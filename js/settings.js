function saveParams (name) {

    var auto_room = $('form input[name="auto_room"]');
    var skip_tuto = $('form input[name="skip_tutorial"]');
    var skip_survey = $('form input[name="skip_survey"]');
    var trial = $('form input[name="trial"]');

    // Check for parameters compatibility
    if (name === "trial") {

        skip_survey.removeProp("checked");
        skip_tuto.removeProp("checked");
        auto_room.removeProp("checked");

    } else {
        trial.removeProp("checked");
    }

    var data = $('#parameterform').serialize();

    // include unchecked checkboxes. use filter to only include unchecked boxes.
    $.each($('form input[type=checkbox]')
    .filter(function(idx){
        return $(this).prop('checked') === false
    }),
    function(idx, el){
        // attach matched element names to the formData with a chosen value.
        var emptyVal = "off";
        data += '&' + $(el).attr('name') + '=' + emptyVal;
    }
    );

    $.post("", data);
}


