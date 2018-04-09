function saveParams () {

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


