import "./css/slides_deckgl.scss";
import React, { useState, useEffect } from "react";
import { render } from "react-dom";
import PropTypes from "prop-types";

import DeckGL, { OrthographicView, COORDINATE_SYSTEM } from "deck.gl";
import { TileLayer } from "@deck.gl/geo-layers";
import { BitmapLayer } from "@deck.gl/layers";
import { load } from "@loaders.gl/core";
import { clamp } from "math.gl";

const INITIAL_VIEW_STATE = {
  target: [13000, 13000, 0],
  zoom: -7,
};

function getTooltip({ tile, bitmap }) {
  if (tile && bitmap) {
    return `\
    tile: x: ${tile.x}, y: ${tile.y}, z: ${tile.z}
    (${bitmap.pixel[0]},${bitmap.pixel[1]}) in ${bitmap.size.width}x${bitmap.size.height}`;
  }
  return null;
}

function App({ slideUrl, autoHighlight = true, onTilesLoad }) {
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
      highlightColor: [60, 60, 60, 200],
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

  return (
    <DeckGL
      views={[new OrthographicView({ id: "ortho" })]}
      layers={[tileLayer]}
      initialViewState={INITIAL_VIEW_STATE}
      controller={true}
      getTooltip={getTooltip}
    />
  );
}

App.propTypes = {
  slideUrl: PropTypes.string,
  autoHighlight: PropTypes.bool,
  onTilesLoad: PropTypes.func,
};

export default {
  renderToDOM: (container, slideUrl) => {
    render(<App slideUrl={slideUrl} />, container);
  },
};
