/* ============================================================
   Nova Console — client
   Persistent Live session: tap Talk once -> continuous voice;
   type anytime. Orb is the hero in talk mode.
   ============================================================ */
"use strict";

const PALETTE = {
  amethyst:[135,80,166], lavender:[222,204,234], gold:[221,164,64],
  rose:[174,78,108], cream:[255,246,229],
};

const els = {
  body: document.body,
  statusText: document.getElementById("statusText"),
  emptyHint: document.getElementById("emptyHint"),
  transcript: document.getElementById("transcript"),
  composer: document.getElementById("composer"),
  textInput: document.getElementById("textInput"),
  talkBtn: document.getElementById("talkBtn"),
  talkLabel: document.getElementById("talkLabel"),
  orb: document.getElementById("orbCanvas"),
  stars: document.getElementById("starCanvas"),
};

const energy = { in:0, out:0 };

let ws = null, audioCtx = null, outGain = null, analyser = null, analyserData = null;
let micStream = null, micSource = null, micNode = null, micSink = null;
let micOn = false, sessionReady = false, connectPromise = null, onReady = null;
let nextPlayTime = 0, lastAudioAt = 0;
const activeSources = new Set();

/* ---------- UI state ---------- */
const LABELS = { idle:"ready", connecting:"connecting", connected:"ready",
  listening:"listening", speaking:"speaking", error:"error" };
function setState(state) {
  els.body.dataset.state = state;
  els.statusText.textContent = LABELS[state] || state;
}
function showNotice(text) { // surface errors/prompts INSIDE the conversation (not under the orb)
  const li = document.createElement("li"); li.className = "turn notice"; li.textContent = text;
  els.transcript.appendChild(li); els.body.classList.add("has-convo");
  els.transcript.scrollTop = els.transcript.scrollHeight;
}
function setMode() {
  els.body.dataset.mode = !sessionReady ? "idle" : micOn ? "talk" : "chat";
}
function talkUI(on) {
  els.talkBtn.setAttribute("aria-pressed", on ? "true" : "false");
  els.talkLabel.textContent = on ? "Stop" : "Talk";
}

/* ---------- transcript (merge streaming fragments per turn) ---------- */
let curTurn = { role:null, el:null };
function appendTranscript(role, text) {
  if (!text) return;
  if (curTurn.role !== role || !curTurn.el) {
    const li = document.createElement("li");
    li.className = `turn ${role}`;
    const who = document.createElement("span");
    who.className = "who";
    if (role === "nova") who.textContent = "Nova";
    else if (role === "system") who.textContent = "System";
    else who.textContent = "Karrie";
    const txt = document.createElement("span"); txt.className = "txt";
    li.append(who, txt); els.transcript.appendChild(li);
    els.body.classList.add("has-convo");      // hides the empty-state hint
    curTurn = { role, el: txt };
  }
  curTurn.el.textContent += text;
  els.transcript.scrollTop = els.transcript.scrollHeight;
}
function endTurn() { curTurn = { role:null, el:null }; }

/* ---------- audio helpers ---------- */
function floatTo16(f32) {
  const out = new Int16Array(f32.length);
  for (let i = 0; i < f32.length; i++) { const s = Math.max(-1, Math.min(1, f32[i])); out[i] = s < 0 ? s*0x8000 : s*0x7fff; }
  return out;
}
function downsample(buf, inRate, outRate) {
  if (outRate >= inRate) return buf;
  const ratio = inRate/outRate, outLen = Math.floor(buf.length/ratio), out = new Float32Array(outLen);
  let oi=0, ii=0;
  while (oi < outLen) { const next = Math.round((oi+1)*ratio); let sum=0,c=0;
    for (; ii<next && ii<buf.length; ii++){ sum+=buf[ii]; c++; } out[oi++] = c?sum/c:0; }
  return out;
}
function playChunk(arrayBuffer) {
  if (!audioCtx) return;
  const pcm = new Int16Array(arrayBuffer), f32 = new Float32Array(pcm.length);
  for (let i=0;i<pcm.length;i++) f32[i] = pcm[i]/0x8000;
  const buf = audioCtx.createBuffer(1, f32.length, 24000); buf.copyToChannel(f32, 0);
  const src = audioCtx.createBufferSource(); src.buffer = buf; src.connect(outGain);
  const t = Math.max(audioCtx.currentTime + 0.02, nextPlayTime);
  src.start(t); nextPlayTime = t + buf.duration; lastAudioAt = performance.now();
  activeSources.add(src); src.onended = () => activeSources.delete(src);
  if (els.body.dataset.state !== "speaking") setState("speaking");
}
function stopPlayback() { activeSources.forEach(s => { try { s.stop(); } catch(_){} }); activeSources.clear(); nextPlayTime = 0; }

