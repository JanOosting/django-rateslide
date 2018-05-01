// Rateslide functions
$('.makecasebookmark').click(function() {
    // GetCenter, getZoom. Store it somewhere
    bm_center = viewer.viewport.getCenter(true);
    bm_zoom   = viewer.viewport.getZoom(true);
    bm_image  = viewer_image;
    var CaseId = $(this).val();
    var textinput = $('#txt_casebookmark').val();
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
            messageobj = JSON.parse(request.responseText);
            alert("Error submitting\nStatus :" + errorThrown + "\nError: " + messageobj.message)
        }
    });
});

$('.makequestionbookmark').click(function() {
    // GetCenter, getZoom. Store it somewhere
    bm_center = viewer.viewport.getCenter(true);
    bm_zoom   = viewer.viewport.getZoom(true);
    bm_image  = viewer_image;
    var QuestionId = $(this).val();
    var textinput = $('#txt_questionbookmark_' + QuestionId).val();
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
            messageobj = JSON.parse(request.responseText);
            alert("Error submitting\nStatus :" + errorThrown + "\nError: " + messageobj.message)
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
    var editname = $(this).attr("name");
    if ($(this).val() !== "") {
        $("#btn_" + editname).removeAttr("disabled");
    } else {
        $("#btn_" + editname).attr("disabled","disabled");
    };
});

$('.deletecasebookmark').click(function() {
    var CaseId = $(this).val();
    var bookmarkid = $('#lb_casebookmark').val();
    $.ajax({
        url : "/rateslide/casebookmark/" + bookmarkid + "/",
        dataType: 'json',
        contentType: "application/json",
        type : "DELETE",
        data : JSON.stringify({
            'Case' : CaseId,
        }),
        success : function(result){
            window.location.reload();
        },
        error : function (request, textStatus, errorThrown) {
            alert("Error deleting\nStatus :" + textStatus + "\nError: " + errorThrown)
        }
    });
});

$('.deletequestionbookmark').click(function() {
    var QuestionId = $(this).val();
    var bookmarkid = $('#lb_questionbookmark_' + QuestionId).val();
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

var current_line = "";


function initialize_case() {
    annotations = new OpenSeadragon.Annotations({ viewer });
    // annotations.setEnable(false);
    annotations.model.addHandler('ANNOTATIONRELEASE_EVENT', (annotation) => {
        var unitname = "px";
        if (current_line) {
            var l = annotations.getLength(annotation);
            if (viewer.scalebarInstance) {
                if (viewer.scalebarInstance.pixelsPerMeter !== 0) {
                    l = 1000 * (l / viewer.scalebarInstance.pixelsPerMeter);
                    unitname="mm"
                } else {
                    unitname="px"
                }
            };
            // This object is meant for histoslide-annotation model
            var line_object = {
              slideid: get_slideid(viewer_image) ,
              length: l,
              length_unit: unitname,
              annotation: annotation.slice(0, 2),
            };
            document.getElementById(current_line + "-length").value = l.toPrecision(3) + " " + unitname;
            document.getElementById(current_line).value = JSON.stringify(line_object);
        };
    });
};


$('.rs-line-button').click(function() {
    var line_color =  $(this).val();
    if (current_line === $(this).attr("id").replace("-button","")) {
        current_line = "";
        annotations.setEnable(false);
    } else {
        current_line = $(this).attr("id").replace("-button","");
        annotations.setEnable(true);
        annotations.model.annotationcolor = line_color;
        annotations.model.annotationname = current_line;
    };

});