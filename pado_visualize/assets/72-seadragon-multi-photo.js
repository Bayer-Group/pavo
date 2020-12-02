(function() {

  // ----------
  var component = OpenSeadragonMultiApp.Photo = function(config) {
    var self = this;

    this.x = config.x;
    this.y = config.y;
    this.title = config.title;
    this.pageUrl = config.pageUrl;
    this.ownerName = config.ownerName;
    this.selected = false;

    var handleError = function() {
      if (config.onError) {
        config.onError();
      }
    };

    if (!config.tags) {
      handleError();
      return;
    }

    // console.log(config.sizes);
    var levels = _.chain(config.sizes)
      .filter(function(v, i) {
        return (/(thumbnail|small 320|medium 640|large)/i).test(v.label) && !(/square/i).test(v.label);
      })
      .map(function(v, i) {
        var output = {
          url: (v.source || '').replace(/\?.*$/, ''),
          width: parseInt(v.width, 10),
          height: parseInt(v.height, 10)
        };

        return output;
      })
      .sortBy('width')
      .value();

    if (!levels.length) {
      handleError();
      return; 
    }

    // console.log(_.pluck(levels, 'width'));

    var level = levels[levels.length - 1];
    var longestSide = Math.max(level.width, level.height);
    if (longestSide < 900) {
      console.log('skipping image', longestSide, level.url, config.sizes);
      handleError();
      return;
    }

    this.targetWidth = Math.sqrt(level.width / level.height);
    this.targetHeight = this.targetWidth * (level.height / level.width);

    this.tags = _.map(config.tags.split(' '), function(v, i) {
      return new OpenSeadragonMultiApp.Tag({
        text: v
      });
    });

    var tileDrawnHandler = function(event) {
      if (event.tiledImage === self.tiledImage) {
        OpenSeadragonMultiApp.viewer.removeHandler('tile-drawn', tileDrawnHandler);
        self.drawn = true;
        OpenSeadragonMultiApp.photos.push(self);

        if (config.onLoad) {
          config.onLoad();
        }
      }
    };

    OpenSeadragonMultiApp.viewer.addHandler('tile-drawn', tileDrawnHandler);

    this.width = this.targetWidth / 10;
    this.height = this.targetHeight / 10;

    OpenSeadragonMultiApp.viewer.addTiledImage({
      index: 0,
      x: this.x - (this.width / 2),
      y: this.y - (this.height / 2),
      width: this.width,
      tileSource: {
        type: 'legacy-image-pyramid',
        levels: levels
      },
      success: function(event) {
        self.tiledImage = event.item;
      }
    });
  };

  // ----------
  component.prototype = {
    // ----------
    frame: function() {
      var self = this;

      if (this.width < this.targetWidth || this.height < this.targetHeight) {
        var speed = 100;
        this.width = Math.min(this.targetWidth, this.width + (this.targetWidth / speed));
        this.height = Math.min(this.targetHeight, this.height + (this.targetHeight / speed));
        this.tiledImage.setWidth(this.width, true);
        this._update();
      } else if (!this.textItem && !OpenSeadragonMultiApp.isTouch) {
        var restOpacity = 0.6;

        this.textItem = new OpenSeadragonMultiApp.TextItem({
          text: this.title + ' by ' + this.ownerName,
          opacity: restOpacity,
          height: 0.025,
          onClick: function() {
            window.open(self.pageUrl);
          },
          onMouseover: function() {
            self.textItem.setOpacity(1);
          },
          onMouseout: function() {
            self.textItem.setOpacity(restOpacity);
          }
        });

        this._update();

        if (this.selected) {
          this.textItem.show();
        }
      }
    },

    // ----------
    select: function() {
      this.selected = true;

      if (this.textItem) {
        this.textItem.show();
      } else if (OpenSeadragonMultiApp.isTouch) {
        $('.mobile-selected') 
          .show();

        if (!OpenSeadragonMultiApp.tagsButtonUsed) {
          $('.tags-button').addClass('animated bounceIn');
        }
        
        $('.attribution')
          .html('<a href="' + 
            this.pageUrl + 
            '" target="_blank">' + 
            this.title + ' by ' + this.ownerName + 
            '</a>');
      }
    },

    // ----------
    deselect: function() {
      this.selected = false;

      if (this.textItem) {
        this.textItem.hide();
      } else if (OpenSeadragonMultiApp.isTouch) {
        $('.mobile-selected') 
          .hide();

        $('.tags-button').removeClass('animated bounceIn');
        
        $('.attribution')
          .empty();
      }
    },

    // ----------
    getPosition: function() {
      return new OpenSeadragon.Point(this.x, this.y);
    },

    // ----------
    setPosition: function(value) {
      this.x = value.x;
      this.y = value.y;

      this._update();
    }, 

    // ----------
    getBounds: function() {
      return new OpenSeadragon.Rect(this.x - (this.width / 2), this.y - (this.height / 2), this.width, this.height);
    },

    // ----------
    getTargetBounds: function() {
      return new OpenSeadragon.Rect(this.x - (this.targetWidth / 2), this.y - (this.targetHeight / 2), 
        this.targetWidth, this.targetHeight);
    },

    // ----------
    _update: function() {
      var box = this.getBounds();
      this.tiledImage.setPosition(box.getTopLeft(), true);    

      if (this.textItem) {
        this.textItem.setPosition(new OpenSeadragon.Point(box.x + 0.02, (box.y + box.height) - (this.textItem.height + 0.02)));
      }  
    }
  };

})();
