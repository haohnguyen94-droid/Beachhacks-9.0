// Google Fonts: Add to your HTML <head>:
// <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />

import { useState, useEffect, useCallback } from "react";

const API_BASE = "http://localhost:8080";

// ─── FALLBACK / DEFAULT DATA ──────────────────────────────────────
// Used while API hasn't returned yet or if the backend is offline.

const FALLBACK_STATS = [
  { label: "STOCKS TRACKED", value: "—" },
  { label: "STRONG SELL", value: "—" },
  { label: "STRONG BUY", value: "—" },
  { label: "AVG. CONFIDENCE", value: "—", suffix: "%" },
];

const FALLBACK_SIGNALS = [];
const FALLBACK_SECTORS = [];
const FALLBACK_HEATMAP = [];
const FALLBACK_MOVERS = [];

// ─── HELPER FUNCTIONS ─────────────────────────────────────────────
function signalColor(signal) {
  if (!signal) return "#f59e0b";
  const s = signal.toUpperCase();
  if (s === "BUY" || s === "STRONG BUY" || s === "BULLISH") return "#00c896";
  if (s === "SELL" || s === "STRONG SELL" || s === "BEARISH") return "#ef4444";
  return "#f59e0b";
}

function signalBgClass(signal) {
  if (!signal) return "bg-[#f59e0b]";
  const s = signal.toUpperCase();
  if (s === "BUY" || s === "STRONG BUY" || s === "BULLISH") return "bg-[#00c896]";
  if (s === "SELL" || s === "STRONG SELL" || s === "BEARISH") return "bg-[#ef4444]";
  return "bg-[#f59e0b]";
}

function labelBgClass(label) {
  if (!label) return "bg-[#f59e0b]";
  const l = label.toUpperCase();
  if (l === "POSITIVE") return "bg-[#00c896]";
  if (l === "NEUTRAL") return "bg-[#f59e0b]";
  return "bg-[#ef4444]";
}

function heatmapColor(value) {
  if (value > 10) return "bg-[#0d4f3c]";
  if (value > 0) return "bg-[#1a3a2e]";
  if (value === 0) return "bg-[#1e2a38]";
  if (value > -15) return "bg-[#2a1a1a]";
  return "bg-[#3d1515]";
}

function heatmapTextColor(value) {
  if (value > 0) return "text-[#00c896]";
  if (value === 0) return "text-[#8899aa]";
  return "text-[#ef4444]";
}

// ─── SUB-COMPONENTS ───────────────────────────────────────────────

function DashboardSidebar({ activeNav, setActiveNav, onAnalyze, analyzing }) {
  const navItems = [
    { id: "dashboard", label: "DASHBOARD", icon: "grid", badge: 3 },
    { id: "watchlist", label: "WATCHLIST", icon: "eye" },
    { id: "markets", label: "MARKETS", icon: "chart" },
  ];
  const accountItems = [
    { id: "profile", label: "PROFILE", icon: "user" },
    { id: "settings", label: "SETTINGS", icon: "gear" },
  ];

  return (
    <div className="w-[200px] min-w-[200px] bg-[#0b1019] flex flex-col h-full border-r border-[#1a2535]">
      <div className="px-5 pt-6 pb-8">
        <div className="font-mono text-[#00c896] text-sm font-bold tracking-wider">SENTIMENTIQ</div>
        <div className="font-mono text-[#4a5e75] text-[10px] tracking-widest mt-0.5">TERMINAL V1.0</div>
      </div>

      <nav className="flex-1 px-3">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveNav(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 text-xs font-sans tracking-wider transition-colors ${
              activeNav === item.id
                ? "bg-[#0f1d2e] text-[#00c896]"
                : "text-[#5a7088] hover:text-[#8899aa] hover:bg-[#111c2a]"
            }`}
          >
            <NavIcon type={item.icon} active={activeNav === item.id} />
            <span className="font-medium">{item.label}</span>
            {item.badge && (
              <span className="ml-auto bg-[#00c896] text-[#0b1019] text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center">
                {item.badge}
              </span>
            )}
          </button>
        ))}

        <div className="mt-8 mb-3 px-3 text-[10px] text-[#3d5268] tracking-widest font-sans">
          ACCOUNT
        </div>
        {accountItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveNav(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 text-xs font-sans tracking-wider transition-colors ${
              activeNav === item.id
                ? "bg-[#0f1d2e] text-[#00c896]"
                : "text-[#5a7088] hover:text-[#8899aa] hover:bg-[#111c2a]"
            }`}
          >
            <NavIcon type={item.icon} active={activeNav === item.id} />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="p-4">
        <button
          onClick={onAnalyze}
          disabled={analyzing}
          className={`w-full font-sans font-bold text-xs py-3 rounded-lg tracking-wider transition-colors ${
            analyzing
              ? "bg-[#1a2535] text-[#5a7088] cursor-wait"
              : "bg-[#00c896] text-[#0b1019] hover:bg-[#00b385]"
          }`}
        >
          {analyzing ? "ANALYZING..." : "+ NEW SIGNAL"}
        </button>
        <div className="flex items-center gap-3 mt-5 px-1 pb-2">
          <div className="w-8 h-8 rounded-full bg-[#1a2535] flex items-center justify-center text-[#00c896] font-mono text-xs font-bold">
            JD
          </div>
          <div>
            <div className="text-[#c8d6e5] text-xs font-sans font-medium">John Doe</div>
            <div className="text-[#3d5268] text-[10px] font-mono tracking-wider">PRO ACCOUNT</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function NavIcon({ type, active }) {
  const color = active ? "#00c896" : "#5a7088";
  const size = 16;
  if (type === "grid")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
        <rect x="1" y="1" width="6" height="6" rx="1" fill={color} />
        <rect x="9" y="1" width="6" height="6" rx="1" fill={color} />
        <rect x="1" y="9" width="6" height="6" rx="1" fill={color} />
        <rect x="9" y="9" width="6" height="6" rx="1" fill={color} />
      </svg>
    );
  if (type === "eye")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
        <ellipse cx="8" cy="8" rx="6" ry="4" stroke={color} strokeWidth="1.5" />
        <circle cx="8" cy="8" r="2" fill={color} />
      </svg>
    );
  if (type === "chart")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
        <polyline points="1,12 5,6 9,9 15,3" stroke={color} strokeWidth="1.5" fill="none" />
      </svg>
    );
  if (type === "user")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="5" r="3" stroke={color} strokeWidth="1.5" />
        <path d="M2 14c0-3 2.5-5 6-5s6 2 6 5" stroke={color} strokeWidth="1.5" fill="none" />
      </svg>
    );
  if (type === "gear")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="3" stroke={color} strokeWidth="1.5" />
        <circle cx="8" cy="8" r="6" stroke={color} strokeWidth="1.5" strokeDasharray="2 3" />
      </svg>
    );
  if (type === "overview")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
        <rect x="1" y="1" width="6" height="6" rx="1" fill={color} />
        <rect x="9" y="1" width="6" height="6" rx="1" fill={color} />
        <rect x="1" y="9" width="6" height="6" rx="1" fill={color} />
        <rect x="9" y="9" width="6" height="6" rx="1" fill={color} />
      </svg>
    );
  if (type === "sector")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="6" stroke={color} strokeWidth="1.5" />
        <path d="M8 2v6l4 4" stroke={color} strokeWidth="1.5" />
      </svg>
    );
  if (type === "correlations")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
        <path d="M2 12 L6 4 L10 8 L14 2" stroke={color} strokeWidth="1.5" fill="none" />
        <path d="M2 14 L6 8 L10 10 L14 6" stroke={color} strokeWidth="1.5" fill="none" strokeDasharray="2 2" />
      </svg>
    );
  if (type === "flows")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
        <path d="M4 12V4M8 12V7M12 12V2" stroke={color} strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  if (type === "history")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="6" stroke={color} strokeWidth="1.5" />
        <path d="M8 4v4l3 2" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    );
  return null;
}

