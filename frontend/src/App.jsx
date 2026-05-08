import { useState, useRef, useEffect, useCallback } from "react";
import * as Chart from "chart.js";

Chart.Chart.register(
  Chart.ArcElement, Chart.BarElement, Chart.LineElement, Chart.PointElement,
  Chart.CategoryScale, Chart.LinearScale, Chart.Tooltip, Chart.Legend,
  Chart.BarController, Chart.DoughnutController, Chart.LineController
);

const API = "http://localhost:8000";

const COLORS = {
  firm: "#2563EB", forecasted: "#0D9488", overdue: "#DC2626",
  demand: "#DC2626", po: "#16A34A", inventory: "#2563EB",
};
const SERIES_PALETTE = ["#2563EB","#0D9488","#E11D48","#D97706","#7C3AED","#0891B2","#C2410C","#4F46E5","#059669","#BE185D"];

// ── Chart rendering ─────────────────────────────────────────────────────────
function useChart(canvasRef, builder, deps) {
  const inst = useRef(null);
  useEffect(() => {
    if (!canvasRef.current) return;
    if (inst.current) inst.current.destroy();
    inst.current = builder(canvasRef.current.getContext("2d"));
    return () => { if (inst.current) { inst.current.destroy(); inst.current = null; } };
  }, deps);
}

function DonutChart({ config }) {
  const ref = useRef(null);
  const segs = config.segments || [];
  useChart(ref, (ctx) => new Chart.Chart(ctx, {
    type: "doughnut",
    data: {
      labels: segs.map(s => s.name),
      datasets: [{
        data: segs.map(s => s.quantity),
        backgroundColor: segs.map(s => {
          const n = s.name.toLowerCase();
          return n.includes("firm") ? COLORS.firm : n.includes("over") ? COLORS.overdue : COLORS.forecasted;
        }),
        borderWidth: 2.5, borderColor: "rgba(255,255,255,0.9)", hoverOffset: 6,
      }],
    },
    options: {
      responsive: true, cutout: "64%",
      plugins: {
        legend: { position: "bottom", labels: { padding: 18, usePointStyle: true, pointStyleWidth: 10, font: { family: "'Outfit', sans-serif", size: 12 } } },
        tooltip: { callbacks: { label: c => { const s = segs[c.dataIndex]; return `${s.name}: ${s.quantity.toLocaleString()} units  ·  $${(s.value / 1e6).toFixed(2)}M`; } } },
      },
    },
    plugins: [{
      id: "center",
      afterDraw(chart) {
        const { ctx: c, width: w, height: h } = chart;
        c.save(); c.textAlign = "center"; c.textBaseline = "middle";
        const y = h / 2 - 12;
        c.font = "700 30px 'Outfit', sans-serif"; c.fillStyle = "#0f172a"; c.fillText((config.total_quantity || 0).toLocaleString(), w / 2, y);
        c.font = "400 11px 'Outfit', sans-serif"; c.fillStyle = "#94a3b8"; c.fillText("TOTAL ORDERS", w / 2, y + 22);
        c.restore();
      },
    }],
  }), [config]);
  return <canvas ref={ref} />;
}

function StackedBarChart({ config }) {
  const ref = useRef(null);
  const bars = config.bars || []; const series = config.series || [];
  useChart(ref, (ctx) => new Chart.Chart(ctx, {
    type: "bar",
    data: {
      labels: bars.map(b => b.label),
      datasets: series.map((name, i) => ({
        label: name, data: bars.map(b => b.stacks[name]?.quantity || 0),
        backgroundColor: SERIES_PALETTE[i % SERIES_PALETTE.length], borderRadius: 2, barPercentage: 0.75,
      })),
    },
    options: {
      responsive: true,
      scales: {
        x: { stacked: true, grid: { display: false }, ticks: { maxRotation: 50, font: { size: 10, family: "'Outfit'" } } },
        y: { stacked: true, grid: { color: "#f1f5f9" }, ticks: { font: { size: 10, family: "'Outfit'" } }, title: { display: true, text: "Quantity", font: { size: 11, family: "'Outfit'" } } },
      },
      plugins: {
        legend: { position: "bottom", labels: { padding: 16, usePointStyle: true, font: { size: 11, family: "'Outfit'" } } },
        tooltip: { callbacks: { label: c => { const st = bars[c.dataIndex]?.stacks[c.dataset.label]; return st ? `${c.dataset.label}: ${st.quantity.toLocaleString()}  ·  $${(st.value / 1e3).toFixed(0)}K` : ""; } } },
      },
    },
  }), [config]);
  return <canvas ref={ref} />;
}