/* ---------- session ---------- */
function ensureSession() {
  if (sessionReady) return Promise.resolve();
  if (connectPromise) return connectPromise;
  connectPromise = new Promise((resolve) => { onReady = resolve; openSession(); });
  return connectPromise;
}
function openSession() {
  setState("connecting"); setMode();
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  audioCtx.resume();
  outGain = audioCtx.createGain();
  analyser = audioCtx.createAnalyser(); analyser.fftSize = 256;
  analyserData = new Uint8Array(analyser.frequencyBinCount);
  outGain.connect(analyser); analyser.connect(audioCtx.destination);
  // token (only for exposed mode) rides in the URL fragment + WS subprotocol, never the query.
  const token = new URLSearchParams(location.hash.slice(1)).get("token");
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const subprotocols = token ? ["nova", "nova-token-" + token] : ["nova"];
  ws = new WebSocket(`${proto}://${location.host}/ws`, subprotocols); ws.binaryType = "arraybuffer";
  ws.onmessage = handleMessage;
  ws.onclose = () => teardown();
  ws.onerror = () => { showNotice("Connection error — is the server running?"); setState("idle"); };
}
function handleMessage(ev) {
  if (ev.data instanceof ArrayBuffer) { playChunk(ev.data); return; }
  let m; try { m = JSON.parse(ev.data); } catch { return; }
  switch (m.type) {
    case "status":
      if (m.state === "connected") {
        sessionReady = true; setMode(); setState(micOn ? "listening" : "connected");
        if (onReady) { onReady(); onReady = null; }
      }
      break;
    case "transcript": appendTranscript(m.role, m.text); break;
    case "turn_complete": endTurn(); break;
    case "interrupted": stopPlayback(); endTurn(); break;
    case "error": showNotice(`Oops — ${m.message}`); setState(sessionReady ? "connected" : "idle"); break;
  }
}
function teardown() {
  sessionReady = false; connectPromise = null; onReady = null; energy.in = energy.out = 0;
  stopMicNodes();
  try { ws && ws.close(); } catch(_){} ws = null;
  stopPlayback();
  if (audioCtx) { audioCtx.close().catch(()=>{}); audioCtx = null; }
  micOn = false; talkUI(false); setMode(); setState("idle");
}

/* ---------- mic (continuous while on) ---------- */
async function startMic() {
  await ensureSession();
  if (micOn) return;
  try {
    micStream = await navigator.mediaDevices.getUserMedia({
      audio:{ channelCount:1, echoCancellation:true, noiseSuppression:true, autoGainControl:true } });
  } catch { showNotice("I need mic access — allow the microphone, then tap Talk."); setState(sessionReady ? "connected" : "idle"); return; }
  micSource = audioCtx.createMediaStreamSource(micStream);
  micNode = audioCtx.createScriptProcessor(2048, 1, 1);
  micSink = audioCtx.createGain(); micSink.gain.value = 0;       // silent sink: keeps node alive, no echo
  micSource.connect(micNode); micNode.connect(micSink); micSink.connect(audioCtx.destination);
  micNode.onaudioprocess = (e) => {
    const input = e.inputBuffer.getChannelData(0);
    let s = 0; for (let i=0;i<input.length;i++) s += input[i]*input[i];
    energy.in = Math.min(1, Math.sqrt(s/input.length) * 4);
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(floatTo16(downsample(input, audioCtx.sampleRate, 16000)).buffer);
  };
  micOn = true; talkUI(true); setMode(); setState("listening");
}
function stopMicNodes() {
  if (micNode) { try { micNode.disconnect(); } catch(_){} micNode.onaudioprocess = null; micNode = null; }
  if (micSink) { try { micSink.disconnect(); } catch(_){} micSink = null; }
  if (micSource) { try { micSource.disconnect(); } catch(_){} micSource = null; }
  if (micStream) { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
}
function stopMic() { stopMicNodes(); micOn = false; talkUI(false); setMode(); if (sessionReady) setState("connected"); }

/* ---------- controls ---------- */
els.talkBtn.addEventListener("click", () => { micOn ? stopMic() : startMic(); });
els.composer.addEventListener("submit", async (e) => {
  e.preventDefault();
  const t = els.textInput.value.trim(); if (!t) return;
  els.textInput.value = "";
  appendTranscript("karrie", t); endTurn();
  await ensureSession();
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type:"text", text:t }));
});

