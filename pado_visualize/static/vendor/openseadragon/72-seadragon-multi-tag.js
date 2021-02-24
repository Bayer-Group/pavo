(function() {

  // ----------
  var component = OpenSeadragonMultiApp.Tag = function(config) {
    var self = this;

    this.item = new OpenSeadragonMultiApp.TextItem({
      text: config.text,
      onClick: function() {
        OpenSeadragonMultiApp.loadForTag(self);
      }
    });
  };

  // ----------
  component.prototype = {
    // ----------
    getText: function() {
      return this.item.text;
    },
    
    // ----------
    getPosition: function() {
      return this.item.getPosition();
    },

    // ----------
    setPosition: function(value) {
      this.item.setPosition(value);
    }, 

    // ----------
    getBounds: function() {
      return this.item.getBounds();
    },

    // ----------
    show: function() {
      this.item.show();
    }, 

    // ----------
    hide: function() {
      this.item.hide();
    }
  };

})();
