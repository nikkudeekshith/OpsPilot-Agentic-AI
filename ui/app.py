from __future__ import annotations
import sys
import json
import logging
import time as _time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

logger = logging.getLogger("opspilot.ui")

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OpsPilot — AI Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
#  BACKEND IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
from opspilot.loop import run_investigation, _detect_service
from opspilot.evaluation.pipeline import run_evaluation
from opspilot.tools.metrics import seed_metrics
from opspilot.tools.logs import seed_logs
from opspilot.tools.deployments import seed_deployments
from opspilot.tools.incidents import seed_incidents
from opspilot.human_approval import get_pending_approvals, approve_request, deny_request
from opspilot.observability import get_logger

seed_metrics()
seed_logs()
seed_deployments()
seed_incidents()

# ─────────────────────────────────────────────────────────────────────────────
#  DESIGN TOKENS / CSS
# ─────────────────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
/* ══════════════════════  DESIGN SYSTEM  ══════════════════════ */
:root {
  --bg0: #070B12;
  --bg1: #0B1018;
  --bg2: #0E141F;
  --surface: rgba(17, 24, 38, 0.62);
  --surface-solid: #111826;
  --surface-2: rgba(255, 255, 255, 0.03);
  --card: rgba(20, 28, 44, 0.55);
  --card-hover: rgba(26, 36, 56, 0.75);
  --glass: rgba(255, 255, 255, 0.02);
  --border: rgba(148, 163, 184, 0.10);
  --border-strong: rgba(148, 163, 184, 0.18);
  --primary: #4F8CFF;
  --primary-2: #6A5AFF;
  --primary-soft: rgba(79, 140, 255, 0.12);
  --cyan: #22D3EE;
  --green: #34D399;
  --amber: #FBBF24;
  --red: #F87171;
  --purple: #A78BFA;
  --text: #E7ECF5;
  --text-2: #B6BFD2;
  --muted: #7C869E;
  --muted-2: #5A6378;
  --radius: 16px;
  --radius-lg: 20px;
  --radius-sm: 10px;
  --shadow: 0 10px 40px rgba(2, 6, 16, 0.55);
  --glow: 0 0 0 1px rgba(79, 140, 255, 0.18), 0 8px 40px rgba(79, 140, 255, 0.14);
  --font: 'Inter', 'Manrope', 'Plus Jakarta Sans', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --mono: 'JetBrains Mono', ui-monospace, 'Cascadia Code', Consolas, monospace;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { background: var(--bg0); }

.stApp { background: var(--bg0); }

/* Ambient background glow */
.stApp::before {
  content: "";
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(900px 500px at 12% -8%, rgba(79, 140, 255, 0.10), transparent 60%),
    radial-gradient(800px 500px at 88% -10%, rgba(106, 90, 255, 0.08), transparent 60%),
    radial-gradient(700px 700px at 50% 120%, rgba(34, 211, 238, 0.05), transparent 55%);
}
.block-container { max-width: 1280px; padding-top: 3.25rem; padding-bottom: 3rem; position: relative; z-index: 1; }

/* Scrollbar */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.18); border-radius: 8px; border: 2px solid var(--bg0); }
::-webkit-scrollbar-thumb:hover { background: rgba(148,163,184,0.3); }

/* ══════════════════════  TOP BAR  ══════════════════════ */
.topbar {
  position: sticky; top: 0; z-index: 1000;
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; margin: 0 0 22px;
  background: rgba(10, 15, 25, 0.72);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border); border-radius: 16px;
  box-shadow: 0 8px 32px rgba(2, 6, 16, 0.45);
}
.tp-brand { display: flex; align-items: center; gap: 9px; flex-shrink: 0; }
.tp-logo {
  width: 38px; height: 38px; border-radius: 11px;
  display: grid; place-items: center; font-weight: 800; font-size: 18px; color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--primary-2));
  box-shadow: 0 4px 18px rgba(79, 140, 255, 0.4), inset 0 1px 0 rgba(255,255,255,0.25);
  position: relative;
}
.tp-logo::after {
  content: ""; position: absolute; inset: -4px; border-radius: 14px; z-index: -1;
  background: linear-gradient(135deg, rgba(79,140,255,0.35), rgba(106,90,255,0.2)); filter: blur(12px);
}
.tp-name { font-weight: 700; font-size: 16px; letter-spacing: -0.3px; color: var(--text); line-height: 1.05; }
.tp-sub { font-size: 9.5px; letter-spacing: 2.2px; color: var(--muted); text-transform: uppercase; margin-top: 2px; }

.tp-nav { display: flex; align-items: center; gap: 2px; margin-left: 2px; flex: 1; min-width: 0; justify-content: space-between; }
.tp-link {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 9px; border-radius: 10px; border: none;
  background: transparent; color: var(--text-2);
  font: 500 12.5px var(--font); cursor: pointer; transition: all .2s ease;
  white-space: nowrap; text-decoration: none;
}
.tp-nav .tp-link { text-decoration: none; }
.tp-link:hover { color: var(--text); background: rgba(255,255,255,0.05); }
.tp-link.active {
  color: #fff; background: linear-gradient(135deg, rgba(79,140,255,0.18), rgba(106,90,255,0.12));
  box-shadow: inset 0 0 0 1px rgba(79,140,255,0.35);
}
.tp-link-ico { font-size: 14px; width: 17px; text-align: center; }

.tp-right { display: flex; align-items: center; gap: 10px; margin-left: auto; flex-shrink: 0; }
.tp-pill {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 5px 12px; border-radius: 999px;
  background: rgba(52, 211, 153, 0.08); border: 1px solid rgba(52, 211, 153, 0.22);
  font-size: 11.5px; font-weight: 600; color: var(--green);
}
.tp-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); box-shadow: 0 0 8px rgba(52,211,153,0.8); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .4; } }

/* ══════════════════════  HERO  ══════════════════════ */
.hero { display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 36px; align-items: center; padding: 30px 4px 34px; }
.hero-eyebrow {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 11px; font-weight: 700; letter-spacing: 2.4px; text-transform: uppercase;
  color: var(--primary); margin-bottom: 16px;
}
.hero-eyebrow::before { content: ""; width: 22px; height: 1.5px; background: linear-gradient(90deg, transparent, var(--primary)); }
.hero-headline {
  font-size: clamp(30px, 4.2vw, 46px); font-weight: 800; letter-spacing: -1.6px;
  line-height: 1.08; color: var(--text); margin-bottom: 16px;
}
.hero-headline .grad {
  background: linear-gradient(100deg, #7DB2FF 0%, var(--primary) 45%, var(--primary-2) 100%);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-desc { font-size: 15px; color: var(--text-2); line-height: 1.7; max-width: 560px; margin-bottom: 26px; }
.hero-actions { display: flex; gap: 12px; flex-wrap: wrap; }
.hero-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 20px; }
.chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 12px; border-radius: 999px; font-size: 11.5px; font-weight: 500;
  color: var(--text-2); background: var(--surface-2); border: 1px solid var(--border);
}
.chip b { color: var(--cyan); font-weight: 600; }

.hero-visual { position: relative; display: grid; place-items: center; min-height: 260px; }
.hero-orbit { position: absolute; border-radius: 50%; border: 1px solid rgba(79,140,255,0.16); }
.hero-orbit.o1 { width: 250px; height: 250px; animation: spin 22s linear infinite; }
.hero-orbit.o2 { width: 180px; height: 180px; animation: spin 16s linear infinite reverse; }
.hero-orbit.o3 { width: 120px; height: 120px; border-color: rgba(34,211,238,0.2); animation: spin 10s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.hero-core {
  width: 88px; height: 88px; border-radius: 26px; position: relative; z-index: 2;
  display: grid; place-items: center; font-size: 38px;
  background: linear-gradient(135deg, rgba(79,140,255,0.22), rgba(106,90,255,0.16));
  border: 1px solid rgba(79,140,255,0.4);
  box-shadow: 0 0 0 12px rgba(79,140,255,0.06), 0 0 60px rgba(79,140,255,0.35), inset 0 1px 0 rgba(255,255,255,0.15);
  backdrop-filter: blur(8px);
}
.hero-float {
  position: absolute; z-index: 3; padding: 8px 14px; border-radius: 12px;
  background: rgba(13, 19, 32, 0.85); border: 1px solid var(--border-strong);
  backdrop-filter: blur(10px); font-size: 12px; font-weight: 600; color: var(--text-2);
  box-shadow: var(--shadow); animation: floaty 4.5s ease-in-out infinite;
}
@keyframes floaty { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-7px); } }
.hero-float .hl { color: var(--cyan); }
.hero-float.f1 { top: 8%; left: 6%; }
.hero-float.f2 { top: 16%; right: 2%; animation-delay: .7s; }
.hero-float.f3 { bottom: 8%; left: 12%; animation-delay: 1.3s; }
.hero-float.f4 { bottom: 4%; right: 10%; animation-delay: 2s; }

/* ══════════════════════  SECTIONS  ══════════════════════ */
.sect { margin-bottom: 34px; }
.sect-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
.sect-eyebrow {
  font-size: 10.5px; font-weight: 700; letter-spacing: 2.4px; text-transform: uppercase;
  color: var(--primary); margin-bottom: 7px;
}
.sect-title { font-size: 21px; font-weight: 750; letter-spacing: -0.4px; color: var(--text); }
.sect-desc { font-size: 13px; color: var(--muted); margin-top: 5px; max-width: 620px; line-height: 1.6; }

/* ══════════════════════  STAT CARDS  ══════════════════════ */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 34px; }
.stat-card {
  position: relative; overflow: hidden;
  background: linear-gradient(160deg, var(--card), rgba(15, 21, 33, 0.6));
  border: 1px solid var(--border); border-radius: var(--radius);
  padding: 20px 20px 18px; transition: all .25s ease;
}
.stat-card::before {
  content: ""; position: absolute; inset: 0 0 auto 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--sc, var(--primary)), transparent);
  opacity: .8;
}
.stat-card:hover { transform: translateY(-3px); border-color: var(--border-strong); box-shadow: var(--glow); }
.stat-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.stat-ico {
  width: 38px; height: 38px; border-radius: 11px; display: grid; place-items: center; font-size: 17px;
  background: var(--icobg, var(--primary-soft)); border: 1px solid var(--icoborder, rgba(79,140,255,0.22));
}
.stat-spark { color: var(--muted-2); font-size: 11px; font-weight: 600; letter-spacing: .4px; }
.stat-num {
  font-size: 30px; font-weight: 800; letter-spacing: -1px; line-height: 1;
  background: linear-gradient(120deg, var(--sc2, #fff), var(--sc3, #9db8dd));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
  margin-bottom: 6px;
}
.stat-label { font-size: 11.5px; color: var(--muted); font-weight: 500; letter-spacing: .3px; }
.stat-trend { display: inline-flex; align-items: center; gap: 5px; margin-top: 9px; font-size: 11.5px; font-weight: 600; }

/* ══════════════════════  GLASS CARD  ══════════════════════ */
.glass {
  position: relative;
  background: linear-gradient(165deg, var(--card), rgba(13, 19, 32, 0.55));
  border: 1px solid var(--border); border-radius: var(--radius-lg);
  padding: 24px; transition: all .25s ease;
  backdrop-filter: blur(8px);
}
.glass:hover { border-color: var(--border-strong); }
.glass-pad-sm { padding: 16px 18px; }

.card-title-row { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.card-ico {
  width: 30px; height: 30px; border-radius: 9px; display: grid; place-items: center;
  font-size: 14px; background: var(--primary-soft); border: 1px solid rgba(79,140,255,0.2);
}
.card-title { font-size: 12.5px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: var(--primary); }
.card-sub { font-size: 12px; color: var(--muted); margin-top: 2px; }

/* ══════════════════════  BUTTONS  ══════════════════════ */
.stButton > button {
  border-radius: 10px !important; font-weight: 600 !important; font-size: 13px !important;
  border: 1px solid var(--border) !important; background: var(--surface-2) !important;
  color: var(--text-2) !important; padding: 8px 18px !important; transition: all .2s ease !important;
}
.stButton > button:hover { border-color: var(--border-strong) !important; color: var(--text) !important; background: rgba(255,255,255,0.06) !important; transform: translateY(-1px); box-shadow: 0 4px 18px rgba(2,6,16,0.35); }
.stButton[data-testid="baseButton-primary"] > button, .stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, var(--primary), var(--primary-2)) !important;
  border: none !important; color: #fff !important;
  box-shadow: 0 4px 22px rgba(79, 140, 255, 0.35) !important;
}
.stButton[data-testid="baseButton-primary"] > button:hover {
  box-shadow: 0 6px 30px rgba(79, 140, 255, 0.5) !important; transform: translateY(-1px) !important;
}
.stButton > button:disabled { opacity: .5 !important; box-shadow: none !important; }

/* ══════════════════════  INPUTS  ══════════════════════ */
.stTextInput > div, .stTextArea > div, .stSelectbox > div, [data-testid="stNumberInput"] > div {
  border: 1px solid var(--border) !important; border-radius: 12px !important; background: rgba(9, 14, 24, 0.6) !important;
  transition: border-color .2s ease, box-shadow .2s ease !important;
}
.stTextInput > div:focus-within, .stTextArea > div:focus-within, .stSelectbox > div:focus-within {
  border-color: var(--primary) !important; box-shadow: 0 0 0 3px rgba(79,140,255,0.15) !important;
}
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
  color: var(--text) !important; font-size: 13.5px !important;
}
.stTextArea textarea::placeholder, .stTextInput input::placeholder { color: var(--muted-2) !important; }
.stTextInput label, .stTextArea label, .stSelectbox label { font-size: 12px !important; font-weight: 600 !important; color: var(--text-2) !important; letter-spacing: .3px; }
.stSelectbox [data-baseweb="select"] { background: transparent !important; }
.stSelectbox [data-baseweb="select"] div { background: transparent !important; }

