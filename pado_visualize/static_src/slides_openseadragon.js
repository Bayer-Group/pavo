import "./_base.js";
// base and annotorious css
import "./css/slides_openseadragon.scss";
import "@recogito/annotorious/src/ImageAnnotator.scss";

import { documentReady } from "./_base";
import OpenSeaDragon from "openseadragon";
import * as Annotorious from "@recogito/annotorious-openseadragon";
import * as SelectorPack from "@recogito/annotorious-selector-pack";

/**
 * Setup the openseadragon viewer
 * @param options
 * @param annoOptions
 * @returns {Promise<unknown>}
 */
function setupOpenSeadragonViewer(options, annoOptions) {
  const defaultOptions = {
    prefixUrl: "/images/",
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
  };
  const defaultAnnoOptions = {
    annotationUrl: null,
    formatter: formatter,
  };

  return new Promise((resolve) => {
    documentReady(function () {
      let osdOptions = Object.assign({}, defaultOptions, options);

      let osdviewer = OpenSeaDragon(osdOptions);
      osdviewer.addHandler("open", function () {
        // To improve load times, ignore the lowest-resolution Deep Zoom
        // levels.  This is a hack: we can't configure the minLevel via
        // OpenSeadragon configuration options when the viewer is created
        // from DZI XML.
        osdviewer.source.minLevel = 8;
      });

      let aOptions = Object.assign({}, defaultAnnoOptions, annoOptions);

      // Initialize the Annotorious plugin
      let anno = Annotorious(osdviewer, {
        formatter: aOptions.formatter,
      });

      // add selectorpack to fix click errors
      SelectorPack(anno);

      anno.on("clickAnnotation", function (a) {
        console.log(a);
        anno.fitBounds(a, false);
      });

      // Load annotations in W3C WebAnnotation format
      const annotation_url = aOptions.annotationUrl;
      anno.loadAnnotations(annotation_url);

      // Attach handlers to listen to events
      anno.on("createAnnotation", function () {
        // Do something
        console.log("created annotation");
      });

      resolve(osdviewer);
    });
  });
}

function formatter(annotation) {
  if (annotation.body.length > 0) {
    const colour = stringToColour(annotation.body[0].value);
    return {
      style: `stroke: ${colour}; fill: ${hexToRgbA(colour)}`,
    };
  }
}

function stringToColour(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  let colour = "#";
  for (let i = 0; i < 3; i++) {
    const value = (hash >> (i * 8)) & 0xff;
    colour += ("00" + value.toString(16)).substr(-2);
  }
  return colour;
}

function hexToRgbA(hex) {
  let c;
  if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
    c = hex.substring(1).split("");
    if (c.length === 3) {
      c = [c[0], c[0], c[1], c[1], c[2], c[2]];
    }
    c = "0x" + c.join("");
    return (
      "rgba(" + [(c >> 16) & 255, (c >> 8) & 255, c & 255].join(",") + ",0.3)"
    );
  }
  throw new Error("Bad Hex");
}

// export the setup function
export default {
  setupOpenSeadragonViewer: setupOpenSeadragonViewer,
};
