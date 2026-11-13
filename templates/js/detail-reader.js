/**
 * DetailReader — reusable modal reader for Work case studies and Project articles.
 * Supports resize (drag handle), zoom (+/-/fit), scroll, keyboard accessibility, and light dismiss.
 *
 * Usage:
 *   var reader = new DetailReader({ workData: [...], blogs: [...] });
 *   reader.openWork(idOrIndex);
 *   reader.openBlog(id);
 *   reader.close();
 */
(function () {
  'use strict';

  var DetailReader = function (options) {
    options = options || {};
    this.workData = options.workData || [];
    this.blogs = options.blogs || [];
    this.type = null;      // 'work' | 'blog'
    this.currentId = null;
    this.currentType = null;
    this.history = [];     // navigation stack for linked cards
    this.zoom = 100;
    this.isFullscreen = false;
    this.isResizing = false;
    this.startX = 0;
    this.startY = 0;
    this.startW = 0;
    this.startH = 0;
    this.focusTrapEl = null;

    this._buildModal();
    this._bindEvents();
  };

  /* ---------- DOM CONSTRUCTION ---------- */

  DetailReader.prototype._buildModal = function () {
    var overlay = document.createElement('div');
    overlay.className = 'detail-reader-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-labelledby', 'detail-reader-heading');

    overlay.innerHTML =
      '<div class="detail-reader-wrapper">' +
        '<div class="detail-reader-toolbar">' +
          '<button class="dr-zoom-btn dr-back-btn" title="Back to previous card (Backspace)" aria-label="Go back" style="display:none;">← Back</button>' +
          '<button class="dr-zoom-btn dr-zoom-out" title="Zoom out (-)" aria-label="Zoom out">−</button>' +
          '<span class="dr-zoom-label">100%</span>' +
          '<button class="dr-zoom-btn dr-zoom-in" title="Zoom in (+)" aria-label="Zoom in">+</button>' +
          '<button class="dr-zoom-btn dr-zoom-fit" title="Reset zoom (0)" aria-label="Reset zoom">Reset</button>' +
          '<button class="dr-zoom-btn dr-fullscreen-btn" title="Toggle full screen (F)" aria-label="Toggle full screen">⤢ Fullscreen</button>' +
          '<button class="detail-reader-close" title="Close (Escape)" aria-label="Close">&times;</button>' +
        '</div>' +
        '<div class="detail-reader-scroll">' +
          '<div class="detail-reader-content" id="detail-reader-heading"></div>' +
        '</div>' +
        '<div class="detail-reader-resize-handle" title="Drag to resize"></div>' +
      '</div>';

    document.body.appendChild(overlay);
    this.overlay = overlay;
    this.wrapper = overlay.querySelector('.detail-reader-wrapper');
    this.scrollArea = overlay.querySelector('.detail-reader-scroll');
    this.content = overlay.querySelector('.detail-reader-content');
    this.zoomLabel = overlay.querySelector('.dr-zoom-label');
    this.resizeHandle = overlay.querySelector('.detail-reader-resize-handle');
    this.backBtn = overlay.querySelector('.dr-back-btn');
  };

  /* ---------- EVENT BINDING ---------- */

  DetailReader.prototype._bindEvents = function () {
    var self = this;

    // Back button
    if (this.backBtn) {
      this.backBtn.addEventListener('click', function () { self.goBack(); });
    }

    // Close buttons
    this.overlay.querySelector('.detail-reader-close').addEventListener('click', function () { self.close(); });

    // Close on backdrop click (light dismiss)
    this.overlay.addEventListener('click', function (e) {
      if (e.target === self.overlay) self.close();
    });

    // Zoom buttons
    this.overlay.querySelector('.dr-zoom-out').addEventListener('click', function () { self.zoomBy(-10); });
    this.overlay.querySelector('.dr-zoom-in').addEventListener('click', function () { self.zoomBy(10); });
    this.overlay.querySelector('.dr-zoom-fit').addEventListener('click', function () { self.zoomFit(); });
    this.overlay.querySelector('.dr-fullscreen-btn').addEventListener('click', function () { self.toggleFullscreen(); });

    // Keyboard
    document.addEventListener('keydown', function (e) {
      if (!self.overlay.classList.contains('active')) return;
      if (e.key === 'Escape') { self.close(); return; }
      if ((e.key === 'Backspace' && document.activeElement && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') || (e.altKey && e.key === 'ArrowLeft')) {
        if (self.history && self.history.length > 0) {
          self.goBack();
          e.preventDefault();
          return;
        }
      }
      if (e.key === '+' || e.key === '=') { self.zoomBy(10); e.preventDefault(); }
      if (e.key === '-' || e.key === '_') { self.zoomBy(-10); e.preventDefault(); }
      if (e.key === '0') { self.zoomFit(); e.preventDefault(); }
      if (e.key === 'f' || e.key === 'F') { self.toggleFullscreen(); e.preventDefault(); }
    });

    // Tab trapping
    this.overlay.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      self._trapTab(e);
    });

    // Resize drag
    this.resizeHandle.addEventListener('mousedown', function (e) { self._startResize(e); });
    document.addEventListener('mousemove', function (e) { self._onResize(e); });
    document.addEventListener('mouseup', function () { self._endResize(); });

    // Touch resize
    this.resizeHandle.addEventListener('touchstart', function (e) { self._startResize(e.touches[0]); });
    document.addEventListener('touchmove', function (e) {
      if (self.isResizing && e.touches[0]) self._onResize(e.touches[0]);
    });
    document.addEventListener('touchend', function () { self._endResize(); });
  };

  /* ---------- DATA SYNC & LOOKUP ---------- */

  DetailReader.prototype._syncData = function () {
    if ((!this.workData || !this.workData.length) && window.WORK_DATA) {
      this.workData = window.WORK_DATA;
    }
    if ((!this.blogs || !this.blogs.length) && window.BLOG_DATA) {
      this.blogs = window.BLOG_DATA;
    }
  };

  DetailReader.prototype._findItem = function (idOrIndex, preferredType) {
    this._syncData();
    var item = null;

    if (preferredType === 'work') {
      if (typeof idOrIndex === 'number' || (!isNaN(parseInt(idOrIndex, 10)) && typeof idOrIndex !== 'string')) {
        item = this.workData[idOrIndex];
      } else {
        item = this.workData.find(function (w) { return w.id === idOrIndex; });
        if (!item && typeof idOrIndex === 'string') {
          var num = parseInt(idOrIndex, 10);
          if (!isNaN(num) && this.workData[num]) item = this.workData[num];
        }
      }
      if (item) return { item: item, type: 'work' };
    } else if (preferredType === 'blog' || preferredType === 'project') {
      item = this.blogs.find(function (b) { return b.id === idOrIndex; });
      if (item) return { item: item, type: 'blog' };
    }

    // Generic lookup across both sets
    item = (this.workData || []).find(function (w) { return w.id === idOrIndex; });
    if (item) return { item: item, type: 'work' };

    item = (this.blogs || []).find(function (b) { return b.id === idOrIndex; });
    if (item) return { item: item, type: 'blog' };

    return null;
  };

  /* ---------- OPEN / CLOSE / NAVIGATION ---------- */

  DetailReader.prototype.openItem = function (idOrEntry, preferredType, pushHistory) {
    this._syncData();
    var match = null;

    if (typeof idOrEntry === 'object' && idOrEntry !== null) {
      var itemType = preferredType || idOrEntry.type || (idOrEntry.company ? 'work' : 'blog');
      match = { item: idOrEntry, type: itemType };
    } else {
      match = this._findItem(idOrEntry, preferredType);
    }

    if (!match || !match.item) return;

    var entry = match.item;
    var type = match.type;
    var isModalActive = this.overlay.classList.contains('active');

    if (pushHistory && isModalActive && this.currentId && this.currentId !== entry.id) {
      this.history.push({ id: this.currentId, type: this.currentType });
    } else if (!isModalActive) {
      this.history = [];
    }

    this.currentId = entry.id;
    this.currentType = type;
    this.type = type;
    this._updateBackButton();

    var html = '';
    if (type === 'work') {
      var metricsHtml = '';
      if (entry.metrics && entry.metrics.length) {
        metricsHtml = '<div class="dr-metrics-row">';
        entry.metrics.forEach(function (m) {
          metricsHtml += '<span class="dr-metric-pill">✦ ' + this._esc(m) + '</span>';
        }.bind(this));
        metricsHtml += '</div>';
      }

      var tagsHtml = '';
      var tags = entry.techStack || entry.tags || [];
      if (tags && tags.length) {
        tagsHtml = '<div class="dr-tags">';
        tags.forEach(function (t) {
          tagsHtml += '<span class="dr-tag">#' + this._esc(t) + '</span>';
        }.bind(this));
        tagsHtml += '</div>';
      }

      var bodyHtml = '';
      if (entry.content) {
        bodyHtml = '<div class="dr-article">' + entry.content + '</div>';
      } else if (entry.bullets && entry.bullets.length) {
        bodyHtml = '<div class="dr-section"><ul class="dr-bullets">' + this._bullets(entry.bullets) + '</ul></div>';
      }

      html =
        '<h1 class="dr-title">' + this._esc(entry.title || entry.role) + '</h1>' +
        '<div class="dr-subtitle">' +
          '<span class="dr-company">' + this._esc(entry.company) + '</span>' +
          '<span class="dr-meta">' + this._esc(entry.role) + ' &bull; ' + this._esc(entry.period || '') + (entry.location ? ' &bull; ' + this._esc(entry.location) : '') + '</span>' +
        '</div>' +
        (entry.category ? '<div class="dr-category-badge">' + this._esc(entry.category) + '</div>' : '') +
        metricsHtml +
        tagsHtml +
        bodyHtml;
    } else {
      var tags = '';
      if (entry.tags && entry.tags.length) {
        tags = '<div class="dr-tags">';
        entry.tags.forEach(function (t) { tags += '<span class="dr-tag">#' + this._esc(t) + '</span>'; }.bind(this));
        tags += '</div>';
      }

      var metaInfo = this._esc(entry.date || '') + ' &bull; ' + this._esc(entry.readTime || '5 min read');
      if (entry.topic) {
        metaInfo = '<span class="dr-category-badge" style="margin-right:0.6rem;margin-bottom:0;">' + this._esc(entry.topic) + '</span> ' + metaInfo;
      }

      html =
        '<h1 class="dr-title">' + this._esc(entry.title) + '</h1>' +
        '<div class="dr-subtitle" style="margin-bottom:1rem;">' + metaInfo + '</div>' +
        tags +
        '<div class="dr-article">' + (entry.content || '') + '</div>';
    }

    html += this._renderRelatedSection(entry.related_items);

    this.content.innerHTML = html;
    this._bindRelatedClicks();
    this._show();
  };

  DetailReader.prototype._renderRelatedSection = function (relatedItems) {
    if (!relatedItems || !relatedItems.length) return '';
    var out =
      '<div class="dr-related-section">' +
        '<div class="dr-related-header">' +
          '<h3 class="dr-related-title">🔗 Connected Case Studies & Deep Dives</h3>' +
          '<p class="dr-related-hint">Explore related production architectures and system implementations</p>' +
        '</div>' +
        '<div class="dr-related-grid">';

    for (var i = 0; i < relatedItems.length; i++) {
      var rel = relatedItems[i];
      var isWork = (rel.type === 'work');
      var badge = isWork ? '💼 Production Work' : '🚀 Deep Dive Project';
      var subtitle = rel.company || rel.category || '';
      out +=
        '<div class="dr-related-card" data-id="' + this._esc(rel.id) + '" role="button" tabindex="0" aria-label="Open connected study: ' + this._esc(rel.title) + '">' +
          '<div class="dr-related-card-top">' +
            '<span class="dr-related-card-badge ' + (isWork ? 'badge-work' : 'badge-project') + '">' + badge + '</span>' +
            (rel.readTime ? '<span class="dr-related-card-time">' + this._esc(rel.readTime) + '</span>' : '') +
          '</div>' +
          '<h4 class="dr-related-card-title">' + this._esc(rel.title) + '</h4>' +
          (subtitle ? '<div class="dr-related-card-meta">' + this._esc(subtitle) + '</div>' : '') +
          '<div class="dr-related-card-action">Explore Connected Study &rarr;</div>' +
        '</div>';
    }

    out += '</div></div>';
    return out;
  };

  DetailReader.prototype._bindRelatedClicks = function () {
    var self = this;
    var relCards = this.content.querySelectorAll('.dr-related-card');
    relCards.forEach(function (card) {
      function triggerRel(e) {
        e.preventDefault();
        e.stopPropagation();
        var id = card.getAttribute('data-id');
        if (id) self.openLinked(id);
      }
      card.addEventListener('click', triggerRel);
      card.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') triggerRel(e);
      });
    });
  };

  DetailReader.prototype.openWork = function (idOrIndex) {
    this.openItem(idOrIndex, 'work', false);
  };

  DetailReader.prototype.openBlog = function (id) {
    this.openItem(id, 'blog', false);
  };

  DetailReader.prototype.openLinked = function (id) {
    this.openItem(id, null, true);
  };

  DetailReader.prototype.goBack = function () {
    if (!this.history || !this.history.length) return;
    var prev = this.history.pop();
    this._updateBackButton();
    this.openItem(prev.id, prev.type, false);
  };

  DetailReader.prototype._updateBackButton = function () {
    if (!this.backBtn) return;
    if (this.history && this.history.length > 0) {
      this.backBtn.style.display = 'inline-flex';
      this.backBtn.textContent = '← Back';
      this.backBtn.title = 'Back to previous study (Backspace)';
    } else {
      this.backBtn.style.display = 'none';
    }
  };

  DetailReader.prototype.close = function () {
    this.overlay.classList.remove('active');
    document.body.style.overflow = '';
    if (this.isFullscreen) {
      this.toggleFullscreen();
    }
    this.zoomFit();
    this.history = [];
    this.currentId = null;
    this.currentType = null;
    this._updateBackButton();
    if (this.focusTrapEl && this.focusTrapEl.focus) this.focusTrapEl.focus();
    this.focusTrapEl = null;
  };

  DetailReader.prototype.toggleFullscreen = function () {
    this.isFullscreen = !this.isFullscreen;
    this.wrapper.classList.toggle('is-fullscreen', this.isFullscreen);
    // Reset manual inline widths so fullscreen class takes effect cleanly
    if (this.isFullscreen) {
      this.wrapper.style.width = '';
      this.wrapper.style.height = '';
    }
    var btn = this.overlay.querySelector('.dr-fullscreen-btn');
    if (btn) {
      btn.innerHTML = this.isFullscreen ? '⤡ Restore' : '⤢ Fullscreen';
      btn.title = this.isFullscreen ? 'Restore window size (F)' : 'Toggle full screen (F)';
    }
  };

  DetailReader.prototype._show = function () {
    this.focusTrapEl = document.activeElement;
    this.overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    this.zoomFit();
    this.scrollArea.scrollTop = 0;
    var closeBtn = this.overlay.querySelector('.detail-reader-close');
    if (closeBtn) closeBtn.focus();
  };

  /* ---------- ZOOM ---------- */

  DetailReader.prototype.zoomBy = function (delta) {
    this.zoom = Math.min(200, Math.max(50, this.zoom + delta));
    this._applyZoom();
  };

  DetailReader.prototype.zoomFit = function () {
    this.zoom = 100;
    this._applyZoom();
  };

  DetailReader.prototype._applyZoom = function () {
    this.content.style.transform = 'scale(' + (this.zoom / 100) + ')';
    this.content.style.transformOrigin = 'top left';
    this.zoomLabel.textContent = this.zoom + '%';
  };

  /* ---------- RESIZE ---------- */

  DetailReader.prototype._startResize = function (e) {
    this.isResizing = true;
    this.startX = e.clientX;
    this.startY = e.clientY;
    var rect = this.wrapper.getBoundingClientRect();
    this.startW = rect.width;
    this.startH = rect.height;
    e.preventDefault();
  };

  DetailReader.prototype._onResize = function (e) {
    if (!this.isResizing) return;
    var dw = e.clientX - this.startX;
    var dh = e.clientY - this.startY;
    var newW = Math.max(400, this.startW + dw);
    var newH = Math.max(300, this.startH + dh);
    this.wrapper.style.width = newW + 'px';
    this.wrapper.style.height = newH + 'px';
  };

  DetailReader.prototype._endResize = function () {
    this.isResizing = false;
  };

  /* ---------- TAB TRAP ---------- */

  DetailReader.prototype._trapTab = function (e) {
    var focusable = this.overlay.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (!focusable.length) return;
    var first = focusable[0];
    var last = focusable[focusable.length - 1];

    if (e.shiftKey) {
      if (document.activeElement === first) { last.focus(); e.preventDefault(); }
    } else {
      if (document.activeElement === last) { first.focus(); e.preventDefault(); }
    }
  };

  /* ---------- HELPERS ---------- */

  DetailReader.prototype._esc = function (str) {
    if (str === null || str === undefined) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  };

  DetailReader.prototype._bullets = function (bullets) {
    if (!bullets || !bullets.length) return '';
    var out = '';
    for (var i = 0; i < bullets.length; i++) {
      out += '<li>' + this._esc(bullets[i]) + '</li>';
    }
    return out;
  };

  /* ---------- GLOBAL CARD CLICK DELEGATION ---------- */

  var _delegationInitialized = false;
  DetailReader.initGlobalCardDelegation = function () {
    if (_delegationInitialized || typeof document === 'undefined') return;
    _delegationInitialized = true;

    document.addEventListener('click', function (e) {
      // 1. Connected pill clicked
      var pill = e.target.closest('.connected-pill, .card-related-pill, .card-related-chip');
      if (pill) {
        e.preventDefault();
        e.stopPropagation();
        var relId = pill.getAttribute('data-id');
        var r = (typeof getDetailReader === 'function') ? getDetailReader() : window.detailReader;
        if (r && relId) r.openLinked(relId);
        return;
      }

      // 2. Card action link clicked
      var openBtn = e.target.closest('.content-card-open, .work-card-open, .project-card-open, .home-work-open');
      if (openBtn) {
        e.preventDefault();
        e.stopPropagation();
        var btnId = openBtn.getAttribute('data-id');
        var r = (typeof getDetailReader === 'function') ? getDetailReader() : window.detailReader;
        if (r && btnId) r.openLinked(btnId);
        return;
      }

      // 3. Whole card clicked
      var card = e.target.closest('.content-card, .work-card, .project-card');
      if (card) {
        var tag = e.target.tagName.toLowerCase();
        if (tag === 'video' || tag === 'source' || tag === 'input' || tag === 'select' || tag === 'button') return;
        var cardId = card.getAttribute('data-id');
        if (!cardId) {
          var btn = card.querySelector('[data-id]');
          if (btn) cardId = btn.getAttribute('data-id');
        }
        var r = (typeof getDetailReader === 'function') ? getDetailReader() : window.detailReader;
        if (r && cardId) r.openLinked(cardId);
      }
    });
  };

  // Expose globally and initialize delegation immediately
  DetailReader.initGlobalCardDelegation();
  window.DetailReader = DetailReader;
})();
