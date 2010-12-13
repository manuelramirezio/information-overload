$(document).ready(
    function()
    {
        $(".message").find(".subject-content").live(
            "click",
            function(e)
            {
                if (e.which != 1) return;

                var _url = $(this).parentsUntil(".message").parent().attr("data-url");
                if (! $.trim(_url)) return false;
                document.location.href = _url;

                e.preventDefault();
                return;
            }
        );
    }
);


