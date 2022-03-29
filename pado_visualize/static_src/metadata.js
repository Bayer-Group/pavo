import "./_base.js";
import "./css/metadata.scss";

import * as LineUpJS from "lineupjs";


/**
 * clear a node
 */
function clearNode(node) {
  if (node.children.length > 0) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }
}


function getGroupedRowsHeight(numRows, rowHeight= 25, marginHeight = 2) {
  return `${numRows * (rowHeight + marginHeight)}px`;
}

/**
 * return thumbnailSize for fitting numImages thumbnails into rectangle
 * @param nodeHeight
 * @param nodeWidth
 * @param numImages
 * @returns {number}
 */
function getOptimalThumbnailSize(nodeHeight, nodeWidth, numImages) {
  const rxy = nodeWidth / nodeHeight;
  const ryx = nodeHeight / nodeWidth;
  const px = Math.ceil(Math.sqrt(numImages * rxy));
  let sx, sy;
  if (Math.floor(px * ryx) * px < numImages) {
    sx = nodeHeight / Math.ceil(px * ryx);
  } else {
    sx = nodeWidth / px;
  }
  const py = Math.ceil(Math.sqrt(numImages * ryx));
  if (Math.floor(py * rxy) * py < numImages) {
    sy = nodeWidth / Math.ceil(py * rxy);
  } else {
    sy = nodeHeight / py;
  }
  return Math.max(sx, sy);
}


/**
 * setup our lineup viewer
 */
