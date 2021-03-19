/* common pado_visualize javascripty things */

function documentReady(fn) {
  if (document.readyState !== "loading") {
    fn();
  } else {
    document.addEventListener("DOMContentLoaded", fn);
  }
}

export { documentReady };
