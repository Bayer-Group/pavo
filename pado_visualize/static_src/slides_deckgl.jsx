import "./css/slides_deckgl.scss";
import React, { useEffect, useState } from "react";
import { render } from "react-dom";
import PropTypes from "prop-types";

import DeckGL, { COORDINATE_SYSTEM } from "deck.gl";
import { OrbitView } from "@deck.gl/core";
import { TileLayer } from "@deck.gl/geo-layers";
import { BitmapLayer, GeoJsonLayer } from "@deck.gl/layers";
import { load } from "@loaders.gl/core";
import { clamp } from "math.gl";

const INITIAL_VIEW_STATE = {
  target: [13000, 13000, 0],
  zoom: -5,
  rotationX: 72.0,
  orthographic: true,
  near: 0.00001,
  far: 20000,
};

const CONTROLLER_STATE = {
  dragPan: true,
  inertia: true,
};

function getTooltip({ tile, bitmap }) {
  if (tile && bitmap) {
    return `\
    tile: x: ${tile.x}, y: ${tile.y}, z: ${tile.z}
    (${bitmap.pixel[0]},${bitmap.pixel[1]}) in ${bitmap.size.width}x${bitmap.size.height}`;
  }
  return null;
}

function stringToColour(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  let colour = [];
  for (let i = 0; i < 3; i++) {
    const value = (hash >> (i * 8)) & 0xff;
    colour.push(value);
  }
  return colour;
}

function App({ slideUrl, annotationUrl, autoHighlight = true, onTilesLoad }) {
  const [dimensions, setDimensions] = useState(null);

  useEffect(() => {
    const getMetaData = async () => {
      const dziSource = `${slideUrl}`;
      const response = await fetch(dziSource);
      const xmlText = await response.text();
      const dziXML = new DOMParser().parseFromString(xmlText, "text/xml");

      if (
        Number(
          dziXML.getElementsByTagName("Image")[0].attributes.Overlap.value
        ) !== 0
      ) {
        // eslint-disable-next-line no-undef, no-console
        console.warn("Overlap parameter is nonzero and should be 0");
      }
      setDimensions({
        height: Number(
          dziXML.getElementsByTagName("Size")[0].attributes.Height.value
        ),
        width: Number(
          dziXML.getElementsByTagName("Size")[0].attributes.Width.value
        ),
        tileSize: Number(
          dziXML.getElementsByTagName("Image")[0].attributes.TileSize.value
        ),
      });
    };
    getMetaData();
  }, []);

  const tileRoot = slideUrl.split("/").slice(0, -1).join("/");
  const tileLayer =
    dimensions &&
    new TileLayer({
      pickable: autoHighlight,
      tileSize: dimensions.tileSize,
      autoHighlight,
      highlightColor: [60, 60, 60, 20],
      minZoom: -7,
      maxZoom: 0,
      coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
      extent: [0, 0, dimensions.width, dimensions.height],
      getTileData: ({ x, y, z }) => {
        const maxLevel = Math.ceil(
          Math.log2(Math.max(dimensions.width, dimensions.height))
        );
        return load(`${tileRoot}/image_files/${maxLevel + z}/${x}_${y}.jpeg`);
      },
      onViewportLoad: onTilesLoad,

      renderSubLayers: (props) => {
        const {
          // eslint-disable-next-line react/prop-types
          bbox: { left, bottom, right, top },
          // eslint-disable-next-line react/prop-types
        } = props.tile;
        const { width, height } = dimensions;
        return new BitmapLayer(props, {
          data: null,
          // eslint-disable-next-line react/prop-types
          image: props.data,
          bounds: [
            clamp(left, 0, width),
            clamp(bottom, 0, height),
            clamp(right, 0, width),
            clamp(top, 0, height),
          ],
        });
      },
    });

  const jsonLayer = new GeoJsonLayer({
    id: "geojson",
    data: annotationUrl,
    opacity: 0.8,
    stroked: false,
    filled: true,
    extruded: true,
    wireframe: true,
    getElevation: (f) => {
      return (
        100.0 * Math.min(60.0, Math.sqrt(300000.0 / f.properties.area)) + 100.0
      );
    },
    getFillColor: (f) => {
      return stringToColour(f.properties.classification.name);
    },
    getLineColor: [0, 0, 0],
    pickable: true,
  });

  return (
    <DeckGL
      views={[
        new OrbitView({
          id: "orbitview",
        }),
      ]}
      layers={[tileLayer, jsonLayer]}
      initialViewState={INITIAL_VIEW_STATE}
      controller={CONTROLLER_STATE}
      getTooltip={getTooltip}
    />
  );
}

App.propTypes = {
  slideUrl: PropTypes.string,
  annotationUrl: PropTypes.string,
  autoHighlight: PropTypes.bool,
  onTilesLoad: PropTypes.func,
};

export default {
  renderToDOM: (container, slideUrl, annotationUrl) => {
    render(
      <App slideUrl={slideUrl} annotationUrl={annotationUrl} />,
      container
    );
  },
};