/* ============================================================
   Visuals — orb + starfield  (always animating)
   ============================================================ */
function lerp(a,b,t){ return a+(b-a)*t; }
function rgba(c,a){ return `rgba(${c[0]},${c[1]},${c[2]},${a})`; }
function fitCanvas(cv){ const dpr=Math.min(window.devicePixelRatio||1,2); const r=cv.getBoundingClientRect();
  cv.width=Math.max(1,Math.round(r.width*dpr)); cv.height=Math.max(1,Math.round(r.height*dpr)); }

const stars = [];
function initStars(){ const cv=els.stars; cv.width=innerWidth; cv.height=innerHeight; stars.length=0;
  const n=Math.round((cv.width*cv.height)/9000);
  for(let i=0;i<n;i++) stars.push({ x:Math.random()*cv.width, y:Math.random()*cv.height,
    r:Math.random()*1.3+0.2, tw:Math.random()*Math.PI*2, sp:Math.random()*0.015+0.003, gold:Math.random()<0.12 }); }
function drawStars(t){ const cv=els.stars, ctx=cv.getContext("2d"); ctx.clearRect(0,0,cv.width,cv.height);
  for(const s of stars){ const a=0.35+0.65*(0.5+0.5*Math.sin(t*0.001+s.tw)); s.y+=s.sp; if(s.y>cv.height)s.y=0;
    ctx.beginPath(); ctx.fillStyle=s.gold?rgba(PALETTE.gold,a*0.9):rgba(PALETTE.lavender,a*0.7);
    ctx.arc(s.x,s.y,s.r,0,Math.PI*2); ctx.fill(); } }

