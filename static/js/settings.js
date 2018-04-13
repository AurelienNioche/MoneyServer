function saveParams (name) {

    // Check for parameters compatibility
    if (name === "trial") {
        $('form input[name="skip_tutorial"]').removeProp("checked");
        $('form input[name="skip_survey"]').removeProp("checked");

    } else {
        $('form input[name="trial"]').removeProp("checked");
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


