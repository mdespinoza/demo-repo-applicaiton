/* ========================================================
   HIDDEN SNAKE GAME — Easter egg
   Trigger: Ctrl+Shift+G  OR  type "snake"
   ======================================================== */
(function () {
  "use strict";

  /* ---------- Activation Sequence ---------- */
  const CODE = "snake";
  let buffer = "";

  /* ---------- Game Constants ---------- */
  const CELL = 20;
  const COLS = 28;
  const ROWS = 22;
  const W = COLS * CELL;
  const H = ROWS * CELL;
  const TICK_MS = 90;

  /* ---------- Neon Palette ---------- */
  const PAL = {
    bg: "#0a0a1a",
    grid: "rgba(0, 255, 170, 0.08)",
    gridLine: "rgba(0, 255, 170, 0.18)",
    snakeHead: "#00ffaa",
    snakeBody: "#00cc88",
    snakeGlow: "rgba(0, 255, 170, 0.6)",
    food: "#ff2d7b",
    foodGlow: "rgba(255, 45, 123, 0.7)",
    foodAlt: "#ffd700",
    foodAltGlow: "rgba(255, 215, 0, 0.7)",
    text: "#00ffaa",
    textSub: "rgba(0, 255, 170, 0.5)",
    border: "rgba(0, 255, 170, 0.15)",
    overlay: "rgba(5, 5, 20, 0.92)",
    scanline: "rgba(0, 0, 0, 0.08)",
    particle: "#00ffaa",
  };

  /* ---------- State ---------- */
  let overlay, canvas, ctx, scoreEl, highEl, closeBtn, gameWrapper;
  let snake, dir, nextDir, food, score, highScore, alive, running, loopId;
  let particles = [];
  let foodPulse = 0;
  let frameCount = 0;

  /* ---------- Keyboard Listener (activation) ---------- */
  document.addEventListener("keydown", function (e) {
    /* Ctrl+Shift+G (or Cmd+Shift+G on Mac) — primary hotkey */
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "g") {
      e.preventDefault();
      toggle();
      return;
    }

    /* Don't capture when typing in inputs */
    const tag = e.target.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
    if (e.target.isContentEditable) return;

    /* Build activation buffer (typing "snake" still works) */
    buffer += e.key.toLowerCase();
    if (buffer.length > CODE.length) buffer = buffer.slice(-CODE.length);
    if (buffer === CODE) {
      buffer = "";
      toggle();
    }
  });

  /* ---------- Build DOM ---------- */
  function buildUI() {
    if (overlay) return;

    overlay = document.createElement("div");
    overlay.id = "snake-overlay";
    overlay.innerHTML = `
      <div class="snake-modal">
        <div class="snake-header">
          <div class="snake-title-area">
            <span class="snake-icon">&#127909;</span>
            <span class="snake-title">SNAKE</span>
            <span class="snake-version">v1.0</span>
          </div>
          <div class="snake-scores">
            <div class="snake-score-box">
              <span class="snake-score-label">SCORE</span>
              <span class="snake-score-value" id="snake-score">0</span>
            </div>
            <div class="snake-score-box hi">
              <span class="snake-score-label">BEST</span>
              <span class="snake-score-value" id="snake-high">0</span>
            </div>
          </div>
          <button class="snake-close" id="snake-close" title="Close (Esc)">&times;</button>
        </div>
        <div class="snake-canvas-wrap" id="snake-canvas-wrap">
          <canvas id="snake-canvas" width="${W}" height="${H}"></canvas>
          <div class="snake-start-overlay" id="snake-start-overlay">
            <div class="snake-start-content">
              <div class="snake-start-title">READY?</div>
              <div class="snake-start-hint">Press any arrow key or WASD to start</div>
              <div class="snake-start-controls">
                <div class="snake-key-row"><span class="snake-key">W</span><span class="snake-key">&uarr;</span></div>
                <div class="snake-key-row">
                  <span class="snake-key">A</span>
                  <span class="snake-key">S</span>
                  <span class="snake-key">D</span>
                  <span class="snake-key-sep">or</span>
                  <span class="snake-key">&larr;</span>
                  <span class="snake-key">&darr;</span>
                  <span class="snake-key">&rarr;</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="snake-footer">
          <span><kbd>Ctrl+Shift+G</kbd> to toggle &middot; <kbd>Esc</kbd> to close &middot; <kbd>R</kbd> restart</span>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    canvas = document.getElementById("snake-canvas");
    ctx = canvas.getContext("2d");
    scoreEl = document.getElementById("snake-score");
    highEl = document.getElementById("snake-high");
    closeBtn = document.getElementById("snake-close");
    gameWrapper = document.getElementById("snake-canvas-wrap");

    closeBtn.addEventListener("click", hide);
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) hide();
    });

    highScore = parseInt(localStorage.getItem("snakeHigh") || "0", 10);
    highEl.textContent = highScore;
  }

  /* ---------- Toggle / Show / Hide ---------- */
  function toggle() {
    buildUI();
    if (overlay.classList.contains("open")) {
      hide();
    } else {
      show();
    }
  }

  function show() {
    buildUI();
    overlay.classList.add("open");
    document.body.style.overflow = "hidden";
    reset();
    drawFrame();
    document.getElementById("snake-start-overlay").style.display = "flex";
    document.addEventListener("keydown", gameKeyHandler);
  }

  function hide() {
    if (!overlay) return;
    overlay.classList.remove("open");
    document.body.style.overflow = "";
    running = false;
    cancelAnimationFrame(loopId);
    document.removeEventListener("keydown", gameKeyHandler);
  }

  /* ---------- Reset ---------- */
  function reset() {
    const mid = Math.floor(ROWS / 2);
    snake = [
      { x: 5, y: mid },
      { x: 4, y: mid },
      { x: 3, y: mid },
    ];
    dir = { x: 1, y: 0 };
    nextDir = { x: 1, y: 0 };
    score = 0;
    alive = true;
    running = false;
    particles = [];
    frameCount = 0;
    foodPulse = 0;
    scoreEl.textContent = "0";
    placeFood();
  }

  /* ---------- Food ---------- */
  function placeFood() {
    let pos;
    do {
      pos = {
        x: Math.floor(Math.random() * COLS),
        y: Math.floor(Math.random() * ROWS),
      };
    } while (snake.some((s) => s.x === pos.x && s.y === pos.y));
    food = pos;
    food.golden = Math.random() < 0.12; /* 12% chance of golden food */
  }

  /* ---------- Particles ---------- */
  function spawnParticles(x, y, color, count) {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 1 + Math.random() * 3;
      particles.push({
        x: x * CELL + CELL / 2,
        y: y * CELL + CELL / 2,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 1,
        decay: 0.02 + Math.random() * 0.03,
        size: 2 + Math.random() * 3,
        color: color,
      });
    }
  }

  /* ---------- Keyboard (in-game) ---------- */
  function gameKeyHandler(e) {
    if (e.key === "Escape") {
      hide();
      return;
    }
    if (e.key.toLowerCase() === "r") {
      reset();
      drawFrame();
      document.getElementById("snake-start-overlay").style.display = "flex";
      return;
    }

    const startOverlay = document.getElementById("snake-start-overlay");
    const dirMap = {
      ArrowUp: { x: 0, y: -1 },
      ArrowDown: { x: 0, y: 1 },
      ArrowLeft: { x: -1, y: 0 },
      ArrowRight: { x: 1, y: 0 },
      w: { x: 0, y: -1 },
      s: { x: 0, y: 1 },
      a: { x: -1, y: 0 },
      d: { x: 1, y: 0 },
    };

    const newDir = dirMap[e.key] || dirMap[e.key.toLowerCase()];
    if (!newDir) return;

    e.preventDefault();

    /* Prevent reversing into self */
    if (newDir.x !== -dir.x || newDir.y !== -dir.y) {
      nextDir = newDir;
    }

    if (!running && alive) {
      startOverlay.style.display = "none";
      running = true;
      gameLoop();
    }
  }

  /* ---------- Game Loop ---------- */
  let lastTick = 0;

  function gameLoop() {
    if (!running) return;

    const now = performance.now();
    if (now - lastTick >= TICK_MS) {
      lastTick = now;
      update();
    }
    drawFrame();
    loopId = requestAnimationFrame(gameLoop);
  }

  /* ---------- Update ---------- */
  function update() {
    if (!alive) return;

    dir = nextDir;
    const head = { x: snake[0].x + dir.x, y: snake[0].y + dir.y };

    /* Wall collision */
    if (head.x < 0 || head.x >= COLS || head.y < 0 || head.y >= ROWS) {
      die();
      return;
    }

    /* Self collision */
    if (snake.some((s) => s.x === head.x && s.y === head.y)) {
      die();
      return;
    }

    snake.unshift(head);

    /* Eat food */
    if (head.x === food.x && head.y === food.y) {
      const pts = food.golden ? 5 : 1;
      score += pts;
      scoreEl.textContent = score;
      const c = food.golden ? PAL.foodAlt : PAL.food;
      spawnParticles(food.x, food.y, c, food.golden ? 20 : 10);
      placeFood();
    } else {
      snake.pop();
    }
  }

  function die() {
    alive = false;
    running = false;
    /* Death particles from head */
    spawnParticles(snake[0].x, snake[0].y, "#ff4444", 30);
    if (score > highScore) {
      highScore = score;
      highEl.textContent = highScore;
      localStorage.setItem("snakeHigh", String(highScore));
    }
  }

  /* ---------- Draw ---------- */
  function drawFrame() {
    frameCount++;
    foodPulse += 0.06;
    ctx.clearRect(0, 0, W, H);

    /* Background */
    ctx.fillStyle = PAL.bg;
    ctx.fillRect(0, 0, W, H);

    /* Grid */
    ctx.strokeStyle = PAL.gridLine;
    ctx.lineWidth = 1;
    for (let x = 0; x <= W; x += CELL) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, H);
      ctx.stroke();
    }
    for (let y = 0; y <= H; y += CELL) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(W, y);
      ctx.stroke();
    }

    /* Scanlines */
    ctx.fillStyle = PAL.scanline;
    for (let y = 0; y < H; y += 4) {
      ctx.fillRect(0, y, W, 2);
    }

    /* Food glow */
    const fGlow = food.golden ? PAL.foodAltGlow : PAL.foodGlow;
    const fColor = food.golden ? PAL.foodAlt : PAL.food;
    const pulse = 0.6 + 0.4 * Math.sin(foodPulse);
    const fx = food.x * CELL + CELL / 2;
    const fy = food.y * CELL + CELL / 2;
    ctx.save();
    ctx.globalAlpha = pulse * 0.5;
    ctx.shadowColor = fGlow;
    ctx.shadowBlur = 20;
    ctx.fillStyle = fColor;
    ctx.beginPath();
    ctx.arc(fx, fy, CELL * 0.55, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    /* Food */
    ctx.save();
    ctx.fillStyle = fColor;
    ctx.shadowColor = fGlow;
    ctx.shadowBlur = 12;
    const fSize = CELL * 0.35 + CELL * 0.05 * Math.sin(foodPulse * 2);
    roundRect(ctx, food.x * CELL + (CELL - fSize * 2) / 2, food.y * CELL + (CELL - fSize * 2) / 2, fSize * 2, fSize * 2, 4);
    ctx.fill();
    ctx.restore();

    /* Snake body */
    snake.forEach(function (seg, i) {
      const t = 1 - i / snake.length;
      const alpha = 0.4 + t * 0.6;

      ctx.save();
      if (i === 0) {
        /* Head */
        ctx.fillStyle = PAL.snakeHead;
        ctx.shadowColor = PAL.snakeGlow;
        ctx.shadowBlur = 16;
        roundRect(ctx, seg.x * CELL + 1, seg.y * CELL + 1, CELL - 2, CELL - 2, 5);
        ctx.fill();

        /* Eyes */
        ctx.shadowBlur = 0;
        ctx.fillStyle = PAL.bg;
        const eyeSize = 3;
        let ex1, ey1, ex2, ey2;
        if (dir.x === 1) { ex1 = 13; ey1 = 5; ex2 = 13; ey2 = 13; }
        else if (dir.x === -1) { ex1 = 5; ey1 = 5; ex2 = 5; ey2 = 13; }
        else if (dir.y === -1) { ex1 = 5; ey1 = 5; ex2 = 13; ey2 = 5; }
        else { ex1 = 5; ey1 = 13; ex2 = 13; ey2 = 13; }
        ctx.beginPath();
        ctx.arc(seg.x * CELL + ex1, seg.y * CELL + ey1, eyeSize, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(seg.x * CELL + ex2, seg.y * CELL + ey2, eyeSize, 0, Math.PI * 2);
        ctx.fill();
      } else {
        /* Body segments */
        ctx.globalAlpha = alpha;
        const grad = ctx.createLinearGradient(
          seg.x * CELL, seg.y * CELL,
          seg.x * CELL + CELL, seg.y * CELL + CELL
        );
        grad.addColorStop(0, PAL.snakeBody);
        grad.addColorStop(1, "rgba(0, 180, 120, " + (alpha * 0.7) + ")");
        ctx.fillStyle = grad;
        ctx.shadowColor = PAL.snakeGlow;
        ctx.shadowBlur = 6 * t;
        const gap = 1.5;
        roundRect(ctx, seg.x * CELL + gap, seg.y * CELL + gap, CELL - gap * 2, CELL - gap * 2, 4);
        ctx.fill();
      }
      ctx.restore();
    });

    /* Particles */
    particles = particles.filter(function (p) {
      p.x += p.vx;
      p.y += p.vy;
      p.vx *= 0.96;
      p.vy *= 0.96;
      p.life -= p.decay;
      if (p.life <= 0) return false;
      ctx.save();
      ctx.globalAlpha = p.life;
      ctx.fillStyle = p.color;
      ctx.shadowColor = p.color;
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
      return true;
    });

    /* Death screen */
    if (!alive) {
      ctx.save();
      ctx.fillStyle = "rgba(10, 10, 26, 0.75)";
      ctx.fillRect(0, 0, W, H);

      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      ctx.font = "bold 36px 'Inter', monospace";
      ctx.fillStyle = "#ff4444";
      ctx.shadowColor = "rgba(255, 68, 68, 0.6)";
      ctx.shadowBlur = 20;
      ctx.fillText("GAME OVER", W / 2, H / 2 - 30);

      ctx.font = "16px 'Inter', monospace";
      ctx.fillStyle = PAL.text;
      ctx.shadowColor = PAL.snakeGlow;
      ctx.shadowBlur = 10;
      ctx.fillText("Score: " + score, W / 2, H / 2 + 10);

      ctx.font = "13px 'Inter', monospace";
      ctx.fillStyle = PAL.textSub;
      ctx.shadowBlur = 0;
      ctx.fillText("Press R to restart", W / 2, H / 2 + 40);

      ctx.restore();
    }

    /* Border glow */
    ctx.save();
    ctx.strokeStyle = alive ? PAL.border : "rgba(255, 68, 68, 0.2)";
    ctx.lineWidth = 2;
    ctx.shadowColor = alive ? PAL.snakeGlow : "rgba(255, 68, 68, 0.4)";
    ctx.shadowBlur = alive ? 8 : 12;
    ctx.strokeRect(0, 0, W, H);
    ctx.restore();
  }

  /* ---------- Rounded Rect Helper ---------- */
  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }
})();