function HorizontalBarChart({ config }) {
  const ref = useRef(null);
  const items = (config.items || []).slice(0, 15);
  useChart(ref, (ctx) => new Chart.Chart(ctx, {
    type: "bar",
    data: {
      labels: items.map(it => it.part),
      datasets: [{ label: "Value ($)", data: items.map(it => it.value), backgroundColor: "#2563EB99", borderColor: "#2563EB", borderWidth: 1, borderRadius: 3, barPercentage: 0.7 }],
    },
    options: {
      indexAxis: "y", responsive: true, maintainAspectRatio: false,
      scales: {
        x: { grid: { color: "#f1f5f9" }, ticks: { callback: v => "$" + (v / 1e3).toFixed(0) + "K", font: { size: 10, family: "'Outfit'" } } },
        y: { grid: { display: false }, ticks: { font: { size: 10, family: "'JetBrains Mono', monospace" } } },
      },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => `$${c.raw.toLocaleString(undefined, { minimumFractionDigits: 2 })}  ·  ${items[c.dataIndex].quantity} units` } } },
    },
  }), [config]);
  return <div style={{ height: Math.max(280, items.length * 34) }}><canvas ref={ref} /></div>;
}

function ComboChart({ config }) {
  const ref = useRef(null);
  const demand = config.demand_quantities || []; const po = config.purchase_order_quantities || []; const inv = config.inventory_values || [];
  const labels = demand.map((_, i) => `M${i + 1}`);
  useChart(ref, (ctx) => new Chart.Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        { type: "bar", label: "Demand", data: demand, backgroundColor: COLORS.demand + "66", borderColor: COLORS.demand, borderWidth: 1, borderRadius: 2, order: 2 },
        { type: "bar", label: "Purchase orders", data: po, backgroundColor: COLORS.po + "66", borderColor: COLORS.po, borderWidth: 1, borderRadius: 2, order: 2 },
        { type: "line", label: "Projected inventory", data: inv, borderColor: COLORS.inventory, backgroundColor: COLORS.inventory + "18", fill: true, tension: 0.35, pointRadius: 2.5, pointBackgroundColor: COLORS.inventory, borderWidth: 2, order: 1 },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10, family: "'Outfit'" } } },
        y: { grid: { color: "#f1f5f9" }, ticks: { font: { size: 10, family: "'Outfit'" } } },
      },
      plugins: {
        legend: { position: "bottom", labels: { padding: 16, usePointStyle: true, font: { size: 11, family: "'Outfit'" } } },
        tooltip: { mode: "index", intersect: false },
      },
    },
  }), [config]);
  return <canvas ref={ref} />;
}