function StatCard({ label, value, suffix }) {
  return (
    <div className="bg-[#111c2a] border border-[#1a2838] rounded-lg p-4">
      <div className="text-[10px] font-mono text-[#5a7088] tracking-widest mb-2">{label}</div>
      <div className="text-[#e8f0f8] text-3xl font-mono font-bold">
        {value}
        {suffix && <span className="text-xl text-[#5a7088]">{suffix}</span>}
      </div>
    </div>
  );
}

function SignalCard({ card, isSelected, onClick }) {
  const barColor = signalColor(card.signal);
  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-lg p-5 transition-all border ${
        isSelected
          ? "bg-[#0f2335] border-[#00c896]/40"
          : "bg-[#111c2a] border-[#1a2838] hover:border-[#2a3e55]"
      }`}
    >
      <div className="flex items-start justify-between mb-1">
        <div>
          <span className="text-[#e8f0f8] text-lg font-mono font-bold">{card.ticker}</span>
          <span className={`ml-3 text-[10px] font-mono font-bold px-2.5 py-1 rounded ${signalBgClass(card.signal)} text-[#0b1019]`}>
            {card.signal}
          </span>
        </div>
      </div>
      <div className="text-[#5a7088] text-xs font-sans mb-3">{card.company || card.name}</div>
      <div className="text-[10px] font-mono text-[#5a7088] tracking-wider mb-1.5">
        CONFIDENCE {card.confidence}%
      </div>
      <div className="w-full bg-[#1a2838] rounded-full h-1.5 mb-3">
        <div
          className="h-1.5 rounded-full transition-all"
          style={{ width: `${card.confidence}%`, backgroundColor: barColor }}
        />
      </div>
      {(card.summary || card.title) && (
        <div className="text-[#6b8299] text-xs font-sans leading-relaxed">
          {card.summary || card.title}
        </div>
      )}
    </button>
  );
}

