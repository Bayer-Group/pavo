// postcss configuration

module.exports = {
  plugins: [
    require("cssnano")({
      preset: "default",
    }),
  ],
};
