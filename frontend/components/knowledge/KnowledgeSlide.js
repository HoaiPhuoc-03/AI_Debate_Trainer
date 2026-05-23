(function () {
  const slides = [
    {
      id: "cer",
      icon: "CER",
      label: "Nền tảng CER",
      title: "CER là gì?",
      summary: "CER là cách xây dựng lập luận gồm Claim, Evidence và Reasoning.",
      example: "Trường học không nên cấm điện thoại hoàn toàn vì điện thoại có thể hỗ trợ học tập nếu dùng đúng cách.",
      takeaway: "Một lập luận tốt cần có ý chính, bằng chứng và phần giải thích logic.",
      keywords: ["Claim", "Evidence", "Reasoning"],
      visual: ["Claim", "Evidence", "Reasoning"],
      tabs: [
        {
          id: "claim",
          label: "Claim",
          title: "Claim - Luận điểm chính",
          description: "Claim là khẳng định chính bạn muốn bảo vệ. Nó cần rõ ràng và có thể tranh luận.",
          example: "Trường học không nên cấm điện thoại hoàn toàn.",
        },
        {
          id: "evidence",
          label: "Evidence",
          title: "Evidence - Bằng chứng hỗ trợ",
          description: "Evidence là ví dụ, số liệu, dẫn chứng hoặc tình huống thực tế giúp claim đáng tin hơn.",
          example: "Một số lớp dùng điện thoại để làm quiz nhanh và tra cứu tài liệu.",
        },
        {
          id: "reasoning",
          label: "Reasoning",
          title: "Reasoning - Liên kết logic",
          description: "Reasoning giải thích vì sao bằng chứng đó ủng hộ claim của bạn.",
          example: "Nếu điện thoại được dùng có kiểm soát, nó trở thành công cụ học thay vì chỉ gây xao nhãng.",
        },
      ],
    },
    {
      id: "argument-building",
      icon: "↗",
      label: "Xây dựng lập luận",
      title: "Cách dựng một lập luận",
      summary: "Một lượt tranh biện tốt nên đi theo trình tự rõ: nêu ý, chứng minh, giải thích và chốt lại.",
      example: "Tôi ủng hộ giới hạn điện thoại trong giờ học vì nó giúp lớp tập trung hơn.",
      takeaway: "Đừng nhảy thẳng tới kết luận. Hãy dẫn người nghe đi qua từng bước.",
      keywords: ["Luận điểm", "Bằng chứng", "Logic", "Kết luận"],
      visual: ["Nêu ý", "Chứng minh", "Giải thích", "Chốt lại"],
      tabs: [
        {
          id: "state-claim",
          label: "Nêu luận điểm",
          title: "Bắt đầu bằng một luận điểm rõ",
          description: "Cho người nghe biết chính xác bạn đang ủng hộ hoặc phản đối điều gì.",
          example: "Tôi cho rằng học sinh nên được dùng điện thoại khi giáo viên cho phép.",
        },
        {
          id: "add-evidence",
          label: "Đưa bằng chứng",
          title: "Thêm bằng chứng cụ thể",
          description: "Dùng ví dụ, số liệu hoặc tình huống thật để làm luận điểm đáng tin hơn.",
          example: "Trong giờ ngoại ngữ, điện thoại có thể dùng để tra từ và nghe phát âm.",
        },
        {
          id: "explain-why",
          label: "Giải thích vì sao",
          title: "Nối bằng chứng với luận điểm",
          description: "Giải thích vì sao bằng chứng vừa nêu thật sự ủng hộ điều bạn nói.",
          example: "Việc tra cứu ngay giúp học sinh hiểu bài tại chỗ thay vì chờ tới cuối buổi.",
        },
        {
          id: "conclude",
          label: "Kết luận lại",
          title: "Chốt lại tác động chính",
          description: "Kết thúc bằng một câu nhắc lại điểm mạnh nhất của lập luận.",
          example: "Vì vậy, quy định dùng có kiểm soát hợp lý hơn lệnh cấm hoàn toàn.",
        },
      ],
    },
    {
      id: "strong-cer",
      icon: "✓",
      label: "Ví dụ áp dụng",
      title: "Ví dụ CER tốt",
      summary: "Một CER tốt có claim cụ thể, bằng chứng rõ và reasoning giải thích tác động.",
      example: "Sinh viên năm nhất không nên làm thêm quá nhiều vì lịch học mới dễ khiến GPA giảm, từ đó làm nền tảng đại học yếu đi.",
      takeaway: "Đừng chỉ nói điều bạn tin. Hãy cho người nghe thấy đường đi của lập luận.",
      keywords: ["Cụ thể", "Có bằng chứng", "Có tác động"],
      visual: ["Claim", "Evidence", "Reasoning"],
      tabs: [
        {
          id: "good-claim",
          label: "Claim rõ",
          title: "Claim tốt phải có phạm vi",
          description: "Một claim tốt không quá chung và cho biết rõ đối tượng, tình huống hoặc điều kiện.",
          example: "Sinh viên năm nhất không nên làm thêm quá 20 giờ mỗi tuần.",
        },
        {
          id: "good-evidence",
          label: "Evidence cụ thể",
          title: "Evidence tốt làm claim đáng tin",
          description: "Bằng chứng nên là ví dụ cụ thể, số liệu hoặc tình huống người nghe dễ kiểm chứng.",
          example: "Lịch học đại học thay đổi nhiều khiến sinh viên cần thêm thời gian tự học.",
        },
        {
          id: "good-reasoning",
          label: "Reasoning chặt",
          title: "Reasoning giải thích tác động",
          description: "Phần reasoning cho thấy vì sao evidence dẫn tới kết luận của bạn.",
          example: "Khi thời gian tự học bị giảm, sinh viên khó theo kịp môn nền tảng.",
        },
      ],
    },
    {
      id: "weak-cer",
      icon: "!",
      label: "Ví dụ đối chiếu",
      title: "Ví dụ CER yếu",
      summary: "CER yếu thường chỉ là cảm nhận cá nhân, thiếu evidence và thiếu cầu nối logic.",
      example: "Đi làm thêm năm nhất là xấu vì mình thấy vậy.",
      takeaway: "Ý kiến chưa phải lập luận. Hãy thêm ví dụ và giải thích nguyên nhân.",
      keywords: ["Thiếu ví dụ", "Thiếu WHY", "Quá chung"],
      visual: ["Opinion", "?", "Conclusion"],
      tabs: [
        {
          id: "too-vague",
          label: "Quá chung",
          title: "Luận điểm quá rộng",
          description: "Câu nói quá rộng làm người nghe khó biết bạn đang bảo vệ điều gì.",
          example: "Điện thoại trong trường học là xấu.",
        },
        {
          id: "no-evidence",
          label: "Thiếu bằng chứng",
          title: "Chỉ nêu ý kiến cá nhân",
          description: "Nếu không có ví dụ hoặc dữ liệu, lập luận dễ giống cảm nhận hơn là tranh biện.",
          example: "Tôi thấy học sinh dùng điện thoại là không tốt.",
        },
        {
          id: "missing-why",
          label: "Thiếu WHY",
          title: "Chưa giải thích nguyên nhân",
          description: "Bạn cần nói vì sao bằng chứng đó dẫn tới kết luận.",
          example: "Điện thoại gây mất tập trung, nhưng chưa giải thích mất tập trung ảnh hưởng kết quả học thế nào.",
        },
      ],
    },
    {
      id: "rebuttal-techniques",
      icon: "?",
      label: "Kỹ thuật phản biện",
      title: "Phản biện có chiến lược",
      summary: "Phản biện mạnh không chỉ nói ngược lại, mà kiểm tra giả định, bằng chứng và hệ quả.",
      example: "Bạn nói cấm điện thoại giúp tập trung. Nhưng vấn đề có thể là cách dùng, không phải bản thân thiết bị.",
      takeaway: "Hãy phản biện vào điểm yếu cụ thể, không phản biện lan man.",
      keywords: ["Giả định", "Bằng chứng", "Hệ quả", "Phản ví dụ"],
      visual: ["Hỏi", "Kiểm tra", "Phản ví dụ"],
      tabs: [
        {
          id: "assumption",
          label: "Hỏi giả định",
          title: "Hỏi lại giả định",
          description: "Tìm điều đối phương đang ngầm cho là đúng nhưng chưa chứng minh.",
          example: "Bạn đang giả định mọi học sinh đều dùng điện thoại sai mục đích, đúng không?",
        },
        {
          id: "evidence-check",
          label: "Kiểm tra bằng chứng",
          title: "Kiểm tra chất lượng bằng chứng",
          description: "Hỏi bằng chứng đó có đủ cụ thể, đáng tin và liên quan tới claim không.",
          example: "Số liệu đó đến từ trường nào và có áp dụng cho học sinh cấp ba không?",
        },
        {
          id: "consequence",
          label: "Chỉ ra hệ quả",
          title: "Chỉ ra hệ quả của đề xuất",
          description: "Đánh giá điều gì sẽ xảy ra nếu ý kiến đối phương được áp dụng.",
          example: "Nếu cấm hoàn toàn, học sinh cũng mất công cụ tra cứu nhanh trong giờ học.",
        },
        {
          id: "counterexample",
          label: "Đưa phản ví dụ",
          title: "Dùng phản ví dụ để làm yếu claim",
          description: "Một phản ví dụ tốt cho thấy claim của đối phương không đúng trong mọi trường hợp.",
          example: "Có lớp dùng điện thoại để làm bài kiểm tra nhanh và vẫn giữ được trật tự.",
        },
      ],
    },
    {
      id: "fallacies",
      icon: "⚖",
      label: "Tư duy phản biện",
      title: "Lỗi ngụy biện logic",
      summary: "Ngụy biện làm lập luận nghe có vẻ mạnh nhưng nền logic lại yếu.",
      example: "Tấn công cá nhân: Bác bỏ người nói thay vì bác bỏ luận điểm của họ.",
      takeaway: "Hãy phản biện vào ý, bằng chứng và giả định, không phản biện vào con người.",
      keywords: ["Người rơm", "Cá nhân", "Trượt dốc"],
      visual: ["Claim", "Bias", "Check"],
      tabs: [
        {
          id: "strawman",
          label: "Người rơm",
          title: "Ngụy biện người rơm",
          description: "Bóp méo hoặc làm yếu luận điểm của đối phương rồi phản bác phiên bản bị bóp méo đó.",
          example: "A nói nên giới hạn điện thoại trong giờ học. B đáp: Bạn muốn học sinh không bao giờ được dùng công nghệ.",
        },
        {
          id: "ad-hominem",
          label: "Công kích cá nhân",
          title: "Công kích cá nhân",
          description: "Bác bỏ người nói bằng đặc điểm cá nhân thay vì phản biện trực tiếp luận điểm.",
          example: "Ý kiến của bạn sai vì bạn còn nhỏ, chưa đủ kinh nghiệm để nói về giáo dục.",
        },
        {
          id: "slippery-slope",
          label: "Trượt dốc",
          title: "Ngụy biện trượt dốc",
          description: "Cho rằng một hành động nhỏ chắc chắn kéo theo chuỗi hậu quả cực đoan mà không chứng minh liên kết.",
          example: "Nếu cho học sinh dùng điện thoại để tra cứu, rồi các em sẽ nghiện mạng xã hội và bỏ học hết.",
        },
        {
          id: "false-dilemma",
          label: "Lưỡng phân sai",
          title: "Lưỡng phân sai",
          description: "Ép vấn đề thành hai lựa chọn cực đoan dù vẫn còn lựa chọn trung gian.",
          example: "Hoặc cấm điện thoại hoàn toàn, hoặc để lớp học hỗn loạn.",
        },
        {
          id: "appeal-emotion",
          label: "Kêu gọi cảm xúc",
          title: "Kêu gọi cảm xúc",
          description: "Dùng cảm xúc mạnh để thay thế bằng chứng hoặc lập luận logic.",
          example: "Nếu bạn không ủng hộ cấm điện thoại, bạn không quan tâm đến tương lai học sinh.",
        },
        {
          id: "bandwagon",
          label: "Số đông",
          title: "Dựa vào số đông",
          description: "Cho rằng điều gì đúng chỉ vì nhiều người tin hoặc làm theo.",
          example: "Nhiều trường cấm điện thoại nên chắc chắn đó là cách đúng nhất.",
        },
      ],
    },
    {
      id: "speaking-improvement",
      icon: "✦",
      label: "Cải thiện bài nói",
      title: "Nói rõ và thuyết phục hơn",
      summary: "Một bài nói tốt cần gọn, cụ thể và có đường dây logic dễ theo dõi.",
      example: "Tôi phản đối cấm hoàn toàn vì giải pháp này bỏ qua các cách dùng điện thoại có ích cho học tập.",
      takeaway: "Người nghe dễ bị thuyết phục khi bạn nói rõ, có ví dụ và không lan man.",
      keywords: ["Rõ", "Cụ thể", "Logic", "Gọn"],
      visual: ["Focus", "Support", "Connect"],
      tabs: [
        {
          id: "clear-claim",
          label: "Rõ luận điểm",
          title: "Nói rõ bạn đang bảo vệ điều gì",
          description: "Mở đầu bằng một câu claim trực tiếp để người nghe không phải đoán ý.",
          example: "Tôi ủng hộ dùng điện thoại có kiểm soát trong lớp học.",
        },
        {
          id: "specific-evidence",
          label: "Cụ thể bằng chứng",
          title: "Bằng chứng càng cụ thể càng tốt",
          description: "Tránh nói chung chung. Hãy dùng tình huống, con số hoặc ví dụ dễ hình dung.",
          example: "Trong 10 phút quiz, học sinh dùng điện thoại để trả lời và giáo viên thấy ngay phần chưa hiểu.",
        },
        {
          id: "logic-link",
          label: "Liên kết logic",
          title: "Nối ví dụ với kết luận",
          description: "Sau khi nêu ví dụ, hãy giải thích ví dụ đó chứng minh điều gì.",
          example: "Vì giáo viên thấy kết quả ngay, họ có thể điều chỉnh bài giảng kịp thời.",
        },
        {
          id: "avoid-rambling",
          label: "Tránh lan man",
          title: "Giữ một trọng tâm mỗi lượt",
          description: "Một lượt tranh biện nên tập trung vào một ý chính thay vì gom quá nhiều ý nhỏ.",
          example: "Lượt này chỉ nói về lợi ích học tập, không chuyển sang chuyện giải trí hay mạng xã hội.",
        },
      ],
    },
    {
      id: "score-guide",
      icon: "★",
      label: "Đánh giá điểm",
      title: "Hiểu điểm CER",
      summary: "Điểm CER giúp bạn biết phần nào của lập luận đang mạnh và phần nào cần luyện thêm.",
      example: "Claim cao nhưng Evidence thấp nghĩa là bạn có ý rõ, nhưng thiếu dẫn chứng hỗ trợ.",
      takeaway: "Muốn điểm cao, hãy làm rõ claim, thêm evidence và giải thích reasoning.",
      keywords: ["Claim score", "Evidence score", "Reasoning score", "Total score"],
      visual: ["Claim", "Evidence", "Reasoning", "Total"],
      tabs: [
        {
          id: "claim-score",
          label: "Claim score",
          title: "Claim score",
          description: "Điểm claim cao khi luận điểm rõ, nhất quán và bám đúng chủ đề.",
          example: "Nói: Tôi phản đối cấm hoàn toàn điện thoại trong giờ học, thay vì Điện thoại có nhiều vấn đề.",
        },
        {
          id: "evidence-score",
          label: "Evidence score",
          title: "Evidence score",
          description: "Điểm evidence cao khi bạn đưa ví dụ, dữ liệu hoặc dẫn chứng cụ thể.",
          example: "Nêu một tình huống lớp học dùng điện thoại để quiz hoặc tra cứu tài liệu.",
        },
        {
          id: "reasoning-score",
          label: "Reasoning score",
          title: "Reasoning score",
          description: "Điểm reasoning cao khi bạn giải thích rõ vì sao evidence dẫn tới kết luận.",
          example: "Giải thích rằng quiz nhanh giúp giáo viên phát hiện lỗ hổng kiến thức ngay trong lớp.",
        },
        {
          id: "total-score",
          label: "Total score",
          title: "Total score",
          description: "Total score là mức cân bằng tổng thể giữa claim, evidence và reasoning.",
          example: "Một lượt có claim rõ, ví dụ cụ thể và giải thích logic thường có điểm tổng cao hơn.",
        },
      ],
    },
    {
      id: "practice-guardrails",
      icon: "×",
      label: "Luyện tập",
      title: "Các lỗi thường gặp",
      summary: "Các lỗi phổ biến làm lượt tranh biện yếu dù ý tưởng ban đầu không tệ.",
      example: "Nói quá rộng, nhảy thẳng tới kết luận, hoặc không phản hồi trực tiếp luận điểm đối phương.",
      takeaway: "Mỗi lượt nên có một claim chính, một evidence rõ và một reasoning đủ chặt.",
      keywords: ["Quá rộng", "Nhảy kết luận", "Lạc ý"],
      visual: ["Focus", "Support", "Connect"],
      tabs: [
        {
          id: "broad",
          label: "Quá rộng",
          title: "Nói quá rộng",
          description: "Ý quá rộng khiến bạn khó chứng minh trong một lượt ngắn.",
          example: "Công nghệ luôn làm học sinh học kém.",
        },
        {
          id: "jump",
          label: "Nhảy kết luận",
          title: "Nhảy thẳng tới kết luận",
          description: "Bạn đưa kết luận nhưng chưa cho người nghe thấy bằng chứng và logic phía sau.",
          example: "Vì vậy phải cấm điện thoại, nhưng chưa chứng minh cấm tốt hơn quản lý có điều kiện.",
        },
        {
          id: "off-topic",
          label: "Lạc ý",
          title: "Không phản hồi trực tiếp",
          description: "Bạn nói một ý đúng nhưng không trả lời luận điểm chính của đối phương.",
          example: "Đối phương nói về tập trung trong lớp, bạn lại chuyển sang giá điện thoại.",
        },
      ],
    },
  ];

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderKeywords(slide) {
    return slide.keywords.map((keyword) => `<span>${escapeHtml(keyword)}</span>`).join("");
  }

  function renderVisual(items) {
    return `
      <div class="knowledge-slide-visual" aria-hidden="true">
        ${items.map((item, index) => `
          <span class="knowledge-visual-node">${escapeHtml(item)}</span>
          ${index < items.length - 1 ? '<span class="knowledge-visual-line"></span>' : ""}
        `).join("")}
      </div>
    `;
  }

  function renderInteractiveTabs(slide) {
    if (!slide.tabs?.length) {
      return `<div class="knowledge-keywords" aria-label="Từ khóa">${renderKeywords(slide)}</div>`;
    }
    return `
      <div class="knowledge-tabs" aria-label="Chọn khái niệm trong slide">
        ${slide.tabs.map((item, index) => `
          <button class="${index === 0 ? "active" : ""}" type="button" data-knowledge-tab="${escapeHtml(item.id)}" aria-controls="tab-panel-${escapeHtml(slide.id)}-${escapeHtml(item.id)}" aria-pressed="${index === 0 ? "true" : "false"}">
            ${escapeHtml(item.label)}
          </button>
        `).join("")}
      </div>
      <div class="knowledge-tab-details" aria-live="polite">
        ${slide.tabs.map((item, index) => `
          <div class="knowledge-tab-panel ${index === 0 ? "active" : ""}" id="tab-panel-${escapeHtml(slide.id)}-${escapeHtml(item.id)}" data-knowledge-tab-panel="${escapeHtml(item.id)}" ${index === 0 ? "" : "hidden"}>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.description)}</p>
            <div class="knowledge-tab-example">
              <span>Ví dụ</span>
              <em>${escapeHtml(item.example)}</em>
            </div>
          </div>
        `).join("")}
      </div>
    `;
  }

  function renderSlide(slide, index, total) {
    return `
      <article class="knowledge-slide ${slide.tabs?.length ? "has-tabs" : ""}" role="group" aria-roledescription="slide" aria-label="${index + 1} / ${total}" data-slide-id="${escapeHtml(slide.id)}">
        <div class="knowledge-slide-icon" aria-hidden="true">${escapeHtml(slide.icon)}</div>
        <div class="knowledge-slide-content">
          <div class="knowledge-slide-label">${escapeHtml(slide.label)}</div>
          <h3>${escapeHtml(slide.title)}</h3>
          <p class="knowledge-slide-summary">${escapeHtml(slide.summary)}</p>
          ${renderVisual(slide.visual)}
          <div class="knowledge-example">
            <span>Ví dụ</span>
            <strong>${escapeHtml(slide.example)}</strong>
          </div>
          <div class="knowledge-takeaway">
            <span aria-hidden="true">💡</span>
            <div>
              <small>Key takeaway</small>
              <strong>${escapeHtml(slide.takeaway)}</strong>
            </div>
          </div>
          ${renderInteractiveTabs(slide)}
        </div>
      </article>
    `;
  }

  window.AIDebateKnowledgeSlides = {
    slides,
    renderSlide,
    renderInteractiveTabs,
  };
})();