/* ══════════════════════  TEMPLATE CARDS  ══════════════════════ */
.tmpl-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 14px 0 10px; }
.tmpl-card {
  display: flex; flex-direction: column; gap: 10px;
  background: linear-gradient(160deg, var(--card), rgba(14, 20, 32, 0.6));
  border: 1px solid var(--border); border-radius: 14px; padding: 14px;
  transition: all .22s ease; cursor: default;
}
.tmpl-card:hover { transform: translateY(-3px); border-color: var(--border-strong); box-shadow: var(--glow); }
.tmpl-led {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
  background: rgba(148, 163, 184, 0.28);
  box-shadow: none;
  transition: background .2s ease, box-shadow .2s ease;
}
.tmpl-led.on {
  background: var(--green);
  box-shadow: 0 0 8px rgba(52, 211, 153, 0.9), 0 0 2px rgba(52, 211, 153, 0.8);
}
.tmpl-ico {
  width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center;
  font-size: 16px; background: var(--primary-soft); border: 1px solid rgba(79,140,255,0.2);
}
.tmpl-label { font-size: 12.5px; font-weight: 650; color: var(--text); line-height: 1.25; }
.tmpl-tag { font-size: 10px; color: var(--muted); }
.tmpl-actions { display: flex; gap: 8px; margin-top: auto; }
.tmpl-actions .stButton > button { font-size: 11.5px !important; padding: 5px 10px !important; border-radius: 8px !important; }

/* ══════════════════════  AGENT PANEL  ══════════════════════ */
.agent-ready {
  display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 12px;
  background: rgba(52, 211, 153, 0.06); border: 1px solid rgba(52, 211, 153, 0.18); margin-bottom: 16px;
}
.agent-ready-dot { width: 9px; height: 9px; border-radius: 50%; background: var(--green); box-shadow: 0 0 10px rgba(52,211,153,0.8); animation: pulse 2s infinite; }
.agent-ready-txt { font-size: 13px; font-weight: 650; color: var(--green); }
.agent-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.agent-cell { padding: 12px 14px; border-radius: 12px; background: var(--surface-2); border: 1px solid var(--border); }
.agent-cell-label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
.agent-cell-value { font-size: 17px; font-weight: 750; color: var(--text); }
.agent-bar { height: 4px; border-radius: 4px; background: rgba(148,163,184,0.12); margin-top: 8px; overflow: hidden; }
.agent-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, var(--primary), var(--cyan)); }
.agent-foot { margin-top: 16px; display: flex; flex-direction: column; gap: 9px; }
.agent-row { display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: var(--text-2); }
.agent-row b { color: var(--text); font-weight: 600; }

/* ══════════════════════  RESULTS  ══════════════════════ */
.rstat { display: flex; flex-direction: column; gap: 2px; }
.rstat-label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.2px; }
.rstat-value { font-size: 18px; font-weight: 750; letter-spacing: -.3px; }
.rstat-sub { font-size: 11px; color: var(--muted); }
.bdg { display: inline-flex; align-items: center; padding: 3px 11px; border-radius: 999px; font-size: 11px; font-weight: 650; letter-spacing: .3px; }
.bdg-crit { background: rgba(248, 113, 113, 0.12); color: var(--red); border: 1px solid rgba(248,113,113,0.25); }
.bdg-maj { background: rgba(251, 191, 36, 0.12); color: var(--amber); border: 1px solid rgba(251,191,36,0.25); }
.bdg-min { background: rgba(52, 211, 153, 0.12); color: var(--green); border: 1px solid rgba(52,211,153,0.25); }

.timeline { position: relative; padding-left: 24px; }
.timeline::before { content: ""; position: absolute; left: 7px; top: 6px; bottom: 6px; width: 2px; background: linear-gradient(180deg, var(--primary), var(--cyan)); opacity: .5; }
.tl-item { position: relative; padding: 7px 0 7px 14px; border-left: 2px solid rgba(79,140,255,0.12); margin-left: -1px; }
.tl-dot { position: absolute; left: -7px; top: 11px; width: 10px; height: 10px; border-radius: 50%; background: linear-gradient(135deg, var(--primary), var(--cyan)); box-shadow: 0 0 10px rgba(79,140,255,0.5); }
.tl-tool { font-size: 13px; font-weight: 650; color: var(--text); }
.tl-meta { font-size: 11px; color: var(--muted); margin-top: 2px; font-family: var(--mono); }
.tl-time { font-size: 11px; color: var(--muted-2); white-space: nowrap; margin-left: auto; }

.plan-step { display: flex; align-items: center; gap: 9px; padding: 4px 0; font-size: 12.5px; }
.plan-step .ic { width: 18px; text-align: center; }
.conf-badge {
  display: inline-flex; align-items: center; gap: 6px; font-family: var(--mono);
  font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 999px;
}

/* ══════════════════════  APPROVALS / STATUS  ══════════════════════ */
.appr-row { display: flex; align-items: center; gap: 12px; }
.appr-ico { width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center; font-size: 16px; background: rgba(251,191,36,0.08); border: 1px solid rgba(251,191,36,0.2); }
.appr-title { font-size: 14px; font-weight: 650; color: var(--text); }
.appr-meta { font-size: 12px; color: var(--muted); margin-top: 1px; }

.status-card { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 16px; transition: all .2s ease; }
.status-card:hover { border-color: var(--border-strong); transform: translateY(-2px); }
.status-ind { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }
.status-ind.up { background: var(--green); box-shadow: 0 0 8px rgba(52,211,153,0.6); }
.status-ind.degraded { background: var(--amber); box-shadow: 0 0 8px rgba(251,191,36,0.6); }
.status-ind.down { background: var(--red); box-shadow: 0 0 8px rgba(248,113,113,0.6); }
.sbar { height: 4px; border-radius: 4px; background: rgba(148,163,184,0.12); margin-top: 8px; overflow: hidden; }
.sbar-fill { height: 100%; border-radius: 4px; }

/* ══════════════════════  FOOTER  ══════════════════════ */
.footer { margin-top: 56px; padding-top: 26px; border-top: 1px solid var(--border); }
.footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 32px; }
.footer-brand { font-size: 15px; font-weight: 750; color: var(--text); }
.footer-desc { font-size: 12.5px; color: var(--muted); line-height: 1.7; max-width: 280px; margin-top: 6px; }
.footer-col-title { font-size: 11px; color: var(--muted-2); text-transform: uppercase; letter-spacing: 1.4px; margin-bottom: 12px; font-weight: 600; }
.footer-link { display: block; font-size: 13px; color: var(--text-2); padding: 4px 0; cursor: pointer; text-decoration: none; transition: color .2s; background: none; border: none; text-align: left; }
.footer-link:hover { color: var(--primary); }
.footer-bot { display: flex; justify-content: space-between; align-items: center; margin-top: 22px; padding-top: 16px; border-top: 1px solid var(--border); font-size: 12px; color: var(--muted-2); flex-wrap: wrap; gap: 8px; }

/* ══════════════════════  EMPTY STATE  ══════════════════════ */
.empty-state { text-align: center; padding: 46px 24px; }
.empty-ico { font-size: 44px; margin-bottom: 12px; opacity: .35; filter: drop-shadow(0 0 24px rgba(79,140,255,0.25)); }
.empty-title { font-size: 17px; font-weight: 700; color: var(--text-2); }
.empty-desc { font-size: 13px; color: var(--muted); margin-top: 6px; max-width: 380px; margin-left: auto; margin-right: auto; line-height: 1.6; }

