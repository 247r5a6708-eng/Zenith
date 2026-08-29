/* ── Nakama Streak · pomodoro.js ── */

class PomodoroTimer {
  constructor() {
    this.CIRC = 427; // 2π × 68 ≈ 427
    this.durations = { 25: 25 * 60, 45: 45 * 60, 60: 60 * 60 };
    this.duration = 25 * 60;
    this.remaining = this.duration;
    this.running = false;
    this.interval = null;

    this.display  = document.getElementById("pom-time");
    this.ring     = document.querySelector(".ring-prog");
    this.statsEl  = document.getElementById("pom-stats");

    this.bind();
    this.updateDisplay();
    this.updateRing(1);
  }

  bind() {
    document.getElementById("pom-start")?.addEventListener("click", () => this.start());
    document.getElementById("pom-pause")?.addEventListener("click", () => this.pause());
    document.getElementById("pom-reset")?.addEventListener("click", () => this.reset());

    document.querySelectorAll(".pom-dur-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".pom-dur-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.setDuration(parseInt(btn.dataset.min));
      });
    });
  }

  setDuration(min) {
    this.pause();
    this.duration = this.durations[min] || min * 60;
    this.remaining = this.duration;
    this.updateDisplay();
    this.updateRing(1);
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.interval = setInterval(() => this.tick(), 1000);
  }

  pause() {
    this.running = false;
    clearInterval(this.interval);
  }

  reset() {
    this.pause();
    this.remaining = this.duration;
    this.updateDisplay();
    this.updateRing(1);
  }

  tick() {
    this.remaining = Math.max(0, this.remaining - 1);
    this.updateDisplay();
    this.updateRing(this.remaining / this.duration);
    if (this.remaining === 0) this.complete();
  }

  updateDisplay() {
    const m = Math.floor(this.remaining / 60);
    const s = this.remaining % 60;
    if (this.display) {
      this.display.textContent = `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
    }
  }

  updateRing(progress) {
    if (!this.ring) return;
    const offset = this.CIRC * (1 - progress);
    this.ring.style.strokeDashoffset = offset;
  }

  async complete() {
    this.pause();
    this.playBeep();
    const durationMin = Math.round(this.duration / 60);

    // Log via API
    try {
      const r = await fetch("/tracker/api/pomodoro/log/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.cookie.split(";")
            .map(c => c.trim())
            .find(c => c.startsWith("csrftoken="))
            ?.split("=")[1] || "",
        },
        body: JSON.stringify({ duration: durationMin }),
      });
      const data = await r.json();
      if (data.success && this.statsEl) {
        this.statsEl.textContent = `Total pomodoros logged: ${data.total_pomodoros}`;
      }
    } catch(e) {
      console.warn("Pomodoro log failed:", e);
    }

    if (typeof showToast === "function") {
      showToast(`✅ ${durationMin}-min session complete!`);
    }

    setTimeout(() => this.reset(), 1500);
  }

  playBeep() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      [0, 0.15, 0.3].forEach(delay => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.value = 660;
        gain.gain.setValueAtTime(0.25, ctx.currentTime + delay);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + 0.25);
        osc.start(ctx.currentTime + delay);
        osc.stop(ctx.currentTime + delay + 0.25);
      });
    } catch(e) {}
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("pom-time")) {
    window._pom = new PomodoroTimer();
  }
});
