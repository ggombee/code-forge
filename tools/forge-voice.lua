-- forge-voice.lua — code-forge 음성 입력 Hammerspoon hook
--
-- ⌘ + Shift + Space   : 토글 (한 번 누르면 녹음 시작, 다시 누르면 종료 + paste)
-- ⌘ + Shift + .       : silence detection 모드 (말 멈추면 자동 종료)
-- ⌘ + Shift + ,       : 상태 확인 (idle / recording)
-- ⌘ + Shift + K       : /clear + 킥오프 붙여넣기 (handoff 자동화 — /handoff가 클립보드에 복사한 프롬프트)
--
-- 설치: ~/.hammerspoon/init.lua 에 다음 1줄 추가:
--   dofile(os.getenv("HOME") .. "/.local/share/forge-voice/forge-voice.lua")
--
-- 또는 본 파일 내용을 init.lua 에 직접 복사.

local function forgeVoice(cmd)
  -- script 위치 — 셋업 시 ~/.local/bin 에 심볼릭 링크 권장
  local scriptCandidates = {
    os.getenv("HOME") .. "/.local/bin/forge-voice.sh",
    os.getenv("HOME") .. "/.local/share/forge-voice/forge-voice.sh",
  }
  local script = nil
  for _, p in ipairs(scriptCandidates) do
    local f = io.open(p, "r")
    if f then f:close(); script = p; break end
  end
  if not script then
    hs.alert.show("❌ forge-voice.sh 없음 — /voice setup 실행")
    return
  end
  -- 백그라운드 실행 (UI block 방지)
  hs.execute("'" .. script .. "' " .. cmd .. " &", true)
end

-- 토글 모드 — 가장 자주 쓰는 진입점
hs.hotkey.bind({"cmd", "shift"}, "space", function()
  forgeVoice("toggle")
end)

-- silence detection — 짧은 발화에 편함
hs.hotkey.bind({"cmd", "shift"}, ".", function()
  forgeVoice("once")
end)

-- 상태 확인
hs.hotkey.bind({"cmd", "shift"}, ",", function()
  local out, _, _, _ = hs.execute("'" .. (os.getenv("HOME") .. "/.local/bin/forge-voice.sh") .. "' status", true)
  hs.alert.show("Forge Voice: " .. (out or "?"))
end)

-- /clear + 킥오프 붙여넣기 (handoff 자동화)
-- /handoff 스킬이 킥오프 프롬프트를 클립보드에 복사한 뒤 안내하는 "/clear 입력 → ⌘V" 수동 2단계를
-- 단축키 하나로. /clear는 모델이 대신 실행 불가(사용자 전용)라 hook이 아닌 키 입력으로 자동화.
hs.hotkey.bind({"cmd", "shift"}, "k", function()
  hs.eventtap.keyStrokes("/clear")
  hs.eventtap.keyStroke({}, "return")
  -- /clear 처리 후 입력창이 비워질 시간을 준 뒤 클립보드(킥오프) 붙여넣기 + 제출
  hs.timer.doAfter(0.8, function()
    hs.eventtap.keyStroke({"cmd"}, "v")
    hs.timer.doAfter(0.2, function() hs.eventtap.keyStroke({}, "return") end)
  end)
  hs.alert.show("🧹 /clear + 킥오프 붙여넣기")
end)

hs.alert.show("🎙️ Forge Voice loaded — ⌘⇧Space · ⌘⇧K=clear+paste")