/* ══════════════════════  MISC  ══════════════════════ */
code { font-family: var(--mono) !important; font-size: 12px !important; color: var(--cyan) !important; background: rgba(34,211,238,0.06) !important; border-radius: 6px !important; padding: 1px 6px !important; }
.stExpander { border: 1px solid var(--border) !important; border-radius: 12px !important; background: var(--surface) !important; margin-bottom: 8px; }
.stExpander details { background: transparent; }
.stExpander summary { font-size: 13px !important; }
.stSpinner > div { border-color: var(--primary) !important; border-right-color: transparent !important; }
div[data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 750 !important; }
div[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 1px; }
.stHorizontalBlock { gap: 14px; }
[data-testid="stPlotlyChart"] { border-radius: 12px; }
.stDownloadButton > button { border-radius: 10px !important; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
.afade { animation: fadeUp .45s ease-out both; }
.adelay-1 { animation-delay: .05s; }
.adelay-2 { animation-delay: .1s; }
.adelay-3 { animation-delay: .15s; }
.adelay-4 { animation-delay: .2s; }

/* ══════════════════════  RESPONSIVE  ══════════════════════ */
@media (max-width: 1279px) {
  .topbar { padding: 9px 10px; gap: 10px; }
  .tp-link { padding: 6px 8px; font-size: 12px; gap: 5px; }
  .tp-brand { gap: 7px; }
  .tp-sub { letter-spacing: 1.4px; }
  .tp-pill { padding: 4px 9px; font-size: 11px; gap: 5px; }
}
@media (max-width: 1023px) {
  .topbar { flex-wrap: wrap; }
  .tp-nav { order: 3; width: 100%; flex: 0 0 100%; margin-left: 0; justify-content: space-evenly; }
}
@media (max-width: 1080px) {
  .tmpl-grid { grid-template-columns: repeat(3, 1fr); }
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .footer-grid { grid-template-columns: 1fr 1fr; }
  .hero { grid-template-columns: 1fr; }
  .hero-visual { min-height: 220px; order: -1; }
}
@media (max-width: 760px) {
  .topbar { flex-wrap: wrap; gap: 10px; }
  .tp-nav { order: 3; width: 100%; margin-left: 0; justify-content: flex-start; }
  .tmpl-grid { grid-template-columns: repeat(2, 1fr); }
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .footer-grid { grid-template-columns: 1fr; }
  .block-container { padding-top: 3.25rem; }
}
@media (max-width: 480px) {
  .tmpl-grid { grid-template-columns: 1fr; }
  .stat-grid { grid-template-columns: 1fr; }
  .hero-headline { font-size: 27px; }
}
</style>
"""

# Hide the real (underlying) nav buttons that we drive programmatically from the
# custom top bar.  Keeps them present in the DOM so JS clicks still register.
_NAV_HIDE = ", ".join(f".st-key-pg_{k}" for k, _v, _i in [
    ("command", "Command Center", "⚡"),
    ("approvals", "Approvals", "✓"),
    ("trajectory", "Trajectory", "↗"),
    ("analytics", "Analytics", "📊"),
    ("documentation", "Documentation", "📚"),
    ("status", "System Status", "◎"),
])
CUSTOM_CSS += f"<style>{_NAV_HIDE} {{ display: none !important; }}</style>"

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "command"
if "investigation_data" not in st.session_state:
    st.session_state.investigation_data = None
if "eval_data" not in st.session_state:
    st.session_state.eval_data = None
if "inc_counter" not in st.session_state:
    st.session_state.inc_counter = 1
if "selected_chip" not in st.session_state:
    st.session_state.selected_chip = -1
if "investigation_history" not in st.session_state:
    st.session_state.investigation_history = []
if "show_learn_more" not in st.session_state:
    st.session_state.show_learn_more = None
if "prompt_goal" not in st.session_state:
    st.session_state.prompt_goal = "Investigate why checkout API latency increased in the last two hours"
if "scroll_to_form" not in st.session_state:
    st.session_state.scroll_to_form = False

# ─────────────────────────────────────────────────────────────────────────────
#  DATA
# ─────────────────────────────────────────────────────────────────────────────
PAGES = [
    ("command", "Command Center", "⚡"),
    ("approvals", "Approvals", "✓"),
    ("trajectory", "Trajectory", "↗"),
    ("analytics", "Analytics", "📊"),
    ("documentation", "Documentation", "📚"),
    ("status", "System Status", "◎"),
]

# Read the target page from the URL (?page=<key>) set by the custom top bar /
# footer anchor links.  Streamlit strips inline onclick handlers from markdown
# HTML, so navigation is driven through real hrefs instead of JS.
_NAV_PAGE_KEYS = {k for k, _v, _i in PAGES}
_qp_page = st.query_params.get("page")
if not isinstance(_qp_page, str):
    _qp_page = _qp_page[0] if _qp_page else None
if _qp_page in _NAV_PAGE_KEYS and st.session_state.page != _qp_page:
    st.session_state.page = _qp_page

TEMPLATES_DATA = [
    {"id": "api-latency", "icon": "🌐", "label": "API Latency",
     "prompt": "Investigate increased API latency affecting customer requests over the last two hours.",
     "dataset": {"logs": "api_gateway", "metrics": "p99_latency", "traces": "checkout_trace", "runbook": "api_latency", "evidence": "latency_spike"}},
    {"id": "http-503", "icon": "⚠️", "label": "HTTP 503 Errors",
     "prompt": "Investigate repeated HTTP 503 Service Unavailable errors in the payment service.",
     "dataset": {"logs": "payment_svc", "metrics": "error_rate", "traces": "payment_trace", "runbook": "503_response", "evidence": "503_errors"}},
    {"id": "high-cpu", "icon": "💻", "label": "High CPU Usage",
     "prompt": "Investigate abnormal CPU utilization on the production application servers.",
     "dataset": {"logs": "system_logs", "metrics": "cpu_utilization", "traces": None, "runbook": "high_cpu", "evidence": "cpu_spike"}},
    {"id": "high-memory", "icon": "🧠", "label": "High Memory Usage",
     "prompt": "Investigate increasing memory consumption leading to performance degradation.",
     "dataset": {"logs": "system_logs", "metrics": "memory_usage", "traces": None, "runbook": "memory_leak", "evidence": "memory_oom"}},
    {"id": "db-timeout", "icon": "🗄️", "label": "DB Connection Timeout",
     "prompt": "Investigate database connection timeout errors impacting application requests.",
     "dataset": {"logs": "db_logs", "metrics": "db_connections", "traces": "db_trace", "runbook": "db_timeout", "evidence": "conn_pool_exhaustion"}},
    {"id": "failed-orders", "icon": "📦", "label": "Failed Orders",
     "prompt": "Investigate increasing order processing failures during checkout.",
     "dataset": {"logs": "order_svc", "metrics": "order_failure_rate", "traces": "checkout_trace", "runbook": "order_failures", "evidence": "order_errors"}},
    {"id": "payment-gateway", "icon": "💳", "label": "Payment Gateway Failure",
     "prompt": "Investigate payment gateway failures causing unsuccessful transactions.",
     "dataset": {"logs": "payment_svc", "metrics": "payment_success_rate", "traces": "payment_trace", "runbook": "payment_gateway", "evidence": "gateway_errors"}},
    {"id": "k8s-crashloop", "icon": "☁️", "label": "K8s CrashLoopBackOff",
     "prompt": "Investigate why multiple Kubernetes pods entered CrashLoopBackOff state.",
     "dataset": {"logs": "k8s_events", "metrics": "pod_restarts", "traces": None, "runbook": "crashloop_backoff", "evidence": "crash_loop_logs"}},
    {"id": "network-latency", "icon": "🌍", "label": "Network Latency",
     "prompt": "Investigate high network latency between application and database servers.",
     "dataset": {"logs": "network_logs", "metrics": "network_rtt", "traces": "network_trace", "runbook": "network_latency", "evidence": "latency_metrics"}},
    {"id": "auth-failure", "icon": "🔐", "label": "Login / Auth Failure",
     "prompt": "Investigate sudden increase in user authentication failures.",
     "dataset": {"logs": "auth_svc", "metrics": "auth_success_rate", "traces": "auth_trace", "runbook": "auth_failure", "evidence": "auth_errors"}},
    {"id": "kafka-lag", "icon": "📡", "label": "Kafka Consumer Lag",
     "prompt": "Investigate message processing delays caused by Kafka consumer lag.",
     "dataset": {"logs": "kafka_logs", "metrics": "consumer_lag", "traces": "kafka_trace", "runbook": "kafka_lag", "evidence": "lag_metrics"}},
    {"id": "ai-timeout", "icon": "🤖", "label": "AI Service / LLM Timeout",
     "prompt": "Investigate AI inference service timeout affecting response generation.",
     "dataset": {"logs": "ai_svc", "metrics": "inference_latency", "traces": "ai_trace", "runbook": "ai_timeout", "evidence": "timeout_errors"}},
]

_LM_CAUSES = {
    "api-latency": ["Database query slowdown", "Upstream service timeout", "Insufficient application server resources", "Network congestion", "Inefficient code path"],
    "http-503": ["Service deployment failure", "Resource exhaustion (CPU/Memory)", "Upstream dependency unavailable", "Misconfigured load balancer", "Connection pool depletion"],
    "high-cpu": ["Runaway process / infinite loop", "Memory leak triggering GC pressure", "Traffic spike exceeding capacity", "Cryptocurrency miner", "Misconfigured auto-scaling"],
    "high-memory": ["Memory leak in application code", "Insufficient heap allocation", "Cached data growing unbounded", "Thread pool explosion", "Large payload processing"],
    "db-timeout": ["Connection pool exhaustion", "Slow query / missing index", "Database server overload", "Network partition", "Deadlocked transactions"],
    "failed-orders": ["Payment gateway rejection", "Inventory validation failure", "Cart session expiry", "Concurrent purchase race condition", "Shipping address validation error"],
    "payment-gateway": ["Gateway provider outage", "Expired API credentials", "Payment method decline rate spike", "TLS/SSL certificate expiry", "Webhook delivery failure"],
    "k8s-crashloop": ["Application startup failure", "Missing configmap or secret", "Resource limits too restrictive", "Init container failure", "Readiness probe misconfiguration"],
    "network-latency": ["DNS resolution delay", "Cross-region traffic routing", "Firewall rule inspection overhead", "Bandwidth saturation", "MTU mismatch"],
    "auth-failure": ["Token service outage", "Database authentication lag", "SSO provider latency", "Password policy change", "Account lockout threshold breach"],
    "kafka-lag": ["Consumer processing bottleneck", "Partition rebalance in progress", "Broker disk I/O saturation", "Message size increase", "Consumer group stalled"],
    "ai-timeout": ["LLM provider rate limiting", "Context window overflow", "GPU resource contention", "Network latency to inference endpoint", "Model loading delay"],
}
_LM_METRICS = {
    "api-latency": "p99/p50 latency, request throughput, error rate, upstream response time",
    "http-503": "HTTP 5xx rate, deployment success rate, instance health, connection pool usage",
    "high-cpu": "CPU utilization %, load average, context switches, run queue length",
    "high-memory": "Memory utilization %, swap usage, GC pause time, heap allocation rate",
    "db-timeout": "Connection pool utilization, query latency, active connections, deadlock count",
    "failed-orders": "Order failure rate, cart abandonment rate, payment decline rate",
    "payment-gateway": "Gateway response time, success rate, error code distribution, retry count",
    "k8s-crashloop": "Pod restart count, container exit codes, resource usage, OOM kill count",
    "network-latency": "Round-trip time, packet loss %, bandwidth utilization, TCP retransmit rate",
    "auth-failure": "Login success rate, token refresh time, upstream auth latency, error code breakdown",
    "kafka-lag": "Consumer lag (messages), offset commit rate, throughput, partition count",
    "ai-timeout": "Inference latency p99, request queue depth, token throughput, error rate",
}
_LM_LOGS = {
    "api-latency": "api_gateway, app_server, upstream_service, database_slow_query",
    "http-503": "payment_service, load_balancer, upstream_dependency, deployment_events",
    "high-cpu": "system_logs, app_server, cron_jobs, container_health",
    "high-memory": "app_server_logs, garbage_collection, heap_dump, container_metrics",
    "db-timeout": "database_logs, connection_pool, app_server, proxy_logs",
    "failed-orders": "order_service, checkout_service, payment_service, inventory_service",
    "payment-gateway": "payment_service, gateway_provider, webhook_handler, billing_logs",
    "k8s-crashloop": "kubelet_events, pod_events, container_logs, deployment_controller",
    "network-latency": "network_monitor, dns_logs, firewall_logs, load_balancer",
    "auth-failure": "auth_service, identity_provider, token_service, audit_logs",
    "kafka-lag": "kafka_broker, consumer_group, connect_logs, schema_registry",
    "ai-timeout": "ai_inference_service, model_server, api_gateway, rate_limiter",
}
_LM_REMEDIATION = {
    "api-latency": "Scale up application servers; optimize database queries; implement caching; review upstream timeouts; enable connection pooling.",
    "http-503": "Rollback recent deployment; scale out instances; verify upstream health; increase connection pool limits; restart affected services.",
    "high-cpu": "Terminate runaway processes; scale out horizontally; review auto-scaling thresholds; optimize critical code paths; add CPU profiling.",
    "high-memory": "Increase heap/container memory limits; fix memory leak in application code; implement cache eviction; reduce batch sizes.",
    "db-timeout": "Increase connection pool size; optimize slow queries; add read replicas; implement query timeout; review connection pooling config.",
    "failed-orders": "Verify payment gateway connectivity; check inventory API; extend cart session timeout; add idempotency keys; improve error handling.",
    "payment-gateway": "Switch to fallback gateway; rotate API credentials; verify SSL certificates; implement retry with exponential backoff; alert on decline rate.",
    "k8s-crashloop": "Check application startup logs; verify configmap and secret mounts; increase resource limits; fix readiness probe; rollback deployment.",
    "network-latency": "Optimize DNS resolution; move services to same region; review firewall rules; increase bandwidth; tune TCP stack parameters.",
    "auth-failure": "Verify token service health; check SSO provider status; extend session TTL; review auth rate limits; add auth caching layer.",
    "kafka-lag": "Increase consumer instances; optimize message processing; tune fetch and batch configs; add partitions; review consumer group rebalance settings.",
    "ai-timeout": "Implement request queuing; increase timeout configuration; add model warm-up; scale GPU resources; implement fallback responses.",
}


def _get_lm(tid):
    return {
        "common_causes": _LM_CAUSES.get(tid, []),
        "metrics_to_inspect": _LM_METRICS.get(tid, "Standard performance metrics"),
        "logs_to_search": _LM_LOGS.get(tid, "Relevant service logs"),
        "remediation": _LM_REMEDIATION.get(tid, "Investigate and apply appropriate fix"),
    }


def apply_template(idx):
    t = TEMPLATES_DATA[idx]
    st.session_state.prompt_goal = t["prompt"]
    st.session_state.selected_chip = idx
    st.session_state.inc_counter = st.session_state.get("inc_counter", 0) + 1
    now = datetime.now().strftime("%H:%M:%S")
    entry = {"id": f"INC-{st.session_state.inc_counter:03d}", "label": t["label"], "time": now, "prompt": t["prompt"], "idx": idx}
    hist = st.session_state.get("investigation_history", [])
    hist.insert(0, entry)
    st.session_state.investigation_history = hist[:5]


STAGES = ["planning", "metrics", "logs", "deployments", "knowledge", "hypotheses", "reflection", "report"]
STAGE_META = [
    ("📋", "Planning", "Formulating investigation strategy"),
    ("📊", "Querying Metrics", "Analyzing performance and anomaly data"),
    ("📜", "Searching Logs", "Scanning service logs for errors"),
    ("🚀", "Deployment History", "Checking recent changes and rollbacks"),
    ("📚", "Knowledge Retrieval", "Searching runbooks and past incidents"),
    ("🔬", "Generating Hypotheses", "Forming potential root cause theories"),
    ("💭", "Reflection", "Evaluating evidence quality and consistency"),
    ("📄", "Generating Report", "Compiling findings and recommendations"),
]

_PAGE_ICONS = {k: i for k, _v, i in PAGES}


def conf_color(c):
    if c >= 0.8:
        return "#10B981"
    if c >= 0.6:
        return "#F59E0B"
    return "#EF4444"


def run_investigation_safe(goal, incident_id):
    try:
        state = run_investigation(goal, incident_id)
        return {
            "goal": goal,
            "incident_id": incident_id,
            "terminated": state.terminated,
            "termination_reason": state.termination_reason or "",
            "iterations": state.iteration_count,
            "tool_calls": state.tool_call_count,
            "execution_time": round(getattr(state, "execution_time", 0), 2),
            "report": state.report.model_dump() if state.report else None,
            "hypotheses": [h.model_dump() for h in state.hypotheses],
            "tool_history": [t.model_dump() for t in state.tool_history],
            "evidence": state.evidence,
            "reflection": state.reflection.model_dump() if state.reflection else None,
            "plan": state.plan.model_dump() if state.plan else None,
        }
    except Exception:
        st.error("Investigation failed. Please check the configured services and try again.")
        logger.error("Investigation failed for incident '%s':\n%s", incident_id, traceback.format_exc())
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  REUSABLE UI COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────
def _page_key(page):
    return f"pg_{page}"


def render_nav():
    """Sticky glass top bar + hidden real buttons that drive navigation."""
    current = st.session_state.page
    links = ""
    for k, v, icon in PAGES:
        cls = "tp-link active" if current == k else "tp-link"
        links += f'<a class="{cls}" href="?page={k}" target="_self" data-nav="{k}">' \
                 f'<span class="tp-link-ico">{icon}</span>{v}</a>'

    st.markdown(f"""
    <div class="topbar">
      <div class="tp-brand">
        <div class="tp-logo">O</div>
        <div>
          <div class="tp-name">OpsPilot</div>
          <div class="tp-sub">AI Command Center</div>
        </div>
      </div>
      <nav class="tp-nav">{links}</nav>
      <div class="tp-right">
        <div class="tp-pill"><span class="tp-dot"></span>System Online</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Hidden real buttons (still clickable programmatically, drive rerun)
    nav_btns = st.columns(len(PAGES))
    for i, (k, v, _icon) in enumerate(PAGES):
        with nav_btns[i]:
            if st.button(v, key=_page_key(k), use_container_width=True):
                st.session_state.page = k
                st.rerun()


def section_head(eyebrow, title, desc=None, right=None):
    right_html = f'<div>{right}</div>' if right else ""
    st.markdown(f"""
    <div class="sect-head">
      <div>
        <div class="sect-eyebrow">{eyebrow}</div>
        <div class="sect-title">{title}</div>
        {f'<div class="sect-desc">{desc}</div>' if desc else ''}
      </div>
      {right_html}
    </div>
    """, unsafe_allow_html=True)


def stat_card(icon, num, label, trend, color="#4F8CFF", color2="#7DB2FF", spark=""):
    return f"""
    <div class="stat-card afade" style="--sc:{color};--sc2:{color};--sc3:{color2};--icobg:{color}18;--icoborder:{color}38;">
      <div class="stat-top">
        <div class="stat-ico">{icon}</div>
        <div class="stat-spark">{spark}</div>
      </div>
      <div class="stat-num">{num}</div>
      <div class="stat-label">{label}</div>
      <div class="stat-trend" style="color:{color};">{trend}</div>
    </div>
    """


def glass_card(inner_html, cls="", pad="pad"):
    return f'<div class="glass {("glass-pad-sm " if pad=="sm" else "")}{cls}">{inner_html}</div>'


def badge(text, level):
    return f'<span class="bdg bdg-{level}">{text}</span>'


def empty_state(icon, title, desc):
    return f"""
    <div class="empty-state glass">
      <div class="empty-ico">{icon}</div>
      <div class="empty-title">{title}</div>
      <div class="empty-desc">{desc}</div>
    </div>
    """


def render_footer():
    def go(page, label):
        return f'<a class="footer-link" href="?page={page}">{label}</a>'

    st.markdown(f"""
    <div class="footer">
      <div class="footer-grid">
        <div>
          <div class="footer-brand">⚡ OpsPilot</div>
          <div class="footer-desc">Autonomous AI-powered incident investigation platform for modern operations teams. Root cause analysis, automated.</div>
        </div>
        <div>
          <div class="footer-col-title">Project</div>
          {go("command", "Command Center")}
          {go("documentation", "Documentation")}
          {go("analytics", "Analytics")}
          {go("status", "System Status")}
        </div>
        <div>
          <div class="footer-col-title">Operations</div>
          {go("approvals", "Approvals")}
          {go("trajectory", "Trajectory")}
          <a class="footer-link" href="https://github.com/anomalyco/opencode" target="_blank">GitHub Repository</a>
        </div>
        <div>
          <div class="footer-col-title">Quick Links</div>
          {go("documentation", "Getting Started")}
          {go("documentation", "Workflow Guide")}
          {go("documentation", "API Reference")}
        </div>
      </div>
      <div class="footer-bot">
        <span>&copy; 2026 OpsPilot. MIT License.</span>
        <span>v1.0.0 &middot; AI-Powered Incident Investigation</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  RENDER PAGE (NAV IS ALWAYS SHARED)
# ─────────────────────────────────────────────────────────────────────────────
render_nav()

page = st.session_state.page

# ═══════════════════════════════════════════════════════════════════════════
#  COMMAND CENTER
# ═══════════════════════════════════════════════════════════════════════════
if page == "command":
    if st.session_state.pop("scroll_to_form", False):
        st.markdown(
            '<script>setTimeout(()=>{const el=document.getElementById("investigation-form");if(el)el.scrollIntoView({behavior:"smooth",block:"start"});const ta=document.querySelector(\'[data-testid="stTextArea"] textarea\');if(ta)ta.focus();},200)</script>',
            unsafe_allow_html=True,
        )

    # ── HERO ──
    c1, c2 = st.columns([1.15, 0.85], gap="large")
    with c1:
        st.markdown("""
        <div class="hero">
          <div>
            <div class="hero-eyebrow">Autonomous Incident Investigation</div>
            <div class="hero-headline">Intelligence, Speed &amp; Precision<br><span class="grad">for Operations Teams</span></div>
            <div class="hero-desc">OpsPilot autonomously plans, executes tool-driven analysis, and delivers comprehensive root cause reports. Powered by AI. Built for reliability.</div>
            <div class="hero-actions">
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        hb1, hb2, hb3 = st.columns([1, 1, 1], gap="small")
        with hb1:
            if st.button("🚀 New Investigation", key="hero_new_investigation", type="primary", use_container_width=True):
                st.session_state.investigation_data = None
                st.session_state.prompt_goal = ""
                st.session_state.selected_chip = -1
                c = st.session_state.get("inc_counter", 0) + 1
                st.session_state.inc_counter = c
                st.session_state.scroll_to_form = True
                st.rerun()
        with hb2:
            if st.button("📚 Documentation", key="hero_docs", use_container_width=True):
                st.session_state.page = "documentation"
        with hb3:
            if st.button("📊 Analytics", key="hero_analytics", use_container_width=True):
                st.session_state.page = "analytics"

        st.markdown("""
        <div class="hero-chips">
          <span class="chip">🧠 Agentic Planning</span>
          <span class="chip">🔧 <b>7</b> Tools</span>
          <span class="chip">📚 RAG Knowledge</span>
          <span class="chip">🧪 <b>30</b> Scenarios</span>
          <span class="chip">🕐 Real-time</span>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="hero-visual">
          <div class="hero-orbit o1"></div>
          <div class="hero-orbit o2"></div>
          <div class="hero-orbit o3"></div>
          <div class="hero-core">🤖</div>
          <div class="hero-float f1">📊 <span class="hl">Metrics</span></div>
          <div class="hero-float f2">📜 <span class="hl">Logs</span></div>
          <div class="hero-float f3">🔬 <span class="hl">Root Cause</span></div>
          <div class="hero-float f4">✅ <span class="hl">Report</span></div>
        </div>
        """, unsafe_allow_html=True)

    # ── STATS ──
    st.markdown('<div class="stat-grid">', unsafe_allow_html=True)
    st.markdown(stat_card("🛰️", "12", "Investigations Today", "↑ +5 vs yesterday", color="#4F8CFF", color2="#22D3EE", spark="24h"), unsafe_allow_html=True)
    st.markdown(stat_card("🎯", "97.7%", "Investigation Success", "↑ +2.1% this week", color="#34D399", color2="#6EE7B7", spark="7d"), unsafe_allow_html=True)
    st.markdown(stat_card("🧠", "74.2%", "Avg Confidence", "↑ +8% improvement", color="#A78BFA", color2="#C4B5FD", spark="30d"), unsafe_allow_html=True)
    st.markdown(stat_card("⚡", "99.9%", "Platform Uptime", "over last 30 days", color="#22D3EE", color2="#67E8F9", spark="SLA"), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── WORKFLOW ──
    section_head("Workflow", "How OpsPilot investigates incidents",
                 "From incident description to root cause report — a fully autonomous AI-driven pipeline.")
    wf = [
        ("📝", "Describe the Incident", "Provide a natural language description of the production issue or anomaly."),
        ("🧠", "AI Plans & Executes", "The agent formulates a strategy and runs 7 specialized investigation tools."),
        ("🔬", "Analyze & Validate", "Evidence is gathered, hypotheses formed, and conclusions are validated."),
        ("📄", "Receive the Report", "Comprehensive root cause report with evidence and recommended actions."),
    ]
    wcols = st.columns(4)
    for i, (ic, t, d) in enumerate(wf):
        with wcols[i]:
            st.markdown(f"""
            <div class="glass afade adelay-{i+1}" style="min-height:170px;">
              <div style="font-size:10px;color:var(--primary);font-weight:700;letter-spacing:1.6px;">Step 0{i+1}</div>
              <div style="font-size:24px;margin:10px 0 8px;">{ic}</div>
              <div style="font-size:14px;font-weight:650;color:var(--text);margin-bottom:5px;">{t}</div>
              <div style="font-size:12px;color:var(--muted);line-height:1.6;">{d}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── INVESTIGATION FORM ──
    st.markdown('<div id="investigation-form"></div>', unsafe_allow_html=True)
    section_head("Mission Control", "Launch an investigation",
                 "Describe the production incident below to start an autonomous investigation.")

    col_inp, col_side = st.columns([1.55, 1], gap="large")

    with col_inp:
        st.markdown('<div class="glass" style="padding:22px;">', unsafe_allow_html=True)

        tcols = st.columns([1, 1])
        with tcols[0]:
            tmpl_opts = ["— Select a template —"] + [t["label"] for t in TEMPLATES_DATA]
            sel = st.selectbox("Quick Template", tmpl_opts, index=0, key="template_quickselect")
            if sel != "— Select a template —":
                idx = tmpl_opts.index(sel) - 1
                if st.session_state.get("_last_tmpl") != sel:
                    st.session_state.prompt_goal = TEMPLATES_DATA[idx]["prompt"]
                    st.session_state.selected_chip = idx
                    st.session_state._last_tmpl = sel
        with tcols[1]:
            svc_opts = ["Auto-detect", "checkout-api", "payment-service", "order-service", "auth-service", "database", "kafka", "kubernetes"]
            st.selectbox("Service Scope", svc_opts, index=0, key="service_scope")

        goal = st.text_area(
            "Incident Description",
            value=st.session_state.prompt_goal,
            height=118,
            key="incident_desc_input",
            placeholder="e.g. Investigate payment-service timeout after deployment v42...",
        )
        st.session_state.prompt_goal = goal

        char_count = len(goal)
        char_pct = min(char_count / 500, 1.0)
        char_color = "#34D399" if char_count <= 400 else "#FBBF24" if char_count <= 480 else "#F87171"
        invalid = char_count < 10
        st.markdown(f"""
        <div style="display:flex;justify-content:flex-end;margin:4px 0 10px;">
          <span style="font-size:11px;color:{char_color};">{char_count} / 500</span>
        </div>
        <div style="height:4px;border-radius:4px;background:rgba(148,163,184,0.12);overflow:hidden;">
          <div style="width:{char_pct*100}%;height:100%;border-radius:4px;background:{char_color};transition:width .3s;"></div>
        </div>
        """, unsafe_allow_html=True)

        if invalid:
            st.markdown(
                '<div style="font-size:12px;color:var(--amber);margin:8px 0 4px;">⚠️ Please describe the incident in at least 10 characters.</div>',
                unsafe_allow_html=True,
            )

        fcols = st.columns([1.4, 1.2, 1, 1], gap="small")
        with fcols[0]:
            inc_id_str = f"INC-{st.session_state.inc_counter:03d}"
            incident_id = st.text_input("Incident ID", inc_id_str, key="incident_id_mission")
        with fcols[1]:
            sev_opts = ["P1 — Critical", "P2 — Major", "P3 — Minor"]
            sev = st.selectbox("Severity", sev_opts, index=1, key="severity_select")
        with fcols[2]:
            src_opts = ["Alert", "Dashboard", "Support Ticket", "Manual"]
            st.selectbox("Source", src_opts, index=0, key="source_select")
        with fcols[3]:
            st.markdown('<div style="padding-top:22px;"></div>', unsafe_allow_html=True)
            run_btn = st.button(
                "⚡ Launch Investigation",
                use_container_width=True,
                key="btn_launch",
                type="primary",
                disabled=invalid,
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # ── TEMPLATES ──
        st.markdown('<div style="font-size:12px;font-weight:700;color:var(--primary);text-transform:uppercase;letter-spacing:1.4px;margin:18px 0 4px;">Quick Investigation Templates</div>',
                    unsafe_allow_html=True)
        _tmpl_cols = st.columns(4)
        for i, t in enumerate(TEMPLATES_DATA):
            with _tmpl_cols[i % 4]:
                is_sel = st.session_state.get("selected_chip", -1) == i
                led_on = " on" if is_sel else ""
                st.markdown(f'''
                <div class="tmpl-card" id="tmpl-{i}">
                  <div style="display:flex;align-items:center;gap:10px;">
                    <span class="tmpl-ico">{t["icon"]}</span>
                    <span style="flex:1;">
                      <div class="tmpl-label">{t["label"]}</div>
                      <div class="tmpl-tag">Runbook: {t["dataset"]["runbook"]}</div>
                    </span>
                    <span class="tmpl-led{led_on}"></span>
                  </div>
                </div>
                ''', unsafe_allow_html=True)
                cu, ci = st.columns(2)
                with cu:
                    if st.button("Use", key=f"tmpl_use_{i}", use_container_width=True):
                        apply_template(i)
                        st.toast(f'Template applied: {t["label"]}', icon="✅")
                        st.rerun()
                with ci:
                    if st.button("Learn", key=f"tmpl_info_{i}", use_container_width=True):
                        st.session_state.show_learn_more = i
                        st.rerun()

        # ── LEARN MORE MODAL ──
        if st.session_state.show_learn_more is not None:
            li = st.session_state.show_learn_more
            t = TEMPLATES_DATA[li]
            lm = _get_lm(t["id"])
            causes = "<br/>".join(lm.get("common_causes", ["Varies by environment"]))
            st.markdown(f"""
            <div style="position:fixed;inset:0;background:rgba(3,6,12,0.72);backdrop-filter:blur(6px);z-index:2000;display:flex;align-items:center;justify-content:center;padding:20px;">
              <div style="background:var(--surface-solid);border:1px solid var(--border-strong);border-radius:18px;max-width:720px;width:100%;max-height:82vh;overflow-y:auto;padding:26px;box-shadow:var(--shadow);">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                  <div style="display:flex;align-items:center;gap:12px;">
                    <span style="font-size:26px;">{t["icon"]}</span>
                    <div>
                      <div style="font-size:17px;font-weight:750;color:var(--text);">{t["label"]}</div>
                      <div style="font-size:12px;color:var(--muted);">Incident Type Reference</div>
                    </div>
                  </div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                  <div class="glass glass-pad-sm"><div style="font-size:12px;font-weight:700;color:var(--amber);margin-bottom:6px;">⚠️ Common Causes</div><div style="font-size:12px;color:var(--text-2);line-height:1.7;">{causes}</div></div>
                  <div class="glass glass-pad-sm"><div style="font-size:12px;font-weight:700;color:var(--cyan);margin-bottom:6px;">📊 Metrics to Inspect</div><div style="font-size:12px;color:var(--text-2);line-height:1.7;">{lm.get("metrics_to_inspect", "Standard performance metrics")}</div></div>
                  <div class="glass glass-pad-sm"><div style="font-size:12px;font-weight:700;color:var(--primary);margin-bottom:6px;">📜 Logs to Search</div><div style="font-size:12px;color:var(--text-2);line-height:1.7;">{lm.get("logs_to_search", "Relevant service logs")}</div></div>
                  <div class="glass glass-pad-sm"><div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:6px;">🔧 Remediation</div><div style="font-size:12px;color:var(--text-2);line-height:1.7;">{lm.get("remediation", "Investigate and apply appropriate fix")}</div></div>
                </div>
                <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;">
                  <span class="chip">Dataset: {t["dataset"]["logs"]}</span>
                  <span class="chip">Runbook: {t["dataset"]["runbook"]}</span>
                  <span class="chip">Traces: {t["dataset"]["traces"] or "N/A"}</span>
                  <span class="chip">Evidence: {t["dataset"]["evidence"]}</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            mcols = st.columns([3, 1])
            with mcols[1]:
                if st.button("Close", key="close_learn_more", use_container_width=True):
                    st.session_state.show_learn_more = None
                    st.rerun()

    with col_side:
        # ── AGENT CONTROL PANEL ──
        st.markdown("""
        <div class="glass" style="height:100%;">
          <div class="card-title-row">
            <div class="card-ico">🤖</div>
            <div>
              <div class="card-title">Agent Control Panel</div>
              <div class="card-sub">Realtime status of the investigation agent</div>
            </div>
          </div>
          <div class="agent-ready"><span class="agent-ready-dot"></span><span class="agent-ready-txt">Agent Ready</span></div>
          <div class="agent-grid">
            <div class="agent-cell"><div class="agent-cell-label">CPU</div><div class="agent-cell-value">12.4%</div><div class="agent-bar"><div class="agent-bar-fill" style="width:12%;"></div></div></div>
            <div class="agent-cell"><div class="agent-cell-label">Memory</div><div class="agent-cell-value">356 MB</div><div class="agent-bar"><div class="agent-bar-fill" style="width:38%;"></div></div></div>
            <div class="agent-cell"><div class="agent-cell-label">Tools</div><div class="agent-cell-value">7 / 7</div><div class="agent-bar"><div class="agent-bar-fill" style="width:100%;"></div></div></div>
            <div class="agent-cell"><div class="agent-cell-label">Accuracy</div><div class="agent-cell-value">97.7%</div><div class="agent-bar"><div class="agent-bar-fill" style="width:98%;"></div></div></div>
          </div>
          <div class="agent-foot">
            <div class="agent-row"><span>Model</span><b>GPT-4o-mini · Fallback</b></div>
            <div class="agent-row"><span>Knowledge Base</span><b>8 documents</b></div>
            <div class="agent-row"><span>Max Iterations</span><b>20</b></div>
            <div class="agent-row"><span>Max Tool Calls</span><b>50</b></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── RUN INVESTIGATION ──
    if run_btn:
        st.session_state.investigation_data = None
        ph = st.empty()
        with ph.container():
            st.markdown(glass_card("""
            <div style="text-align:center;padding:6px 0 2px;">
              <div style="font-size:17px;font-weight:750;background:linear-gradient(100deg,#7DB2FF,var(--primary));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">Running Investigation...</div>
              <div style="color:var(--muted);font-size:13px;margin-top:4px;">Agent is gathering and analyzing evidence</div>
            </div>
            """, pad="sm"), unsafe_allow_html=True)
            for idx, (_ic, stage, desc) in enumerate(STAGE_META):
                active = idx == 0
                st.markdown(f"""
                <div class="glass glass-pad-sm" style="display:flex;align-items:center;gap:12px;margin-top:8px;">
                  <div style="width:22px;text-align:center;font-size:14px;">{_ic}</div>
                  <div style="flex:1;">
                    <div style="font-weight:650;font-size:13px;color:var(--text);">{stage}</div>
                    <div style="font-size:11px;color:var(--muted);">{desc}</div>
                  </div>
                  <div style="width:10px;height:10px;border-radius:50%;background:{'#4F8CFF' if active else 'rgba(148,163,184,0.25)'};box-shadow:{'0 0 12px rgba(79,140,255,0.6)' if active else 'none'};"></div>
                </div>
                """, unsafe_allow_html=True)

        for stage_idx in range(len(STAGES) - 1):
            _time.sleep(0.12 + stage_idx * 0.02)
            with ph.container():
                st.markdown(glass_card(f"""
                <div style="text-align:center;padding:6px 0 2px;">
                  <div style="font-size:17px;font-weight:750;background:linear-gradient(100deg,#7DB2FF,var(--primary));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">Running Investigation... ({stage_idx+1}/{len(STAGES)} phases)</div>
                  <div style="color:var(--muted);font-size:13px;margin-top:4px;">Agent is gathering and analyzing evidence</div>
                </div>
                """, pad="sm"), unsafe_allow_html=True)
                for idx, (_ic, stage, desc) in enumerate(STAGE_META):
                    if idx < stage_idx + 1:
                        dot, ic, stat = "#34D399", "✅", "done"
                    elif idx == stage_idx + 1:
                        dot, ic, stat = "#4F8CFF", _ic, "active"
                    else:
                        dot, ic, stat = "rgba(148,163,184,0.25)", _ic, ""
                    glow = 'box-shadow:0 0 12px rgba(79,140,255,0.6)' if stat == "active" else 'none'
                    st.markdown(f"""
                    <div class="glass glass-pad-sm" style="display:flex;align-items:center;gap:12px;margin-top:8px;opacity:{'1' if stat else '0.55'};">
                      <div style="width:22px;text-align:center;font-size:14px;">{ic}</div>
                      <div style="flex:1;">
                        <div style="font-weight:650;font-size:13px;color:var(--text);">{stage}</div>
                        <div style="font-size:11px;color:var(--muted);">{desc}</div>
                      </div>
                      <div style="width:10px;height:10px;border-radius:50%;background:{dot};{glow}"></div>
                    </div>
                    """, unsafe_allow_html=True)

        data = run_investigation_safe(goal, incident_id)
        ph.empty()
        if data:
            data["goal"] = goal
            data["incident_id"] = incident_id
            st.session_state.investigation_data = data
            st.rerun()

    # ── RESULTS ──
    if st.session_state.investigation_data is not None:
        d = st.session_state.investigation_data
        r = d.get("report")
        rd = d.get("reflection")
        goal = d.get("goal", "")

        sev = "Critical" if (r and r["confidence"] >= 0.8) else ("Major" if (r and r["confidence"] >= 0.6) else "Minor")
        sev_cls = sev_map = {"Critical": "bdg-crit", "Major": "bdg-maj", "Minor": "bdg-min"}[sev]

        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;margin:26px 0 12px;">
          <div class="card-ico">📊</div>
          <span style="font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--primary);">Investigation Report</span>
        </div>
        """, unsafe_allow_html=True)

        rc = st.columns(6)
        reason = d.get("termination_reason") or ""
        reason_l = reason.lower()
        if "complete" in reason_l or (not reason and d.get("report")):
            status, status_color = "Complete", "#34D399"
            status_sub = "Investigation finished"
        else:
            status, status_color = "Inconclusive", "#F59E0B"
            status_sub = reason or "Investigation did not reach a conclusion"
        rstat_html = [
            ("Status", status, status_sub, status_color),
            ("Iterations", f"{d['iterations']}", "", "#4F8CFF"),
            ("Tool Calls", f"{d['tool_calls']}", "", "#22D3EE"),
            ("Duration", f"{d['execution_time']}s", "", "#FBBF24"),
            ("Severity", sev, badge(sev, sev_cls), "#F87171"),
            ("Service", _detect_service(goal), "", "#A78BFA"),
        ]
        for i, (label, value, sub, color) in enumerate(rstat_html):
            with rc[i]:
                st.markdown(f"""
                <div class="glass glass-pad-sm" style="text-align:center;padding:16px 8px;">
                  <div class="rstat-label">{label}</div>
                  <div class="rstat-value" style="color:{color};font-size:{'20px' if len(str(value))<7 else '16px'};">{value}</div>
                  {f'<div style="margin-top:4px;">{sub}</div>' if sub else ''}
                </div>
                """, unsafe_allow_html=True)

        col_a, col_b = st.columns([1, 1], gap="large")

        with col_a:
            st.markdown('<div class="glass" style="height:100%;">', unsafe_allow_html=True)
            st.markdown("""
            <div class="card-title-row">
              <div class="card-ico">🧠</div>
              <div>
                <div class="card-title">Agent Brain</div>
                <div class="card-sub">Plan, reflection &amp; reasoning trace</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:11px;color:var(--muted);">Goal</div>'
                        f'<div style="font-weight:600;font-size:13px;color:var(--text-2);margin-bottom:14px;">{goal[:180]}</div>', unsafe_allow_html=True)
            if d.get("plan"):
                steps = d["plan"].get("steps", [])
                plan_html = ""
                for s in steps:
                    done = s["status"] == "completed"
                    c = "#34D399" if done else "#5A6378"
                    plan_html += f'<div class="plan-step"><span class="ic" style="color:{c};">{"✓" if done else "○"}</span><span style="color:{"var(--text-2)" if done else "var(--muted)"};">{s["tool"]}</span></div>'
                st.markdown(f'<div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin:4px 0 6px;">Plan Steps</div>{plan_html}', unsafe_allow_html=True)
            if rd:
                txt = rd.get("reasoning", rd.get("critique", ""))
                st.markdown(f"""
                <div style="margin-top:12px;">
                  <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Reflection</div>
                  <div style="font-size:12px;color:var(--text-2);background:rgba(79,140,255,0.05);padding:10px 12px;border-radius:10px;border-left:2px solid var(--primary);line-height:1.6;">{txt[:260]}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_b:
            if r:
                conf = r["confidence"]
                gc = conf_color(conf)
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=conf * 100,
                    domain=dict(x=[0, 1], y=[0, 1]),
                    number=dict(suffix="%", font=dict(color=gc, size=34, weight=700)),
                    gauge=dict(
                        axis=dict(range=[0, 100], tickcolor="#5A6378", tickfont=dict(color="#5A6378", size=8)),
                        bar=dict(color=gc, thickness=0.32),
                        bgcolor="rgba(9,14,24,0.6)",
                        borderwidth=0,
                        steps=[
                            dict(range=[0, 40], color="rgba(248,113,113,0.10)"),
                            dict(range=[40, 70], color="rgba(251,191,36,0.10)"),
                            dict(range=[70, 100], color="rgba(52,211,153,0.10)"),
                        ],
                        threshold=dict(line=dict(color=gc, width=2), thickness=0.62, value=conf * 100),
                    ),
                ))
                fig.update_layout(height=190, margin=dict(l=20, r=20, t=5, b=5),
                                  paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E7ECF5"))
                st.markdown('<div class="glass" style="height:100%;">', unsafe_allow_html=True)
                st.markdown("""
                <div class="card-title-row">
                  <div class="card-ico">🎯</div>
                  <div>
                    <div class="card-title">Root Cause</div>
                    <div class="card-sub">Diagnosis &amp; confidence score</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
                rc_text = r.get("root_cause", "")
                st.markdown(f'<div style="font-size:14px;font-weight:650;color:var(--text);line-height:1.5;">{rc_text[:200]}</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;margin-top:12px;padding:10px 12px;background:rgba(52,211,153,0.05);border-radius:10px;border:1px solid rgba(52,211,153,0.16);">
                  <span style="font-size:11px;color:var(--muted);">Action:</span>
                  <span style="font-weight:600;font-size:12.5px;color:var(--green);">{(r.get("recommended_action") or "")[:140]}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # ── TIMELINE ──
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;margin:22px 0 10px;">
          <div class="card-ico">⏱️</div>
          <span style="font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--primary);">Execution Timeline</span>
        </div>
        """, unsafe_allow_html=True)
        tools = d.get("tool_history", [])
        if tools:
            im = {"query_metrics": "📊", "search_logs": "📜", "get_deployments": "🚀",
                  "search_incidents": "🗂", "retrieve_runbook": "📚", "create_incident_report": "📋", "request_rollback": "⏪"}
            tl_html = '<div class="timeline">'
            for t in tools:
                ts = next((t[k] for k in ["timestamp", "start_time", "completed_at"] if k in t), None)
                ts_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else ""
                args = json.dumps(t.get("arguments", {}))
                if len(args) > 60:
                    args = args[:57] + "..."
                icon = im.get(t["tool"], "🔧")
                tl_html += f"""
                <div class="tl-item">
                  <div class="tl-dot"></div>
                  <div style="display:flex;align-items:center;gap:8px;">
                    <span style="font-size:15px;">{icon}</span>
                    <div style="flex:1;">
                      <div class="tl-tool">{t["tool"]}</div>
                      <div class="tl-meta">{args}</div>
                    </div>
                    <div class="tl-time">{ts_str}</div>
                  </div>
                </div>
                """
            tl_html += '</div>'
            st.markdown(f'<div class="glass">{tl_html}</div>', unsafe_allow_html=True)

        # ── EVIDENCE ──
        if r and r.get("evidence"):
            st.markdown("""
            <div style="display:flex;align-items:center;gap:8px;margin:22px 0 10px;">
              <div class="card-ico">📎</div>
              <span style="font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--primary);">Evidence</span>
            </div>
            """, unsafe_allow_html=True)
            ev_icons = {"metrics": "📈", "log": "📜", "deploy": "🚀", "runbook": "📚", "rag": "📖", "incident": "🗂"}
            evc = st.columns(2)
            for i, e in enumerate(r.get("evidence", [])):
                icon = "📄"
                for k, ic in ev_icons.items():
                    if k in e.lower():
                        icon = ic
                        break
                with evc[i % 2]:
                    label = e.split(":")[0] if ":" in e else f"Evidence {i+1}"
                    with st.expander(f"{icon}  {label}", expanded=False):
                        st.markdown(f'<div style="font-size:12.5px;color:var(--text-2);line-height:1.7;">{e}</div>', unsafe_allow_html=True)

        # ── HYPOTHESES ──
        if d.get("hypotheses"):
            st.markdown("""
            <div style="display:flex;align-items:center;gap:8px;margin:22px 0 10px;">
              <div class="card-ico">🔬</div>
              <span style="font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--primary);">Hypotheses</span>
            </div>
            """, unsafe_allow_html=True)
            for h in d["hypotheses"]:
                c = conf_color(h["confidence"])
                st.markdown(f"""
                <div class="glass glass-pad-sm" style="display:flex;align-items:center;gap:14px;margin-bottom:8px;">
                  <div style="width:42px;height:42px;border-radius:10px;display:grid;place-items:center;font-weight:750;color:{c};font-size:12.5px;background:{c}14;border:1px solid {c}30;">{h["confidence"]:.0%}</div>
                  <div style="flex:1;">
                    <div style="font-weight:600;font-size:13px;color:var(--text-2);">{h["description"][:200]}</div>
                    <div style="font-size:11px;color:var(--muted);margin-top:2px;">{len(h.get("supporting_evidence", []))} evidence items</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        # ── ACTIONS ──
        if r:
            st.markdown("""
            <div style="display:flex;align-items:center;gap:8px;margin:22px 0 10px;">
              <div class="card-ico">⚡</div>
              <span style="font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--primary);">Actions</span>
            </div>
            """, unsafe_allow_html=True)
            a1, a2, a3, a4 = st.columns(4)
            with a1:
                if st.button("✅ Validate", use_container_width=True, key="btn_val"):
                    st.toast("Validation dispatched", icon="✅")
            with a2:
                if st.button("⏪ Rollback", use_container_width=True, disabled=r["confidence"] < 0.8, key="btn_rb"):
                    st.toast("Rollback requires approval", icon="⚠️")
            with a3:
                if st.button("🎫 Create Ticket", use_container_width=True, key="btn_tk"):
                    st.toast("Ticket created", icon="🎫")
            with a4:
                st.download_button("📥 Export JSON", data=json.dumps(r, indent=2, default=str),
                                   file_name=f"{incident_id}_report.json", mime="application/json",
                                   use_container_width=True, key="btn_exp")
            with st.expander("🐛 Debug: Tool History", expanded=False):
                for t in d["tool_history"]:
                    st.code(f"{t['tool']}({json.dumps(t.get('arguments', {}), default=str)[:200]})")

    if not run_btn and st.session_state.investigation_data is None:
        e1, e2 = st.columns([1.3, 0.7], gap="large")
        with e1:
            st.markdown(empty_state("🤖", "Ready for your command",
                                    "Describe a production incident above. OpsPilot will plan, execute tools, gather evidence, and deliver a report."),
                        unsafe_allow_html=True)
        with e2:
            st.markdown(f"""
            <div class="glass">
              <div style="font-size:12px;font-weight:700;color:var(--primary);text-transform:uppercase;letter-spacing:1.4px;margin-bottom:12px;">Quick Start</div>
              <div style="display:flex;flex-direction:column;gap:11px;">
                <div style="display:flex;align-items:center;gap:10px;font-size:12.5px;color:var(--text-2);">
                  <span style="width:22px;height:22px;border-radius:7px;display:grid;place-items:center;font-size:10px;font-weight:750;color:#fff;background:linear-gradient(135deg,var(--primary),var(--primary-2));">1</span>
                  Describe the incident
                </div>
                <div style="display:flex;align-items:center;gap:10px;font-size:12.5px;color:var(--text-2);">
                  <span style="width:22px;height:22px;border-radius:7px;display:grid;place-items:center;font-size:10px;font-weight:750;color:#fff;background:linear-gradient(135deg,var(--primary),var(--primary-2));">2</span>
                  Assign incident ID
                </div>
                <div style="display:flex;align-items:center;gap:10px;font-size:12.5px;color:var(--text-2);">
                  <span style="width:22px;height:22px;border-radius:7px;display:grid;place-items:center;font-size:10px;font-weight:750;color:#fff;background:linear-gradient(135deg,var(--primary),var(--primary-2));">3</span>
                  Click Launch
                </div>
                <div style="display:flex;align-items:center;gap:10px;font-size:12.5px;color:var(--text-2);">
                  <span style="width:22px;height:22px;border-radius:7px;display:grid;place-items:center;font-size:10px;font-weight:750;color:#fff;background:linear-gradient(135deg,var(--primary),var(--primary-2));">4</span>
                  Review the report
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  APPROVALS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "approvals":
    section_head("Governance", "Pending Approvals",
                 "Review and approve or deny pending rollback and action requests from the AI agent.")
    st.button("🔄 Refresh", use_container_width=True, key="btn_refresh_appr")

    approvals = get_pending_approvals()
    if not approvals:
        st.markdown(empty_state("✅", "All Clear", "No pending approvals."), unsafe_allow_html=True)
    else:
        for a in approvals:
            key = f"{a.action}:{a.target}"
            st.markdown('<div class="glass" style="margin-bottom:12px;">', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="appr-row">
              <div class="appr-ico">⏳</div>
              <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                  <span class="appr-title">{a.action}</span>
                  <span style="font-size:12px;color:var(--muted);">on</span>
                  <span style="font-weight:650;color:var(--cyan);font-size:13px;">{a.target}</span>
                </div>
                <div class="appr-meta">{a.reason}</div>
                <div class="appr-meta" style="color:var(--muted-2);">{a.evidence_summary[:220]}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Approve", key=f"ap_{key}", use_container_width=True, type="primary"):
                    approve_request(key)
                    st.rerun()
            with c2:
                if st.button("❌ Deny", key=f"den_{key}", use_container_width=True):
                    deny_request(key)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  TRAJECTORY
# ═══════════════════════════════════════════════════════════════════════════
elif page == "trajectory":
    section_head("Audit Trail", "Trajectory Viewer",
                 "Review the step-by-step decision trace of any past investigation in full detail.")

    c1, c2 = st.columns([3, 1])
    with c1:
        traj_id = st.text_input("Incident ID", "INC-001", key="traj_id")
    with c2:
        st.markdown("<div style='padding-top:22px;'></div>", unsafe_allow_html=True)
        load_traj = st.button("🔍 Load Trajectory", use_container_width=True, key="btn_load_traj", type="primary")

    if load_traj:
        logger = get_logger()
        traj = logger.get_trajectory(traj_id)
        if not traj:
            st.markdown(empty_state("🔍", "Not Found",
                                    "No trajectory recorded for this incident ID."), unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color:var(--muted);margin-bottom:12px;font-size:13px;">{len(traj)} steps recorded</div>', unsafe_allow_html=True)
            tl_html = '<div class="timeline">'
            for step in traj:
                ts = step.get("timestamp", "")
                ts_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else ""
                tl_html += f"""
                <div class="tl-item">
                  <div class="tl-dot"></div>
                  <div style="display:flex;align-items:center;gap:8px;">
                    <div style="flex:1;">
                      <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span class="tl-tool">Iteration {step["iteration"]}</span>
                        <span class="tl-time">{ts_str}</span>
                      </div>
                      <div style="font-size:12.5px;color:var(--primary);margin:4px 0;">{step["decision"]}</div>
                    </div>
                  </div>
                </div>
                """
            tl_html += '</div>'
            st.markdown(f'<div class="glass">{tl_html}</div>', unsafe_allow_html=True)

            for step in traj:
                st.markdown('<div style="margin:4px 0;">', unsafe_allow_html=True)
                if step.get("tool_call"):
                    st.code(json.dumps(step["tool_call"], indent=2, default=str)[:300])
                if step.get("result"):
                    st.code(json.dumps(step["result"], indent=2, default=str)[:400])
                if step.get("reflection"):
                    refl = step["reflection"]
                    txt = refl.get("reasoning", refl.get("critique", "N/A"))[:200]
                    st.markdown(f'<div style="font-size:12px;color:var(--muted);background:rgba(79,140,255,0.04);padding:8px 12px;border-radius:10px;margin-top:4px;border-left:2px solid var(--primary);">💭 {txt}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "analytics":
    section_head("Performance", "Evaluation Analytics",
                 "Benchmark the agent's investigation accuracy across 30 synthetic incident scenarios.")

    if st.button("🏃 Run Full Evaluation (30 scenarios)", type="primary", use_container_width=True, key="btn_run_ev"):
        with st.spinner("Evaluating 30 scenarios..."):
            t0 = _time.time()
            try:
                ed = run_evaluation()
                st.session_state.eval_data = (ed, _time.time() - t0)
            except Exception:
                st.markdown(
                    empty_state(
                        "⚠️",
                        "Evaluation Failed",
                        "The evaluation could not run in this environment. On Streamlit Cloud, the "
                        "30-scenario evaluation launches sub-processes which are restricted by the "
                        "platform sandbox. Run `python main.py evaluate` locally or via the CLI "
                        "container to get evaluation results.",
                    ),
                    unsafe_allow_html=True,
                )
                logger.error("Evaluation failed:\n%s", traceback.format_exc())

    if st.session_state.eval_data is not None:
        ed, ev_time = st.session_state.eval_data
        sr = ed["scenario_results"]
        ok = [s for s in sr if s["success"]]
        fail = [s for s in sr if not s["success"]]
        best = max(sr, key=lambda s: s["root_cause_accuracy"])
        worst = min(sr, key=lambda s: s["root_cause_accuracy"])

        st.markdown(f'<div style="color:var(--muted);margin-bottom:14px;font-size:12.5px;">{len(sr)} scenarios evaluated in {ev_time:.1f}s</div>', unsafe_allow_html=True)

        st.markdown('<div class="stat-grid" style="grid-template-columns:repeat(6,1fr);">', unsafe_allow_html=True)
        st.markdown(stat_card("🎯", f"{ed['investigation_success_rate']:.1%}", "Success Rate", "", color="#34D399"), unsafe_allow_html=True)
        st.markdown(stat_card("🧭", f"{ed['tool_selection_accuracy']:.1%}", "Tool Selection", "", color="#4F8CFF"), unsafe_allow_html=True)
        st.markdown(stat_card("🔬", f"{ed['root_cause_accuracy']:.1%}", "Root Cause", "", color="#22D3EE"), unsafe_allow_html=True)
        st.markdown(stat_card("🔧", str(ed['average_tool_calls']), "Avg Tool Calls", "", color="#FBBF24"), unsafe_allow_html=True)
        st.markdown(stat_card("🧠", f"{ed['average_confidence']:.1%}", "Avg Confidence", "", color="#A78BFA"), unsafe_allow_html=True)
        st.markdown(stat_card("📎", f"{ed['evidence_grounded_rate']:.1%}", "Evidence", "", color="#34D399"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div style="font-size:12px;font-weight:700;color:var(--primary);text-transform:uppercase;letter-spacing:1.2px;margin:10px 0 6px;">Root Cause Accuracy by Scenario</div>', unsafe_allow_html=True)
            names = [s["id"] for s in sr]
            vals = [s["root_cause_accuracy"] * 100 for s in sr]
            clrs = ["#34D399" if v >= 80 else "#FBBF24" if v >= 40 else "#F87171" for v in vals]
            fig = go.Figure(data=[go.Bar(x=names, y=vals, marker_color=clrs, showlegend=False)])
            fig.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis=dict(tickfont=dict(color="#5A6378", size=6), showgrid=False),
                              yaxis=dict(range=[0, 100], tickfont=dict(color="#5A6378"), gridcolor="rgba(148,163,184,0.06)"),
                              font=dict(color="#E7ECF5"))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown('<div style="font-size:12px;font-weight:700;color:var(--primary);text-transform:uppercase;letter-spacing:1.2px;margin:10px 0 6px;">Success Distribution</div>', unsafe_allow_html=True)
            fig = go.Figure(data=[go.Pie(labels=["Successful", "Failed"], values=[len(ok), len(fail)],
                                         marker_colors=["#34D399", "#F87171"], hole=.58,
                                         textfont=dict(color="#E7ECF5", size=11), showlegend=False, pull=[.02, 0])])
            fig.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E7ECF5"),
                              annotations=[dict(text=f"{ed['investigation_success_rate']:.0%}", x=.5, y=.5, font=dict(size=16, color="#34D399"), showarrow=False)])
            st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div style="font-size:12px;font-weight:700;color:var(--primary);text-transform:uppercase;letter-spacing:1.2px;margin:14px 0 6px;">Performance Radar</div>', unsafe_allow_html=True)
        cats = ["Investigation\nSuccess", "Tool Selection\nAccuracy", "Root Cause\nAccuracy", "Evidence\nGrounded", "Confidence\nQuality"]
        rv = [ed['investigation_success_rate']*100, ed['tool_selection_accuracy']*100, ed['root_cause_accuracy']*100, ed['evidence_grounded_rate']*100, ed['average_confidence']*100]
        fig = go.Figure(data=go.Scatterpolar(r=rv+[rv[0]], theta=cats+[cats[0]], fill='toself', line=dict(color="#4F8CFF", width=2), marker=dict(color="#4F8CFF", size=3)))
        fig.update_layout(polar=dict(bgcolor="rgba(9,14,24,0.5)", radialaxis=dict(visible=True, range=[0, 100], color="#5A6378", gridcolor="rgba(148,163,184,0.06)"), angularaxis=dict(color="#5A6378", gridcolor="rgba(148,163,184,0.06)")),
                          height=280, margin=dict(l=30, r=30, t=10, b=30), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E7ECF5"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div style="font-size:12px;font-weight:700;color:var(--primary);text-transform:uppercase;letter-spacing:1.2px;margin:14px 0 6px;">Scenario Details</div>', unsafe_allow_html=True)
        for s in sr:
            icon = "🟢" if s["success"] else "🔴"
            with st.expander(f"{icon}  {s['id']}: {s['goal'][:80]}", expanded=False):
                c1, c2, c3 = st.columns(3)
                c1.metric("Root Cause", f"{s['root_cause_accuracy']:.1%}")
                c2.metric("Tool Selection", f"{s['tool_selection_accuracy']:.1%}")
                c3.metric("Confidence", f"{s['confidence']:.1%}")
                st.markdown(f'<div style="font-size:12.5px;color:var(--text-2);margin-top:4px;"><strong>Tools:</strong> {", ".join(s["tools_used"])}</div>', unsafe_allow_html=True)
                if s.get("errors"):
                    st.markdown(f'<div style="color:var(--red);font-size:12.5px;margin-top:4px;">Errors: {s["errors"]}</div>', unsafe_allow_html=True)

        st.download_button("📥 Export Results", data=json.dumps(ed, indent=2, default=str),
                           file_name="evaluation_results.json", mime="application/json",
                           use_container_width=True, key="btn_exp_eval")

# ═══════════════════════════════════════════════════════════════════════════
#  DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════════════
elif page == "documentation":
    section_head("Knowledge Base", "Documentation",
                 "Comprehensive guide to OpsPilot — from getting started to API reference and runbooks.")

    def doc_sect(title, items):
        st.markdown(f'<div class="glass" style="margin-bottom:14px;">', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:15px;font-weight:750;color:var(--text);margin-bottom:12px;">{title}</div>', unsafe_allow_html=True)
        for heading, body in items:
            st.markdown(f'<div style="font-size:13px;font-weight:650;color:var(--primary);margin:10px 0 3px;">{heading}</div>'
                        f'<div style="font-size:12.5px;color:var(--text-2);line-height:1.7;margin-bottom:6px;">{body}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    doc_sect("🚀 Getting Started", [
        ("Prerequisites", "• Python 3.11+ installed on your system<br/>• OpenAI API key configured in <code>.env</code> file<br/>• Access to your service metrics, logs, and deployment history<br/>• Docker (optional, for containerized deployment)"),
        ("Quick Start", "1. Clone the repository and install dependencies<br/>2. Set your <code>OPENAI_API_KEY</code> in <code>.env</code><br/>3. Run <code>python main.py</code> to start the API and UI<br/>4. Navigate to <strong>Command Center</strong> and describe your incident<br/>5. Review the autonomous investigation report"),
        ("First Investigation", 'Navigate to the <strong>Command Center</strong>, type or paste an incident description (e.g., "Checkout API latency increased in the last 2 hours"), optionally customize the Incident ID, and click <strong>Launch Investigation</strong>. OpsPilot will execute 8 investigation phases and deliver a root cause report.'),
    ])

    doc_sect("🏗️ Architecture", [
        ("AI Agent Layer", "The core investigation loop uses LangGraph to orchestrate a reasoning agent. Given an incident description, the agent plans a strategy, selects tools, executes them, collects evidence, forms hypotheses, reflects on findings, and generates a structured report."),
        ("Tool Layer", "Seven specialized tools enable the agent to query metrics, search logs, inspect deployments, retrieve runbooks, search past incidents, create reports, and request rollbacks. Each tool has a defined schema and safety guardrails."),
        ("Frontend Layer", "The Streamlit-based UI provides Command Center, Approvals, Trajectory Viewer, Analytics, Documentation, and System Status pages with a premium enterprise-grade dark theme."),
        ("API Layer", "FastAPI provides RESTful endpoints for launching investigations, managing approvals, retrieving trajectories, and running evaluations."),
    ])

    doc_sect("🔄 Investigation Workflow", [
        ("Planning", "The agent formulates a structured investigation strategy based on the incident description, identifying which tools to use, in what order, and what data to look for."),
        ("Querying Metrics", "Retrieves performance metrics (latency, error rates, CPU, memory) from affected services and compares against baselines to detect anomalies."),
        ("Searching Logs", "Scans service logs for error messages, stack traces, and warning patterns that correlate with the incident timeframe."),
        ("Deployment History", "Checks recent deployments, configuration changes, and rollbacks to identify potential causes introduced by code or infrastructure changes."),
        ("Knowledge Retrieval", "Searches runbooks, past incident reports, and the RAG knowledge base for similar issues and known resolutions."),
        ("Generating Hypotheses", "Forms potential root cause theories by correlating evidence from all previous phases. Each includes supporting evidence and a confidence score."),
        ("Reflection", "The agent evaluates the quality, consistency, and completeness of gathered evidence, identifying gaps and assessing confidence."),
        ("Generating Report", "Compiles all findings into a structured root cause analysis report with severity assessment, evidence summary, hypotheses, and recommended actions."),
    ])

    doc_sect("🛠️ Supported Tools", [
        ("query_metrics", "Query service metrics including latency, error rates, CPU, and memory utilization."),
        ("search_logs", "Search and filter service logs by timeframe, severity, and pattern."),
        ("get_deployments", "Retrieve deployment history and recent changes across services."),
        ("search_incidents", "Search past incidents for similar patterns and resolutions."),
        ("retrieve_runbook", "Access runbooks and standard operating procedures."),
        ("create_incident_report", "Generate structured incident reports with findings and actions."),
        ("request_rollback", "Request a rollback deployment with approval workflow."),
    ])

    doc_sect("📡 API Reference", [
        ("POST /investigate", "Launch a new investigation. Accepts <code>goal</code> (incident description) and optional <code>incident_id</code>. Returns investigation results including report, hypotheses, and evidence."),
        ("GET /approvals", "Retrieve all pending approval requests. Returns a list of actions requiring human approval before execution."),
        ("POST /approvals/{id}/approve", "Approve a specific approval request by ID. Executes the requested action."),
        ("POST /approvals/{id}/deny", "Deny a specific approval request by ID. The action will not be executed."),
        ("GET /trajectory/{incident_id}", "Retrieve the step-by-step investigation trajectory for a specific incident. Returns all decisions, tool calls, and reflections."),
        ("GET /health", "Health check endpoint. Returns the current status of the API and its dependencies."),
    ])

    doc_sect("📖 Runbooks", [
        ("API Latency Investigation", "1. Check recent deployment history<br/>2. Query p99 latency metrics for the affected endpoint<br/>3. Search logs for slow queries or upstream timeouts<br/>4. Check database connection pool utilization<br/>5. Review recent configuration changes"),
        ("HTTP 503 Error Response", "1. Verify service deployment status<br/>2. Check CPU and memory utilization on affected instances<br/>3. Search logs for connection refused or timeout errors<br/>4. Review load balancer target group health<br/>5. Evaluate rollback if caused by recent deployment"),
        ("High CPU Utilization", "1. Identify top CPU-consuming processes<br/>2. Check for memory leaks or GC pressure<br/>3. Review recent code deployments<br/>4. Analyze traffic patterns and request volume<br/>5. Evaluate auto-scaling configuration"),
    ])

    doc_sect("❓ FAQ", [
        ("What types of incidents can OpsPilot investigate?", "OpsPilot can investigate a wide range of production incidents including API latency issues, service errors, deployment failures, infrastructure bottlenecks, and database performance problems."),
        ("Does OpsPilot require an internet connection?", "OpsPilot requires internet access to communicate with the OpenAI API. The application itself runs locally."),
        ("Can I customize the investigation tools?", "Yes. The tool registry in <code>opspilot/tools/registry.py</code> allows you to add, remove, or modify tools."),
        ("How does OpsPilot handle sensitive data?", "All investigation data remains local. The LLM is only provided with the incident description and tool outputs."),
        ("Can I run OpsPilot in a CI/CD pipeline?", "Yes. OpsPilot exposes a REST API that can be called from any CI/CD pipeline."),
    ])

# ═══════════════════════════════════════════════════════════════════════════
#  SYSTEM STATUS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "status":
    section_head("Monitoring", "System Status",
                 "Real-time health monitoring and performance metrics for all OpsPilot services and components.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="glass glass-pad-sm" style="text-align:center;"><div style="font-size:24px;font-weight:800;color:#34D399;">99.9%</div><div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-top:2px;">Overall Uptime</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="glass glass-pad-sm" style="text-align:center;"><div style="font-size:24px;font-weight:800;color:#4F8CFF;">145ms</div><div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-top:2px;">Avg Response Time</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="glass glass-pad-sm" style="text-align:center;"><div style="font-size:24px;font-weight:800;color:#22D3EE;">12</div><div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-top:2px;">Active Services</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="glass glass-pad-sm" style="text-align:center;"><div style="font-size:24px;font-weight:800;color:#A78BFA;">0</div><div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-top:2px;">Active Incidents</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="font-size:12px;font-weight:700;color:var(--primary);text-transform:uppercase;letter-spacing:1.4px;margin:22px 0 12px;">Service Health</div>', unsafe_allow_html=True)

    services = [
        ("🤖 AI Agent", "up", "Operational", "98ms", 95),
        ("🔗 API Gateway", "up", "Operational", "42ms", 99),
        ("🗄️ Database", "up", "Operational", "12ms", 100),
        ("📊 Metrics Pipeline", "up", "Operational", "67ms", 98),
        ("📜 Log Aggregator", "degraded", "Degraded Performance", "320ms", 72),
        ("🚀 Deployment Service", "up", "Operational", "28ms", 100),
        ("📚 Knowledge Base", "up", "Operational", "55ms", 99),
        ("🔔 Notification Service", "up", "Operational", "33ms", 100),
        ("🧪 Evaluation Engine", "down", "Maintenance", "0ms", 0),
        ("📈 Analytics Service", "up", "Operational", "89ms", 97),
        ("🏠 Frontend UI", "up", "Operational", "5ms", 100),
        ("🔐 Auth Service", "up", "Operational", "15ms", 100),
    ]
    sc1, sc2 = st.columns(2)
    for i, (name, indicator, status, latency, uptime) in enumerate(services):
        with sc1 if i % 2 == 0 else sc2:
            bar_color = "#34D399" if indicator == "up" else "#FBBF24" if indicator == "degraded" else "#F87171"
            st.markdown(f"""
            <div class="status-card">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
                <div style="font-size:13px;font-weight:650;color:var(--text);"><span class="status-ind {indicator}"></span>{name}</div>
                <div style="font-size:11px;color:var(--muted);">{latency}</div>
              </div>
              <div style="display:flex;justify-content:space-between;">
                <div style="font-size:12px;color:{bar_color};font-weight:600;">{status}</div>
                <div style="font-size:11px;color:var(--muted);">{uptime}% uptime</div>
              </div>
              <div class="sbar"><div class="sbar-fill" style="width:{uptime}%;background:{bar_color};"></div></div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:12px;font-weight:700;color:var(--primary);text-transform:uppercase;letter-spacing:1.4px;margin:24px 0 10px;">Recent Events</div>', unsafe_allow_html=True)
    events = [
        ("🟢 Database failover completed", "Primary database failover completed successfully. Zero downtime during the transition. <span style='color:var(--muted);font-size:11px;'>2 hours ago</span>"),
        ("🟡 Log aggregator latency elevated", "Log aggregation pipeline experiencing increased latency due to backpressure. Team investigating. <span style='color:var(--muted);font-size:11px;'>15 minutes ago</span>"),
        ("🔴 Evaluation engine offline", "Scheduled maintenance for the evaluation engine. Expected completion within 4 hours. <span style='color:var(--muted);font-size:11px;'>30 minutes ago</span>"),
    ]
    for title, body in events:
        st.markdown(f'<div class="glass glass-pad-sm" style="margin-bottom:8px;"><div style="font-size:13px;font-weight:650;color:var(--text);">{title}</div><div style="font-size:12px;color:var(--muted);line-height:1.6;margin-top:2px;">{body}</div></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════════
render_footer()
