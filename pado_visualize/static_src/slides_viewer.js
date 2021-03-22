import { documentReady } from "./js/common";

import OpenSeadragon from "openseadragon";
import images from "../../node_modules/openseadragon/build/openseadragon/images/*.png";

function setupOpenSeadragonViewer(options) {
  const navImages = (function (imageObj) {
    /* to make parcel aware of the image assets we need
     * to explicitly reference them in a js module here */
    const _mapToKey = (filename) => {
      let name = filename.split("_")[0];
      if (name === "zoomin") {
        name = "zoomIn";
      } else if (name === "zoomout") {
        name = "zoomOut";
      }
      return name;
    };
    const _mapToAction = (action) => {
      if (action === "grouphover") {
        return "GROUP";
      } else if (action === "pressed") {
        return "DOWN";
      } else {
        return action.toUpperCase();
      }
    };

    let out = {};
    for (let [sourceFilename, targetFilename] of Object.entries(imageObj)) {
      // eslint-disable-next-line no-unused-vars
      let [name, action, _ext] = sourceFilename.split(/[_.]/);
      name = _mapToKey(name);
      action = _mapToAction(action);
      if (!Object.prototype.hasOwnProperty.call(out, name)) {
        out[name] = {};
      }
      out[name][action] = targetFilename;
    }
    return out;
  })(images);

  const defaultOptions = {
    prefixUrl: "",
    navImages: navImages,
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

  return new Promise((resolve) => {
    documentReady(function () {
      let osdOptions = Object.assign({}, options, defaultOptions);

      let osdviewer = new OpenSeadragon(osdOptions);
      osdviewer.addHandler("open", function () {
        // To improve load times, ignore the lowest-resolution Deep Zoom
        // levels.  This is a hack: we can't configure the minLevel via
        // OpenSeadragon configuration options when the viewer is created
        // from DZI XML.
        window.osdviewer.source.minLevel = 8;
      });

      resolve(osdviewer);
      // osdvieweranno = OpenSeadragon.Annotorious(window.osdviewer);
      /* anno.loadAnnotations(annotations); */
    });
  });
}

window.setupOpenSeadragonViewer = setupOpenSeadragonViewer;
