window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
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
