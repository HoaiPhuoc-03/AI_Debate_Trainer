(function () {
  function render(total) {
    return `
      <div class="knowledge-carousel-progress" aria-hidden="true">
        <div class="knowledge-progress-track"><span class="knowledge-progress-fill"></span></div>
        <div class="knowledge-progress-dots">
          ${Array.from({ length: total }, (_, index) => `<button type="button" data-knowledge-dot="${index}" aria-label="Tới slide ${index + 1}"></button>`).join("")}
        </div>
      </div>
    `;
  }

  function update(root, index, total) {
    const fill = root.querySelector(".knowledge-progress-fill");
    if (fill) fill.style.width = `${((index + 1) / total) * 100}%`;
    root.querySelectorAll("[data-knowledge-dot]").forEach((dot, dotIndex) => {
      dot.classList.toggle("active", dotIndex === index);
      dot.setAttribute("aria-current", dotIndex === index ? "step" : "false");
    });
  }

  window.AIDebateKnowledgeProgress = {
    render,
    update,
  };
})();
