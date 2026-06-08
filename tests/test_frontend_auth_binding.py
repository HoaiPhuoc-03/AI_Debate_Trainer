import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_HTML = ROOT_DIR / "frontend" / "web.html"


def read_frontend():
    return FRONTEND_HTML.read_text(encoding="utf-8")


class FrontendAuthBindingTests(unittest.TestCase):
    def test_frontend_no_longer_hard_codes_demo_user_identity(self):
        html = read_frontend()

        self.assertNotIn("Minh Nguyen", html)
        self.assertNotIn("minh@debate.trainer", html)
        self.assertNotIn('value="password"', html)
        self.assertNotIn('userName: "Minh Nguyen"', html)

    def test_frontend_login_binds_to_backend_auth_session(self):
        html = read_frontend()

        self.assertIn("/api/v1/auth/login", html)
        self.assertIn("/api/v1/auth/me", html)
        self.assertIn("applyAuthSession(data", html)
        self.assertIn('const AUTH_TOKEN_KEY = "access_token"', html)
        self.assertIn("data?.access_token || data?.token", html)
        self.assertIn("sessionStorage.getItem(AUTH_TOKEN_KEY)", html)
        self.assertIn("const storage = persist ? localStorage : sessionStorage", html)
        self.assertIn("storage.setItem(AUTH_TOKEN_KEY, token)", html)
        self.assertIn("remember-login", html)
        self.assertIn("request.headers.Authorization", html)

    def test_frontend_logout_clears_auth_state_and_stored_token(self):
        html = read_frontend()

        self.assertIn("/api/v1/auth/logout", html)
        self.assertIn("clearAuthState()", html)
        self.assertIn("localStorage.removeItem(AUTH_TOKEN_KEY)", html)
        self.assertIn("sessionStorage.removeItem(AUTH_TOKEN_KEY)", html)
        self.assertIn("state.currentUser = null", html)

    def test_frontend_progress_uses_backend_current_user_data(self):
        html = read_frontend()

        self.assertIn("/api/v1/debate/progress/overview", html)
        self.assertIn("recent_topics", html)
        self.assertNotIn("const data = [", html)

    def test_frontend_requires_single_session_topic_input(self):
        html = read_frontend()

        self.assertIn("session-topic-input", html)
        self.assertIn("validateSessionTopic", html)
        self.assertIn("setSessionTopic", html)
        self.assertNotIn("topic-options", html)
        self.assertNotIn("const topics = [", html)
        self.assertNotIn("custom_topic:", html)

    def test_frontend_renders_topic_bank_controls(self):
        html = read_frontend()

        self.assertIn("const TOPIC_PAGE_SIZE = 9", html)
        self.assertIn('id="topic-search-input"', html)
        self.assertIn('id="topic-difficulty-filter"', html)
        self.assertIn('id="topic-category-strip"', html)
        self.assertIn('id="topic-grid"', html)
        self.assertIn('id="topic-load-more-row"', html)
        self.assertIn("loadDebateTopics()", html)
        self.assertIn("/api/v1/debate/topics?limit=100", html)
        self.assertIn("/api/v1/debate/topic-categories", html)

    def test_frontend_topic_bank_uses_recommended_tab_and_load_more(self):
        html = read_frontend()

        self.assertIn('topicMode: "recommended"', html)
        self.assertIn("topicVisibleCount: TOPIC_PAGE_SIZE", html)
        self.assertIn("Gợi ý cho bạn", html)
        self.assertIn("visibleTopics = topics.slice(0, visibleCount)", html)
        self.assertIn("function showMoreTopics()", html)
        self.assertIn("state.topicVisibleCount += TOPIC_PAGE_SIZE", html)
        self.assertIn("Xem thêm chủ đề", html)
        self.assertIn("Đang hiển thị", html)

    def test_frontend_topic_filters_reset_visible_count(self):
        html = read_frontend()

        self.assertIn("function resetTopicVisibleCount", html)
        self.assertIn("setTopicCategoryFilter(category)", html)
        self.assertIn("setTopicDifficultyFilter(difficulty)", html)
        self.assertIn("setTopicSearch(value)", html)
        self.assertIn("resetTopicVisibleCount();\n    renderTopicExplorer();", html)
        self.assertIn("resetTopicVisibleCount({ scroll: false });", html)

    def test_frontend_topic_selection_and_custom_override_are_wired(self):
        html = read_frontend()

        self.assertIn("function selectTopicCard(topicId)", html)
        self.assertIn("state.selectedTopicId = topic.id", html)
        self.assertIn("state.customTopic = normalizeTopicText(value)", html)
        self.assertIn("applySelectedTopicIfNoCustom()", html)
        self.assertIn("const selectedBankTopic = !state.customTopic && state.selectedTopicId", html)
        self.assertIn("sessionBody.topic_id = selectedBankTopic.id", html)
        self.assertIn("sessionBody.topic_category = selectedBankTopic.category", html)
        self.assertIn("sessionBody.topic_tags = Array.isArray(selectedBankTopic.tags)", html)

    def test_frontend_topic_bank_has_local_fallback(self):
        html = read_frontend()

        self.assertIn("const DEFAULT_TOPIC_BANK = [", html)
        self.assertIn("state.topicBankFallback = true", html)
        self.assertIn("Không tải được ngân hàng chủ đề, đang dùng danh sách mặc định.", html)

    def test_frontend_topic_cards_use_light_pastel_palette(self):
        html = read_frontend()

        self.assertIn("--topic-card-bg", html)
        self.assertIn("--topic-card-selected-bg", html)
        self.assertIn("--topic-title", html)
        self.assertIn("linear-gradient(135deg, #f8fbff 0%, #eef4ff 55%, #f6f1ff 100%)", html)
        self.assertIn("linear-gradient(135deg, #edf7ff 0%, #e9f2ff 45%, #f4efff 100%)", html)
        self.assertIn(".topic-category-badge", html)
        self.assertIn(".topic-difficulty-badge.basic", html)
        self.assertIn(".topic-difficulty-badge.intermediate", html)
        self.assertIn(".topic-difficulty-badge.advanced", html)
        self.assertIn("function topicDifficultyClass(difficulty)", html)
        self.assertNotIn("topic-card {\n    min-height: 210px;\n    padding: 18px;\n    display: grid;\n    gap: 12px;\n    align-content: start;\n    border-radius: 18px;\n    border: 1px solid rgba(148, 163, 184, 0.22);\n    background: rgba(15, 23, 42, 0.58);", html)

    def test_frontend_arena_includes_debate_topic_bar(self):
        html = read_frontend()

        self.assertIn('class="debate-topic-bar" id="debate-topic-bar"', html)
        self.assertIn('id="debate-topic-bar-title"', html)
        self.assertIn('id="debate-topic-bar-meta"', html)
        self.assertIn(".debate-topic-bar", html)
        self.assertIn(".debate-topic-bar__label", html)
        self.assertIn(".debate-topic-bar__title", html)
        self.assertIn(".debate-topic-bar__meta", html)
        self.assertIn(".debate-topic-badge", html)
        self.assertIn("function renderDebateTopicBar()", html)
        self.assertIn("function getPracticeDisplayTopic()", html)
        self.assertIn('getPracticeDisplayTopic() || "Chưa có chủ đề tranh biện"', html)
        self.assertIn('getPracticeDisplayTopic() || "Chưa có topic"', html)
        self.assertIn("renderDebateTopicBar();", html)

    def test_frontend_arena_includes_practice_mode_bar(self):
        html = read_frontend()

        self.assertIn('class="practice-mode-bar" id="practice-mode-bar"', html)
        self.assertIn('id="practice-mode-icon"', html)
        self.assertIn('id="practice-mode-title"', html)
        self.assertIn('id="practice-mode-description"', html)
        self.assertIn(".practice-mode-bar", html)
        self.assertIn(".practice-mode-icon", html)
        self.assertIn(".practice-mode-label", html)
        self.assertIn(".practice-mode-title", html)
        self.assertIn(".practice-mode-description", html)
        self.assertIn("const PRACTICE_MODE_DETAILS", html)
        self.assertIn("const PRACTICE_MODE_ALIASES", html)
        self.assertIn('claim_practice: "claim_writing"', html)
        self.assertIn('evidence_practice: "find_evidence"', html)
        self.assertIn('argument_builder: "full_argument"', html)
        self.assertIn('cer: "full_argument"', html)
        self.assertIn("function getActivePracticeMode()", html)
        self.assertIn("function normalizePracticeMode(value)", html)
        self.assertIn("function getPracticeModeConfig(value = getActivePracticeMode())", html)
        self.assertIn("function renderPracticeModeBar()", html)
        self.assertIn('setText("practice-mode-title", mode.title)', html)
        self.assertIn("renderPracticeModeBar();", html)

    def test_frontend_practice_round_flow_is_wired(self):
        html = read_frontend()

        self.assertIn("practice: {", html)
        self.assertIn("currentPrompt: null", html)
        self.assertIn("usedPracticePrompts: []", html)
        self.assertIn("usedPracticeTopics: []", html)
        self.assertIn("lastPracticePrompt: \"\"", html)
        self.assertIn("currentPromptType: null", html)
        self.assertIn("hasEvaluation: false", html)
        self.assertIn('id="practice-next-button"', html)
        self.assertIn("function initializePracticeRound", html)
        self.assertIn("function generatePracticePrompt", html)
        self.assertIn("/api/v1/debate/practice-prompt", html)
        self.assertIn("function handleNextPracticeRound", html)
        self.assertIn("function resetPracticeRoundUi()", html)
        self.assertIn('data-practice-next', html)
        self.assertIn("nextButton.addEventListener(\"click\", handleNextPracticeRound)", html)
        self.assertIn("state.practice.isGeneratingPrompt = true", html)
        self.assertIn("previous_prompts: state.practice.usedPracticePrompts", html)
        self.assertIn("previous_topics: state.practice.usedPracticeTopics", html)
        self.assertIn("session_id: state.sessionId", html)
        self.assertIn("category: state.selectedTopicCategory || null", html)
        self.assertIn("avoid_repeating: true", html)
        self.assertIn("function rememberPracticePrompt", html)
        self.assertIn("renderPracticeNextButton();", html)
        self.assertIn("body.practice_mode = state.practice.mode", html)
        self.assertIn("body.practice_prompt = state.practice.currentPrompt", html)
        self.assertIn("body.practice_topic = state.practice.currentTopic", html)
        self.assertIn("body.practice_round = state.practice.round", html)
        self.assertIn("ĐỀ BÀI CỦA LUMI", html)
        self.assertIn("CLAIM CẦN TÌM BẰNG CHỨNG", html)
        self.assertIn("LUẬN ĐIỂM YẾU CẦN PHẢN BIỆN", html)
        self.assertIn("CHỦ ĐỀ XÂY DỰNG LẬP LUẬN", html)
        self.assertIn("Tiếp theo →", html)
        self.assertIn(
            'const SINGLE_SKILL_PRACTICE_MODES = ["claim_writing", "find_evidence", "quick_rebuttal", "full_argument"]',
            html,
        )

        next_button_body = html.split("function renderPracticeNextButton()", 1)[1].split(
            "function bindPracticeRoundControls", 1
        )[0]
        self.assertIn("state.practice.hasEvaluation", next_button_body)
        self.assertIn("!state.practice.isAwaitingUserAnswer", next_button_body)

        reset_body = html.split("function resetPracticeRoundUi()", 1)[1].split(
            "async function initializePracticeRound", 1
        )[0]
        self.assertIn('input.value = ""', reset_body)
        self.assertIn('state.pendingVoiceTranscript = ""', reset_body)
        self.assertIn('state.voiceDraftState = "idle"', reset_body)
        self.assertIn("clearVoiceSourceAudio()", reset_body)
        self.assertIn("clearSpeechAudioCache()", reset_body)
        self.assertIn("renderCER(null)", reset_body)
        self.assertIn("renderFeedback(null)", reset_body)

    def test_quick_rebuttal_label_is_rendered_once_by_frontend(self):
        html = read_frontend()

        self.assertIn("function formatWeakArgumentText(text)", html)
        self.assertIn('label: "Lập luận yếu:"', html)
        self.assertIn('.replace(/^lập luận yếu\\s*:?\\s*/i, "")', html)
        render_body = html.split("function renderPracticePrompt(", 1)[1].split(
            "function renderPracticePromptLoading", 1
        )[0]
        self.assertIn(
            "formatWeakArgumentText(promptData.weak_argument || rawPrompt)",
            render_body,
        )
        self.assertIn("${escapeHtml(promptLabel)}", render_body)

    def test_frontend_arena_shows_user_and_lumi_stance_badges(self):
        html = read_frontend()

        self.assertIn('id="user-argument-panel"', html)
        self.assertIn('id="lumi-rebuttal-panel"', html)
        self.assertIn('id="user-stance-badge"', html)
        self.assertIn('id="lumi-stance-badge"', html)
        self.assertIn(".stance-badge--support", html)
        self.assertIn(".stance-badge--oppose", html)
        self.assertIn(".debate-card--support", html)
        self.assertIn(".debate-card--oppose", html)
        self.assertIn("function normalizeStance(value)", html)
        self.assertIn("function getOppositeStance(stance)", html)
        self.assertIn("function getStanceLabel(stance)", html)
        self.assertIn("function getStanceClass(stance)", html)
        self.assertIn("function renderArenaStanceBadges()", html)
        self.assertIn('const lumiStance = getOppositeStance(userStance)', html)
        self.assertIn('badge.textContent = `${owner} · ${getStanceLabel(stance)}`', html)

    def test_frontend_ends_session_from_arena(self):
        html = read_frontend()

        self.assertIn("Kết thúc phiên", html)
        self.assertIn("finishSession()", html)
        self.assertIn("/end", html)
        self.assertNotIn("Rời phiên", html)

    def test_frontend_defaults_to_blue_theme(self):
        html = read_frontend()

        self.assertIn('<body data-theme="blue-pastel">', html)
        self.assertIn('const DEFAULT_THEME = "blue-pastel";', html)
        self.assertIn("return DEFAULT_THEME;", html)

    def test_frontend_login_opens_post_login_navigation_hub(self):
        html = read_frontend()

        self.assertIn('id="view-home"', html)
        self.assertIn("Thiết lập hồ sơ", html)
        self.assertIn("Đấu trường tranh biện", html)
        self.assertIn("Xem tiến độ", html)
        self.assertIn('enterApp("account", "home")', html)
        self.assertIn('enterApp("guest", "home")', html)
        self.assertIn('goToArenaFromHub()', html)
        self.assertIn('goToSummaryFromHub()', html)

    def test_frontend_arena_uses_focus_mode(self):
        html = read_frontend()

        self.assertIn('body[data-view="arena"] .sidebar', html)
        self.assertIn('body[data-view="arena"] .topbar', html)
        self.assertIn('body[data-view="arena"] #view-arena', html)
        self.assertIn("syncArenaFocusMode(view)", html)
        self.assertIn("requestArenaFullscreen()", html)
        self.assertIn("exitArenaFullscreen()", html)

    def test_frontend_keeps_inline_voice_toolbar_on_text_arena(self):
        html = read_frontend()

        self.assertIn('id="voice-draft-bar"', html)
        self.assertIn('id="voice-draft-button" type="button" onclick="startVoiceDraft()"', html)
        self.assertIn('id="voice-retry-button" type="button" onclick="startVoiceDraft()"', html)
        self.assertIn('id="voice-draft-status"', html)
        self.assertIn("Nhập bằng giọng nói", html)
        self.assertIn("function renderArgumentControls()", html)
        self.assertIn("renderArgumentControls();", html)
        self.assertNotIn('id="mode-options"', html)
        self.assertNotIn("Cách nhập lập luận", html)

    def test_frontend_voice_profile_stays_on_text_arena_and_uses_rebuttal_tts(self):
        html = read_frontend()

        self.assertIn("function isVoiceInputMode()", html)
        self.assertIn("function syncInputModeDataset()", html)
        self.assertIn('document.body.dataset.inputMode = isVoiceInputMode() ? "voice" : "text"', html)
        self.assertIn('document.getElementById("voice-draft-bar")?.scrollIntoView', html)
        self.assertNotIn('id="voice-arena-panel"', html)
        self.assertNotIn('body[data-view="arena"][data-input-mode="voice"] .arena-layout', html)
        self.assertNotIn('Voice-only', html)
        self.assertIn('id="rebuttal-audio-box"', html)
        self.assertIn('id="rebuttal-audio-player" controls preload="metadata"', html)
        self.assertIn("/api/v1/speech/tts", html)
        self.assertIn('responseType: "blob"', html)
        self.assertIn("let speechAudioCache = { text: \"\", url: \"\" }", html)
        self.assertIn("function clearSpeechAudioCache()", html)
        self.assertIn("function getRebuttalSpeechUrl(text)", html)
        self.assertIn("function generateRebuttalAudio(text)", html)
        self.assertIn("speechAudioCache.text === clean", html)
        self.assertIn("Không tạo được âm thanh phản biện", html)
        self.assertIn(': (error.message || "Không tạo được âm thanh phản biện")', html)
        self.assertIn("await generateRebuttalAudio(turn.ai_rebuttal)", html)
        self.assertNotIn("window.speechSynthesis", html)

    def test_frontend_voice_input_uses_media_recorder_backend_stt_only(self):
        html = read_frontend()

        self.assertIn("function startVoiceDraft()", html)
        self.assertIn("function stopVoiceDraft()", html)
        self.assertIn("isListening: false", html)
        self.assertIn('voiceDraftState: "idle"', html)
        self.assertIn("let mediaRecorder = null", html)
        self.assertIn("let voiceChunks = []", html)
        self.assertIn("function getMediaRecorderMimeType()", html)
        self.assertIn("function transcribeSpeechBlob(blob)", html)
        self.assertIn("function applyVoiceTranscript(text)", html)
        self.assertNotIn('id="voice-live-transcript"', html)
        self.assertNotIn('id="voice-submit-btn"', html)
        self.assertNotIn('id="voice-source-audio"', html)
        self.assertNotIn('id="voice-source-player" controls preload="metadata"', html)
        self.assertIn("let voiceSourceAudio = { url: \"\", type: \"\", size: 0 }", html)
        self.assertIn("function saveVoiceSourceAudio(blob)", html)
        self.assertIn("saveVoiceSourceAudio(blob);", html)
        self.assertNotIn("Âm thanh gốc đã lưu", html)
        self.assertIn("pendingVoiceTranscript", html)
        self.assertIn("function renderVoiceTranscript()", html)
        self.assertIn("/api/v1/speech/stt?language=vi", html)
        self.assertIn("state.practice.currentTopic", html)
        self.assertIn("practice_topic=${encodeURIComponent(practiceTopic)}", html)
        self.assertIn("practice_stance=${encodeURIComponent(state.stance)}", html)
        self.assertIn('language: "vi"', html)
        self.assertIn("rawBody: blob", html)
        self.assertIn("new MediaRecorder(voiceStream", html)
        self.assertIn("navigator.mediaDevices?.getUserMedia", html)
        self.assertIn("!window.MediaRecorder", html)
        self.assertIn("await startMediaRecorderDraft();", html)
        self.assertIn("function getSpeechLanguage()", html)
        self.assertIn("state.isListening = true", html)
        self.assertIn("input.value = existing ? `${existing} ${clean}` : clean", html)
        self.assertIn("state.pendingVoiceTranscript = input.value.trim()", html)
        self.assertIn("Đã nhận diện giọng nói. Bạn có thể chỉnh sửa trước khi gửi.", html)
        self.assertIn("function submitPendingVoiceTranscript()", html)
        self.assertIn("updateCharCount();", html)
        self.assertNotIn("await submitArgument({ fromVoice: true })", html)
        self.assertIn("Trình duyệt không hỗ trợ MediaRecorder", html)
        self.assertIn("Không thể truy cập micro. Vui lòng kiểm tra quyền microphone.", html)
        self.assertNotIn("SpeechRecognition", html)
        self.assertNotIn("webkitSpeechRecognition", html)
        self.assertNotIn("startWebSpeechTurn", html)
        self.assertNotIn("voiceRecognition", html)

    def test_free_debate_timer_follows_turn_lifecycle_not_input_content(self):
        html = read_frontend()
        demo = (ROOT_DIR / "frontend" / "scripts" / "demoSession.js").read_text(encoding="utf-8")

        self.assertIn("const turnTimerState = {", html)
        self.assertIn('currentSpeaker: "user"', html)
        self.assertIn("function startUserTurnTimer({ reset = true } = {})", html)
        self.assertIn("function stopUserTurnTimer()", html)
        self.assertIn("function resetUserTurnTimer()", html)
        self.assertIn("startUserTurnTimer({ reset: !turnTimerState.timerStartedForTurn })", html)
        self.assertIn('turnTimerState.currentSpeaker = "ai"', html)
        self.assertIn("startUserTurnTimer({ reset: completedUserTurn })", html)
        self.assertIn('window.addEventListener("pagehide", stopUserTurnTimer)', html)
        self.assertIn("startUserTurnTimer({ reset: true })", demo)

        char_count_body = html.split("function updateCharCount()", 1)[1].split("function setLoading", 1)[0]
        voice_render_body = html.split("function renderVoiceTranscript()", 1)[1].split("function clearVoiceSourceAudio", 1)[0]
        self.assertNotIn("startUserTurnTimer", char_count_body)
        self.assertNotIn("resetUserTurnTimer", char_count_body)
        self.assertNotIn("initTurnTimer", char_count_body)
        self.assertNotIn("startUserTurnTimer", voice_render_body)
        self.assertNotIn("resetUserTurnTimer", voice_render_body)
        self.assertNotIn("initTurnTimer", voice_render_body)

    def test_practice_history_is_grouped_by_prompt_without_changing_free_debate(self):
        html = read_frontend()

        self.assertIn('currentGroupId: ""', html)
        self.assertIn("groups: []", html)
        self.assertIn("function registerPracticeGroup(promptData = {})", html)
        self.assertIn("function getCurrentPracticeGroup()", html)
        self.assertIn("function recordPracticeGroupError(group, userArgument, errorMessage)", html)
        self.assertIn('`${ui.label}:`', html)
        self.assertIn("turn.practice_group_id = practiceGroup.id", html)
        self.assertIn("turn.practice_group_title = practiceGroup.title", html)
        self.assertIn("recordPracticeGroupError(practiceGroup, argument, error.message)", html)
        self.assertIn('class="chat-topic-group chat-topic-group--${Number(group.colorIndex || 0) % 5}"', html)
        self.assertIn('data-practice-group-id="${escapeHtml(group.id)}"', html)
        self.assertIn("const groupTurns = state.history.filter(turn => turn.practice_group_id === group.id)", html)
        self.assertIn("if (!isGroupedPracticeMode())", html)
        self.assertIn("state.history.slice(-3)", html)

        transcript_body = html.split("function renderTranscript()", 1)[1].split("function renderSummary", 1)[0]
        self.assertIn("groups.map(group =>", transcript_body)
        self.assertIn("group.failedAttempts", transcript_body)
        self.assertNotIn("state.history.slice(-3).map(turn => `", transcript_body)

    def test_practice_history_group_styles_include_five_distinct_variants(self):
        html = read_frontend()

        self.assertIn(".chat-topic-group {", html)
        self.assertIn(".chat-topic-header {", html)
        self.assertIn(".chat-topic-badge {", html)
        self.assertIn(".chat-topic-body {", html)
        self.assertIn("max-height: 520px", html)
        self.assertIn("max-height: 420px", html)
        self.assertIn("max-height: 460px", html)
        self.assertIn("overflow-y: auto", html)
        self.assertIn("overscroll-behavior: contain", html)
        self.assertIn(".chat-topic-body::-webkit-scrollbar-thumb", html)
        self.assertIn('<div class="chat-topic-body">', html)
        for index in range(1, 5):
            self.assertIn(f".chat-topic-group--{index} {{", html)

    def test_frontend_includes_lumi_mascot_companion(self):
        html = read_frontend()

        self.assertIn("assets/lumi-paper-dragon-cutout.png", html)
        self.assertTrue((ROOT_DIR / "frontend" / "assets" / "lumi-paper-dragon-cutout.png").exists())
        self.assertIn('id="lumi-companion"', html)
        self.assertIn("LUMI_MESSAGES", html)
        self.assertIn("renderLumiCompanion()", html)
        self.assertIn("Phản biện của Lumi", html)
        self.assertIn("LUMI_GOOD_CER_THRESHOLD", html)
        self.assertIn("lumiThinking", html)
        self.assertIn("lumiVictory", html)
        self.assertIn("lumiAura", html)
        self.assertIn("lumiWingGlint", html)
        self.assertIn('class="lumi-title-token"', html)
        self.assertIn('body[data-lumi-state="thinking"] .lumi-title-token img', html)
        self.assertIn("prefers-reduced-motion: reduce", html)
        self.assertIn(".lumi-stage-token {\n    position: relative;", html)
        self.assertIn("display: block;\n    overflow: visible;", html)
        self.assertIn(".lumi-stage-token img {\n    position: absolute;", html)
        self.assertIn('syncLumiState("thinking")', html)

    def test_frontend_login_uses_generated_dragon_battle_background(self):
        html = read_frontend()

        self.assertIn('id="auth-home"', html)
        self.assertIn('url("assets/login-dragon-battle-bg.png") center / cover no-repeat', html)
        self.assertTrue((ROOT_DIR / "frontend" / "assets" / "login-dragon-battle-bg.png").exists())
        self.assertNotIn('class="login-dragon-scene"', html)
        self.assertNotIn('class="login-weapon login-sword"', html)
        self.assertNotIn("loginDragonFloat", html)
        self.assertIn("goToAuthView('login')", html)

    def test_frontend_loads_onboarding_tutorial_assets(self):
        html = read_frontend()

        self.assertIn('href="styles/onboarding.css"', html)
        self.assertIn('href="styles/tutorial.css"', html)
        self.assertIn('href="styles/tooltips.css"', html)
        self.assertIn('src="scripts/onboarding.js"', html)
        self.assertIn('src="scripts/tutorial.js"', html)
        self.assertIn('src="scripts/demoSession.js"', html)
        self.assertIn('src="components/knowledge/knowledgeHero.js"', html)

        for path in [
            "frontend/assets/mascot/dragon-clean.png",
            "frontend/assets/mascot/lightbulb.svg",
            "frontend/styles/onboarding.css",
            "frontend/styles/tutorial.css",
            "frontend/styles/tooltips.css",
            "frontend/scripts/onboarding.js",
            "frontend/scripts/tutorial.js",
            "frontend/scripts/demoSession.js",
            "frontend/components/knowledge/knowledgeHero.js",
            "frontend/components/onboarding/README.md",
            "frontend/components/tooltips/README.md",
            "frontend/components/tutorial/README.md",
            "frontend/components/knowledge/README.md",
            "frontend/components/demo/README.md",
        ]:
            self.assertTrue((ROOT_DIR / path).exists(), path)

    def test_onboarding_tutorial_assets_expose_required_features(self):
        onboarding = (ROOT_DIR / "frontend" / "scripts" / "onboarding.js").read_text(encoding="utf-8")
        tutorial = (ROOT_DIR / "frontend" / "scripts" / "tutorial.js").read_text(encoding="utf-8")
        demo = (ROOT_DIR / "frontend" / "scripts" / "demoSession.js").read_text(encoding="utf-8")
        knowledge_hero = (ROOT_DIR / "frontend" / "components" / "knowledge" / "knowledgeHero.js").read_text(encoding="utf-8")

        self.assertIn("ai_debate_trainer.onboarding.seen", onboarding)
        self.assertIn("Chào mừng đến với AI Debate Trainer", onboarding)
        self.assertIn("Xem phiên demo", onboarding)
        self.assertIn("Bắt đầu tranh biện", onboarding)
        self.assertIn("window.enterApp = function wrappedEnterApp", onboarding)

        self.assertIn("Kiến thức nền tảng để tranh biện", tutorial)
        self.assertIn("AIDebateKnowledgeHero?.render", tutorial)
        self.assertIn("Kiến thức nền tảng để tranh biện", knowledge_hero)
        self.assertIn("Nếu bạn là người chưa từng tranh biện, hãy đọc phần này cùng Lumi", knowledge_hero)
        self.assertIn("assets/mascot/dragon-clean.png", knowledge_hero)
        self.assertIn("assets/mascot/lightbulb.svg", knowledge_hero)
        self.assertIn("knowledge-mascot", knowledge_hero)
        self.assertIn("knowledge-copy", knowledge_hero)
        self.assertIn("knowledge-nudge", knowledge_hero)
        self.assertIn("function analyzeArgument", tutorial)
        self.assertIn("Strong reasoning detected.", tutorial)
        self.assertIn("CER_HELP", tutorial)
        self.assertIn("No debate sessions yet", tutorial)

        self.assertIn("chạy thử trên giao diện", demo)
        self.assertIn("Phát lại demo", demo)
        self.assertIn("Bắt đầu phiên thật", demo)
        self.assertIn("function simulateTurn", demo)
        self.assertIn("function ensureBackendDemoSession", demo)
        self.assertIn("function boostDemoCER", demo)
        self.assertIn("function applyDemoScoreBoost", demo)
        self.assertIn('/api/v1/debate/session', demo)
        self.assertIn("originalSubmitArgument", demo)
        self.assertIn("function startDemoVoiceDraft", demo)
        self.assertIn("VOICE_SAMPLE_TRANSCRIPT", demo)
        self.assertNotIn("function buildDemoRebuttal", demo)
        self.assertNotIn("function analyzeArgument", demo)
        self.assertNotIn("Replay demo", demo)
        self.assertNotIn("Start real session", demo)
        self.assertNotIn("frontend-only", demo)
        self.assertNotIn("claim: 78", demo)
        self.assertNotIn("evidence: 65", demo)
        self.assertNotIn("reasoning: 74", demo)


if __name__ == "__main__":
    unittest.main()
