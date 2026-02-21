const API_BASE = "http://127.0.0.1:5000";

const form = document.getElementById("triageForm");
const submitBtn = document.getElementById("submitBtn");
const resetBtn = document.getElementById("resetBtn");

const resultCard = document.getElementById("resultCard");
const badge = document.getElementById("badge");
const stepsList = document.getElementById("stepsList");
const summaryBox = document.getElementById("summaryBox");
const disclaimer = document.getElementById("disclaimer");
const callBox = document.getElementById("callBox");
const callBtn = document.getElementById("callBtn");

const statusHint = document.getElementById("statusHint");
const primaryStep = document.getElementById("primaryStep");
const primaryActionBtn = document.getElementById("primaryActionBtn");

const aiBtn = document.getElementById("aiBtn");
const aiStatus = document.getElementById("aiStatus");
const freeText = document.getElementById("freeText");

// ---------- Helpers ----------
function toArabicBreathing(v) {
  if (v === "yes") return "نعم";
  if (v === "no") return "لا";
  if (v === "abnormal") return "غير طبيعي";
  return v ?? "-";
}
function toArabicYesNo(v) {
  if (v === "yes") return "نعم";
  if (v === "no") return "لا";
  return v ?? "-";
}
function toArabicBleeding(v) {
  if (v === "none") return "لا يوجد";
  if (v === "mild") return "بسيط";
  if (v === "severe") return "شديد";
  return v ?? "-";
}

function setBadge(levelText) {
  badge.textContent = levelText || "—";
}

function setLoading(isLoading) {
  submitBtn.disabled = isLoading;
  submitBtn.textContent = isLoading ? "جاري التقييم..." : "قيّم الحالة";
}

function setAiLoading(isLoading) {
  aiBtn.disabled = isLoading;
  aiBtn.classList.toggle("isLoading", isLoading);
}

function getPayload() {
  const data = new FormData(form);
  const age = Number(data.get("age"));

  return {
    age: Number.isFinite(age) ? age : 0,
    breathing: data.get("breathing"),
    conscious: data.get("conscious"),
    bleeding: data.get("bleeding"),
    chest_pain: data.get("chest_pain"),
    pain_level: data.get("pain_level"),
    vomiting: data.get("vomiting"),
    dizziness: data.get("dizziness"),
  };
}

function formatSummary(summary) {
  const s = summary || {};
  const notes = Array.isArray(s.notes) ? s.notes : (s.notes ? [String(s.notes)] : []);

  return [
    `العمر: ${s.age ?? "-"}`,
    `التنفس: ${toArabicBreathing(s.breathing)}`,
    `الوعي: ${toArabicYesNo(s.conscious)}`,
    `النزيف: ${toArabicBleeding(s.bleeding)}`,
    `ملاحظات: ${notes.length ? notes.join("، ") : "—"}`
  ].join("\n");
}

// ✅ status styling
function applyResultTheme(levelText) {
  resultCard.classList.remove("result--green", "result--yellow", "result--red");
  const t = levelText || "";
  if (t.includes("🟢")) resultCard.classList.add("result--green");
  else if (t.includes("🟡")) resultCard.classList.add("result--yellow");
  else if (t.includes("🔴")) resultCard.classList.add("result--red");
}

function makeHint(levelText, callNow) {
  const t = levelText || "";
  if (callNow || t.includes("🔴")) return "تنبيه: التقييم يشير إلى حالة طارئة. الأفضل الاتصال فورًا.";
  if (t.includes("🟡")) return "الحالة متوسطة: اتبع أهم خطوة بالأسفل وراقب الأعراض.";
  if (t.includes("🟢")) return "الحالة مطمئنة غالبًا: اتبع الإرشادات وقدّم رعاية أساسية.";
  return "اتبع أهم خطوة بالأسفل.";
}