function DetailModal({ detail, signal, onClose }) {
  // Build dynamic detail from signal data returned by the API
  const ticker = detail?.ticker || signal?.ticker || "—";
  const company = detail?.company || signal?.company || ticker;
  const direction = signal?.direction || detail?.signal || "HOLD";
  const confidence = signal?.confidence_pct || detail?.confidence || 0;
  const sourceCount = signal?.source_count || 0;
  const aggScore = signal?.aggregate_score || 0;
  const dist = signal?.score_distribution || { positive: 0, negative: 0, neutral: 0 };
  const totalDist = (dist.positive || 0) + (dist.negative || 0) + (dist.neutral || 0) || 1;

  const sentimentBreakdown = [
    { label: "POSITIVE", pct: Math.round(((dist.positive || 0) / totalDist) * 100), color: "#00c896" },
    { label: "NEUTRAL", pct: Math.round(((dist.neutral || 0) / totalDist) * 100), color: "#3b82f6" },
    { label: "NEGATIVE", pct: Math.round(((dist.negative || 0) / totalDist) * 100), color: "#ef4444" },
  ];

  // Build supporting signals from the signal's sources array, deduplicating by source_name
  const uniqueSources = [];
  const seenSources = new Set();
  for (const s of signal?.sources || []) {
    const sourceName = (s.source_name || "newsdata").toUpperCase();
    if (!seenSources.has(sourceName)) {
      seenSources.add(sourceName);
      uniqueSources.push({
        source: sourceName,
        label: (s.direction || "neutral").toUpperCase(),
        text: s.title || s.text?.slice(0, 120) || "",
        url: s.url || "#",
      });
      if (uniqueSources.length >= 3) break;
    }
  }
  const supportingSignals = uniqueSources;

  const signalLabel = confidence >= 80 ? `STRONG ${direction}` : direction;

  return (
    <div className="absolute inset-0 z-50 flex items-start justify-center pt-8 bg-[#0b1019]/80 backdrop-blur-sm">
      <div className="bg-[#111c2a] border border-[#1a2838] rounded-xl w-[900px] max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-[#1a2838]">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-[#ef4444]" />
            <span className="w-3 h-3 rounded-full bg-[#f59e0b]" />
            <span className="w-3 h-3 rounded-full bg-[#00c896]" />
            <span className="text-[#8899aa] text-xs font-mono ml-3">
              {company.toUpperCase()} ({ticker}) — {signalLabel}
            </span>
          </div>
          <button onClick={onClose} className="text-[#5a7088] text-xs font-mono hover:text-[#8899aa] flex items-center gap-1">
            ✕ Close
          </button>
        </div>

        <div className="p-8">
          {/* Ticker header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <div className="flex items-center gap-4 mb-1">
                <span className="text-[#e8f0f8] text-5xl font-mono font-bold">{ticker}</span>
                <span className={`${signalBgClass(direction)} text-[#0b1019] text-xs font-mono font-bold px-3 py-1.5 rounded`}>
                  {signalLabel}
                </span>
              </div>
              <div className="text-[#8899aa] text-lg font-sans mb-2">{company}</div>
              <div className="text-[10px] font-mono text-[#4a5e75] tracking-wider">
                {sourceCount} sources analyzed &middot; Score: {aggScore.toFixed(4)}
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] font-mono text-[#5a7088] tracking-widest mb-1">
                AGGREGATE CONFIDENCE
              </div>
              <div className="text-6xl font-mono font-bold leading-none" style={{ color: signalColor(direction) }}>
                {Math.round(confidence)}
                <span className="text-2xl align-top">%</span>
              </div>
            </div>
          </div>

          <div className="flex gap-8">
            {/* Left: AI Reasoning + Sentiment + Volume */}
            <div className="flex-1">
              {/* AI Reasoning */}
              <div className="mb-8">
                <div className="flex items-center gap-2 mb-4">
                  <span className="w-2 h-2 rounded-full bg-[#00c896]" />
                  <span className="text-[10px] font-mono text-[#5a7088] tracking-widest">
                    AI REASONING & SYNTHESIS
                  </span>
                </div>
                <p className="text-[#c8d6e5] text-sm font-sans leading-relaxed mb-4">
                  Analysis of{" "}
                  <span className="text-[#00c896] font-bold">{sourceCount} data points</span>{" "}
                  indicates a{" "}
                  <span className="font-bold" style={{ color: signalColor(direction) }}>
                    {direction === "BUY" ? "bullish" : direction === "SELL" ? "bearish" : "neutral"} trend
                  </span>{" "}
                  for {ticker}. Aggregate sentiment score of {aggScore.toFixed(4)} with{" "}
                  {Math.round(confidence)}% directional agreement across{" "}
                  {dist.positive || 0} positive, {dist.negative || 0} negative, and{" "}
                  {dist.neutral || 0} neutral signals from financial media sources.
                </p>
                <p className="text-[#c8d6e5] text-sm font-sans leading-relaxed">
                  <span className="font-bold" style={{ color: signalColor(direction) }}>
                    {signal?.signal_strength ? signal.signal_strength.charAt(0).toUpperCase() + signal.signal_strength.slice(1) : "Moderate"} conviction
                  </span>{" "}
                  based on FinBERT sentiment scoring weighted by source credibility and recency decay.
                  {signal?.forced_hold && (
                    <span className="text-[#f59e0b]"> Signal forced to HOLD: insufficient data for high-confidence directional call.</span>
                  )}
                </p>
              </div>

              {/* Sentiment Breakdown */}
              <div className="mb-8">
                <div className="text-[10px] font-mono text-[#5a7088] tracking-widest mb-4">
                  SENTIMENT BREAKDOWN
                </div>
                {sentimentBreakdown.map((s) => (
                  <div key={s.label} className="mb-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-mono font-bold" style={{ color: s.color }}>
                        {s.label}
                      </span>
                      <span className="text-xs font-mono text-[#8899aa]">{s.pct}%</span>
                    </div>
                    <div className="w-full bg-[#1a2838] rounded-full h-1.5">
                      <div
                        className="h-1.5 rounded-full"
                        style={{ width: `${s.pct}%`, backgroundColor: s.color }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Data Volume */}
              <div>
                <div className="text-[10px] font-mono text-[#5a7088] tracking-widest mb-4">
                  SIGNAL METADATA
                </div>
                <div className="flex justify-between py-2 border-b border-[#1a2838]">
                  <span className="text-xs font-sans text-[#8899aa]">Total Sources</span>
                  <span className="text-xs font-mono text-[#e8f0f8] font-medium">{sourceCount}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-[#1a2838]">
                  <span className="text-xs font-sans text-[#8899aa]">Signal Strength</span>
                  <span className="text-xs font-mono text-[#e8f0f8] font-medium">{signal?.signal_strength || "—"}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-[#1a2838]">
                  <span className="text-xs font-sans text-[#8899aa]">Majority Direction</span>
                  <span className="text-xs font-mono text-[#e8f0f8] font-medium">{signal?.majority_direction || "—"}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-xs font-sans text-[#8899aa]">Generated At</span>
                  <span className="text-xs font-mono text-[#e8f0f8] font-medium">
                    {signal?.generated_at ? new Date(signal.generated_at).toLocaleTimeString() : "—"}
                  </span>
                </div>
              </div>
            </div>

            {/* Right: Supporting Signals */}
            <div className="w-[260px]">
              <div className="text-[10px] font-mono text-[#5a7088] tracking-widest mb-4">
                SUPPORTING SIGNALS ({supportingSignals.length})
              </div>
              {supportingSignals.length === 0 && (
                <div className="text-xs font-sans text-[#3d5268]">No source details available.</div>
              )}
              {supportingSignals.map((sig, i) => (
                <div
                  key={i}
                  className="bg-[#0f1923] border border-[#1a2838] rounded-lg p-4 mb-3"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono text-[#00c896] font-bold tracking-wider">
                      {sig.source}
                    </span>
                    <span
                      className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${labelBgClass(
                        sig.label
                      )} text-[#0b1019]`}
                    >
                      {sig.label}
                    </span>
                  </div>
                  <div className="text-xs font-sans text-[#8899aa] leading-relaxed mb-3">{sig.text}</div>
                  {sig.url && sig.url !== "#" && (
                    <a
                      href={sig.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] font-mono text-[#00c896] hover:text-[#00e0a8] hover:underline transition-colors"
                    >
                      → Read full article
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MarketsSidebar({ activeMarketNav, setActiveMarketNav }) {
  const navItems = [
    { id: "overview", label: "Overview", icon: "overview" },
    { id: "sector", label: "Sector Analysis", icon: "sector" },
    { id: "correlations", label: "Correlations", icon: "correlations" },
    { id: "flows", label: "Flows", icon: "flows" },
    { id: "history", label: "History", icon: "history" },
  ];

  return (
    <div className="w-[200px] min-w-[200px] bg-[#0b1019] flex flex-col h-full border-r border-[#1a2535]">
      <div className="px-5 pt-5 pb-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-[#1a2535] flex items-center justify-center text-[#00c896] font-mono text-[9px] font-bold">
          OP_01
        </div>
        <div>
          <div className="text-[#c8d6e5] text-xs font-mono font-bold">OPERATOR_01</div>
          <div className="text-[#00c896] text-[10px] font-mono tracking-wider">TERMINAL ACTIVE</div>
        </div>
      </div>

      <nav className="flex-1 px-3">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveMarketNav(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 text-xs font-sans transition-colors ${
              activeMarketNav === item.id
                ? "bg-[#0f1d2e] text-[#00c896]"
                : "text-[#5a7088] hover:text-[#8899aa] hover:bg-[#111c2a]"
            }`}
          >
            <NavIcon type={item.icon} active={activeMarketNav === item.id} />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="p-4">
        <button className="w-full bg-[#00c896] text-[#0b1019] font-sans font-bold text-xs py-3 rounded-lg tracking-wider hover:bg-[#00b385] transition-colors">
          EXECUTE TRADE
        </button>
        <div className="flex items-center gap-3 mt-5 px-1 pb-2">
          <button className="text-[#5a7088] hover:text-[#8899aa]">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
              <text x="8" y="11" textAnchor="middle" fill="currentColor" fontSize="8">?</text>
            </svg>
          </button>
          <button className="text-[#5a7088] hover:text-[#8899aa]">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

function SentimentHeatmap({ data }) {
  const cells = data && data.length > 0 ? data : [{ label: "—", value: 0 }];
  return (
    <div className="bg-[#111c2a] border border-[#1a2838] rounded-lg p-5 mb-5">
      <div className="flex items-center gap-2 mb-4">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <rect x="1" y="1" width="4" height="4" rx="0.5" fill="#5a7088" />
          <rect x="6" y="1" width="4" height="4" rx="0.5" fill="#5a7088" />
          <rect x="1" y="6" width="4" height="4" rx="0.5" fill="#5a7088" />
          <rect x="6" y="6" width="4" height="4" rx="0.5" fill="#5a7088" />
        </svg>
        <span className="text-[10px] font-mono text-[#5a7088] tracking-widest">SENTIMENT HEATMAP</span>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {cells.map((cell) => (
          <div
            key={cell.label}
            className={`${heatmapColor(cell.value)} rounded-lg p-3 text-center`}
          >
            <div className="text-[9px] font-mono text-[#5a7088] tracking-wider mb-1">
              {cell.label}
            </div>
            <div className={`text-lg font-mono font-bold ${heatmapTextColor(cell.value)}`}>
              {cell.value > 0 ? `+${String(cell.value).padStart(2, "0")}` : cell.value === 0 ? "00" : String(cell.value)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TopMoversPanel({ data }) {
  const movers = data && data.length > 0 ? data : [];
  return (
    <div className="bg-[#111c2a] border border-[#1a2838] rounded-lg p-5 mb-5">
      <div className="flex items-center gap-2 mb-4">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <polyline points="1,10 5,4 9,7 13,2" stroke="#5a7088" strokeWidth="1.5" fill="none" />
        </svg>
        <span className="text-[10px] font-mono text-[#5a7088] tracking-widest">TOP MOVERS</span>
      </div>
      {movers.length === 0 && (
        <div className="text-xs font-sans text-[#3d5268] py-4 text-center">Run analysis to see movers</div>
      )}
      {movers.map((m) => (
        <div key={m.ticker} className="flex items-center gap-3 py-3 border-b border-[#1a2838] last:border-0">
          <div className={`w-9 h-9 rounded-lg ${m.positive ? "bg-[#0d2e25]" : "bg-[#2e1515]"} flex items-center justify-center font-mono text-xs font-bold ${m.positive ? "text-[#00c896]" : "text-[#ef4444]"}`}>
            {m.abbr}
          </div>
          <div className="flex-1">
            <div className="text-xs font-mono text-[#e8f0f8] font-bold">{m.ticker}</div>
            <div className="text-[10px] font-sans text-[#5a7088]">{m.sector}</div>
          </div>
          <div className={`text-sm font-mono font-bold ${m.positive ? "text-[#00c896]" : "text-[#ef4444]"}`}>
            {m.change}
          </div>
        </div>
      ))}
    </div>
  );
}

function AlertsFeed({ signals }) {
  // Find the most extreme negative signal for the alert
  const worst = signals && signals.length > 0
    ? signals.reduce((min, s) => (s.aggregate_score < min.aggregate_score ? s : min), signals[0])
    : null;

  return (
    <div className="bg-[#111c2a] border border-[#1a2838] rounded-lg p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm">🚨</span>
        <span className="text-[10px] font-mono text-[#5a7088] tracking-widest">ALERTS FEED</span>
      </div>
      {worst && worst.aggregate_score < 0 ? (
        <div className="flex gap-3">
          <div className="w-0.5 bg-[#ef4444] rounded-full" />
          <div>
            <div className="text-[10px] font-mono text-[#ef4444] font-bold tracking-wider mb-1">
              {worst.aggregate_score < -0.2 ? "CRITICAL DROP" : "SENTIMENT WARNING"}
            </div>
            <div className="text-xs font-sans text-[#8899aa] leading-relaxed">
              {worst.ticker} sentiment score at {worst.aggregate_score.toFixed(2)} across {worst.source_count} sources.
            </div>
            <div className="text-[10px] font-mono text-[#3d5268] mt-1">
              {worst.generated_at ? new Date(worst.generated_at).toLocaleTimeString() : "—"}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-xs font-sans text-[#3d5268] py-2">No alerts at this time.</div>
      )}
    </div>
  );
}

function TrendChart({ points, color }) {
  const chartColor = color || "#ef4444";
  const maxVal = Math.max(...points);
  const minVal = Math.min(...points);
  const range = maxVal - minVal || 1;
  const w = 540;
  const h = 120;
  const stepX = w / (points.length - 1);

  const pathPoints = points
    .map((p, i) => {
      const x = i * stepX;
      const y = h - ((p - minVal) / range) * (h - 10) - 5;
      return `${x},${y}`;
    })
    .join(" ");

  const areaPath = `M0,${h} L${pathPoints
    .split(" ")
    .map((p, i) => (i === 0 ? p : `L${p}`))
    .join(" ")} L${w},${h} Z`;

  const gradId = `trendGrad-${chartColor.replace("#", "")}`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-[120px]">
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={chartColor} stopOpacity="0.3" />
          <stop offset="100%" stopColor={chartColor} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#${gradId})`} />
      <polyline points={pathPoints} fill="none" stroke={chartColor} strokeWidth="2" />
    </svg>
  );
}

function StatusBar({ totalArticles, analyzing }) {
  return (
    <div className="h-8 bg-[#0b1019] border-t border-[#1a2535] flex items-center px-4 gap-6 text-[10px] font-mono">
      <div className="flex items-center gap-1.5">
        <span className={`w-1.5 h-1.5 rounded-full ${analyzing ? "bg-[#f59e0b] animate-pulse" : "bg-[#00c896]"}`} />
        <span className={analyzing ? "text-[#f59e0b] tracking-wider" : "text-[#00c896] tracking-wider"}>
          {analyzing ? "ANALYZING" : "TERMINAL_ACTIVE"}
        </span>
      </div>
      <div className="flex items-center gap-1.5 text-[#3d5268]">
        <span className="tracking-wider">&gt;</span>
        <span className="w-2 h-3.5 bg-[#3d5268] animate-pulse" />
      </div>
      <div className="ml-auto flex items-center gap-6 text-[#3d5268]">
        <span className="tracking-wider">ARTICLES: {totalArticles}</span>
        <span className="tracking-wider">API: {API_BASE}</span>
      </div>
    </div>
  );
}

function LoadingOverlay({ message }) {
  return (
    <div className="absolute inset-0 z-40 bg-[#0b1019]/70 backdrop-blur-sm flex items-center justify-center">
      <div className="bg-[#111c2a] border border-[#1a2838] rounded-xl p-8 text-center max-w-md">
        <div className="w-10 h-10 border-2 border-[#00c896] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <div className="text-[#00c896] font-mono text-sm font-bold tracking-wider mb-2">
          PROCESSING
        </div>
        <div className="text-[#8899aa] text-xs font-sans leading-relaxed">{message}</div>
      </div>
    </div>
  );
}

// ─── WATCHLIST VIEW ───────────────────────────────────────────────
function WatchlistView({ onSelectTicker }) {
  const [sortBy, setSortBy] = useState("score");
  const [tickerInput, setTickerInput] = useState("");
  const [watchlistSignals, setWatchlistSignals] = useState([]);
  const [adding, setAdding] = useState(false);
  const [inputError, setInputError] = useState("");

  // Load watchlist on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/watchlist`)
      .then((r) => r.json())
      .then((d) => {
        if (d.watchlist) setWatchlistSignals(d.watchlist);
      })
      .catch(() => {});
  }, []);

  const addTicker = async () => {
    const ticker = tickerInput.trim().toUpperCase();
    if (!ticker) return;

    // Client-side duplicate check
    if (watchlistSignals.some((s) => s.ticker === ticker)) {
      setInputError(`${ticker} is already in your watchlist.`);
      return;
    }

    setAdding(true);
    setInputError("");

    try {
      const resp = await fetch(`${API_BASE}/api/watchlist/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker }),
      });
      const result = await resp.json();

      if (result.error) {
        setInputError(result.error);
      } else if (result.signal) {
        setWatchlistSignals((prev) => [...prev, result.signal]);
        setTickerInput("");
      }
    } catch {
      setInputError("Failed to connect to API.");
    } finally {
      setAdding(false);
    }
  };

  const removeTicker = async (ticker) => {
    try {
      await fetch(`${API_BASE}/api/watchlist/${ticker}`, { method: "DELETE" });
      setWatchlistSignals((prev) => prev.filter((s) => s.ticker !== ticker));
    } catch {}
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") addTicker();
  };

  const sorted = [...watchlistSignals].sort((a, b) => {
    if (sortBy === "score") return Math.abs(b.aggregate_score) - Math.abs(a.aggregate_score);
    if (sortBy === "confidence") return b.confidence_pct - a.confidence_pct;
    return a.ticker.localeCompare(b.ticker);
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-xl font-sans font-bold text-[#e8f0f8] mb-1">Watchlist</h2>
          <p className="text-xs font-sans text-[#5a7088]">{watchlistSignals.length} tickers tracked</p>
        </div>
        <div className="flex gap-2">
          {["score", "confidence", "ticker"].map((s) => (
            <button
              key={s}
              onClick={() => setSortBy(s)}
              className={`px-3 py-1 rounded text-[10px] font-mono font-bold tracking-wider transition-colors ${
                sortBy === s
                  ? "bg-[#00c896] text-[#0b1019]"
                  : "bg-[#111c2a] text-[#5a7088] border border-[#1a2838]"
              }`}
            >
              {s.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Add ticker input */}
      <div className="bg-[#111c2a] border border-[#1a2838] rounded-xl p-5 mb-5">
        <div className="text-[10px] font-mono text-[#5a7088] tracking-widest mb-3">ADD TICKER TO WATCHLIST</div>
        <div className="flex gap-3">
          <input
            type="text"
            value={tickerInput}
            onChange={(e) => { setTickerInput(e.target.value.toUpperCase()); setInputError(""); }}
            onKeyDown={handleKeyDown}
            placeholder="e.g. AAPL, TSLA, NVDA..."
            disabled={adding}
            className="flex-1 bg-[#0b1019] border border-[#1a2838] rounded-lg px-4 py-2.5 text-sm font-mono text-[#e8f0f8] placeholder-[#3d5268] focus:outline-none focus:border-[#00c896] transition-colors"
          />
          <button
            onClick={addTicker}
            disabled={adding || !tickerInput.trim()}
            className={`px-6 py-2.5 rounded-lg text-xs font-mono font-bold tracking-wider transition-colors ${
              adding
                ? "bg-[#1a2535] text-[#5a7088] cursor-wait"
                : !tickerInput.trim()
                ? "bg-[#1a2535] text-[#3d5268] cursor-not-allowed"
                : "bg-[#00c896] text-[#0b1019] hover:bg-[#00b385]"
            }`}
          >
            {adding ? "ANALYZING..." : "+ ADD"}
          </button>
        </div>
        {inputError && (
          <div className="mt-2 text-xs font-mono text-[#ef4444]">{inputError}</div>
        )}
      </div>

      {watchlistSignals.length === 0 ? (
        <div className="bg-[#111c2a] border border-[#1a2838] border-dashed rounded-xl p-12 text-center">
          <div className="text-[#3d5268] text-xs font-mono tracking-widest mb-2">YOUR WATCHLIST IS EMPTY</div>
          <div className="text-[#5a7088] text-xs font-sans">Add a ticker above to analyze its sentiment and generate a signal.</div>
        </div>
      ) : (
        <div className="bg-[#111c2a] border border-[#1a2838] rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="text-[10px] font-mono text-[#3d5268] tracking-widest border-b border-[#1a2838]">
                <th className="text-left px-5 py-3 font-normal">TICKER</th>
                <th className="text-left px-5 py-3 font-normal">COMPANY</th>
                <th className="text-left px-5 py-3 font-normal">SIGNAL</th>
                <th className="text-left px-5 py-3 font-normal">CONFIDENCE</th>
                <th className="text-left px-5 py-3 font-normal">SCORE</th>
                <th className="text-left px-5 py-3 font-normal">STRENGTH</th>
                <th className="text-left px-5 py-3 font-normal">SOURCES</th>
                <th className="text-left px-5 py-3 font-normal"></th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((s) => (
                <tr
                  key={s.ticker}
                  className="border-t border-[#1a2838] cursor-pointer hover:bg-[#0f1d2e] transition-colors"
                >
                  <td className="px-5 py-3 text-xs font-mono text-[#00c896] font-bold" onClick={() => onSelectTicker(s)}>{s.ticker}</td>
                  <td className="px-5 py-3 text-xs font-sans text-[#8899aa]" onClick={() => onSelectTicker(s)}>{s.company}</td>
                  <td className="px-5 py-3" onClick={() => onSelectTicker(s)}>
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${signalBgClass(s.direction)} text-[#0b1019]`}>
                      {s.direction}
                    </span>
                  </td>
                  <td className="px-5 py-3" onClick={() => onSelectTicker(s)}>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-[#1a2838] rounded-full h-1.5">
                        <div
                          className="h-1.5 rounded-full"
                          style={{ width: `${s.confidence_pct}%`, backgroundColor: signalColor(s.direction) }}
                        />
                      </div>
                      <span className="text-xs font-mono text-[#8899aa]">{s.confidence_pct}%</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-xs font-mono" style={{ color: signalColor(s.direction) }} onClick={() => onSelectTicker(s)}>
                    {s.aggregate_score > 0 ? "+" : ""}{s.aggregate_score.toFixed(4)}
                  </td>
                  <td className="px-5 py-3 text-xs font-mono text-[#8899aa]" onClick={() => onSelectTicker(s)}>{s.signal_strength}</td>
                  <td className="px-5 py-3 text-xs font-mono text-[#8899aa]" onClick={() => onSelectTicker(s)}>{s.source_count}</td>
                  <td className="px-5 py-3">
                    <button
                      onClick={(e) => { e.stopPropagation(); removeTicker(s.ticker); }}
                      className="text-[#3d5268] hover:text-[#ef4444] transition-colors text-xs font-mono"
                      title="Remove from watchlist"
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── DASHBOARD VIEW ───────────────────────────────────────────────
function DashboardView({ data, analyzing, onAnalyze }) {
  const [activeNav, setActiveNav] = useState("dashboard");
  const [selectedCard, setSelectedCard] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [watchlistDetail, setWatchlistDetail] = useState(null);
  const [filter, setFilter] = useState("ALL");
  const [featuredOffset, setFeaturedOffset] = useState(0);

  const signals = data?.signals || FALLBACK_SIGNALS;

  // Pick 3 tickers starting at featuredOffset, wrapping around
  const cards = signals.length > 0
    ? Array.from({ length: Math.min(3, signals.length) }, (_, i) => {
        const sig = signals[(featuredOffset + i) % signals.length];
        return {
          ticker: sig.ticker,
          company: sig.company,
          signal: sig.direction,
          confidence: Math.round(sig.confidence_pct),
          summary: sig.sources?.[0]?.title || sig.sources?.[0]?.text?.slice(0, 180) || "",
          title: sig.sources?.[0]?.title || "",
          source: sig.sources?.[0]?.source_name || "",
        };
      })
    : [];

  const shuffleFeatured = () => {
    if (signals.length <= 3) return;
    setFeaturedOffset((prev) => (prev + 3) % signals.length);
  };

  const filters = ["ALL", "SELL", "BUY", "HOLD"];
  const filtered =
    filter === "ALL"
      ? cards
      : cards.filter((c) => c.signal === filter);

  const stats = data?.stats
    ? [
        { label: "STOCKS TRACKED", value: String(data.stats.stocks_tracked) },
        { label: "STRONG SELL", value: String(data.stats.strong_sell) },
        { label: "STRONG BUY", value: String(data.stats.strong_buy) },
        { label: "AVG. CONFIDENCE", value: String(data.stats.avg_confidence), suffix: "%" },
      ]
    : FALLBACK_STATS;

  // Find the full signal for the selected card (for detail modal)
  const selectedSignal = selectedCard
    ? signals.find((s) => s.ticker === selectedCard)
    : null;

  const selectedFeatured = selectedCard
    ? cards.find((f) => f.ticker === selectedCard)
    : null;

  return (
    <div className="flex h-full relative">
      <DashboardSidebar
        activeNav={activeNav}
        setActiveNav={setActiveNav}
        onAnalyze={onAnalyze}
        analyzing={analyzing}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Search bar */}
        <div className="h-14 border-b border-[#1a2535] flex items-center px-6 gap-4">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="5" stroke="#3d5268" strokeWidth="1.5" />
            <line x1="11" y1="11" x2="14" y2="14" stroke="#3d5268" strokeWidth="1.5" />
          </svg>
          <span className="text-xs font-mono text-[#3d5268] tracking-wider">
            SEARCH ASSETS, TICKERS, SIGNALS...
          </span>
          <div className="ml-auto flex items-center gap-3">
            <div className="flex items-center gap-2 bg-[#111c2a] border border-[#1a2838] rounded-lg px-3 py-1.5">
              <span className="text-[10px] font-mono text-[#5a7088] tracking-wider">MARKET STATUS</span>
              <span className="w-2 h-2 rounded-full bg-[#00c896]" />
              <span className="text-[10px] font-mono text-[#00c896] font-bold">OPEN</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-[#1a2535] flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 1v3M7 10v3M1 7h3M10 7h3" stroke="#5a7088" strokeWidth="1.5" />
              </svg>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {activeNav === "watchlist" ? (
            <WatchlistView
              onSelectTicker={(signal) => {
                setWatchlistDetail(signal);
                setShowDetail(true);
              }}
            />
          ) : (
            <>
              {/* Stats */}
              <div className="grid grid-cols-4 gap-4 mb-6">
                {stats.map((s) => (
                  <StatCard key={s.label} {...s} />
                ))}
              </div>

              {/* Filters + Shuffle */}
              <div className="flex items-center gap-2 mb-5">
                {filters.map((f) => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`px-4 py-1.5 rounded-lg text-[10px] font-mono font-bold tracking-wider transition-colors ${
                      filter === f
                        ? "bg-[#00c896] text-[#0b1019]"
                        : "bg-[#111c2a] text-[#5a7088] border border-[#1a2838] hover:border-[#2a3e55]"
                    }`}
                  >
                    {f}
                  </button>
                ))}
                {signals.length > 3 && (
                  <button
                    onClick={shuffleFeatured}
                    className="ml-auto flex items-center gap-2 px-4 py-1.5 rounded-lg text-[10px] font-mono font-bold tracking-wider bg-[#111c2a] text-[#5a7088] border border-[#1a2838] hover:border-[#00c896] hover:text-[#00c896] transition-colors"
                  >
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <path d="M1 6a5 5 0 0 1 9-3M11 6a5 5 0 0 1-9 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                      <path d="M10 1v2.5h-2.5M2 11V8.5h2.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    NEXT 3
                  </button>
                )}
              </div>

              {/* Signal cards */}
              {cards.length === 0 && !analyzing && (
                <div className="bg-[#111c2a] border border-[#1a2838] border-dashed rounded-xl p-12 text-center">
                  <div className="text-[#3d5268] text-xs font-mono tracking-widest mb-3">NO SIGNALS YET</div>
                  <div className="text-[#5a7088] text-sm font-sans mb-6">
                    Click "+ NEW SIGNAL" to fetch 50 articles from NewsData, score them with FinBERT, and generate live signals.
                  </div>
                  <button
                    onClick={onAnalyze}
                    className="bg-[#00c896] text-[#0b1019] font-sans font-bold text-xs px-8 py-3 rounded-lg tracking-wider hover:bg-[#00b385] transition-colors"
                  >
                    RUN ANALYSIS
                  </button>
                </div>
              )}

              <div className="flex flex-col gap-3">
                {filtered.map((card) => (
                  <SignalCard
                    key={card.ticker}
                    card={card}
                    isSelected={selectedCard === card.ticker}
                    onClick={() => {
                      setSelectedCard(card.ticker);
                      setShowDetail(true);
                    }}
                  />
                ))}
              </div>
            </>
          )}
        </div>

        <StatusBar totalArticles={data?.total_articles || 0} analyzing={analyzing} />
      </div>

      {analyzing && (
        <LoadingOverlay message="Orchestrator is fetching 50 articles from NewsData.io, scoring each with FinBERT sentiment analysis, and aggregating into trading signals..." />
      )}

      {showDetail && selectedCard && selectedSignal && (
        <DetailModal
          detail={selectedFeatured}
          signal={selectedSignal}
          onClose={() => setShowDetail(false)}
        />
      )}

      {showDetail && watchlistDetail && (
        <DetailModal
          detail={{ ticker: watchlistDetail.ticker, company: watchlistDetail.company }}
          signal={watchlistDetail}
          onClose={() => { setShowDetail(false); setWatchlistDetail(null); }}
        />
      )}
    </div>
  );
}

// ─── MARKETS VIEW ─────────────────────────────────────────────────
function MarketsView({ data }) {
  const [activeMarketNav, setActiveMarketNav] = useState("overview");

  const sectors = data?.sectors || FALLBACK_SECTORS;
  const heatmap = data?.heatmap || FALLBACK_HEATMAP;
  const movers = data?.top_movers || FALLBACK_MOVERS;
  const signals = data?.signals || FALLBACK_SIGNALS;
  const totalArticles = data?.total_articles || 0;

  const sectorNames = sectors.map((s) => s.name);
  const [activeSector, setActiveSector] = useState(sectorNames[0] || "Technology");

  const currentSector = sectors.find((s) => s.name === activeSector) || sectors[0];

  // Build synthetic trend points from the sector score
  const trendPoints = currentSector
    ? Array.from({ length: 15 }, (_, i) => {
        const base = (currentSector.avg_score || 0) * 50 + 50;
        const noise = Math.sin(i * 0.7) * 8 + Math.cos(i * 1.3) * 5;
        return Math.max(5, Math.min(95, base + noise + (i - 7) * (currentSector.avg_score || 0) * 3));
      })
    : [50, 50, 50, 50, 50];

  const trendColor = currentSector && currentSector.avg_score >= 0 ? "#00c896" : "#ef4444";

  const hasData = sectors.length > 0;

  return (
    <div className="flex h-full">
      <MarketsSidebar
        activeMarketNav={activeMarketNav}
        setActiveMarketNav={setActiveMarketNav}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Top nav */}
        <div className="h-14 border-b border-[#1a2535] flex items-center px-6">
          <span className="font-mono text-[#00c896] text-sm font-bold tracking-wider mr-8">
            KINETIC LEDGER
          </span>
          {["MARKETS", "SENTIMENT", "PORTFOLIO", "TERMINAL"].map((item) => (
            <button
              key={item}
              className={`text-xs font-sans font-medium tracking-wider px-4 py-1 mr-2 transition-colors ${
                item === "MARKETS"
                  ? "text-[#00c896] border-b-2 border-[#00c896]"
                  : "text-[#5a7088] hover:text-[#8899aa]"
              }`}
            >
              {item}
            </button>
          ))}
          <div className="ml-auto flex items-center gap-4">
            <button className="text-[#5a7088] hover:text-[#8899aa]">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M9 2v3M9 13v3M2 9h3M13 9h3" stroke="currentColor" strokeWidth="1.5" />
                <circle cx="9" cy="2" r="1" fill="currentColor" />
              </svg>
            </button>
            <button className="text-[#5a7088] hover:text-[#8899aa]">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="9" r="3" stroke="currentColor" strokeWidth="1.5" />
                <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5" strokeDasharray="2 3" />
              </svg>
            </button>
            <button className="text-[#5a7088] hover:text-[#8899aa]">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5" />
                <circle cx="9" cy="7" r="2.5" stroke="currentColor" strokeWidth="1.5" />
                <path d="M4 15c0-2.5 2-4.5 5-4.5s5 2 5 4.5" stroke="currentColor" strokeWidth="1.5" />
              </svg>
            </button>
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Main content */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* Header */}
            <h1 className="text-3xl font-sans font-bold text-[#e8f0f8] mb-2">Sectors</h1>
            <p className="text-xs font-sans text-[#5a7088] mb-5">
              AI-powered sentiment across every market sector — updated every 15 minutes.
            </p>
            <div className="flex items-center gap-8 mb-6">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#00c896]" />
                <span className="text-xs font-mono text-[#e8f0f8] font-bold">{sectors.length} Sectors</span>
                <span className="text-xs font-mono text-[#5a7088]">Tracked</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#00c896]" />
                <span className="text-xs font-mono text-[#e8f0f8] font-bold">{totalArticles}</span>
                <span className="text-xs font-mono text-[#5a7088]">Articles Analyzed</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#f59e0b]" />
                <span className="text-xs font-mono text-[#e8f0f8] font-bold">Last updated</span>
                <span className="text-xs font-mono text-[#5a7088]">just now</span>
              </div>
            </div>

            {!hasData && (
              <div className="bg-[#111c2a] border border-[#1a2838] border-dashed rounded-xl p-12 text-center">
                <div className="text-[#3d5268] text-xs font-mono tracking-widest mb-3">NO SECTOR DATA</div>
                <div className="text-[#5a7088] text-sm font-sans">
                  Run the analysis from the Dashboard to populate market sector data.
                </div>
              </div>
            )}

            {hasData && (
              <>
                {/* Sector tabs */}
                <div className="flex gap-2 mb-6 flex-wrap">
                  {sectorNames.map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveSector(tab)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-sans font-medium transition-colors border ${
                        activeSector === tab
                          ? "bg-[#00c896]/15 text-[#00c896] border-[#00c896]/40"
                          : "bg-[#111c2a] text-[#8899aa] border-[#1a2838] hover:border-[#2a3e55]"
                      }`}
                    >
                      <span
                        className={`w-2 h-2 rounded-full ${
                          activeSector === tab ? "bg-[#00c896]" : "bg-[#5a7088]"
                        }`}
                      />
                      {tab}
                    </button>
                  ))}
                </div>

                {/* Sector detail card */}
                {currentSector && (
                  <div className="bg-[#111c2a] border border-[#1a2838] rounded-xl p-6 mb-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h2 className="text-2xl font-sans font-bold text-[#e8f0f8] mb-2">
                          {currentSector.name}
                        </h2>
                        <div className="flex items-center gap-3">
                          <span className={`${signalBgClass(currentSector.sentiment)} text-[#0b1019] text-[10px] font-mono font-bold px-2.5 py-1 rounded`}>
                            {currentSector.sentiment}
                          </span>
                          <span className="text-xs font-mono text-[#5a7088]">
                            CONFIDENCE {currentSector.confidence}%
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] font-mono text-[#5a7088] tracking-widest mb-1">
                          24H IMPACT
                        </div>
                        <div className="text-2xl font-mono font-bold" style={{ color: signalColor(currentSector.sentiment) }}>
                          {currentSector.impact}
                        </div>
                      </div>
                    </div>

                    {/* Stats row */}
                    <div className="grid grid-cols-4 gap-4 mb-6">
                      <div className="bg-[#0f1923] border border-[#1a2838] rounded-lg p-4">
                        <div className="text-[9px] font-mono text-[#5a7088] tracking-widest mb-2">BEARISH SIGNALS</div>
                        <div className="text-2xl font-mono font-bold text-[#e8f0f8]">{currentSector.stats?.bearish || 0}</div>
                      </div>
                      <div className="bg-[#0f1923] border border-[#1a2838] rounded-lg p-4">
                        <div className="text-[9px] font-mono text-[#5a7088] tracking-widest mb-2">BULLISH SIGNALS</div>
                        <div className="text-2xl font-mono font-bold text-[#e8f0f8]">{currentSector.stats?.bullish || 0}</div>
                      </div>
                      <div className="bg-[#0f1923] border border-[#1a2838] rounded-lg p-4">
                        <div className="text-[9px] font-mono text-[#5a7088] tracking-widest mb-2">NEUTRAL FLUX</div>
                        <div className="text-2xl font-mono font-bold text-[#e8f0f8]">{currentSector.stats?.neutral || 0}</div>
                      </div>
                      <div className="bg-[#0f1923] border border-[#1a2838] rounded-lg p-4">
                        <div className="text-[9px] font-mono text-[#5a7088] tracking-widest mb-2">AVG CONF. SCORE</div>
                        <div className="text-2xl font-mono font-bold text-[#e8f0f8]">{currentSector.stats?.avg_conf || "—"}</div>
                      </div>
                    </div>

                    {/* 30D Trend */}
                    <div className="mb-2">
                      <div className="text-[10px] font-mono text-[#5a7088] tracking-widest mb-3">
                        SENTIMENT TREND
                      </div>
                      <TrendChart points={trendPoints} color={trendColor} />
                    </div>
                  </div>
                )}

                {/* Constituent Performance */}
                {currentSector && currentSector.constituents && (
                  <div className="bg-[#111c2a] border border-[#1a2838] rounded-xl p-6">
                    <div className="flex items-center justify-between mb-5">
                      <div className="text-[10px] font-mono text-[#5a7088] tracking-widest">
                        CONSTITUENT PERFORMANCE
                      </div>
                      <button className="text-xs font-mono text-[#00c896] hover:text-[#00b385] tracking-wider">
                        VIEW FULL LEDGER
                      </button>
                    </div>
                    <table className="w-full">
                      <thead>
                        <tr className="text-[10px] font-mono text-[#3d5268] tracking-widest">
                          <th className="text-left pb-3 font-normal">TICKER</th>
                          <th className="text-left pb-3 font-normal">COMPANY NAME</th>
                          <th className="text-left pb-3 font-normal">SIGNAL</th>
                          <th className="text-left pb-3 font-normal">CONF %</th>
                          <th className="text-left pb-3 font-normal">SCORE</th>
                          <th className="text-left pb-3 font-normal">24H CHG</th>
                        </tr>
                      </thead>
                      <tbody>
                        {currentSector.constituents.map((c) => (
                          <tr key={c.ticker} className="border-t border-[#1a2838]">
                            <td className="py-3 text-xs font-mono text-[#00c896] font-bold">{c.ticker}</td>
                            <td className="py-3 text-xs font-sans text-[#8899aa]">{c.name}</td>
                            <td className="py-3">
                              <span
                                className="text-xs font-mono font-bold"
                                style={{ color: signalColor(c.signal) }}
                              >
                                {c.signal}
                              </span>
                            </td>
                            <td className="py-3 text-xs font-mono text-[#8899aa]">{c.conf}</td>
                            <td className="py-3 text-xs font-mono text-[#00c896]">{c.score}</td>
                            <td className="py-3 text-xs font-mono text-[#8899aa]">{c.change}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Right sidebar */}
          <div className="w-[300px] min-w-[300px] border-l border-[#1a2535] overflow-y-auto p-5">
            <SentimentHeatmap data={heatmap} />
            <TopMoversPanel data={movers} />
            <AlertsFeed signals={signals} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── ROOT COMPONENT ───────────────────────────────────────────────
export default function SentimentIQ() {
  const [view, setView] = useState("dashboard");
  const [data, setData] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  // Try to load cached results on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/results`)
      .then((r) => r.json())
      .then((d) => {
        if (!d.error) setData(d);
      })
      .catch(() => {});
  }, []);

  const runAnalysis = useCallback(async () => {
    setAnalyzing(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/api/analyze`, { method: "POST" });
      const result = await resp.json();
      if (result.error) {
        setError(result.error);
      } else {
        setData(result);
      }
    } catch (err) {
      setError(`Failed to connect to API at ${API_BASE} — is the backend running?`);
    } finally {
      setAnalyzing(false);
    }
  }, []);

  return (
    <div className="w-full h-screen bg-[#0d1117] text-[#e8f0f8] font-sans flex flex-col overflow-hidden">
      {/* View toggle + status */}
      <div className="h-10 bg-[#080c14] border-b border-[#1a2535] flex items-center px-4 gap-2 shrink-0">
        <button
          onClick={() => setView("dashboard")}
          className={`px-4 py-1 rounded text-[10px] font-mono font-bold tracking-widest transition-colors ${
            view === "dashboard"
              ? "bg-[#00c896] text-[#0b1019]"
              : "text-[#5a7088] hover:text-[#8899aa]"
          }`}
        >
          DASHBOARD
        </button>
        <button
          onClick={() => setView("markets")}
          className={`px-4 py-1 rounded text-[10px] font-mono font-bold tracking-widest transition-colors ${
            view === "markets"
              ? "bg-[#00c896] text-[#0b1019]"
              : "text-[#5a7088] hover:text-[#8899aa]"
          }`}
        >
          MARKETS
        </button>

        {data && (
          <span className="ml-4 text-[10px] font-mono text-[#3d5268] tracking-wider">
            {data.total_articles} articles / {data.total_tickers} tickers
          </span>
        )}

        {error && (
          <span className="ml-4 text-[10px] font-mono text-[#ef4444] tracking-wider">
            {error}
          </span>
        )}
      </div>

      <div className="flex-1 overflow-hidden">
        {view === "dashboard" ? (
          <DashboardView data={data} analyzing={analyzing} onAnalyze={runAnalysis} />
        ) : (
          <MarketsView data={data} />
        )}
      </div>
    </div>
  );
}
