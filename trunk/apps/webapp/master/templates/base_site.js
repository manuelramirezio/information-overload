$(document).ready(
    function()
    {
        $(".datetime").live(
            "click",
            function()
            {
                var _datetime = $(this).attr("data-datetime");
                var _since = $(this).attr("data-since");

                var _is_datetime = $(this).attr("data-which") == "datetime";
                $(this).find("span.value").text(
                    _is_datetime ? _since : _datetime
                );
                $(this).attr(
                    "data-which",
                    _is_datetime ? "since" : "datetime"
                );
                $(this).blur();
            }
        );

        setTimeout(
            function()
            {
                if ($("#service-messages .msg").length < 1) return false;

                $("#service-messages").hide("slide", {direction: "up"});
            },
            3000
        );
    }
);
