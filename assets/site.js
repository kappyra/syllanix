(function () {
  "use strict";
  var root = document.documentElement;
  var store = {
    get: function (key) { try { return localStorage.getItem("syllanix-" + key); } catch (e) { return null; } },
    set: function (key, value) { try { localStorage.setItem("syllanix-" + key, value); } catch (e) {} },
    del: function (key) { try { localStorage.removeItem("syllanix-" + key); } catch (e) {} }
  };
  var validThemes = { warm: true, light: true, dark: true };
  function getTheme() {
    var current = store.get("theme");
    return validThemes[current] ? current : "warm";
  }
  function applyTheme(theme) {
    var normalized = validThemes[theme] ? theme : "warm";
    root.setAttribute("data-theme", normalized);
    var selector = document.getElementById("theme-select");
    if (selector) { selector.value = normalized; }
  }
  applyTheme(getTheme());

  /* ---------- Три темы: исходная тёплая, белая, тёмная ---------- */
  var legacyButton = document.getElementById("theme-toggle");
  if (legacyButton) {
    var selector = document.createElement("select");
    selector.id = "theme-select";
    selector.className = "theme-select";
    selector.setAttribute("aria-label", "Тема оформления: тёплая, белая или тёмная");
    [
      { value: "warm", label: "☀ Тёплая" },
      { value: "light", label: "◻ Белая" },
      { value: "dark", label: "☾ Тёмная" }
    ].forEach(function (item) {
      var option = document.createElement("option");
      option.value = item.value;
      option.textContent = item.label;
      selector.appendChild(option);
    });
    legacyButton.replaceWith(selector);
    selector.value = getTheme();
    selector.addEventListener("change", function () {
      if (!validThemes[selector.value]) { return; }
      store.set("theme", selector.value);
      applyTheme(selector.value);
    });
  }

  /* ---------- Сайдбар / drawer ---------- */
  var sidebar = document.getElementById("sidebar");
  var menuButton = document.getElementById("menu-toggle");
  var backdrop = document.getElementById("drawer-backdrop");
  var mobileQuery = window.matchMedia("(max-width: 1023px)");
  var lastFocus = null;
  function isMobile() { return mobileQuery.matches; }
  function setDrawer(open) {
    if (!sidebar || !menuButton) { return; }
    if (isMobile()) {
      document.body.classList.toggle("drawer-open", open);
      sidebar.classList.toggle("open", open);
      menuButton.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) {
        lastFocus = document.activeElement;
        var first = sidebar.querySelector("a, button, summary");
        if (first) { first.focus(); }
      } else if (lastFocus) { lastFocus.focus(); }
    } else {
      var reading = document.body.classList.toggle("reading-mode");
      menuButton.setAttribute("aria-expanded", reading ? "false" : "true");
      store.set("sidebar", reading ? "collapsed" : "open");
    }
  }
  if (menuButton) {
    menuButton.addEventListener("click", function (event) {
      // Ссылка #sidebar — резервный путь без JS; с JS используем доступный drawer.
      event.preventDefault();
      if (isMobile()) { setDrawer(!document.body.classList.contains("drawer-open")); }
      else { setDrawer(false); }
    });
  }
  if (backdrop) {
    backdrop.addEventListener("click", function (event) {
      event.preventDefault();
      setDrawer(false);
      // Убираем возможный #sidebar из адресной строки (резервный режим).
      if (window.location.hash === "#sidebar") { history.replaceState(null, "", location.pathname + location.search); }
    });
  }
  if (!isMobile() && store.get("sidebar") === "collapsed") { document.body.classList.add("reading-mode"); }
  if (menuButton && !isMobile()) { menuButton.setAttribute("aria-expanded", document.body.classList.contains("reading-mode") ? "false" : "true"); }
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && document.body.classList.contains("drawer-open")) { setDrawer(false); }
    if (event.key === "Tab" && document.body.classList.contains("drawer-open") && sidebar) {
      var focusables = sidebar.querySelectorAll("a[href], button, summary, input");
      if (!focusables.length) { return; }
      var first = focusables[0], last = focusables[focusables.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });

  /* ---------- Поиск ---------- */
  var dialog = document.getElementById("search-dialog");
  var searchInput = document.getElementById("search-input");
  var results = document.getElementById("search-results");
  var searchOpenButton = document.getElementById("search-open");
  var searchCloseButton = document.getElementById("search-close");
  var searchIndex = null, searchLoading = false, searchLastFocus = null;
  function loadIndex() {
    if (searchIndex || searchLoading) { return; }
    searchLoading = true;
    fetch("search.json", { credentials: "same-origin" })
      .then(function (response) { return response.ok ? response.json() : null; })
      .then(function (data) { if (data && Array.isArray(data.chapters)) { searchIndex = data.chapters; if (searchInput && searchInput.value.trim().length >= 2) { runSearch(searchInput.value); } } })
      .catch(function () { searchIndex = []; })
      .finally(function () { searchLoading = false; });
  }
  function clearResults() { if (results) { results.textContent = ""; } }
  function renderResults(items, query) {
    if (!results) { return; }
    clearResults();
    if (!items.length) {
      var empty = document.createElement("li");
      empty.className = "search-empty";
      empty.textContent = "Ничего не найдено по запросу «" + query + "»";
      results.appendChild(empty);
      return;
    }
    items.slice(0, 30).forEach(function (item) {
      var li = document.createElement("li");
      var link = document.createElement("a");
      link.href = item.url;
      link.textContent = (item.number ? item.number + ". " : "") + item.title;
      var meta = document.createElement("span");
      meta.className = "search-meta";
      meta.textContent = item.summary || "";
      link.appendChild(meta);
      li.appendChild(link);
      results.appendChild(li);
    });
  }
  function runSearch(query) {
    var needle = query.toLowerCase().trim();
    if (needle.length < 2) { clearResults(); return; }
    if (!searchIndex) { loadIndex(); return; }
    renderResults(searchIndex.filter(function (item) {
      var haystack = ((item.title || "") + " " + (item.summary || "") + " " + (item.headings || []).join(" ") + " " + (item.text || "")).toLowerCase();
      return haystack.indexOf(needle) !== -1;
    }), needle);
  }
  function openSearch() {
    if (!dialog) { return; }
    searchLastFocus = document.activeElement;
    dialog.classList.add("open");
    dialog.removeAttribute("hidden");
    if (searchInput) { searchInput.focus(); searchInput.select(); }
    loadIndex();
  }
  function closeSearch() {
    if (!dialog) { return; }
    dialog.classList.remove("open");
    dialog.setAttribute("hidden", "");
    if (searchLastFocus) { searchLastFocus.focus(); }
  }
  if (searchOpenButton) { searchOpenButton.addEventListener("click", openSearch); }
  if (searchCloseButton) { searchCloseButton.addEventListener("click", closeSearch); }
  if (searchInput) {
    searchInput.addEventListener("input", function () { loadIndex(); runSearch(searchInput.value); });
    searchInput.addEventListener("keydown", function (event) { if (event.key === "Escape") { closeSearch(); } });
  }
  if (dialog) {
    dialog.addEventListener("click", function (event) { if (event.target === dialog) { closeSearch(); } });
  }
  document.addEventListener("keydown", function (event) {
    var tag = (event.target && event.target.tagName || "").toLowerCase();
    var typing = tag === "input" || tag === "textarea" || (event.target && event.target.isContentEditable);
    if (event.key === "/" && !typing) { event.preventDefault(); openSearch(); return; }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); openSearch(); return; }
    if (event.key === "Escape" && dialog && dialog.classList.contains("open")) { closeSearch(); }
    if (typing) { return; }
    if (document.body.classList.contains("drawer-open")) { return; }
    if (event.key === "ArrowLeft") { var prev = document.querySelector('a[rel="prev"]'); if (prev) { window.location.href = prev.href; } }
    else if (event.key === "ArrowRight") { var next = document.querySelector('a[rel="next"]'); if (next) { window.location.href = next.href; } }
  });

  /* ---------- Drawer: кнопка закрытия и закрытие по ссылке ---------- */
  var drawerClose = document.getElementById("drawer-close");
  if (drawerClose) { drawerClose.addEventListener("click", function () { setDrawer(false); }); }
  if (sidebar) {
    sidebar.addEventListener("click", function (event) {
      var link = event.target.closest && event.target.closest("a");
      if (link && isMobile()) { setDrawer(false); }
    });
  }

  /* ---------- Кнопки копирования и подписи языка ---------- */
  document.querySelectorAll("pre > code").forEach(function (code) {
    var pre = code.parentElement;
    if (!pre || pre.closest(".code-block")) { return; }
    var match = (code.className || "").match(/language-([a-z0-9+#.-]+)/i);
    var language = match ? match[1].toLowerCase() : "";
    var wrapper = document.createElement("div");
    wrapper.className = "code-block";
    var meta = document.createElement("div");
    meta.className = "code-meta";
    var label = document.createElement("span");
    label.textContent = language || "код";
    var button = document.createElement("button");
    button.type = "button";
    button.className = "copy-btn";
    button.textContent = "Копировать";
    button.addEventListener("click", function () {
      var text = code.innerText;
      var done = function () { button.textContent = "Скопировано"; setTimeout(function () { button.textContent = "Копировать"; }, 1400); };
      if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(text).then(done, done); }
      else { var area = document.createElement("textarea"); area.value = text; document.body.appendChild(area); area.select(); try { document.execCommand("copy"); } catch (e) {} document.body.removeChild(area); done(); }
    });
    meta.appendChild(label);
    meta.appendChild(button);
    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(meta);
    wrapper.appendChild(pre);
  });

  /* ---------- Callout-блоки ---------- */
  document.querySelectorAll("blockquote").forEach(function (quote) {
    var text = (quote.textContent || "").trim().toLowerCase();
    var variant = null;
    if (/^(совет|подсказка|попробуйте)/.test(text)) { variant = "callout-tip"; }
    else if (/^(внимание|осторожно|важно)/.test(text)) { variant = "callout-warn"; }
    else if (/^(заметка|примечание)/.test(text)) { variant = "callout-note"; }
    if (variant) { quote.classList.add("callout"); quote.classList.add(variant); }
  });

  /* ---------- Просмотр рисунков: клавиатура, экранные считыватели, мобильный масштаб ---------- */
  var lightbox = document.getElementById("lightbox");
  if (lightbox) {
    var lightboxImage = lightbox.querySelector("img");
    var lightboxClose = document.getElementById("lightbox-close");
    var previousFigureFocus = null;
    function openFigure(image) {
      previousFigureFocus = image;
      if (lightboxImage) {
        lightboxImage.src = image.currentSrc || image.src;
        lightboxImage.alt = image.alt;
      }
      lightbox.classList.add("open");
      lightbox.removeAttribute("hidden");
      document.body.classList.add("figure-open");
      if (lightboxClose) { lightboxClose.focus(); }
    }
    function closeFigure() {
      lightbox.classList.remove("open");
      lightbox.setAttribute("hidden", "");
      document.body.classList.remove("figure-open");
      if (previousFigureFocus) { previousFigureFocus.focus(); }
    }
    document.querySelectorAll("figure img").forEach(function (image) {
      image.setAttribute("tabindex", "0");
      image.setAttribute("role", "button");
      image.setAttribute("aria-label", "Увеличить иллюстрацию: " + (image.alt || "рисунок"));
      image.addEventListener("click", function () { openFigure(image); });
      image.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openFigure(image);
        }
      });
    });
    lightbox.addEventListener("click", function (event) {
      if (event.target === lightbox) { closeFigure(); }
    });
    if (lightboxClose) {
      lightboxClose.addEventListener("click", function (event) {
        event.stopPropagation();
        closeFigure();
      });
    }
    document.addEventListener("keydown", function (event) {
      if (!lightbox.classList.contains("open")) { return; }
      if (event.key === "Escape") { event.preventDefault(); closeFigure(); }
      if (event.key === "Tab" && lightboxClose) { event.preventDefault(); lightboxClose.focus(); }
    });
  }

  /* ---------- Прогресс чтения ---------- */
  var progressBar = document.querySelector(".reading-progress > span");
  if (progressBar) {
    var updateProgress = function () {
      var scrollable = document.documentElement.scrollHeight - window.innerHeight;
      var ratio = scrollable > 0 ? Math.min(1, Math.max(0, window.scrollY / scrollable)) : 0;
      progressBar.style.width = (ratio * 100).toFixed(1) + "%";
    };
    window.addEventListener("scroll", updateProgress, { passive: true });
    window.addEventListener("resize", updateProgress);
    updateProgress();
  }

  /* ---------- Карта обучения ---------- */
  var mapPage = document.querySelector(".map-page");
  if (mapPage) {
    var viewport = mapPage.querySelector(".map-viewport");
    var svg = viewport ? viewport.querySelector("svg") : null;
    var baseViewBox = svg ? (svg.getAttribute("viewBox") || "").split(/\s+/).map(Number) : null;
    var state = { x: 0, y: 0, w: 0, h: 0, dragging: false, startX: 0, startY: 0, origin: null };
    var activePointers = new Map();
    var pinchStart = null;
    function applyViewBox() {
      if (!svg) { return; }
      svg.setAttribute("viewBox", state.x + " " + state.y + " " + state.w + " " + state.h);
    }
    function fitWidth() {
      if (!svg || !baseViewBox) { return; }
      var rect = viewport.getBoundingClientRect();
      var ratio = rect.width > 0 ? rect.height / rect.width : 0.6;
      if (rect.width > 0 && window.innerWidth < 768) {
        // На телефоне открываем всю ширину карты (без обрезки справа),
        // дальше пользователь зумит/панорамирует.
        state.w = baseViewBox[2];
        state.h = baseViewBox[2] * ratio;
      } else {
        // На десктопе — по ширине, но не мельче 11px для подписей глав.
        var minReadable = rect.width > 0 ? rect.width * 18 / 11 : baseViewBox[2];
        state.w = Math.min(baseViewBox[2], minReadable);
        state.h = state.w * ratio;
      }
      state.x = 0; state.y = 0;
      mapPage.classList.toggle("zoomed", state.w < baseViewBox[2] * 0.92);
      applyViewBox();
    }
    function resetView() { fitWidth(); }
    function zoom(factor, cx, cy) {
      if (!svg) { return; }
      var newW = Math.max(120, Math.min(state.w * factor, baseViewBox[2] * 6));
      var newH = newW * (state.h / state.w);
      var ratioX = cx === undefined ? 0.5 : (cx - state.x) / state.w;
      var ratioY = cy === undefined ? 0.5 : (cy - state.y) / state.h;
      state.x = state.x + (state.w - newW) * ratioX;
      state.y = state.y + (state.h - newH) * ratioY;
      state.w = newW; state.h = newH;
      mapPage.classList.toggle("zoomed", state.w < baseViewBox[2] * 0.92);
      applyViewBox();
    }
    if (svg) {
      resetView();
      mapPage.querySelectorAll(".map-node.chapter").forEach(function (chapterNode) {
        var chapterId = chapterNode.getAttribute("data-chapter") || "";
        var related = mapPage.querySelectorAll('.map-node.concept[data-chapter="' + chapterId.replace(/"/g, "") + '"]');
        chapterNode.addEventListener("mouseenter", function () {
          related.forEach(function (node) { node.classList.add("concept-active"); });
        });
        chapterNode.addEventListener("mouseleave", function () {
          related.forEach(function (node) { node.classList.remove("concept-active"); });
        });
      });
      viewport.addEventListener("wheel", function (event) {
        event.preventDefault();
        var rect = viewport.getBoundingClientRect();
        var cx = state.x + (event.clientX - rect.left) / rect.width * state.w;
        var cy = state.y + (event.clientY - rect.top) / rect.height * state.h;
        zoom(event.deltaY > 0 ? 1.15 : 0.87, cx, cy);
      }, { passive: false });
      viewport.addEventListener("pointerdown", function (event) {
        activePointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
        if (activePointers.size === 2) {
          var points = Array.from(activePointers.values());
          pinchStart = { distance: Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y), width: state.w };
          state.dragging = false;
          return;
        }
        if (event.target.closest && event.target.closest("a")) { return; }
        state.dragging = true; state.startX = event.clientX; state.startY = event.clientY;
        state.origin = { x: state.x, y: state.y };
        viewport.classList.add("dragging");
        if (viewport.setPointerCapture) { viewport.setPointerCapture(event.pointerId); }
      });
      viewport.addEventListener("pointermove", function (event) {
        if (activePointers.has(event.pointerId)) { activePointers.set(event.pointerId, { x: event.clientX, y: event.clientY }); }
        if (pinchStart && activePointers.size === 2) {
          var pts = Array.from(activePointers.values());
          var distance = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
          if (distance > 0) { zoom(pinchStart.width / distance); }
          return;
        }
        if (!state.dragging) { return; }
        var rect = viewport.getBoundingClientRect();
        state.x = state.origin.x - (event.clientX - state.startX) / rect.width * state.w;
        state.y = state.origin.y - (event.clientY - state.startY) / rect.height * state.h;
        applyViewBox();
      });
      var stopDrag = function (event) {
        if (event && event.pointerId !== undefined) { activePointers.delete(event.pointerId); }
        if (activePointers.size < 2) { pinchStart = null; }
        state.dragging = false; viewport.classList.remove("dragging");
      };
      viewport.addEventListener("pointerup", stopDrag);
      viewport.addEventListener("pointercancel", stopDrag);
      viewport.addEventListener("pointerleave", stopDrag);
      document.addEventListener("keydown", function (event) {
        if ((event.target && (event.target.tagName === "INPUT" || event.target.tagName === "SELECT"))) { return; }
        if (event.key === "+" || event.key === "=") { event.preventDefault(); zoom(0.85); }
        else if (event.key === "-") { event.preventDefault(); zoom(1.18); }
        else if (event.key === "0") { event.preventDefault(); resetView(); }
      });
    }
    var partFilter = document.getElementById("map-part-filter");
    var searchFilter = document.getElementById("map-search");
    var routeToggle = document.getElementById("map-route-toggle");
    function applyFilters() {
      var part = partFilter ? partFilter.value : "all";
      var query = searchFilter ? searchFilter.value.trim().toLowerCase() : "";
      mapPage.querySelectorAll(".map-node").forEach(function (node) {
        var nodePart = node.getAttribute("data-part") || "";
        var title = (node.getAttribute("data-title") || "").toLowerCase();
        var visible = (part === "all" || nodePart === part || node.classList.contains("part")) && (!query || title.indexOf(query) !== -1 || !node.classList.contains("chapter"));
        node.classList.toggle("dim", !visible);
      });
      mapPage.querySelectorAll(".map-edge").forEach(function (edge) {
        var edgePart = edge.getAttribute("data-part") || "";
        edge.classList.toggle("dim", part !== "all" && edgePart && edgePart !== part);
      });
    }
    if (partFilter) { partFilter.addEventListener("change", applyFilters); }
    if (searchFilter) { searchFilter.addEventListener("input", applyFilters); }
    if (routeToggle) {
      routeToggle.addEventListener("click", function () {
        var active = mapPage.classList.toggle("route-mode");
        routeToggle.setAttribute("aria-pressed", active ? "true" : "false");
      });
    }
    var mapModeButtons = document.querySelectorAll("[data-map-mode]");
    function setMapMode(mode) {
      mapPage.classList.toggle("list-mode", mode === "list");
      mapModeButtons.forEach(function (button) {
        button.setAttribute("aria-pressed", button.getAttribute("data-map-mode") === mode ? "true" : "false");
      });
      if (mode === "map" && svg) {
        // Контейнер снова видим — пересчитываем стартовый вид по ширине.
        window.requestAnimationFrame(function () { fitWidth(); });
      }
    }
    mapModeButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        var mode = button.getAttribute("data-map-mode") || "map";
        store.set("map-mode", mode);
        setMapMode(mode);
      });
    });
    // На телефоне по умолчанию показываем доступный списочный режим,
    // если пользователь ещё не выбрал «Карту» вручную.
    var savedMapMode = store.get("map-mode");
    if (savedMapMode === "map" || savedMapMode === "list") {
      setMapMode(savedMapMode);
    } else if (window.matchMedia("(max-width: 767px)").matches) {
      setMapMode("list");
    }
  }
})();