(function() {

  // ----------
  var component = OpenSeadragonMultiApp.TextItem = function(config) {
    _.extend(this, _.pick(config, 'text', 'opacity', 'height', 'onClick', 'onMouseover', 'onMouseout', 'shadow', 'bold'));

    _.defaults(this, {
      opacity: 1,
      height: 0.05,
      position: new OpenSeadragon.Point(0, 0),
      shadow: '2px 2px 0 rgba(0, 0, 0, 0.5)',
      debugRect: false
    });

    // this.text = config.text;
    // this.onClick = config.onClick;
    // this.onMouseover = config.onMouseover;
    // this.onMouseover = config.onMouseover;
    // this.opacity = config.opacity || 1;
    // this.height = config.height || 0.05;
    // this.position = new OpenSeadragon.Point(0, 0);
    // this.debugRect = false;
  };

  // ----------
  component.prototype = {
    // ----------
    getPosition: function() {
      return new OpenSeadragon.Point(this.position.x, this.position.y);
    },

    // ----------
    setPosition: function(value) {
      if (value) {
        this.position = value;
      }

      if (this.node) {
        this.node
          .attr('x', this.position.x)
          .attr('y', this.position.y + (this.height * 0.75));
      }

      if (this.rectNode) {
        this.rectNode
          .attr('x', this.position.x)
          .attr('y', this.position.y);
      }
    },

    // ----------
    getBounds: function() {
      return new OpenSeadragon.Rect(this.position.x, this.position.y, this.width, this.height);
    },

    // ----------
    setOpacity: function(value) {
      this.opacity = value;

      if (this.node) {
        this.node.style('opacity', this.opacity);
      }
    },

    // ----------
    show: function() {
      var self = this;

      if (this.node) {
        return;
      }

      this.rectNode = d3.select(OpenSeadragonMultiApp.svgNode).append('rect')
        .style('stroke', this.debugRect ? '#fff' : 'none')
        .style('fill', 'none')
        .style('stroke-width', '0.001px')
        .style('cursor', 'pointer')
        .attr('pointer-events', 'fill')
        .on('click', function() {
          if (self.onClick) {
            self.onClick(self);
          }
        })
        .on('mouseover', function() {
          if (self.onMouseover) {
            self.onMouseover(self);
          }
        })
        .on('mouseout', function() {
          if (self.onMouseout) {
            self.onMouseout(self);
          }
        });

      this.node = d3.select(OpenSeadragonMultiApp.svgNode).append('text')
        .style('fill', '#fff')
        .style('font-size', this.height + 'px')
        .style('text-shadow', this.shadow)
        .style('opacity', this.opacity)
        .text(this.text);

      if (this.bold) {
        this.node.style('font-weight', 'bold');
      }

      this.width = this.node.node().getComputedTextLength();

      this.node
        .attr('width', this.width)
        .attr('height', this.height);

      if (this.rectNode) {
        this.rectNode
          .attr('width', this.width)
          .attr('height', this.height);
      }

      this.setPosition();
    },

    // ----------
    hide: function() {
      if (this.node) {
        this.node.remove();
        this.node = null;
      }

      if (this.rectNode) {
        this.rectNode.remove();
        this.rectNode = null;
      }
    }
  };

})();