function ring(ctx, r, segs, rot, color, lw, fill){
  ctx.save(); ctx.rotate(rot); ctx.strokeStyle=color; ctx.lineWidth=lw; ctx.lineCap="round";
  const seg=Math.PI*2/segs, gap=seg*(1-fill);
  for(let i=0;i<segs;i++){ ctx.beginPath(); ctx.arc(0,0,r,i*seg+gap/2,(i+1)*seg-gap/2); ctx.stroke(); }
  ctx.restore();
}
function ticks(ctx, r, n, rot, color){
  ctx.save(); ctx.rotate(rot); ctx.strokeStyle=color; ctx.lineWidth=1;
  for(let i=0;i<n;i++){ const a=(i/n)*Math.PI*2, long=i%4===0, r0=r-(long?6:3), r1=r+(long?6:3);
    ctx.beginPath(); ctx.moveTo(Math.cos(a)*r0,Math.sin(a)*r0); ctx.lineTo(Math.cos(a)*r1,Math.sin(a)*r1); ctx.stroke(); }
  ctx.restore();
}
function drawOrb(t){
  const cv=els.orb, ctx=cv.getContext("2d");
  const w=cv.width, h=cv.height, cx=w/2, cy=h/2, half=Math.min(w,h)/2;
  const base=half*0.34;
  ctx.clearRect(0,0,w,h);

  let out=0; if(analyser){ analyser.getByteFrequencyData(analyserData); let sum=0;
    for(let i=0;i<analyserData.length;i++) sum+=analyserData[i]; out=Math.min(1,(sum/analyserData.length)/90); }
  energy.out=lerp(energy.out,out,0.25); energy.in*=0.92;
  const speaking=els.body.dataset.state==="speaking";
  const level=Math.min(1, speaking?energy.out:energy.in);
  const breathe=0.5+0.5*Math.sin(t*0.0016), pulse=1+level*0.4+breathe*0.04;
  const ringCol=speaking?PALETTE.amethyst:PALETTE.lavender;
  const coreCol=speaking?PALETTE.gold:PALETTE.amethyst;
  const hot=PALETTE.gold;

  ctx.save();
  ctx.globalCompositeOperation="lighter"; // additive: soft, edgeless glow

  // ambient glow — radius CAPPED inside the canvas so it always fades out (no square box)
  const glowR=Math.min(base*(2.3+level*1.5), half*0.9);
  const g=ctx.createRadialGradient(cx,cy,base*0.25,cx,cy,glowR);
  g.addColorStop(0,rgba(coreCol,0.20+level*0.34));
  g.addColorStop(0.55,rgba(coreCol,0.05));
  g.addColorStop(1,rgba(coreCol,0));
  ctx.fillStyle=g; ctx.beginPath(); ctx.arc(cx,cy,glowR,0,Math.PI*2); ctx.fill();

  ctx.translate(cx,cy);
  ring(ctx, base*1.78*pulse, 18, t*0.00018, rgba(ringCol,0.45+level*0.3), 2.2, 0.66);   // outer HUD segments
  ticks(ctx, base*1.50*pulse, 48, t*-0.0001, rgba(hot,0.22+level*0.3));                  // tick ring
  ring(ctx, base*1.32*pulse, 7,  t*-0.00034, rgba(hot,0.40+level*0.3), 1.6, 0.45);       // inner arc segments (counter-rotate)
  for(let k=0;k<2;k++){ const rr=base*(1.12+k*0.1)*pulse; ctx.save(); ctx.rotate(t*(0.0001+k*0.00006));
    ctx.beginPath(); ctx.lineWidth=1; ctx.strokeStyle=rgba(ringCol,0.16-k*0.05);
    for(let a=0;a<=Math.PI*2+0.1;a+=0.25){ const wob=1+0.03*Math.sin(a*6+t*0.002+k);
      const x=Math.cos(a)*rr*wob,y=Math.sin(a)*rr*wob; a===0?ctx.moveTo(x,y):ctx.lineTo(x,y);} ctx.stroke(); ctx.restore(); }

  const cr=base*pulse;
  const cg=ctx.createRadialGradient(0,0,cr*0.1,0,0,cr*1.7); // core bloom
  cg.addColorStop(0,rgba(PALETTE.cream,0.85)); cg.addColorStop(0.4,rgba(ringCol,0.5)); cg.addColorStop(1,rgba(coreCol,0));
  ctx.fillStyle=cg; ctx.beginPath(); ctx.arc(0,0,cr*1.7,0,Math.PI*2); ctx.fill();
  ctx.restore(); // end additive

  // solid core + 3-segment reactor center (normal blend)
  ctx.save(); ctx.translate(cx,cy);
  const core=ctx.createRadialGradient(-cr*0.25,-cr*0.3,cr*0.1,0,0,cr);
  core.addColorStop(0,rgba(PALETTE.cream,0.97)); core.addColorStop(0.45,rgba(ringCol,0.92)); core.addColorStop(1,rgba(coreCol,0.9));
  ctx.fillStyle=core; ctx.beginPath(); ctx.arc(0,0,cr,0,Math.PI*2); ctx.fill();
  ctx.globalCompositeOperation="lighter"; ctx.rotate(t*0.0003);
  for(let i=0;i<3;i++){ ctx.rotate(Math.PI*2/3);
    ctx.beginPath(); ctx.moveTo(0,-cr*0.18); ctx.lineTo(cr*0.52,-cr*0.5); ctx.lineTo(cr*0.52,cr*0.04); ctx.closePath();
    ctx.fillStyle=rgba(hot,0.16+level*0.26); ctx.fill(); }
  ctx.restore();

  // orbiting sparkles (additive)
  ctx.save(); ctx.translate(cx,cy); ctx.globalCompositeOperation="lighter";
  for(let i=0;i<9;i++){ const a=(i/9)*Math.PI*2 + t*0.0004*(i%2?1:-1);
    const rr=base*(1.45+0.45*Math.sin(t*0.002+i*1.7));
    ctx.fillStyle=rgba(i%3?hot:PALETTE.lavender, 0.22+level*0.3);
    ctx.beginPath(); ctx.arc(Math.cos(a)*rr,Math.sin(a)*rr,1.3+level*1.6,0,Math.PI*2); ctx.fill(); }
  ctx.restore();
}
function loop(t){
  drawStars(t); drawOrb(t);
  if(els.body.dataset.state==="speaking" && activeSources.size===0 && performance.now()-lastAudioAt>350)
    setState(micOn?"listening":(sessionReady?"connected":"idle"));
  requestAnimationFrame(loop);
}
function resize(){ fitCanvas(els.orb); initStars(); }
addEventListener("resize", resize);
addEventListener("orientationchange", () => setTimeout(resize, 200));
// keep canvas resolution synced to the orb box (handles the idle<->talk size transition)
if (window.ResizeObserver) new ResizeObserver(() => fitCanvas(els.orb)).observe(els.orb);
resize(); setMode(); setState("idle"); requestAnimationFrame(loop);
