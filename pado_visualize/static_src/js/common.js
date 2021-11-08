/* common pado_visualize javascripty things */
import "../images/pathological-heart.jpg";
import "normalize.css";
import "../css/base.scss";
import "regenerator-runtime/runtime";
import "core-js/stable";

function documentReady(fn) {
  if (document.readyState !== "loading") {
    fn();
  } else {
    document.addEventListener("DOMContentLoaded", fn);
  }
}

export { documentReady };
