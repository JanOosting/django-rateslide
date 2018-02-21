// Rateslide functions
$('.makecasebookmark').click(function() {
    // GetCenter, getZoom. Store it somewhere
    bm_center = viewer.viewport.getCenter(true);
    bm_zoom   = viewer.viewport.getZoom(true);
    bm_image  = viewer_image;
    var CaseId = $(this).val();
    var textinput = $('#txt_casebookmark').val()
    $.ajax({
        url : "/rateslide/casebookmark/0/",
        dataType: 'json',
        contentType: "application/json",
        type : "POST",
        data : JSON.stringify({
            'Text' : textinput,
            'Case' : CaseId,
            'Slide' : viewer_image.replace("/histoslide/","").replace(".dzi",""),
            'CenterX' : bm_center.x.toString(),
            'CenterY' : bm_center.y.toString(),
            'Zoom' : bm_zoom.toString(),
            'order' : '1'
        }),
        success : function(result){
            window.location.reload();
        },
        error : function (request, textStatus, errorThrown) {
            alert("Error submitting\nStatus :" + textStatus + "\nError: " + errorThrown)
        }
    });
});

$('.makequestionbookmark').click(function() {
    // GetCenter, getZoom. Store it somewhere
    bm_center = viewer.viewport.getCenter(true);
    bm_zoom   = viewer.viewport.getZoom(true);
    bm_image  = viewer_image;
    var QuestionId = $(this).val();
    var textinput = $('#txt_questionbookmark_' + QuestionId).val()
    $.ajax({
        url : "/rateslide/questionbookmark/0/",
        dataType: 'json',
        contentType: "application/json",
        type : "POST",
        data : JSON.stringify({
            'Text' : textinput,
            'Question' : QuestionId,
            'Slide' : viewer_image.replace("/histoslide/","").replace(".dzi",""),
            'CenterX' : bm_center.x.toString(),
            'CenterY' : bm_center.y.toString(),
            'Zoom' : bm_zoom.toString(),
            'order' : '1'
        }),
        success : function(result){
            window.location.reload();
        },
        error : function (request, textStatus, errorThrown) {
            alert("Error submitting\nStatus :" + textStatus + "\nError: " + errorThrown)
        }
    });
});

function gotoBookmark(bm) {
    bm_center = new OpenSeadragon.Point(
        bm.CenterX,
        bm.CenterY
    );
    bm_zoom = bm.Zoom;
    bm_image = bm.Slide + ".dzi";
    bm_goto=true;
    $("#slide"+bm.Slide).prop("checked",true);
    open_slide("/histoslide/"+bm_image);
    // Change selected slide button
}

$(".goto_casebookmark").click(function(ev) {
    $.getJSON("/rateslide/casebookmark/" + $(this).attr("value") + "/", {}, gotoBookmark );
});

$(".goto_questionbookmark").click(function(ev) {
    $.getJSON("/rateslide/questionbookmark/" + $(this).attr("value") + "/", {}, gotoBookmark);
});

$('.bookmarktext').keyup(function () {
    // Disable submit bookmark button when text is empty
    var editname = $(this).attr("name")
    if ($(this).val() != "") {
        $("#btn_" + editname).removeAttr("disabled");
    } else {
        $("#btn_" + editname).attr("disabled","disabled");
    };
});

$('.deletequestionbookmark').click(function() {
    var QuestionId = $(this).val();
    var bookmarkid = $('#lb_questionbookmark_' + QuestionId).val()
    $.ajax({
        url : "/rateslide/questionbookmark/" + bookmarkid + "/",
        dataType: 'json',
        contentType: "application/json",
        type : "DELETE",
        data : JSON.stringify({
            'Question' : QuestionId,
        }),
        success : function(result){
            window.location.reload();
        },
        error : function (request, textStatus, errorThrown) {
            alert("Error deleting\nStatus :" + textStatus + "\nError: " + errorThrown)
        }
    });
});