function setupLineUp(options) {
  const defaultOptions = {
    id: null,
    metadata: [],
  };
  const luOptions = Object.assign({}, defaultOptions, options);
  const luElement = document.getElementById(luOptions.id);

  /* --- Renderers --------------------------------------------------------- */

  class ThumbnailRenderer {
    constructor() {
      this.title = "ThumbnailRenderer";
    }

    canRender(col) {
      return col instanceof LineUpJS.StringColumn;
    }

    create(col) {
      return {
        template: `<div class="thumbnail-container"><img alt="thumbnail" class="thumbnail" src=""></div>`,
        update: (node, row, i, group) => {
          const img = node.firstChild;
          img.src = `/slides/thumbnail_${row.v["image_url"]}_200.jpg`;

          if (col.isGroupedBy() === 0) {
            // we're grouping by image, display the first node and expand the view
            if (i === 0) {
              const multiRowSize = getGroupedRowsHeight(group.order.length, rowHeight);
              node.style.height = multiRowSize;
              img.style.maxHeight = multiRowSize;
              img.style.maxWidth = multiRowSize;
              node.style.display = "flex";
            } else {
              // the other rows should show nothing
              node.style.display = "none";
            }

          } else {
            // we're grouping something else
            const singleRowSize = getGroupedRowsHeight(1, rowHeight);
            node.style.height = singleRowSize;
            img.style.maxHeight = singleRowSize;
            img.style.maxWidth = singleRowSize;
            node.style.display = "flex";

          }
        },
      };
    }

    // noinspection JSUnusedGlobalSymbols
    createGroup(col, context) {
      return {
        template: `<div class="thumbnail-container"></div>`,
        update: (node, group) => {
          context.tasks.groupRows(col, group, null, (rows) => {
            clearNode(node);
            const height = groupRowHeight;
            const width = col.getWidth();

            const uniqueImageUrls = [...new Set(rows.map(row => row.v["image_url"]))]
            const thumbnailSize = getOptimalThumbnailSize(height, width, uniqueImageUrls.length);

            for (const imageUrl of uniqueImageUrls) {
              let img = document.createElement("img");
              img.src = `/slides/thumbnail_${imageUrl}_200.jpg`;
              img.classList.add("thumbnail");
              img.style.maxHeight = `${thumbnailSize}px`;
              img.style.maxWidth = `${thumbnailSize}px`;
              node.appendChild(img);
            }
          });
        },
      };
    }

  }

  class MyActionRenderer {
    constructor() {
      this.title = "MyActionRenderer";
    }

    canRender(col) {
      return col instanceof LineUpJS.ActionColumn;
    }

    create(col) {
      const actions = col.actions;
      return {
        template: `
          <div class="icon-container">
            <span id="action0" class='button fas fa-search'></span>
            <span id="action1" class='button fas fa-search-plus'></span>
          </div>
        `,
        update: (n, d) => {
          const children = n.childNodes;
          children.forEach(function (ni, i) {
            if (ni.tagName === "SPAN") {
              ni.onclick = function (event) {
                event.preventDefault();
                event.stopPropagation();
                // FIXME I think this is a abusive usage of the index
                let actionIdx = ni.id.slice(-1);
                setTimeout(() => actions[actionIdx].action(d), 1);
              };
            }
          });
        },
      };
    }

    // noinspection JSUnusedGlobalSymbols
    createGroup(col) {
      const actions = col.groupActions;
      return {
        template: `
          <div class="icon-container">
            <span id="action0" class='button fas fa-search fa-2x'></span>
            <span id="action1" class='button fas fa-search-plus fa-2x'></span>
          </div>`,
        update: (n, group) => {
          const children = n.childNodes;
          children.forEach(function (ni, i) {
            if (ni.tagName === "SPAN") {
              ni.onclick = function (event) {
                event.preventDefault();
                event.stopPropagation();
                let actionIdx = ni.id.slice(-1);
                setTimeout(() => actions[actionIdx].action(group), 1);
              };
            }
          });
        },
      };
    }
  }

  class IconRenderer {
    constructor(iconMap) {
      this.title = "IconRenderer";
      this.iconMap = new Map(Object.entries(iconMap));
    }

    canRender(col) {
      return col instanceof LineUpJS.CategoricalColumn;
    }

    create(col) {
      return {
        template: `
          <div class="icon-container">
            <span id="annotator_icon_id" class='fas' > </span>
          </div>
        `,
        update: (node, row, i, group) => {
          const annotator_type = row.v[col.desc.column];

          const icon = node.children[0];
          icon.classList.remove( ...this.iconMap.values() );

          const iconClass = this.iconMap.get(annotator_type);
          if (iconClass) {
            icon.classList.add(iconClass);
          }
        },
      };
    }
  }

  /* ---------------------------------------------------------------------------
  Actions
  --------------------------------------------------------------------------- */
  const openSeaDragonRowAction = {
    name: "OSD Row Action",
    action: (row) => {
      window.location.href = `/slides/viewer/${row.v["image_url"]}/osd`;
    },
  };
  const DeckGLRowAction = {
    name: "DGL Row Action",
    action: (row) => {
      window.location.href = `/slides/viewer/${row.v["image_url"]}/deckgl`;
    },
  };
  const openSeaDragonGroupAction = {
    name: "OSD Group Operation",
    action: (group) => {
      window.location.href = `/slides/viewer/${group["name"]}/osd`;
    },
  };
  const DeckGLGroupAction = {
    name: "DGL Group Action",
    action: (group) => {
      window.location.href = `/slides/viewer/${group["name"]}/deckgl`;
    },
  };

  /* ---------------------------------------------------------------------------
  Build lineup
  --------------------------------------------------------------------------- */

  // load data
  const builder = LineUpJS.builder(luOptions.metadata);

  // create builder
  builder
    .column(
      LineUpJS.buildCategoricalColumn("image_url")
        .renderer("thumbnail", "thumbnail", "none")
        .label("Image")
        .width(200)
    )
    .column(
      LineUpJS.buildCategoricalColumn("classification")
        .renderer("categorical", "upset")
        .label("Finding")
        .width(160)
    )
    .column(
      LineUpJS.buildCategoricalColumn("annotation_type")
        .renderer("annotation_type", "catdistributionbar")
        .label("Type")
        .width(100)
    )
    .column(
      LineUpJS.buildCategoricalColumn("annotator_type")
        .renderer("annotator_type", "categorical", "categorical")
        .label("Source")
        .width(100)
    )
    .column(
      LineUpJS.buildCategoricalColumn("annotator_name")
        .renderer("categorical", "categorical", "categorical")
        .label("Annotator")
        .width(160)
    )
    .column(
        LineUpJS.buildCategoricalColumn("annotation_metric")
        .renderer("annotation_metric", "categorical", "categorical")
        .label("Metric")
        .width(100)
    )
    .column(
      LineUpJS.buildNumberColumn("annotation_value")
        .label("Score")
        .renderer("brightness", "histogram")
        .width(100)
    )
    .column(
      LineUpJS.buildNumberColumn("annotation_area")
        .label("Area")
        .renderer("brightness", "histogram")
        .width(100)
    )
    .column(
      LineUpJS.buildNumberColumn("annotation_count")
        .label("Count")
        .renderer("brightness", "histogram")
        .width(100)
    )
    .column(
      LineUpJS.buildCategoricalColumn("compound_name")
        .renderer("categorical", "categorical", "categorical")
        .label("Compound")
        .width(160)
    )
    .column(
      LineUpJS.buildCategoricalColumn("organ")
        .renderer("categorical", "categorical", "categorical")
        .label("Organ")
        .width(160)
    )
    .column(
      LineUpJS.buildCategoricalColumn("species")
        .renderer("categorical", "categorical", "categorical")
        .label("Species")
        .width(160)
    )
    .column(
      LineUpJS.buildActionsColumn()
        .renderer("myaction", "myaction")
        .groupActions([openSeaDragonGroupAction, DeckGLGroupAction])
        .actions([openSeaDragonRowAction, DeckGLRowAction])
        .label("Action")
        .width(160)
    );

  // configure builder
  // fixme: these two constants should be reachable from within the renderer;
  const rowHeight = 25;
  const groupRowHeight = 150;
  builder
    .ranking(
      LineUpJS.buildRanking()
        .aggregate()
        // .column("Action")
        .groupBy("image_url")
        .column("image_url")
        .column("classification")
        .column("annotation_type")
        .column("annotator_type")
        .column("annotator_name")
        .column("annotation_metric")
        .column("annotation_area")
        .column("annotation_count")
        .column("annotation_value")
        .column("compound_name")
        .column("species")
        .column("organ")
    )
    .registerRenderer("thumbnail", new ThumbnailRenderer())
    .registerRenderer("myaction", new MyActionRenderer())
    .registerRenderer("annotator_type", new IconRenderer({
      human: "fa-user-md",
      dataset: "fa-file-alt",
      model: "fa-laptop-code",
    }))
    .registerRenderer("annotation_type", new IconRenderer({
      slide: "fa-ticket-alt",
      heatmap: "fa-chess-board",
      contour: "fa-draw-polygon",
    }))
    .registerRenderer("annotation_metric", new IconRenderer({
      area: "fa-percentage",
      score: "fa-list-ol",
      count: "fa-shapes",
    }))
    .sidePanel(true, true)
    .singleSelection()
    .groupRowHeight(groupRowHeight)
    .rowHeight(rowHeight);

  // build lineup
  const lineup = builder.build(luElement);

  /*
  // add listeners
  lineup.on("selectionChanged", selectionChangedListener);
  lineup.on("groupSelectionChanged", selectionChangedListener);

  // ---------------------------------------------------------------------------
  // Define listeners
  // ---------------------------------------------------------------------------
  function selectionChangedListener(itemIdx) {
    // Do something when the selection changed
    const imageId = lineup.data.getRow(itemIdx).v["image_url"];

    // Simulate an HTTP redirect:
    window.location.href = `/slides/viewer/${imageId}/osd`;
  }
  */
}

export default {
  setupLineUp: setupLineUp,
};
