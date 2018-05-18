
    function goToFileName(element) {
        var filename = element.options[element.selectedIndex].text;
        start();
        refreshLogs(filename, 0);
    }

    function stop () {
        LOGS.refresh = false;

    }

    function start () {
        LOGS.refresh = true;

    }

    function refreshLogs(filename, n_lines) {

        if (LOGS.refresh) {

            if (filename === undefined) {
                filename = $("#logfile").find(":selected").text();
            }

            if (n_lines === undefined) {
                 n_lines = $("#logs").text().split("\n").length;
            }

            $.ajax({
                type: "GET",
                url: '/logs/?refresh_logs=1&filename=' + filename + '&n_lines=' + n_lines,
                success: function (data) {
                    if (data["logs"].length > 0) {
                        $('#logs').html(data["logs"]);
                    }
                    ScrollToBottom();
                }

            });
        }
    }

    function scrollToBottom() {
         // Make the scrollbar go down
         LOGS.logs.scrollTop = LOGS.logs.scrollHeight;
    }
