window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        load_open_seadragon: function(url_pathname) {
            if (!url_pathname.startsWith("/slide/overview/")) {
                console.log("no seadragon slide " + url_pathname);
                return "";
            }
            let sources = url_pathname + "/image.dzi"
            window.osdviewer = new OpenSeadragon({
                id: "seadragon-container",
                tileSources: sources,
                prefixUrl: "/assets/img/openseadragon-icons/",
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
            /*
            window.osdviewer.addHandler("open", function() {
                // To improve load times, ignore the lowest-resolution Deep Zoom
                // levels.  This is a hack: we can't configure the minLevel via
                // OpenSeadragon configuration options when the viewer is created
                // from DZI XML.
                window.osdviewer.source.minLevel = 8;
            });
            */
            console.log("initialized osd for " + sources);
            return sources;
        },
        load_open_seadragon_multi: function(url_pathname) {
            if (!url_pathname.startsWith("/slide/tiles/")) {
                console.log("no seadragon slide " + url_pathname);
                return "";
            }
            let sources = url_pathname + "/image.dzi";

            $(document).ready(function() {
                OpenSeadragonMultiApp.init({
                    id: "seadragon-multi-container",
                    prefixUrl: "/assets/img/openseadragon-icons/",
                    preserveViewport: true,
                    zoomPerScroll: 2,
              });
            });
            // OpenSeadragonMultiApp.init();

            console.log("initialized osd for " + sources);
            return sources;
        }


    }
});
