(function() {

  // ----------
  window.OpenSeadragonMultiApp = {
    // ----------
    init: function(config) {
      var self = this;

      if (!window.console) {
        window.console = {
          log: function() {},
          warn: function() {},
          error: function() {},
          assert: function() {}
        };
      }

      FastClick.attach(document.body);

      this.photos = [];
      this.tagsButtonUsed = false;

      this.auto = (location.hash === '#auto');

      this.isTouch = 'ontouchstart' in document.documentElement;
      // this.isTouch = true;
      if (!this.isTouch) {
        $('html').addClass('no-touch');
      }

      this.viewer = OpenSeadragon(config);

      /*
      this.viewer.addHandler("open", function(event) {
        // To improve load times, ignore the lowest-resolution Deep Zoom
        // levels.  This is a hack: we can't configure the minLevel via
        // OpenSeadragon configuration options when the viewer is created
        // from DZI XML.
        self.viewer.source.minLevel = 8;
      });
       */

      var $viewer = $(this.viewer.element).on('mousemove', function(event) {
        self.hoverPhoto = self.hitTest(new OpenSeadragon.Point(event.clientX, event.clientY));
        $viewer.css({
          cursor: self.hoverPhoto ? 'pointer' : 'default'
        });
      });

      this.viewer.addHandler('zoom', function(event) {
          self.updateButtons();
      });

      this.viewer.addHandler('pan', function(event) {
          self.updateButtons();
      });

      this.viewer.addHandler('canvas-click', function(event) {
        if (!event.quick) {
          return;
        }

        var photo = self.hitTest(event.position);
        if (photo) {
          self.select(photo);
        }
      });

      this.spin(true);
      /*
      this.flickrRequest({
        method: 'interestingness.getList',
        content: {
          per_page: 40,
          extras: 'tags,owner_name'
        },
        success: function(data) {
          self.processPhotos(data, new OpenSeadragon.Point(0, 0), function() {
            if (self.auto) {
              self.startAuto();
            }
          });
        }
      });
      */
      this.fakeFlickrGetList({
        success: function(data) {
          self.processPhotos(data, new OpenSeadragon.Point(0, 0));
        }
      });


      $('.info-button').click(function() {
        $('.modal').show();
      });

      $('.modal .cover').click(function() {
        $('.modal').hide();
      });

      $('.tags-button').click(function() {
        self.tagsButtonUsed = true;
        self.showMobileTags();
      });

      $('.tag-list-container .cover').click(function() {
        self.hideMobileTags();
      });

      $('.tag-list-container .close-button').click(function() {
        self.hideMobileTags();
      });

      this.viewer.viewport.fitBounds(new OpenSeadragon.Rect(-4, -4, 8, 8), true);
      this.svgNode = this.viewer.svgOverlay();
      $(window).resize(function() {
        self.viewer.svgOverlay('resize');
      });


      this.frame();
    },

    // ----------
    startAuto: function() {
      var self = this;

      setTimeout(function() {
        var index = Math.floor(Math.random() * self.photos.length);
        var photo = self.photos[index];
        self.select(photo);
        setTimeout(function() {
          var tagIndex = Math.floor(Math.random() * photo.tags.length);
          var tag = photo.tags[tagIndex];
          self.loadForTag(tag, function() {
            self.startAuto();
          });
        }, 5000);
      }, 5000);
    },

    // ----------
    select: function(photo) {
      if (this.selectedPhoto) {
        this.selectedPhoto.deselect();
      }

      if (photo) {
        this.viewer.world.setItemIndex(photo.tiledImage, this.viewer.world.getItemCount() - 1);
        this.fitPhoto(photo, OpenSeadragonMultiApp.isTouch ? 0.05 : 0.3);
        photo.select();
      }

      this.showTags(photo);
      this.selectedPhoto = photo;
    },

    // ----------
    loadForTag: function(tag, onDone) {
      var self = this;

      if (this.selectedPhoto) {
        this.fitPhoto(this.selectedPhoto, 1.5);
      } else {
        this.viewer.viewport.zoomBy(0.5);
      }

      this.select(null);
      this.spin(true);

      this.flickrRequest({
        method: 'photos.search',
        content: {
          per_page: 10,
          extras: 'tags,owner_name',
          sort: 'interestingness-desc',
          tags: tag.getText()
        },
        success: function(data) {
          var pos;
          if (self.isTouch) {
            pos = self.viewer.viewport.getBounds(true).getCenter();
          } else {
            pos = tag.getPosition();
          }

          self.processPhotos(data, pos, onDone);
        },
        error: function() {
          if (onDone) {
            onDone();
          }
        }
      });
    },

    // ----------
    processPhotos: function(data, center, onDone) {
      var self = this;

      if (!data || !data.photos || !data.photos.photo || !data.photos.photo.length) {
        console.error('[App.processPhotos] bad data', data);
        if (onDone) {
          onDone();
        }

        return;
      }

      var expected = data.photos.photo.length;
      var done = 0;

      var increment = function() {
        done++;
        if (done === expected && onDone) {
          onDone();
        }
      };

      // console.log(data);
      _.each(data.photos.photo, function(v, i) {
        setTimeout(function() {
          new self.Photo({
            x: center.x + ((Math.random() - 0.5) * 3),
            y: center.y + ((Math.random() - 0.5) * 1),
            tags: v.tags,
            ownerName: v.ownername,
            pageUrl: "/slide/" + v.id + "/image.dzi",
            title: v.title,
            onLoad: function() {
              self.spin(false);
              increment();
            },
            onError: function() {
              increment();
            }
          });
        }, 200 * i);
        // console.log(v.o_width);
      });
    },

    // ----------
    getAdjustment: function(itemBox, boxes) {
      var self = this;

      var output = new OpenSeadragon.Point(0, 0);
      var itemCenter = itemBox.getCenter();

      _.each(boxes, function(box) {
        if (itemBox === box) {
          return;
        }

        var intersection = self.intersection(itemBox, box);
        if (!intersection) {
          return;
        }

        var diff = itemCenter.minus(box.getCenter());
        if (itemBox.width < box.width / 2) {
          if (Math.abs(diff.x) > Math.abs(diff.y)) {
              output.x += self.sign(diff.x) * intersection.width;
            } else {
              output.y += self.sign(diff.y) * intersection.height;
            }
        } else {
          if (intersection.width < intersection.height) {
            output.x += self.sign(diff.x) * intersection.width;
          } else {
            output.y += self.sign(diff.y) * intersection.height;
          }
        }
      });

      var limit = 0.1;
      output.x = Math.min(limit, Math.max(-limit, output.x));
      output.y = Math.min(limit, Math.max(-limit, output.y));
      return output;
    },

    // ----------
    frame: function() {
      var self = this;

      requestAnimationFrame(function() {
        self.frame();
      });

      var photoBoxes = [];

      _.each(this.photos, function(photo) {
        photo.frame();
        photo.box = photo.getBounds();
        photoBoxes.push(photo.box);
      });

      _.each(this.photos, function(photo) {
        if (!photo.drawn || photo === self.selectedPhoto) {
          photo.diff = new OpenSeadragon.Point(0, 0);
          return;
        }

        photo.diff = self.getAdjustment(photo.box, photoBoxes);
      });

      // this.maxSpeed = this.maxSpeed || 0;

      _.each(this.photos, function(photo) {
        if (photo.diff.x || photo.diff.y) {
          // self.maxSpeed = Math.max(photo.diff.x, photo.diff.y, self.maxSpeed);
          var pos = photo.getPosition()
            .plus(photo.diff.times(0.2));

          photo.setPosition(pos);
        }
      });

      if (this.selectedPhoto) {
        var buffer = 0.01;
        var tagBoxes = [];
        tagBoxes.push(this.selectedPhoto.box);

        _.each(this.selectedPhoto.tags, function(tag) {
          tag.box = tag.getBounds();
          tag.box.x -= buffer;
          tag.box.y -= buffer;
          tag.box.width += buffer * 2;
          tag.box.height += buffer * 2;
          tagBoxes.push(tag.box);
        });

        _.each(this.selectedPhoto.tags, function(tag) {
          tag.diff = self.getAdjustment(tag.box, tagBoxes);
        });

        _.each(this.selectedPhoto.tags, function(tag) {
          if (tag.diff.x || tag.diff.y) {
            var pos = tag.getPosition()
              .plus(tag.diff.times(0.2));

            tag.setPosition(pos);
          }
        });
      }

      // console.log(self.maxSpeed);
      this.viewer.forceRedraw();
    },

    // ----------
    flickrRequest: function(config) {
      var apiKey = 'fa19dbf7a2f0bb5b0a8938379f710b59';
      var url = 'https://api.flickr.com/services/rest/?method=flickr.' +
        config.method +
        '&api_key=' +
        apiKey +
        '&format=json';

      $.ajax({
        url: url,
        data: config.content,
        dataType: 'jsonp',
        jsonp: 'jsoncallback',
        success: config.success,
        error: config.error
      });
    },

    fakeFlickrGetList: function (config) {
      $.ajax({
        url: "/wsickr/get_list.json",
        data: config.content,
        dataType: 'json',
        success: config.success,
        error: config.error
      });
    },

    // ----------
    fitPhoto: function(photo, buffer) {
      var box = photo.getTargetBounds();
      box.x -= buffer;
      box.y -= buffer;
      box.width += buffer * 2;
      box.height += buffer * 2;
      this.viewer.viewport.fitBounds(box);
    },

    // ----------
    getFocusedPhoto: function() {
      var self = this;

      if (!this.viewer) {
        return null;
      }

      var box = this.viewer.viewport.getBounds(true);
      if (box.width > 2 && box.height > 2) {
        return null;
      }

      var pos = box.getCenter();
      var best;
      _.each(this.photos, function(v, i) {
        var center = v.getBounds().getCenter();
        var distance = self.distance(pos, center);
        if (!best || best.distance > distance) {
          best = {
            photo: v,
            distance: distance
          };
        }
      });

      return best ? best.photo : null;
    },

    // ----------
    updateButtons: function() {
      if (!this.selectedPhoto) {
        return;
      }

      var photoBounds = this.selectedPhoto.getBounds();
      var viewBounds = this.viewer.viewport.getBounds(false);
      var intersection = this.intersection(photoBounds, viewBounds);

      var photoArea = photoBounds.width * photoBounds.height;
      var viewArea = viewBounds.width * viewBounds.height;
      var intersectionArea = intersection ? intersection.width * intersection.height : 0;

      if ((intersectionArea < viewArea * 0.5 && intersectionArea < photoArea * 0.33) || photoArea < viewArea * 0.10) {
        this.select(null);
      }
    },

    // ----------
    hitTest: function(pixel) {
      var pos = this.viewer.viewport.pointFromPixel(pixel);

      var photo = _.find(this.photos, function(v, i) {
        var box = v.getBounds();
        return (pos.x > box.x && pos.y > box.y && pos.x < box.x + box.width && pos.y < box.y + box.height);
      });

      return photo;
    },

    // ----------
    showTags: function(photo) {
      var self = this;

      if (this.isTouch) {
        return;
      }

      _.each(this.photos, function(v, i) {
        _.each(v.tags, function(v2, i2) {
          v2.hide();
        });
      });

      if (photo) {
        var box = photo.getBounds();
        var tl = box.getTopLeft();

        _.each(photo.tags, function(v, i) {
          v.setPosition(new OpenSeadragon.Point(tl.x + (Math.random() * box.width), tl.y + (Math.random() * box.height)));
          v.show();
        });
      }
    },

    // ----------
    showMobileTags: function() {
      var self = this;

      if (!this.selectedPhoto) {
        return;
      }

      this.selectedPhoto.deselect();

      $('.info-button').hide();
      $('.tag-list-container').show();
      var $list = $('.tag-list .content');

      _.each(this.selectedPhoto.tags, function(v, i) {
        $('<div class="unit">' + v.getText() + '</div>')
          .click(function(event) {
            event.preventDefault();
            event.stopPropagation();
            self.hideMobileTags();
            self.loadForTag(v);
          })
          .appendTo($list);
      });
    },

    // ----------
    hideMobileTags: function() {
      $('.info-button')
        .show();

      $('.tag-list-container')
        .hide();

      $('.tag-list .content')
        .empty();

      if (this.selectedPhoto) {
        this.selectedPhoto.select();
      }
    },

    // ----------
    inside: function(point, rect) {
      return (point.x >= rect.x && point.x < rect.x + rect.width && point.y >= rect.y && point.y < rect.y + rect.height);
    },

    // ----------
    distance: function(point1, point2) {
      var diffX = point1.x - point2.x;
      var diffY = point1.y - point2.y;
      return Math.sqrt((diffX * diffX) + (diffY * diffY));
    },

    // ----------
    intersection: function(rect1, rect2) {
        var left = Math.max(rect1.x, rect2.x);
        var top = Math.max(rect1.y, rect2.y);
        var right = Math.min(rect1.x + rect1.width, rect2.x + rect2.width);
        var bottom = Math.min(rect1.y + rect1.height, rect2.y + rect2.height);

        if (bottom > top && right > left) {
          return new OpenSeadragon.Rect(left, top, right - left, bottom - top);
        }

        return null;
    },

    // ----------
    sign: function(value) {
      return value > 0 ? 1 : (value < 0 ? -1 : 0);
    },

    // ----------
    spin: function(value) {
      if (value) {
        this.spinner = new Spinner({
          color: '#fff'
        }).spin($("body")[0]);
      } else {
        this.spinner.stop();
      }
    }
  };

  // ----------
  //$(document).ready(function() {
  //  OpenSeadragonMultiApp.init();
  //});

})();
