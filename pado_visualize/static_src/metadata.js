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
  const lineup = LineUpJS.asLineUp(luOptions.id, luOptions.metadata);
}

export default {
    setupLineUp: setupLineUp
};
