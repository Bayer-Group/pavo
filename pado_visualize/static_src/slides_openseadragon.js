import "./_base.js";
// base and annotorious css
import "./css/slides_openseadragon.scss";
import "@recogito/annotorious/src/ImageAnnotator.scss";

import { documentReady } from "./_base";
import OpenSeaDragon from "openseadragon";
import * as Annotorious from "@recogito/annotorious-openseadragon";
import * as SelectorPack from "@recogito/annotorious-selector-pack";

/* GLOBAL STATE */
const _osdViewers = new Map(); // maps viewer ids to osd instances
const _osdAnnos = new Map(); // maps viewer ids to annotorious instances

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
      _osdViewers.set(osdOptions.id, osdviewer);
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
      _osdAnnos.set(osdOptions.id, anno);

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

/**
 * return the corresponding Openseadragon instance
 * @param viewerId
 * @returns {any}
 */
function getViewer(viewerId) {
  return _osdViewers.get(viewerId);
}

/**
 * return the corresponding Annotorious instance
 * @param viewerId
 * @returns {any}
 */
function getAnno(viewerId) {
  return _osdAnnos.get(viewerId);
}

/**
 * Attach TileSource
 * @param viewer_id
 * @param tileSource
 * @param options
 */
function attachTileSource(viewer_id, tileSource, options) {
  const viewer = getViewer(viewer_id);
  options = Object.assign({}, options || {}, tileSource);
  viewer.addTiledImage(options);
}

/**
 * return the prediction tilesource
 * @param viewer_id
 * @param idx
 * @returns {OpenSeadragon.TiledImage|*}
 */
function getTileSource(viewer_id, idx) {
  const viewer = getViewer(viewer_id);
  return viewer.world.getItemAt(Number(idx) + 1);
}

/**
 * removes the tileSource at index + 1
 * @param viewer_id
 * @param idx
 */
function removeTileSource(viewer_id, idx) {
  const viewer = getViewer(viewer_id);
  const item = viewer.world.getItemAt(Number(idx) + 1);
  viewer.world.removeItem(item);
}

/**
 * set the opacity of the tileSource at index + 1
 * @param viewer_id
 * @param idx
 * @param opacity
 */
function setPredictionOpacity(viewer_id, idx, opacity) {
  const viewer = getViewer(viewer_id);
  viewer.world.getItemAt(Number(idx) + 1).setOpacity(opacity);
}

/**
 * set the annotation visibility
 * @param viewer_id
 * @param visible
 */
function setAnnotationVisibility(viewer_id, visible) {
  const anno = getAnno(viewer_id);
  anno.setVisible(visible);
}

/* UTILITIES */

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
  attachTileSource: attachTileSource,
  getTileSource: getTileSource,
  removeTileSource: removeTileSource,
  getViewer: getViewer,
  getAnno: getAnno,
  setPredictionOpacity: setPredictionOpacity,
  setAnnotationVisibility: setAnnotationVisibility,
};
