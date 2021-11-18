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


  class ThumbnailRenderer {
    constructor() {
      this.title = 'ThumbnailRenderer';
    }

    canRender(col) {
      return col instanceof LineUpJS.StringColumn;
    }

    create(col) {
      return {
        template: `<p></p>`,
        update: (n, d) => {
          n.textContent = '';
        }
      };
    }

    createGroup(col) {
      return {
        template: `<img alt="thumbnail" class="thumbnail"> </img>`,
        update: (n, d) => {
          n.src = `/slides/thumbnail_${d.name}_200.jpg`
        }
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
      const align = col.alignment || 'center';
      return {
        template: `
          <div class="icon-container"> 
            <span class='fas fa-search' > </span>
          </div>
        `,
        update: (n, d) => {
        }
      };
    }

    createGroup(col) {
      return {
        template: `
          <div class="icon-container"> 
            <span class='fas fa-search'></span>
          </div>`,
        update: (n, d) => {
        }
      };
    }
  }

  const groupAction = {
    // TODO do something with an entire slide here
    name: "Group Operation",
    action: (rows) => alert(rows.map((d) => d.v))
  };
  const rowAction = {
    name: "Row Action",
    icon: "&#x2794; row operate &#x2794;",
    action: (row) => {
      // TODO: Do something with a single row here
      console.log(row.v['image_url']);
    }
  };

  const builder = LineUpJS.builder(luOptions.metadata);
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
      .renderer('categorical', 'categorical', 'categorical')
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

  builder.ranking(
    LineUpJS.buildRanking()
      .aggregate()
      // .allColumns()
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
  );
  builder.registerRenderer("thumbnail", new ThumbnailRenderer());
  builder.registerRenderer("myaction", new MyActionRenderer());
  builder.sidePanel(true, true);
  builder.singleSelection();
  builder.groupRowHeight(150);

  const lineup = builder.build(luElement);

  lineup.on("selectionChanged", selectionChangedListener);

  // ---- functions ------------------------------------------------------------
  function selectionChangedListener(itemIdx) {
    // Do something when the selection changed
    var imageURL = lineup.data._data[itemIdx]['image_url']
    console.log(imageURL);

    // Simulate an HTTP redirect:
    window.location.href = `/slides/viewer/${imageURL}/osd`;
  }

}

export default {
  setupLineUp: setupLineUp,
};



