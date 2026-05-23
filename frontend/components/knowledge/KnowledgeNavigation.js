(function () {
  function render() {
    return `
      <div class="knowledge-carousel-nav" aria-label="Điều hướng bài học">
        <button class="secondary-btn knowledge-prev" type="button" data-knowledge-prev aria-label="Slide trước">← Trước</button>
        <div class="knowledge-slide-count" aria-live="polite"></div>
        <button class="primary-btn knowledge-next" type="button" data-knowledge-next aria-label="Slide tiếp theo">Tiếp theo →</button>
      </div>
    `;
  }

  function update(root, index, total) {
    const nav = root.querySelector(".knowledge-carousel-nav");
    const prev = nav?.querySelector("[data-knowledge-prev]");
    const next = nav?.querySelector("[data-knowledge-next]");
    const count = root.querySelector(".knowledge-slide-count");
    if (prev) prev.disabled = index === 0;
    if (next) next.textContent = index === total - 1 ? "Hoàn tất" : "Tiếp theo →";
    if (count) count.textContent = `Slide ${index + 1} / ${total}`;
  }

  window.AIDebateKnowledgeNavigation = {
    render,
    update,
  };
})();
