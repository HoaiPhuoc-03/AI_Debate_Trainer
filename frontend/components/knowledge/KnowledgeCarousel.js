(function () {
  const STORAGE_KEY = "ai_debate_trainer.knowledge.lastSlide";
  const swipeThreshold = 42;
  const state = {
    root: null,
    index: 0,
    startX: 0,
    currentX: 0,
    dragging: false,
  };

  function getSlides() {
    return window.AIDebateKnowledgeSlides?.slides || [];
  }

  function getSavedIndex(total) {
    const saved = Number(localStorage.getItem(STORAGE_KEY));
    return Number.isFinite(saved) ? Math.min(Math.max(saved, 0), total - 1) : 0;
  }

  function render() {
    const slides = getSlides();
    const total = slides.length;
    return `
      <section class="knowledge-carousel" data-knowledge-carousel tabindex="0" aria-label="Bài học kiến thức tranh biện">
        ${window.AIDebateKnowledgeProgress.render(total)}
        <div class="knowledge-carousel-stage">
          <button class="knowledge-side-arrow knowledge-side-prev" type="button" data-knowledge-prev aria-label="Slide trước">←</button>
          <div class="knowledge-carousel-viewport" data-knowledge-viewport>
            <div class="knowledge-carousel-track" data-knowledge-track>
              ${slides.map((slide, index) => window.AIDebateKnowledgeSlides.renderSlide(slide, index, total)).join("")}
            </div>
          </div>
          <button class="knowledge-side-arrow knowledge-side-next" type="button" data-knowledge-next aria-label="Slide tiếp theo">→</button>
        </div>
        <div class="knowledge-checkpoint">
          <span aria-hidden="true">✓</span>
          <strong>Bạn đã hiểu?</strong>
          <small>Dùng mũi tên, kéo chuột hoặc swipe để học tiếp từng bước.</small>
        </div>
        ${window.AIDebateKnowledgeNavigation.render()}
      </section>
    `;
  }

  function update() {
    if (!state.root) return;
    const slides = getSlides();
    const total = slides.length;
    const track = state.root.querySelector("[data-knowledge-track]");
    if (track) {
      track.style.transform = `translate3d(${-state.index * 100}%, 0, 0)`;
    }
    window.AIDebateKnowledgeProgress.update(state.root, state.index, total);
    window.AIDebateKnowledgeNavigation.update(state.root, state.index, total);
    state.root.querySelectorAll(".knowledge-side-prev").forEach((button) => {
      button.disabled = state.index === 0;
    });
    state.root.querySelectorAll(".knowledge-side-next").forEach((button) => {
      button.disabled = state.index === total - 1;
      button.textContent = "→";
    });
    state.root.querySelectorAll(".knowledge-slide").forEach((slide, index) => {
      slide.classList.toggle("active", index === state.index);
      slide.setAttribute("aria-hidden", index === state.index ? "false" : "true");
    });
    localStorage.setItem(STORAGE_KEY, String(state.index));
  }

  function resetTabsForActiveSlide() {
    if (!state.root) return;
    const activeSlide = state.root.querySelector(".knowledge-slide.active");
    const firstTab = activeSlide?.querySelector("[data-knowledge-tab]");
    if (firstTab) selectKnowledgeTab(firstTab);
  }

  function goTo(index) {
    const total = getSlides().length;
    const previous = state.index;
    state.index = Math.min(Math.max(index, 0), total - 1);
    update();
    if (state.index !== previous) resetTabsForActiveSlide();
  }

  function next() {
    const total = getSlides().length;
    if (state.index >= total - 1) {
      window.AIDebateKnowledge?.close?.();
      return;
    }
    goTo(state.index + 1);
  }

  function prev() {
    goTo(state.index - 1);
  }

  function onPointerDown(event) {
    if (event.target.closest("[data-knowledge-tab]")) return;
    const viewport = event.target.closest("[data-knowledge-viewport]");
    if (!viewport) return;
    state.dragging = true;
    state.startX = event.clientX;
    state.currentX = event.clientX;
    viewport.setPointerCapture?.(event.pointerId);
    state.root.classList.add("is-dragging");
  }

  function onPointerMove(event) {
    if (!state.dragging) return;
    state.currentX = event.clientX;
  }

  function onPointerUp(event) {
    const tabButton = event.target.closest?.("[data-knowledge-tab]");
    if (tabButton) {
      selectKnowledgeTab(tabButton);
      return;
    }
    if (!state.dragging) return;
    const delta = state.currentX - state.startX;
    state.dragging = false;
    state.root.classList.remove("is-dragging");
    if (Math.abs(delta) < swipeThreshold) return;
    if (delta < 0) next();
    else prev();
  }

  function onKeydown(event) {
    if (event.key === "ArrowRight") {
      event.preventDefault();
      next();
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      prev();
    } else if (event.key === "Home") {
      event.preventDefault();
      goTo(0);
    } else if (event.key === "End") {
      event.preventDefault();
      goTo(getSlides().length - 1);
    }
  }

  function selectKnowledgeTab(button) {
    const slide = button.closest(".knowledge-slide");
    if (!slide) return;
    const target = button.dataset.knowledgeTab;
    slide.querySelectorAll("[data-knowledge-tab]").forEach((item) => {
      const isActive = item === button;
      item.classList.toggle("active", isActive);
      item.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
    slide.querySelectorAll("[data-knowledge-tab-panel]").forEach((panel) => {
      const isActive = panel.dataset.knowledgeTabPanel === target;
      panel.classList.toggle("active", isActive);
      panel.hidden = !isActive;
    });
  }

  function mount(container) {
    const root = container?.querySelector?.("[data-knowledge-carousel]") || container;
    if (!root || root.__knowledgeCarouselMounted) {
      if (root) {
        state.root = root;
        update();
      }
      return;
    }
    state.root = root;
    state.index = getSavedIndex(getSlides().length);
    root.__knowledgeCarouselMounted = true;
    root.addEventListener("click", (event) => {
      const tabButton = event.target.closest("[data-knowledge-tab]");
      if (tabButton) {
        event.preventDefault();
        selectKnowledgeTab(tabButton);
        return;
      }
      const dot = event.target.closest("[data-knowledge-dot]");
      if (dot) {
        goTo(Number(dot.dataset.knowledgeDot));
        return;
      }
      if (event.target.closest("[data-knowledge-prev]")) {
        prev();
        return;
      }
      if (event.target.closest("[data-knowledge-next]")) {
        next();
      }
    });
    root.addEventListener("keydown", onKeydown);
    root.addEventListener("pointerdown", onPointerDown);
    root.addEventListener("pointermove", onPointerMove);
    root.addEventListener("pointerup", onPointerUp);
    root.addEventListener("pointercancel", onPointerUp);
    update();
    resetTabsForActiveSlide();
  }

  window.AIDebateKnowledgeCarousel = {
    render,
    mount,
    goTo,
    next,
    prev,
    reset() {
      localStorage.removeItem(STORAGE_KEY);
      goTo(0);
    },
    get activeIndex() {
      return state.index;
    },
  };
})();
