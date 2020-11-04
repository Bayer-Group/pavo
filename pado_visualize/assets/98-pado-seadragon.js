window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        load_open_seadragon: function(url_pathname) {
            if (!url_pathname.startsWith("/slide/")) {
                console.log("no seadragon slide " + url_pathname);
                return "";
            }
            let sources = url_pathname + "/image.dzi"
            let viewer = new OpenSeadragon({
                id: "seadragon-container",
                tileSources: sources,
                prefixUrl: "/assets/",
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
            return sources;
        }
    }
});
