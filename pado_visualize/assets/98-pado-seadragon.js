$(document).ready(function() {
    let sources = $("#seadragon-container").attr("data-tilesources");

    if (!sources) {
        console.log("no tilesources set " + sources);
        return;
    }
    var viewer = new OpenSeadragon({
        id: "seadragon-container",
            tileSources: sources,
            prefixUrl: "/slide",
            showNavigator: true,
            showRotationControl: true,
            animationTime: 0.5,
            blendTime: 0.1,
            constrainDuringPan: true,
            maxZoomPixelRatio: 2,
            minZoomLevel: 1,
            visibilityRatio: 1,
            zoomPerScroll: 2,
            timeout: 120000,
    });
    viewer.addHandler("open", function() {
        // To improve load times, ignore the lowest-resolution Deep Zoom
        // levels.  This is a hack: we can't configure the minLevel via
        // OpenSeadragon configuration options when the viewer is created
        // from DZI XML.
        viewer.source.minLevel = 8;
    });

    console.log("initialized osd for " + sources);
});
