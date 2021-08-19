import "./base";
import "./css/slides.scss";

/* global fetch, DOMParser */
import { documentReady } from "./js/common";
import React, {useState, useEffect} from 'react';
import {render} from 'react-dom';

import DeckGL, {OrthographicView, COORDINATE_SYSTEM} from 'deck.gl';
import {TileLayer} from '@deck.gl/geo-layers';
import {BitmapLayer} from '@deck.gl/layers';
import {load} from '@loaders.gl/core';
import {clamp} from 'math.gl';

const INITIAL_VIEW_STATE = {
  target: [13000, 13000, 0],
  zoom: -7,
};

const ROOT_URL =
  '/static/dzis';

function getTooltip({tile, bitmap}) {
  if (tile && bitmap) {
    return `\
    tile: x: ${tile.x}, y: ${tile.y}, z: ${tile.z}
    (${bitmap.pixel[0]},${bitmap.pixel[1]}) in ${bitmap.size.width}x${bitmap.size.height}`;
  }
  return null;
}

export default function App({autoHighlight = true, onTilesLoad}) {
  const [dimensions, setDimensions] = useState(null);
  const [maxLayer, setMaxLayer] = useState(null);
  const [minZoom, setMinZoom] = useState(null);

  useEffect(() => {
    const getMetaData = async () => {
      const dziSource = `${ROOT_URL}/tg20022.dzi`;
      const response = await fetch(dziSource);
      const xmlText = await response.text();
      const dziXML = new DOMParser().parseFromString(xmlText, 'text/xml');

      if (Number(dziXML.getElementsByTagName('Image')[0].attributes.Overlap.value) !== 0) {
        // eslint-disable-next-line no-undef, no-console
        console.warn('Overlap parameter is nonzero and should be 0');
      }
      const height = Number(dziXML.getElementsByTagName('Size')[0].attributes.Height.value);
      const width = Number(dziXML.getElementsByTagName('Size')[0].attributes.Width.value);
      const tileSize = Number(dziXML.getElementsByTagName('Image')[0].attributes.TileSize.value);
      setDimensions({
        height: height,
        width: width,
        tileSize: tileSize
      });
      const maxLayer = Math.ceil(Math.log2(Math.max(width, height)));
      setMaxLayer(maxLayer);
      const minZoom = - Math.ceil(Math.log2(Math.max(width, height)) - Math.log2(tileSize));
      setMinZoom(minZoom);
    };
    getMetaData();
  }, []);

  const tileLayer =
    dimensions &&
    new TileLayer({
      pickable: autoHighlight,
      tileSize: dimensions.tileSize,
      autoHighlight,
      highlightColor: [60, 60, 60, 30],
      minZoom: minZoom,
      maxZoom: 0,
      coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
      extent: [0, 0, dimensions.width, dimensions.height],
      getTileData: ({x, y, z}) => {
        return load(`${ROOT_URL}/tg20022_files/${maxLayer + z}/${x}_${y}.jpeg`);
      },
      onViewportLoad: onTilesLoad,

      renderSubLayers: props => {
        const {
          bbox: {left, bottom, right, top}
        } = props.tile;
        const {width, height} = dimensions;
        return new BitmapLayer(props, {
          data: null,
          image: props.data,
          bounds: [
            clamp(left, 0, width),
            clamp(bottom, 0, height),
            clamp(right, 0, width),
            clamp(top, 0, height)
          ]
        });
      }
    });

  return (
    <DeckGL
      views={[new OrthographicView({id: 'ortho'})]}
      layers={[tileLayer]}
      initialViewState={INITIAL_VIEW_STATE}
      controller={true}
      getTooltip={getTooltip}
    />
  );
}

export function renderToDOM(container) {
  render(<App />, container);
}


window.slides_deckgl_render_to_dom = renderToDOM;
