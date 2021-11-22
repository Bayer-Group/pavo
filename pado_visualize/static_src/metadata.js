import "./_base.js";
import "./css/metadata.scss";

/** you won this time webpack *shaking fist* */
// import "./vendor/lineupjs/0a90cd2d51265d96e0f3.ttf";
// import "./vendor/lineupjs/7fe2c712e328094b844b.woff";
// import "./vendor/lineupjs/8d1e317a83ec2b6cddd4.svg";
// import "./vendor/lineupjs/dee14f29dff532d4a714.woff2";
// import "./vendor/lineupjs/LineUpJS.css";
// import * as LineUpJS from "./vendor/lineupjs/LineUpJS.js";

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

  /* ---------------------------------------------------------------------------
  Renderers
  --------------------------------------------------------------------------- */
  class ThumbnailRenderer {
    constructor() {
      this.title = 'ThumbnailRenderer';
    }

    canRender(col) {
      return col instanceof LineUpJS.StringColumn;
    }

    create(col) {
      return {
        template: `<div><div/>`,
        update: (node, row, i, group) => {
          if (this.isFirstGroupMember(i)) {
            let img = document.createElement('img');
            img.src = `/slides/thumbnail_${group.name}_200.jpg`;
            node.children[0].classList.add('thumbnail');
            let marginHeight = 2;
            let numRows = group.order.length;
            node.style.height = `${numRows * (rowHeight + marginHeight)}px`;
            node.children[0].appendChild(img);
          } 
        }
      };
    }

    createGroup(col) {
      return {
        template: `<img alt="thumbnail" class="thumbnail"> </img>`,
        update: (node, group) => {
          node.src = `/slides/thumbnail_${group.name}_200.jpg`;
        }
      };
    }

    isFirstGroupMember(i) {
      return i == 0;
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
            <span class='button fas fa-search' > </span>
          </div>
        `,
        update: (n, d) => {
          var children = n.childNodes;
          children.forEach(function(ni, i){
              ni.onclick = function (event) {
                event.preventDefault();
                event.stopPropagation();
                setTimeout(() => actions[0].action(d), 1);
              };
          });
        }
      };
    }

    createGroup(col) {
      const actions = col.groupActions;
      return {
        template: `
          <div class="icon-container"> 
            <span class='button grouped fas fa-search fa-2x'></span>
          </div>`,
        update: (n, group) => {
          var children = n.childNodes;
          children.forEach( function(ni, i) {
            ni.onclick = function(event) {
              event.preventDefault();
              event.stopPropagation();
              setTimeout(() => actions[0].action(group), 1);
            }
          })
        }
      };
    }
  }

  class AnnotatorRenderer {
    constructor() {
      this.title = "AnnotatorRenderer";
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
        update: (n, d) => {
          var annotator_type = d.v['annotator_type'];
          var icon = n.getElementsByTagName('span')[0];
          if (annotator_type == 'model'){
            icon.classList.add('fa-laptop-code');
          } else if (annotator_type == 'human'){
            icon.classList.add('fa-user');
          } else if (annotator_type == 'unknown'){
            icon.classList.add('fa-question');
          }
        }
      };
    }
  }

  /*
  Action methods
  */
  const rowAction = {
    name: "Row Action",
    action: (row) => {
      // TODO: Do something more interesting with a single row here
      window.location.href = `/slides/viewer/${row.v['image_url']}/osd`;
    }
  };
  const groupAction = {
    // TODO do something more interesting with an entire slide here
    name: "Group Operation",
    action: (group) => {
      window.location.href = `/slides/viewer/${group['name']}/osd`;
    }
  };

  /* ---------------------------------------------------------------------------
  Build lineup
  --------------------------------------------------------------------------- */

  // load data
  const builder = LineUpJS.builder(luOptions.metadata);

  // create builder
  builder
    .column(LineUpJS.buildCategoricalColumn('image_url')
      .renderer('thumbnail', 'thumbnail', 'none')
      .label('Image')
      .width(200)
    )
    .column(LineUpJS.buildCategoricalColumn('classification')
      .renderer('categorical', 'upset')
      .label('Finding')
      .width(160)
    )
    .column(LineUpJS.buildBooleanColumn('annotation')
      .renderer('upset', 'catdistributionbar')
      .label('Annotation')
      .width(160)
    )
    .column(LineUpJS.buildCategoricalColumn('annotator_type')
      .renderer('annotator', 'categorical', 'categorical')
      .label('Annotator Type')
      .width(160)
    )
    .column(LineUpJS.buildCategoricalColumn('annotator_name')
      .renderer('categorical', 'categorical', 'categorical')
      .label('Annotator Name')
      .width(160)
    )
    .column(LineUpJS.buildNumberColumn('annotation_area')
      .label('Annotation Area')
      .renderer('brightness', 'histogram')
      .width(160)
    )
    .column(LineUpJS.buildNumberColumn('annotation_count')
      .label('Annotation Count')
      .renderer('brightness', 'histogram')
      .width(160)
    )
    .column(LineUpJS.buildCategoricalColumn('compound_name')
      .renderer('categorical', 'categorical', 'categorical')
      .label('Compound')
      .width(160)
    )
    .column(LineUpJS.buildCategoricalColumn('organ')
      .renderer('categorical', 'categorical', 'categorical')
      .label('Organ')
      .width(160)
    )
    .column(LineUpJS.buildCategoricalColumn('species')
      .renderer('categorical', 'categorical', 'categorical')
      .label('Species')
      .width(160)
    )
    .column(LineUpJS.buildActionsColumn() 
      .renderer('myaction', 'myaction')
      .groupAction(groupAction)
      .action(rowAction)
      .label('Action')
      .width(80)
    )
  ;

  // configure builder
  const rowHeight = 25;   /* needed as a global variable */
  builder
    .ranking(
      LineUpJS.buildRanking()
        .aggregate()
        .column('Action')
        .groupBy('image_url')
        .sortBy('annotation')
        .column('image_url')
        .column('classification')
        .column('annotation')
        .column('annotator_type')
        .column('annotator_name')
        .column('annotation_area')
        .column('annotation_count')
        .column('compound_name')
        .column('species')
        .column('organ')
    )
    .registerRenderer("thumbnail", new ThumbnailRenderer())
    .registerRenderer("myaction", new MyActionRenderer())
    .registerRenderer("annotator", new AnnotatorRenderer())
    .sidePanel(true, true)
    .singleSelection()
    .groupRowHeight(150)
    .rowHeight(rowHeight)
  ;

  // build lineup
  const lineup = builder.build(luElement);

  // add listeners
  lineup.on("selectionChanged", selectionChangedListener);
  lineup.on("groupSelectionChanged", selectionChangedListener);

  /* ---------------------------------------------------------------------------
  Define listeners
  --------------------------------------------------------------------------- */
  function selectionChangedListener(itemIdx) {
    // Do something when the selection changed
    var imageURL = lineup.data._data[itemIdx]['image_url']

    // Simulate an HTTP redirect:
    window.location.href = `/slides/viewer/${imageURL}/osd`;
  }

}

export default {
  setupLineUp: setupLineUp,
};



