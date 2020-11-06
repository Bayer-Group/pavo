
console.log('If you see this alert, then your custom JavaScript script has run!');

$(document).ready(() => {
    $( "body" ).delegate( ".thumbnail-card", "click", function() {
        console.log("yeah");
        // $.get( "http://127.0.0.1:9000" );
    });

    $( "body" ).delegate( ".pado-body", "mousemove", function(e) {
        $(this).css({backgroundPositionX: (e.clientX * 0.01) + "px"});
        console.log(e.clientX, e.clientY);
    });

});

