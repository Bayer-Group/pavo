/**
 * @fileOverview The webpack configuration for pavo
 * This file should take care of translating the pavo/static_src
 * folder to shippable sources in pavo/static
 */
// are we in development mode?
// const devMode = process.env.NODE_ENV !== "production";

// path related config
const path = require("path");
const srcDir = [__dirname, "pavo", "static_src"];
const outDir = [__dirname, "pavo", "static"];

// css plugin config (see https://github.com/webpack-contrib/css-loader#recommend)
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
// copy files to dist dir plugin
const CopyPlugin = require("copy-webpack-plugin");
// assets manifest plugin for setup.py build_js
const WebpackAssetsManifest = require("webpack-assets-manifest");

// the actual webpack config
module.exports = {
  entry: {
    // todo: use glob to gather the entry points?
    _base: path.resolve(...srcDir, "_base.js"),
    home: path.resolve(...srcDir, "home.js"),
    metadata: path.resolve(...srcDir, "metadata.js"),
    slides: path.resolve(...srcDir, "slides.js"),
    slides_deckgl: path.resolve(...srcDir, "slides_deckgl.jsx"),
    slides_openseadragon: path.resolve(...srcDir, "slides_openseadragon.js"),
  },
  output: {
    path: path.resolve(...outDir),
    library: ["pavo", "[name]"],
    libraryExport: "default",
  },
  devtool: "source-map",
  module: {
    rules: [
      {
        // one css rule to rule them all
        test: /\.(sa|sc|c)ss$/i,
        use: [
          MiniCssExtractPlugin.loader,
          "css-loader",
          "postcss-loader",
          "sass-loader",
        ],
      },
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: ["babel-loader"],
      },
      // assets: https://webpack.js.org/guides/asset-modules/
      {
        // fonts
        test: /\.(woff|woff2|eot|ttf|otf|svg)$/i,
        exclude: [/images/],
        type: "asset/resource",
        generator: {
          filename: "fonts/[name][ext][query]",
        },
      },
      {
        // images
        test: /\.(png|jpe?g|gif)$/i,
        type: "asset/resource",
        generator: {
          filename: "images/[name][ext][query]",
        },
      },
    ],
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: "[name].css",
    }),
    new CopyPlugin({
      patterns: [
        {
          from: path.posix.join(
            path.posix.normalize(
              path.relative(
                path.resolve(__dirname),
                path.dirname(require.resolve("openseadragon"))
              )
            ),
            "images",
            "*.png"
          ),
          to: "images/openseadragon/[name][ext]",
        },
      ],
    }),
    new WebpackAssetsManifest({
      output: "../../webpack-output-manifest.json",
    }),
  ],
};
