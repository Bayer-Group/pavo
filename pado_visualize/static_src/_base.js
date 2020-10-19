/* common pado_visualize javascripty things */
import "normalize.css";
import "./css/base.scss";
import "core-js/stable";

/* images used in the base layout */
import "./images/pathological-heart.jpg";

/* common functions */
function documentReady(fn) {
  if (document.readyState !== "loading") {
    fn();
  } else {
    document.addEventListener("DOMContentLoaded", fn);
  }
}

export { documentReady };