async function postJSON(path, bodyObj) {
  const url = API_BASE.replace(/\/+$/, "") + path;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bodyObj),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} - ${text || "Request failed"}`);
  }
  return res.json();
}

// ---------- AI: extract + auto-fill ----------
function setIfKnown(id, val) {
  if (val === undefined || val === null) return;
  if (val === "" || val === "unknown") return;
  const el = document.getElementById(id);
  if (el) el.value = val;
}

function fillFormFromAI(r) {
  if (r.age !== undefined && r.age !== null && r.age !== "" && !Number.isNaN(Number(r.age))) {
    document.getElementById("age").value = Number(r.age);
  }

  setIfKnown("breathing", r.breathing);
  setIfKnown("conscious", r.conscious);
  setIfKnown("bleeding", r.bleeding);
  setIfKnown("chest_pain", r.chest_pain);
  setIfKnown("pain_level", r.pain_level);
  setIfKnown("vomiting", r.vomiting);
  setIfKnown("dizziness", r.dizziness);
}

function renderSteps(steps) {
  stepsList.innerHTML = "";
  (steps || []).forEach((step) => {
    const li = document.createElement("li");
    li.textContent = step;
    stepsList.appendChild(li);
  });
}

/**
 * ✅ أهم خطوة الآن (ذكية)
 * - 🔴: ثبّت أهم خطوة = اتصل فورًا
 * - 🟡: خله يوجه لعرض الخطوات
 * - 🟢: أول خطوة
 */
function renderPrimaryStep(steps, levelText, callNow) {
  const t = levelText || "";
  const first = (steps && steps.length) ? steps[0] : "—";

  if (callNow || t.includes("🔴")) {
    primaryStep.textContent = "اتصل بالإسعاف الآن ولا تنتظر.";
    primaryActionBtn.textContent = "اتصل الآن";
    primaryActionBtn.onclick = () => {
      callBox.classList.remove("hidden");
      callBox.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    return;
  }

  if (t.includes("🟡")) {
    primaryStep.textContent = first || "راقب الأعراض واطلب مساعدة إذا ساءت الحالة.";
    primaryActionBtn.textContent = "عرض الخطوات";
    primaryActionBtn.onclick = () => {
      stepsList.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    return;
  }

  primaryStep.textContent = first;
  primaryActionBtn.textContent = "ابدأ الآن";
  primaryActionBtn.onclick = () => {
    stepsList.scrollIntoView({ behavior: "smooth", block: "start" });
  };
}

function renderResult(resp) {
  resultCard.classList.remove("hidden");

  setBadge(resp.level);
  applyResultTheme(resp.level);

  statusHint.textContent = makeHint(resp.level, !!resp.call_now);

  // call box
  if (resp.call_now) {
    callBox.classList.remove("hidden");

    if (resp.call_tel) {
      callBtn.href = `tel:${resp.call_tel}`;
      callBtn.textContent = `اتصل على ${resp.call_tel}`;
    } else {
      callBtn.href = "tel:911";
      callBtn.textContent = "اتصل على 911";
    }
  } else {
    callBox.classList.add("hidden");
    callBtn.href = "tel:911";
    callBtn.textContent = "اتصل على 911";
  }

  renderSteps(resp.steps || []);
  renderPrimaryStep(resp.steps || [], resp.level, !!resp.call_now);

  summaryBox.textContent = formatSummary(resp.summary);
  disclaimer.textContent = resp.disclaimer || "";

  resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

aiBtn.addEventListener("click", async () => {
  const text = (freeText.value || "").trim();
  if (!text) {
    alert("اكتب وصف الحالة أولًا");
    return;
  }

  setAiLoading(true);
  aiStatus.textContent = "جاري التحليل...";

  try {
    const r = await postJSON("/ai/extract_local", { text });
    fillFormFromAI(r);

    aiStatus.textContent = "تم التحليل ✅ جاري التقييم...";

    const payload = getPayload();
    const triageResp = await postJSON("/triage", payload);

    renderResult(triageResp);
  } catch (e) {
    console.error(e);
    aiStatus.textContent = "";
    alert("صار خطأ في AI المحلي.\n" + String(e.message || e));
  } finally {
    setAiLoading(false);
    setTimeout(() => { aiStatus.textContent = ""; }, 4000);
  }
});

// ---------- Triage submit ----------
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = getPayload();

  try {
    setLoading(true);
    const resp = await postJSON("/triage", payload);
    renderResult(resp);
  } catch (err) {
    console.error(err);
    alert("صار خطأ في الاتصال بالسيرفر.\nتأكد Flask شغال.\n\n" + String(err.message || err));
  } finally {
    setLoading(false);
  }
});

// ===== Theme Toggle =====
const themeToggle = document.getElementById("themeToggle");

function applyTheme(theme) {
  if (theme === "light") {
    document.body.classList.add("light");
    if (themeToggle) themeToggle.checked = false;
  } else {
    document.body.classList.remove("light");
    if (themeToggle) themeToggle.checked = true;
  }
}

const savedTheme = localStorage.getItem("theme") || "dark";
applyTheme(savedTheme);

if (themeToggle) {
  themeToggle.addEventListener("change", () => {
    const theme = themeToggle.checked ? "dark" : "light";
    localStorage.setItem("theme", theme);
    applyTheme(theme);
  });
}

resetBtn.addEventListener("click", () => {
  form.reset();
  resultCard.classList.add("hidden");
  callBox.classList.add("hidden");
  aiStatus.textContent = "";

  resultCard.classList.remove("result--green", "result--yellow", "result--red");
  badge.textContent = "—";
  stepsList.innerHTML = "";
  summaryBox.textContent = "";
  disclaimer.textContent = "";
  statusHint.textContent = "—";
  primaryStep.textContent = "—";
  primaryActionBtn.textContent = "ابدأ الآن";
  primaryActionBtn.onclick = null;
});