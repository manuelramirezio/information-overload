var EventHandler = {
    afterCalled_archive: function()
    {
        var _is_archived = $(this).attr("data-is_archived") == "yes";
        $(this).find("label").text(
            _is_archived ? $(this).attr("data-label-no") : $(this).attr("data-label-yes")
        );
        $(this).attr("data-is_archived", _is_archived ? "no" : "yes");
        $(this).attr("data-action", _is_archived ? "archive" : "unarchive");
    },
    afterCalled_star: function()
    {
        var _action = $(this).attr("data-action");
        $(this).removeClass("is_starred");
        $(this).addClass(_action == "star" ? "is_starred" : "");
        $(this).attr("data-action", _action == "star" ? "unstar" : "star");
    },
    afterCalled_archive_all: function()
    {
        document.location.href = "?";
    }
}
EventHandler["afterCalled_unarchive"] = EventHandler["afterCalled_archive"];
EventHandler["afterCalled_unstar"] = EventHandler["afterCalled_star"];

$(document).ready(
    function()
    {
        $(".action").live(
            "click",
            function(e)
            {
                e.preventDefault();

                var _this = this;
                $.post(
                    $(this).attr("data-url"),
                    {
                        action: $(this).attr("data-action")
                    },
                    function(data, status, request)
                    {
                        if (request.status == 200)
                        {
                            $(_this).trigger("afterCalled");
                        }
                    }
                );

                return false;
            }
        );

        $(".action").live(
            "afterCalled",
            function()
            {
                var _action = $(this).attr("data-action");
                var _method = EventHandler["afterCalled_" + _action];
                if (! _method)
                {
                    return false;
                }

                _method.bind(this)();
            }
        );
        $(".input-labels").tag(
            {
                seperator: ",",
                afterUpdated: function(l)
                {
                    var _labels = new Array();
                    $(l).each(
                        function()
                        {
                            _labels.push($(this).text());
                        }
                    );

                    $.post(
                        $(this).attr("data-url"),
                        {
                            action: $(this).attr("data-action"),
                            labels: _labels.join(",")
                        },
                        function (data, status, request)
                        {
                        }
                    );
                }
            }
        );

        $(".connect_with").live(
            "click",
            function(e)
            {
                e.preventDefault();
            }
        );
    }
);


