
    function getDatabaseURL() {

        $("#progressbar").addClass("active");
        $("#progressbar").text("");
        $("#progressdiv").hide();
        $("#progressdiv").show();

        $.ajax({
            method: "GET",
            url: "/data/?sqlite=true",
            success: function (data) {
                downloadDB(data["url"]);
                $("#progressbar").text("Conversion done!");
                $("#progressbar").removeClass("active");
            }
        })
    }

    function flushDB () {
        $("#progressbar").addClass("active");
        $("#progressbar").text("");
        $("#progressdiv").hide();
        $("#progressdiv").show();

        $.ajax({
            method: "GET",
            url: "/data/?flush=true",
            success: function () {
                console.log("Flushed!");
                $("#progressbar").text("Database flushed!");
                $("#progressbar").removeClass("active");
            }
        });

    }

    function downloadDB(url) {
        var link = document.createElement("a");
        link.href = "/static/" + url;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }