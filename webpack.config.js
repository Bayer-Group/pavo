/**
 * @fileoverview The webpack configuration for pado_visualize
 * This file should take care of translating the pado_visualize/static_src
 * folder to shippable sources in pado_visualize/static
 */
// are we in development mode?
const devMode = process.env.NODE_ENV !== "production";

// path related config
const path = require("path");
const srcDir = [__dirname, "pado_visualize", "static_src"];
const outDir = [__dirname, "pado_visualize", "static"];

// css plugin config (see https://github.com/webpack-contrib/css-loader#recommend)
const ExtractCssChunks = require("extract-css-chunks-webpack-plugin");

// the actual webpack config
module.exports = {
  entry: {
    // todo: use glob to gather the entry points
    home: path.resolve(...srcDir, "base.js"),
    slides: path.resolve(...srcDir, "slides.js"),
    metadata: path.resolve(...srcDir, "metadata.js"),
  },
  output: {
    path: path.resolve(...outDir),
    publicPath: "/static",
  },
  module: {
    rules: [
      {
        // one css rule to rule them all
        test: /\.(sa|sc|c)ss$/i,
        use: [
          ExtractCssChunks.loader,
          "css-loader",
          "postcss-loader",
          "sass-loader",
        ],
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: ["babel-loader"],
      },
      // assets: https://webpack.js.org/guides/asset-modules/
      {
        // images
        test: /\.(png|jpe?g|gif)$/i,
        type: "asset/resource",
        generator: {
          filename: "images/[name][ext][query]",
        },
      },
      {
        // fonts
        test: /\.(svg|eot|ttf|woff|woff2)$/i,
        type: "asset/resource",
        generator: {
          filename: "fonts/[name][ext][query]",
        },
      },
    ],
  },
  plugins: [
    new ExtractCssChunks({
      filename: "[name].css",
    }),
  ],
};