function DataTable({ config }) {
  const cols = config.columns || []; const rows = config.rows || [];
  const fmt = (col, val) => {
    if (val == null) return "—";
    if (col.includes("price") || col.includes("value")) return "$" + Number(val).toLocaleString();
    if (col.includes("date") || col.includes("placement") || col.includes("arrival")) return String(val).slice(0, 10);
    if (typeof val === "number") return val.toLocaleString();
    return String(val);
  };
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0, fontSize: 12.5 }}>
        <thead>
          <tr>{cols.map(c => <th key={c} style={{ textAlign: "left", padding: "9px 12px", background: "#f8fafc", borderBottom: "2px solid #e2e8f0", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "#64748b", position: "sticky", top: 0 }}>{c.replace(/_/g, " ")}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ borderBottom: "1px solid #f1f5f9" }}>
              {cols.map(c => <td key={c} style={{ padding: "8px 12px", borderBottom: "1px solid #f1f5f9", fontFamily: c === "part" ? "'JetBrains Mono', monospace" : "inherit", fontSize: c === "part" ? 11 : 12.5 }}>{fmt(c, row[c])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ChartRenderer({ config }) {
  if (!config) return null;
  const t = config.chart_type;
  return (
    <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 10, padding: "14px 16px", marginTop: 8 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: "#475569", letterSpacing: "-0.01em" }}>{config.title}</span>
        <span style={{ fontSize: 10, color: "#94a3b8", fontFamily: "'JetBrains Mono', monospace" }}>{config.endpoint}</span>
      </div>
      {t === "donut" && <DonutChart config={config} />}
      {t === "stacked_bar" && <StackedBarChart config={config} />}
      {t === "horizontal_bar" && <HorizontalBarChart config={config} />}
      {t === "combo_bar_line" && <ComboChart config={config} />}
      {t === "table" && <DataTable config={config} />}
    </div>
  );
}

// ── Pipeline panel ──────────────────────────────────────────────────────────
function PipelinePanel({ steps }) {
  const [open, setOpen] = useState(false);
  if (!steps || steps.length === 0) return null;
  return (
    <div style={{ marginTop: 6 }}>
      <button onClick={() => setOpen(o => !o)}
        style={{ fontSize: 10, color: "#64748b", background: "none", border: "none", cursor: "pointer", padding: 0, display: "flex", alignItems: "center", gap: 4, fontFamily: "'Outfit'" }}>
        <span style={{ transform: open ? "rotate(90deg)" : "rotate(0deg)", display: "inline-block", transition: "transform 0.15s" }}>▶</span>
        {open ? "Hide" : "Show"} pipeline ({steps.length} steps)
      </button>
      {open && (
        <div style={{ marginTop: 6, padding: "8px 12px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 8, display: "flex", flexDirection: "column", gap: 4 }}>
          {steps.map((s, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#2563EB", flexShrink: 0 }} />
              <span style={{ fontSize: 11, fontWeight: 600, color: "#1e293b", minWidth: 140 }}>{s.step}</span>
              <span style={{ fontSize: 11, color: "#64748b", flex: 1 }}>{s.detail}</span>
              <span style={{ fontSize: 10, color: "#94a3b8", fontFamily: "'JetBrains Mono', monospace" }}>{s.elapsed_ms}ms</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Metadata badge ──────────────────────────────────────────────────────────
function MetaBadge({ metadata, responseTimeMs }) {
  if (!metadata && !responseTimeMs) return null;
  const fmtTime = (ms) => ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6, alignItems: "center" }}>
      {metadata?.category && <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, background: metadata.category === "Demand Planning" ? "#dbeafe" : "#d1fae5", color: metadata.category === "Demand Planning" ? "#1e40af" : "#065f46", fontWeight: 500 }}>{metadata.category}</span>}
      {metadata?.endpoint && <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, background: "#f1f5f9", color: "#475569", fontFamily: "'JetBrains Mono', monospace" }}>{metadata.endpoint}</span>}
      {metadata?.confidence_score != null && <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, background: "#fef9c3", color: "#854d0e" }}>{(metadata.confidence_score * 100).toFixed(0)}% match</span>}
      {metadata?.iterations && <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, background: "#f1f5f9", color: "#94a3b8" }}>{metadata.iterations} steps</span>}
      {responseTimeMs != null && (
        <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, background: "#f0fdf4", color: "#166534", fontFamily: "'JetBrains Mono', monospace", display: "flex", alignItems: "center", gap: 3 }}>
          ⏱ {fmtTime(responseTimeMs)}
        </span>
      )}
    </div>
  );
}

// ── Main App ────────────────────────────────────────────────────────────────
export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [activeConv, setActiveConv] = useState(null);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }); }, [messages]);
  useEffect(() => { loadConversations(); }, []);

  async function loadConversations() {
    try {
      const res = await fetch(`${API}/api/conversations`);
      const data = await res.json();
      setConversations(data.conversations || []);
    } catch { setConversations([]); }
  }

  async function startNewConversation() {
    try {
      const res = await fetch(`${API}/api/conversations`, { method: "POST" });
      const data = await res.json();
      setActiveConv(data.conversation_id);
      setMessages([]);
      setError(null);
      loadConversations();
      inputRef.current?.focus();
    } catch {
      setActiveConv("local-" + Date.now());
      setMessages([]);
    }
  }

  async function loadConversation(convId) {
    setActiveConv(convId);
    setError(null);
    try {
      const res = await fetch(`${API}/api/conversations/${convId}`);
      const data = await res.json();
      setMessages((data.messages || []).map(m => ({
        role: m.role, content: m.content,
        chart_config: m.metadata?.chart_config || null,
        metadata: m.metadata || null,
      })));
    } catch { setMessages([]); }
  }

  async function sendQuery(query) {
    if (!query.trim() || loading) return;
    setError(null);
    const userMsg = { role: "user", content: query.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), conversation_id: activeConv }),
      });

      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const result = await res.json();

      if (!activeConv && result.conversation_id) setActiveConv(result.conversation_id);

      setMessages(prev => [...prev, {
        role: "assistant",
        content: result.response,
        chart_config: result.chart_config || null,
        metadata: result.metadata || null,
        needs_clarification: result.needs_clarification || false,
        response_time_ms: result.response_time_ms || null,
        pipeline_steps: result.pipeline_steps || [],
      }]);

      loadConversations();
    } catch (err) {
      setError(err.message);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: `Unable to reach the backend at ${API}. Please ensure the FastAPI server is running:\n\ncd backend && uvicorn api.server:app --reload --port 8000`,
      }]);
    }
    setLoading(false);
  }

  async function deleteConversation(convId, e) {
    e.stopPropagation();
    try {
      await fetch(`${API}/api/conversations/${convId}`, { method: "DELETE" });
      if (activeConv === convId) { setActiveConv(null); setMessages([]); }
      loadConversations();
    } catch {}
  }

  const grouped = {};
  conversations.forEach(c => {
    const g = c.time_group || "Other";
    if (!grouped[g]) grouped[g] = [];
    grouped[g].push(c);
  });

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "'Outfit', sans-serif", background: "#f8fafc", color: "#0f172a" }}>
      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <div style={{ width: 272, background: "#0f172a", color: "#e2e8f0", display: "flex", flexDirection: "column", flexShrink: 0 }}>
        {/* Brand */}
        <div style={{ padding: "20px 18px 16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: "linear-gradient(135deg, #2563EB, #0D9488)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, fontWeight: 700, color: "#fff" }}>FT</div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600, letterSpacing: "-0.02em" }}>FactoryTwin</div>
              <div style={{ fontSize: 10, color: "#64748b", marginTop: 1 }}>Manufacturing AI assistant</div>
            </div>
          </div>
        </div>

        {/* New chat button */}
        <div style={{ padding: "0 12px 12px" }}>
          <button onClick={startNewConversation} style={{ width: "100%", padding: "10px 14px", background: "#1e293b", border: "1px solid #334155", borderRadius: 8, color: "#e2e8f0", cursor: "pointer", fontSize: 13, fontWeight: 500, fontFamily: "'Outfit'", textAlign: "left", display: "flex", alignItems: "center", gap: 8, transition: "background 0.15s" }}
            onMouseEnter={e => e.currentTarget.style.background = "#334155"} onMouseLeave={e => e.currentTarget.style.background = "#1e293b"}>
            <span style={{ fontSize: 16, lineHeight: 1 }}>+</span> New conversation
          </button>
        </div>

        {/* Conversation list */}
        <div style={{ flex: 1, overflowY: "auto", padding: "0 8px" }}>
          {Object.entries(grouped).map(([group, convs]) => (
            <div key={group}>
              <div style={{ fontSize: 10, fontWeight: 600, color: "#475569", textTransform: "uppercase", letterSpacing: "0.08em", padding: "12px 10px 4px" }}>{group}</div>
              {convs.map(c => (
                <div key={c.conversation_id} onClick={() => loadConversation(c.conversation_id)}
                  style={{ padding: "8px 10px", borderRadius: 6, cursor: "pointer", fontSize: 12, marginBottom: 1, display: "flex", alignItems: "center", justifyContent: "space-between", background: c.conversation_id === activeConv ? "#1e293b" : "transparent", color: c.conversation_id === activeConv ? "#fff" : "#94a3b8", transition: "background 0.1s" }}
                  onMouseEnter={e => { if (c.conversation_id !== activeConv) e.currentTarget.style.background = "#1e293b40"; }} onMouseLeave={e => { if (c.conversation_id !== activeConv) e.currentTarget.style.background = "transparent"; }}>
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>{c.title}</span>
                  <span onClick={(e) => deleteConversation(c.conversation_id, e)} style={{ opacity: 0.4, cursor: "pointer", fontSize: 14, marginLeft: 6, lineHeight: 1 }} title="Delete">&times;</span>
                </div>
              ))}
            </div>
          ))}
        </div>

        {/* Status */}
        <div style={{ padding: "10px 16px", borderTop: "1px solid #1e293b", fontSize: 10, color: "#475569" }}>
          Connected to {API}
        </div>
      </div>

      {/* ── Main area ───────────────────────────────────────────────── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Header */}
        <div style={{ padding: "10px 28px", borderBottom: "1px solid #e2e8f0", background: "#fff", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontSize: 14, fontWeight: 500, color: "#334155" }}>
            {activeConv ? (conversations.find(c => c.conversation_id === activeConv)?.title || "Conversation") : "FactoryTwin AI"}
          </span>
          {error && <span style={{ fontSize: 11, color: "#dc2626", padding: "2px 10px", background: "#fef2f2", borderRadius: 6 }}>Backend unreachable</span>}
        </div>

        {/* Messages */}
        <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", padding: "24px 28px" }}>
          {messages.length === 0 && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 16 }}>
              <div style={{ width: 56, height: 56, borderRadius: 14, background: "linear-gradient(135deg, #2563EB22, #0D948822)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ fontSize: 26 }}>⚙</span>
              </div>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 600, letterSpacing: "-0.02em", color: "#0f172a" }}>FactoryTwin AI assistant</div>
                <div style={{ fontSize: 13, color: "#64748b", marginTop: 6, lineHeight: 1.6 }}>Ask questions about demand planning, supply chain,<br />material shortages, and purchase orders</div>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 8, width: "100%", maxWidth: 420 }}>
                {["Show me total aggregate demand for Minneapolis",
                  "Monthly demand breakdown by platform",
                  "Material shortage analysis for Titanium Bolt",
                  "What purchase orders should I place this week?",
                  "Show me demand drill-down for January 2025"
                ].map(q => (
                  <button key={q} onClick={() => { if (!activeConv) startNewConversation().then?.(() => sendQuery(q)) || sendQuery(q); else sendQuery(q); }}
                    style={{ padding: "10px 16px", borderRadius: 8, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", fontSize: 13, color: "#475569", textAlign: "left", fontFamily: "'Outfit'", transition: "all 0.15s", lineHeight: 1.4 }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = "#2563EB"; e.currentTarget.style.color = "#2563EB"; e.currentTarget.style.background = "#eff6ff"; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = "#e2e8f0"; e.currentTarget.style.color = "#475569"; e.currentTarget.style.background = "#fff"; }}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} style={{ marginBottom: 20, display: "flex", gap: 12, flexDirection: msg.role === "user" ? "row-reverse" : "row", alignItems: "flex-start" }}>
              {/* Avatar */}
              <div style={{ width: 30, height: 30, borderRadius: 8, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 600,
                background: msg.role === "user" ? "#2563EB" : "#f1f5f9", color: msg.role === "user" ? "#fff" : "#475569",
              }}>
                {msg.role === "user" ? "U" : "AI"}
              </div>
              {/* Content */}
              <div style={{ maxWidth: 640, minWidth: 0 }}>
                <div style={{
                  padding: "12px 16px", borderRadius: 12, fontSize: 13.5, lineHeight: 1.7, whiteSpace: "pre-wrap", wordBreak: "break-word",
                  background: msg.role === "user" ? "#2563EB" : "#fff",
                  color: msg.role === "user" ? "#fff" : "#1e293b",
                  border: msg.role === "assistant" ? "1px solid #e2e8f0" : "none",
                  boxShadow: msg.role === "assistant" ? "0 1px 3px rgba(0,0,0,0.04)" : "none",
                }}>
                  {msg.content}
                </div>
                {msg.chart_config && <ChartRenderer config={msg.chart_config} />}
                {msg.role === "assistant" && <PipelinePanel steps={msg.pipeline_steps} />}
                {msg.role === "assistant" && <MetaBadge metadata={msg.metadata} responseTimeMs={msg.response_time_ms} />}
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ display: "flex", gap: 10, alignItems: "flex-start", marginBottom: 20 }}>
              <div style={{ width: 30, height: 30, borderRadius: 8, background: "#f1f5f9", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 600, color: "#475569" }}>AI</div>
              <div style={{ padding: "14px 18px", background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12 }}>
                <div style={{ display: "flex", gap: 5, alignItems: "center" }}>
                  {[0,1,2].map(i => <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: "#2563EB", animation: `bounce 1.2s ease-in-out ${i * 0.15}s infinite` }} />)}
                  <span style={{ fontSize: 12, color: "#94a3b8", marginLeft: 8 }}>Agents are processing your query...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input bar */}
        <div style={{ padding: "12px 28px 18px", borderTop: "1px solid #e2e8f0", background: "#fff" }}>
          <div style={{ display: "flex", gap: 10, maxWidth: 720, margin: "0 auto" }}>
            <input ref={inputRef} value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendQuery(input); } }}
              placeholder="Ask about your factory data..."
              disabled={loading}
              style={{ flex: 1, padding: "12px 18px", borderRadius: 10, border: "1.5px solid #cbd5e1", fontSize: 14, outline: "none", fontFamily: "'Outfit'", background: "#f8fafc", transition: "border-color 0.15s" }}
              onFocus={e => e.target.style.borderColor = "#2563EB"} onBlur={e => e.target.style.borderColor = "#cbd5e1"}
            />
            <button onClick={() => sendQuery(input)} disabled={loading || !input.trim()}
              style={{ padding: "12px 24px", borderRadius: 10, border: "none", background: "#2563EB", color: "#fff", fontWeight: 600, fontSize: 14, cursor: loading ? "not-allowed" : "pointer", fontFamily: "'Outfit'", opacity: (!input.trim() || loading) ? 0.45 : 1, transition: "opacity 0.15s, transform 0.1s", letterSpacing: "-0.01em" }}
              onMouseDown={e => { if (!loading && input.trim()) e.currentTarget.style.transform = "scale(0.97)"; }}
              onMouseUp={e => e.currentTarget.style.transform = "scale(1)"}>
              Send
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        @keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-6px)} }
        * { box-sizing: border-box; margin: 0; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
      `}</style>
    </div>
  );
}
