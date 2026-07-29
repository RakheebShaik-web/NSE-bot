"use client";

import { useMemo, useState } from "react";

type Period = "1Y" | "3Y" | "ALL";

const years = [
  { year: "2020", strategy: 31.4, nifty: 14.9 },
  { year: "2021", strategy: 38.7, nifty: 24.1 },
  { year: "2022", strategy: -8.6, nifty: 4.3 },
  { year: "2023", strategy: 27.9, nifty: 20.0 },
  { year: "2024", strategy: 22.6, nifty: 8.8 },
  { year: "2025", strategy: 16.8, nifty: 10.4 },
  { year: "2026", strategy: 9.2, nifty: 4.8 },
];

const trades = [
  ["12 Jul 2026", "TRENT", "Consumer", "91.8", "₹5,412", "₹5,793", "+7.04%", "Time exit"],
  ["12 Jul 2026", "BEL", "Industrials", "89.6", "₹426", "₹449", "+5.40%", "Time exit"],
  ["28 Jun 2026", "COFORGE", "Technology", "87.9", "₹1,742", "₹1,656", "−4.94%", "ATR stop"],
  ["28 Jun 2026", "M&M", "Automobile", "86.7", "₹3,176", "₹3,339", "+5.13%", "Time exit"],
  ["14 Jun 2026", "BHARTIARTL", "Telecom", "85.4", "₹1,986", "₹2,078", "+4.63%", "Time exit"],
  ["31 May 2026", "DIXON", "Consumer", "84.2", "₹15,420", "₹14,801", "−4.01%", "ATR stop"],
];

const factors = [
  ["6M momentum", 30, "+0.041"],
  ["12M momentum", 25, "+0.036"],
  ["3M momentum", 15, "+0.028"],
  ["20D relative strength", 10, "+0.019"],
  ["Relative volume", 10, "+0.014"],
  ["Liquidity", 5, "+0.008"],
  ["Low volatility", 5, "+0.011"],
];

const equityAll = [100,104,101,109,116,113,128,137,132,148,161,157,174,191,183,207,225,219,244,271,263,289,318,306,342,371,363,405,438,427,469,512];
const niftyAll = [100,102,98,106,111,108,117,123,119,128,136,132,142,151,146,157,166,162,174,185,181,191,203,198,211,223,219,231,242,238,250,261];
const drawdowns = [0,-1,-6,-1,0,-3,0,0,-4,0,0,-3,0,0,-4,0,0,-3,0,0,-3,0,0,-4,0,0,-2,0,0,-3,0,0];

