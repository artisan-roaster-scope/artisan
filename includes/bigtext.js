/*! BigText - v0.1.6 - 2014-04-21
 * https://github.com/zachleat/bigtext
 * Copyright (c) 2014 Zach Leatherman (@zachleat)
 * MIT License */

(function(window, $) {
  "use strict";

  var counter = 0,
    $headCache = $('head'),
    oldBigText = window.BigText,
    oldjQueryMethod = $.fn.bigtext,
    BigText = {
      DEBUG_MODE: false,
      DEFAULT_MIN_FONT_SIZE_PX: null,
      DEFAULT_MAX_FONT_SIZE_PX: 528,
      GLOBAL_STYLE_ID: 'bigtext-style',
      STYLE_ID: 'bigtext-id',
      LINE_CLASS_PREFIX: 'bigtext-line',
      EXEMPT_CLASS: 'bigtext-exempt',
      noConflict: function(restore)
      {
        if(restore) {
          $.fn.bigtext = oldjQueryMethod;
          window.BigText = oldBigText;
        }
        return BigText;
      },
      test: {
        noFractionalFontSize: (function() {
          if( !( 'getComputedStyle' in window ) || !( 'body' in document ) ) {
            return true;
          }
          var test = $('<div/>').css({
              position: 'absolute',
              'font-size': '14.1px'
            }).appendTo(document.body).get(0),
            computedStyle = window.getComputedStyle( test, null );

          return computedStyle ? computedStyle.getPropertyValue( 'font-size' ) === '14px' : true;
        })()
      },
      init: function() {
        if(!$('#'+BigText.GLOBAL_STYLE_ID).length) {
          $headCache.append(BigText.generateStyleTag(BigText.GLOBAL_STYLE_ID, ['.bigtext * { white-space: nowrap; } .bigtext > * { display: block; }',
                                          '.bigtext .' + BigText.EXEMPT_CLASS + ', .bigtext .' + BigText.EXEMPT_CLASS + ' * { white-space: normal; }']));
        }
      },
      bindResize: function(eventName, resizeFunction) {
        if($.throttle) {
          // https://github.com/cowboy/jquery-throttle-debounce
          $(window).unbind(eventName).bind(eventName, $.throttle(100, resizeFunction));
        } else {
          if($.fn.smartresize) {
            // https://github.com/lrbabe/jquery-smartresize/
            eventName = 'smartresize.' + eventName;
          }
          $(window).unbind(eventName).bind(eventName, resizeFunction);
        }
      },
      getStyleId: function(id)
      {
        return BigText.STYLE_ID + '-' + id;
      },
      generateStyleTag: function(id, css)
      {
        return $('<style>' + css.join('\n') + '</style>').attr('id', id);
      },
      clearCss: function(id)
      {
        var styleId = BigText.getStyleId(id);
        $('#' + styleId).remove();
      },
      generateCss: function(id, linesFontSizes, lineWordSpacings, minFontSizes)
      {
        var css = [];

        BigText.clearCss(id);

        for(var j=0, k=linesFontSizes.length; j<k; j++) {
          css.push('#' + id + ' .' + BigText.LINE_CLASS_PREFIX + j + ' {' +
            (minFontSizes[j] ? ' white-space: normal;' : '') +
            (linesFontSizes[j] ? ' font-size: ' + linesFontSizes[j] + 'px;' : '') +
            (lineWordSpacings[j] ? ' word-spacing: ' + lineWordSpacings[j] + 'px;' : '') +
            '}');
        }

        return BigText.generateStyleTag(BigText.getStyleId(id), css);
      },
      jQueryMethod: function(options)
      {
        BigText.init();

        options = $.extend({
          minfontsize: BigText.DEFAULT_MIN_FONT_SIZE_PX,
          maxfontsize: BigText.DEFAULT_MAX_FONT_SIZE_PX,
          childSelector: '',
          resize: true
        }, options || {});

        this.each(function()
        {
          var $t = $(this).addClass('bigtext'),
            maxWidth = $t.width(),
            id = $t.attr('id'),
            $children = options.childSelector ? $t.find( options.childSelector ) : $t.children();

          if(!id) {
            id = 'bigtext-id' + (counter++);
            $t.attr('id', id);
          }

          if(options.resize) {
            BigText.bindResize('resize.bigtext-event-' + id, function()
            {
              // TODO only call this if the width has changed.
              BigText.jQueryMethod.call($('#' + id), options);
            });
          }

          BigText.clearCss(id);

          $children.addClass(function(lineNumber, className)
          {
            // remove existing line classes.
            return [className.replace(new RegExp('\\b' + BigText.LINE_CLASS_PREFIX + '\\d+\\b'), ''),
                BigText.LINE_CLASS_PREFIX + lineNumber].join(' ');
          });

          var sizes = calculateSizes($t, $children, maxWidth, options.maxfontsize, options.minfontsize);
          $headCache.append(BigText.generateCss(id, sizes.fontSizes, sizes.wordSpacings, sizes.minFontSizes));
        });

        return this.trigger('bigtext:complete');
      }
    };

  function testLineDimensions($line, maxWidth, property, size, interval, units, previousWidth)
  {
    var width;
    previousWidth = typeof previousWidth === 'number' ? previousWidth : 0;
    $line.css(property, size + units);

    width = $line.width();

    if(width >= maxWidth) {
// console.log(width, ' previous: ' + previousWidth, property + ' at ' + interval, 'prior: ' + (parseFloat(size) - interval), 'new:' + parseFloat(size));
      $line.css(property, '');

      if(width === maxWidth) {
        return {
          match: 'exact',
          size: parseFloat((parseFloat(size) - 0.1).toFixed(3))
        };
      }

      // Since this is an estimate, we calculate how far over the width we went with the new value.
      // If this is word-spacing (our last resort guess) and the over is less than the under, we keep the higher value.
      // Otherwise, we revert to the underestimate.
      var under = maxWidth - previousWidth,
        over = width - maxWidth;

      return {
        match: 'estimate',
        size: parseFloat((parseFloat(size) - (property === 'word-spacing' && previousWidth && ( over < under ) ? 0 : interval)).toFixed(3))
      };
    }

    return width;
  }

  function calculateSizes($t, $children, maxWidth, maxFontSize, minFontSize)
  {
    var $c = $t.clone(true)
      .addClass('bigtext-cloned')
      .css({
        fontFamily: $t.css('font-family'),
        textTransform: $t.css('text-transform'),
        wordSpacing: $t.css('word-spacing'),
        letterSpacing: $t.css('letter-spacing'),
        position: 'absolute',
        left: BigText.DEBUG_MODE ? 0 : -9999,
        top: BigText.DEBUG_MODE ? 0 : -9999
      })
      .appendTo(document.body);

    // font-size isn't the only thing we can modify, we can also mess with:
    // word-spacing and letter-spacing. WebKit does not respect subpixel
    // letter-spacing, word-spacing, or font-size.
    // TODO try -webkit-transform: scale() as a workaround.
    var fontSizes = [],
      wordSpacings = [],
      minFontSizes = [],
      ratios = [];

    $children.css('float', 'left').each(function() {
      var $line = $(this),
        // TODO replace 8, 4 with a proportional size to the calculated font-size.
        intervals = BigText.test.noFractionalFontSize ? [8, 4, 1] : [8, 4, 1, 0.1],
        lineMax,
        newFontSize;

      if($line.hasClass(BigText.EXEMPT_CLASS)) {
        fontSizes.push(null);
        ratios.push(null);
        minFontSizes.push(false);
        return;
      }

      // TODO we can cache this ratio?
      var autoGuessSubtraction = 32, // font size in px
        currentFontSize = parseFloat($line.css('font-size')),
        ratio = ( $line.width() / currentFontSize ).toFixed(6);

      newFontSize = parseInt( maxWidth / ratio, 10 ) - autoGuessSubtraction;

      outer: for(var m=0, n=intervals.length; m<n; m++) {
        inner: for(var j=1, k=10; j<=k; j++) {
          if(newFontSize + j*intervals[m] > maxFontSize) {
            newFontSize = maxFontSize;
            break outer;
          }

          lineMax = testLineDimensions($line, maxWidth, 'font-size', newFontSize + j*intervals[m], intervals[m], 'px', lineMax);
          if(typeof lineMax !== 'number') {
            newFontSize = lineMax.size;

            if(lineMax.match === 'exact') {
              break outer;
            }
            break inner;
          }
        }
      }

      ratios.push(maxWidth / newFontSize);

      if(newFontSize > maxFontSize) {
        fontSizes.push(maxFontSize);
        minFontSizes.push(false);
      } else if(!!minFontSize && newFontSize < minFontSize) {
        fontSizes.push(minFontSize);
        minFontSizes.push(true);
      } else {
        fontSizes.push(newFontSize);
        minFontSizes.push(false);
      }
    }).each(function(lineNumber) {
      var $line = $(this),
        wordSpacing = 0,
        interval = 1,
        maxWordSpacing;

      if($line.hasClass(BigText.EXEMPT_CLASS)) {
        wordSpacings.push(null);
        return;
      }

      // must re-use font-size, even though it was removed above.
      $line.css('font-size', fontSizes[lineNumber] + 'px');

      for(var m=1, n=3; m<n; m+=interval) {
        maxWordSpacing = testLineDimensions($line, maxWidth, 'word-spacing', m, interval, 'px', maxWordSpacing);
        if(typeof maxWordSpacing !== 'number') {
          wordSpacing = maxWordSpacing.size;
          break;
        }
      }

      $line.css('font-size', '');
      wordSpacings.push(wordSpacing);
    }).removeAttr('style');

    if( !BigText.DEBUG_MODE ) {
      $c.remove();
    } else {
      $c.css({
        'background-color': 'rgba(255,255,255,.4)'
      });
    }

    return {
      fontSizes: fontSizes,
      wordSpacings: wordSpacings,
      ratios: ratios,
      minFontSizes: minFontSizes
    };
  }

  $.fn.bigtext = BigText.jQueryMethod;
  window.BigText = BigText;

})(this, jQuery);
