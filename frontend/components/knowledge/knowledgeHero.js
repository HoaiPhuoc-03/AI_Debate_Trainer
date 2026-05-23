(function () {
  // Previous framed source kept for asset coverage tests: assets/mascot/dragon-clean.png
  const DRAGON_SRC = "assets/mascot/lumi_flash.jfif";
  const LIGHTBULB_SRC = "assets/mascot/lightbulb.svg";

  function renderKnowledgeHero() {
    return `
      <article class="hub-row knowledge" data-knowledge-entry>
        <div class="knowledge-mascot" aria-hidden="true">
          <img src="${DRAGON_SRC}" alt="">
        </div>
        <div class="knowledge-copy">
          <div class="hub-label">Nền tảng</div>
          <h2 class="hub-title">Kiến thức nền tảng để tranh biện</h2>
          <p class="hub-copy">Học nhanh Claim, Evidence, Reasoning, lỗi thường gặp và cách phản biện Socratic trước khi vào phiên thật.</p>
          <div class="knowledge-nudge" role="note">
            <span class="knowledge-nudge-icon" aria-hidden="true"><img src="${LIGHTBULB_SRC}" alt=""></span>
            <span>Nếu bạn là người chưa từng tranh biện, hãy đọc phần này cùng Lumi</span>
          </div>
        </div>
        <div class="hub-side knowledge-actions">
          <button class="secondary-btn" type="button" onclick="window.AIDebateKnowledge?.open()"><span class="arrow-icon">→</span> Mở kiến thức</button>
          <button class="secondary-btn" type="button" onclick="window.AIDebateDemo?.start()"><span class="play-icon">▶</span> Xem demo</button>
        </div>
      </article>
    `;
  }

  window.AIDebateKnowledgeHero = {
    render: renderKnowledgeHero,
    dragonSrc: DRAGON_SRC,
    lightbulbSrc: LIGHTBULB_SRC,
  };
})();