function points(values: number[], width = 1000, height = 260, pad = 12) {
  const min = Math.min(...values), max = Math.max(...values);
  return values.map((v, i) => {
    const x = pad + (i / (values.length - 1)) * (width - pad * 2);
    const y = height - pad - ((v - min) / Math.max(max - min, 1)) * (height - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
}

function Shell({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`shell ${className}`}><div className="core">{children}</div></div>;
}

export default function Home() {
  const [period, setPeriod] = useState<Period>("ALL");
  const [section, setSection] = useState("Overview");
  const series = useMemo(() => {
    const n = period === "1Y" ? 9 : period === "3Y" ? 18 : equityAll.length;
    return { equity: equityAll.slice(-n), nifty: niftyAll.slice(-n) };
  }, [period]);

  return (
    <main>
      <div className="grain" />
      <nav className="island" aria-label="Primary">
        <button className="brand" onClick={() => setSection("Overview")}><span className="brand-mark">L</span>LEADER / INDIA</button>
        <div className="nav-links">
          {["Overview", "Trades", "Factors", "Validation"].map((item) => (
            <button key={item} className={section === item ? "active" : ""} onClick={() => {
              setSection(item);
              document.getElementById(item.toLowerCase())?.scrollIntoView({ behavior: "smooth" });
            }}>{item}</button>
          ))}
        </div>
        <div className="live"><span /> RESEARCH BUILD</div>
      </nav>

      <header className="hero reveal">
        <div>
          <span className="eyebrow">NIFTY 500 · MOMENTUM RESEARCH</span>
          <h1>Signal quality,<br /><em>without the fiction.</em></h1>
        </div>
        <div className="hero-note">
          <p>Point-in-time universe. Next-open execution. Conservative costs. Every result designed to survive contact with the Indian market.</p>
          <div className="asof">AS OF <strong>30 JUL 2026</strong></div>
        </div>
      </header>

      <section id="overview" className="overview-grid reveal">
        <Shell className="equity-card">
          <div className="card-head">
            <div><span className="label">PORTFOLIO EQUITY</span><h2>₹5.12L <small>from ₹1.00L</small></h2></div>
            <div className="periods">{(["1Y","3Y","ALL"] as Period[]).map(p => <button key={p} onClick={() => setPeriod(p)} className={period===p?"selected":""}>{p}</button>)}</div>
          </div>
          <div className="chart-wrap">
            <div className="axis"><span>₹5L</span><span>₹3L</span><span>₹1L</span></div>
            <svg viewBox="0 0 1000 260" role="img" aria-label="Strategy and NIFTY 50 equity curves">
              <defs>
                <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#b8ff6a" stopOpacity=".22"/><stop offset="1" stopColor="#b8ff6a" stopOpacity="0"/></linearGradient>
              </defs>
              {[25,80,135,190,245].map(y=><line key={y} x1="10" x2="990" y1={y} y2={y} className="gridline"/>)}
              <polygon points={`12,248 ${points(series.equity)} 988,248`} fill="url(#fill)"/>
              <polyline points={points(series.nifty)} className="nifty-line"/>
              <polyline points={points(series.equity)} className="strategy-line"/>
            </svg>
            <div className="legend"><span className="strategy-dot"/> Leader India <strong>+412%</strong><span className="nifty-dot"/> NIFTY 50 <strong>+161%</strong></div>
          </div>
        </Shell>

        <div className="metric-stack">
          <Shell><div className="metric"><span>CAGR</span><strong>24.9%</strong><small>vs 14.8% benchmark</small></div></Shell>
          <Shell><div className="metric"><span>MAX DRAWDOWN</span><strong className="amber">−18.6%</strong><small>Recovery: 94 sessions</small></div></Shell>
          <Shell><div className="metric"><span>OOS SHARPE</span><strong>1.31</strong><small>Target threshold: 1.00</small></div></Shell>
        </div>

        <Shell className="status-card">
          <div className="status-inner">
            <span className="label">MODEL STATUS</span>
            <div className="status-orbit"><div><b>7</b><small>factors</small></div></div>
            <h3>Accuracy-first configuration</h3>
            <p>No leverage · ₹5Cr liquidity floor · 10-session hold · 2.5× ATR stop</p>
            <div className="regime"><span>MARKET REGIME</span><strong><i/> RISK ON</strong></div>
          </div>
        </Shell>
      </section>

      <section className="section reveal">
        <div className="section-title"><div><span className="eyebrow">DOWNSIDE ANATOMY</span><h2>Drawdown, made visible.</h2></div><p>Underwater periods measured from the previous portfolio high. Lower and shorter is better.</p></div>
        <Shell>
          <div className="drawdown-core">
            <div className="dd-stat"><strong>−18.6%</strong><span>WORST DECLINE</span></div>
            <svg viewBox="0 0 1000 180" role="img" aria-label="Portfolio drawdown curve">
              <line x1="12" x2="988" y1="18" y2="18" className="zero"/>
              <polygon points={`12,18 ${drawdowns.map((v,i)=>`${12+i/(drawdowns.length-1)*976},${18+Math.abs(v)*7}`).join(" ")} 988,18`} className="dd-fill"/>
              <polyline points={drawdowns.map((v,i)=>`${12+i/(drawdowns.length-1)*976},${18+Math.abs(v)*7}`).join(" ")} className="dd-line"/>
            </svg>
          </div>
        </Shell>
      </section>

      <section id="validation" className="section split reveal">
        <div>
          <span className="eyebrow">YEAR-BY-YEAR</span>
          <h2>Consistency over spectacle.</h2>
          <p className="lede">A credible model should not depend on one miraculous year. Negative years remain visible.</p>
        </div>
        <Shell>
          <div className="year-table">
            <div className="year-row header"><span>YEAR</span><span>LEADER</span><span>NIFTY 50</span><span>ALPHA</span></div>
            {years.map(y => <div className="year-row" key={y.year}><strong>{y.year}</strong><span className={y.strategy>=0?"positive":"negative"}>{y.strategy>0?"+":""}{y.strategy}%</span><span>{y.nifty>0?"+":""}{y.nifty}%</span><b>{(y.strategy-y.nifty)>0?"+":""}{(y.strategy-y.nifty).toFixed(1)}%</b></div>)}
          </div>
        </Shell>
      </section>

      <section id="trades" className="section reveal">
        <div className="section-title"><div><span className="eyebrow">TRADE LEDGER</span><h2>Every position, auditable.</h2></div><button className="export">Export CSV <span>↗</span></button></div>
        <Shell>
          <div className="table-wrap">
            <table><thead><tr>{["ENTRY","SYMBOL","SECTOR","SCORE","ENTRY","EXIT","NET P&L","REASON"].map(h=><th key={h}>{h}</th>)}</tr></thead>
            <tbody>{trades.map((r,i)=><tr key={i}>{r.map((v,j)=><td key={j} className={j===6?(v.includes("+")?"positive":"negative"):""}>{v}</td>)}</tr>)}</tbody></table>
          </div>
        </Shell>
      </section>

      <section id="factors" className="section split factors reveal">
        <div>
          <span className="eyebrow">FACTOR DIAGNOSTICS</span>
          <h2>Built on evidence,<br/>not decoration.</h2>
          <p className="lede">Weights prioritize NSE-supported medium-term momentum. IC values shown here are presentation data until your point-in-time dataset is connected.</p>
          <div className="warning">DEMO DATA <span>Replace with verified walk-forward outputs before making capital decisions.</span></div>
        </div>
        <Shell>
          <div className="factor-list">
            <div className="factor-head"><span>FACTOR</span><span>WEIGHT</span><span>OOS IC</span></div>
            {factors.map(([name,weight,ic])=><div className="factor" key={name}><span>{name}</span><div className="bar"><i style={{transform:`scaleX(${Number(weight)/30})`}}/></div><strong>{weight}%</strong><b>{ic}</b></div>)}
          </div>
        </Shell>
      </section>

      <footer><div><span className="brand-mark">L</span><strong>LEADER SCORE INDIA</strong></div><p>Hypothetical research · Not investment advice · Results shown are illustrative demo data</p><span>v0.1 / INDIA</span></footer>
    </main>
  );
}
