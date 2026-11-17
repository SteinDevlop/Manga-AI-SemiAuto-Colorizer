/* SUMI Home — landing page from main.html mockup. */

import { useEffect, useState } from "react";

export default function Home() {
  // Scroll reveal
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  // Comparison slider
  const [split, setSplit] = useState(50);
  const [dragging, setDragging] = useState(false);

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    setDragging(true);
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const val = ((e.clientX - rect.left) / rect.width) * 100;
    setSplit(Math.min(95, Math.max(5, val)));
  };

  const handlePointerUp = () => {
    setDragging(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowLeft") {
      setSplit((s) => Math.max(5, s - 5));
    } else if (e.key === "ArrowRight") {
      setSplit((s) => Math.min(95, s + 5));
    }
  };

  // Gallery filter
  const [filter, setFilter] = useState("all");

  const categories = [
    { id: "all", label: "All" },
    { id: "action", label: "Action" },
    { id: "fantasy", label: "Fantasy" },
    { id: "romance", label: "Romance" },
    { id: "portrait", label: "Portraits" },
    { id: "cinematic", label: "Cinematic" },
  ];

  const exhibits = [
    { id: "1", title: "Blade of the Seventh Gate", cat: "action", ratio: "ratio-tall" },
    { id: "2", title: "Aether Observatory", cat: "fantasy", ratio: "ratio-wide" },
    { id: "3", title: "Platform 4, After Rain", cat: "romance", ratio: "ratio-medium" },
    { id: "4", title: "Kurogane", cat: "portrait", ratio: "ratio-medium" },
    { id: "5", title: "Shinjuku Midnight", cat: "cinematic", ratio: "ratio-medium" },
  ];

  return (
    <div className="page home">
      {/* Hero Section */}
      <section className="hero">
        <div className="container hero-spread">
          <div className="hero-left reveal">
            <div className="hero-meta-row">
              <span className="accent-bar" aria-hidden="true">
                <span style={{ background: "var(--vermilion)" }} />
                <span style={{ background: "var(--electric)" }} />
                <span style={{ background: "var(--saffron)" }} />
              </span>
              <span className="mono-label">AI-Powered Manga Colorization</span>
            </div>

            <h1 className="hero-title">
              Color <em>changes</em> everything.
            </h1>

            <p className="hero-text">
              Your favorite manga, reimagined in color. Preserve the original art. Experience a new dimension.
            </p>

            <div className="hero-actions">
              <button type="button" className="btn-vermilion" onClick={() => {}}>
                Start Colorizing
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <path d="M3 8H13M13 8L9 4M13 8L9 12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>

            <div className="hero-annotations">
              <span className="mono-label">CH. 00 // OPENING SPREAD</span>
              <span className="mono-label">G-PEN &amp; SCREENTONE FIDELITY</span>
            </div>
          </div>

          <div className="hero-visual reveal">
            <div className="hero-plate-frame">
              <span className="plate-corner-tag">PLATE 00 // TOKYO DUSK</span>
              <div className="hero-plate-inner">
                <svg viewBox="0 0 560 616" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" aria-label="Colorized manga illustration overlooking Tokyo at twilight">
                  <defs>
                    <linearGradient id="heroSky" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#19284f" />
                      <stop offset="46%" stopColor="#315bea" />
                      <stop offset="76%" stopColor="#f04438" />
                      <stop offset="100%" stopColor="#f2c94c" />
                    </linearGradient>
                    <pattern id="heroTone" width="5" height="5" patternUnits="userSpaceOnUse">
                      <circle cx="2" cy="2" r="0.85" fill="#111111" opacity="0.16" />
                    </pattern>
                  </defs>
                  <rect width="560" height="616" fill="url(#heroSky)" />
                  <rect width="560" height="320" fill="url(#heroTone)" />
                  <circle cx="150" cy="295" r="76" fill="#fff8e1" opacity="0.85" />
                  <path d="M-15 270 Q55 188 135 230 Q205 155 295 198 Q380 142 465 195 Q525 170 575 215 L575 350 L-15 350 Z" fill="#fef3d6" stroke="#111111" strokeWidth="2" />
                  <path d="M35 288 Q115 245 205 275 Q295 230 390 272 Q465 240 535 282" fill="none" stroke="#f04438" strokeWidth="5" opacity="0.45" />
                  <path d="M0 400 L0 322 L42 322 L42 350 L76 350 L76 294 L120 294 L120 356 L160 356 L160 314 L214 314 L214 352 L272 352 L272 288 L322 288 L322 342 L386 342 L386 306 L444 306 L444 345 L498 345 L498 298 L560 298 L560 400 Z" fill="#1b2440" stroke="#111111" strokeWidth="2" />
                  <g fill="#f2c94c">
                    <rect x="88" y="310" width="6" height="8" />
                    <rect x="102" y="310" width="6" height="8" />
                    <rect x="284" y="304" width="7" height="9" />
                    <rect x="300" y="304" width="7" height="9" />
                    <rect x="398" y="322" width="6" height="8" />
                    <rect x="514" y="314" width="7" height="9" />
                  </g>
                  <path d="M0 95 Q240 160 560 74" fill="none" stroke="#111111" strokeWidth="1.6" opacity="0.7" />
                  <path d="M0 122 Q265 190 560 116" fill="none" stroke="#111111" strokeWidth="1.2" opacity="0.55" />
                  <rect x="0" y="400" width="560" height="216" fill="#d9d5cc" stroke="#111111" strokeWidth="2.4" />
                  <line x1="0" y1="364" x2="560" y2="364" stroke="#111111" strokeWidth="2.4" />
                  <g stroke="#111111" strokeWidth="2">
                    <line x1="48" y1="364" x2="48" y2="400" />
                    <line x1="148" y1="364" x2="148" y2="400" />
                    <line x1="248" y1="364" x2="248" y2="400" />
                    <line x1="448" y1="364" x2="448" y2="400" />
                  </g>
                  <path d="M312 296 Q226 274 128 302 Q168 328 242 322 Q284 318 318 318 Z" fill="#f04438" stroke="#111111" strokeWidth="2.4" />
                  <path d="M248 616 L270 348 Q276 300 322 296 L380 296 Q418 300 430 350 L468 616 Z" fill="#16223f" stroke="#111111" strokeWidth="2.8" />
                  <path d="M274 350 Q280 308 322 300 L310 362 L292 490 L262 490 Z" fill="#315bea" opacity="0.55" />
                  <path d="M314 296 L338 364 L368 306" fill="#f7f5f0" stroke="#111111" strokeWidth="2.2" />
                  <path d="M326 270 L326 302 L362 302 L362 270 Z" fill="#f2c9b4" stroke="#111111" strokeWidth="2.2" />
                  <path d="M308 232 Q304 272 334 280 Q368 282 374 246 Q376 206 342 202 Q312 202 308 232 Z" fill="#fae2d6" stroke="#111111" strokeWidth="2.4" />
                  <path d="M308 236 L301 248 L310 251" fill="none" stroke="#111111" strokeWidth="2" strokeLinecap="round" />
                  <path d="M317 232 Q328 226 337 233 Q328 240 317 232 Z" fill="#ffffff" stroke="#111111" strokeWidth="2" />
                  <circle cx="326" cy="232" r="4.5" fill="#f04438" stroke="#111111" strokeWidth="1.3" />
                  <circle cx="325" cy="232" r="2" fill="#111111" />
                  <path d="M302 226 Q296 184 338 178 Q388 176 394 226 Q396 258 378 278 Q374 250 364 236 Q348 218 328 220 Q312 222 302 226 Z" fill="#111111" />
                  <path d="M306 206 Q278 198 260 212 Q282 214 304 218 Z" fill="#111111" />
                  <path d="M308 210 Q324 190 356 192" fill="none" stroke="#f2c94c" strokeWidth="2.6" opacity="0.85" />
                </svg>
              </div>
              <div className="hero-plate-caption">
                <span className="mono-label">FIG. 00 — INK TO SPECTRUM</span>
                <span className="color-block-tag">
                  PALETTE:
                  <span style={{ width: 8, height: 8, background: "var(--electric)", display: "inline-block" }} />
                  <span style={{ width: 8, height: 8, background: "var(--vermilion)", display: "inline-block" }} />
                  <span style={{ width: 8, height: 8, background: "var(--saffron)", display: "inline-block" }} />
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Colorization Showcase */}
      <section className="comparison-section" id="comparison">
        <div className="container">
          <div className="section-top reveal">
            <div>
              <div className="section-index">
                <span className="index-dot" style={{ background: "var(--vermilion)" }} />
                <span className="mono-label">01 // Interactive Comparison</span>
              </div>
              <h2 className="section-heading">Original ink meets <em>living</em> color.</h2>
            </div>
            <span className="mono-label">DRAG VERTICAL DIVIDER TO INSPECT</span>
          </div>

          <div className="comparison-shell reveal">
            <div
              className="comparison-stage"
              id="comparisonStage"
              style={{ "--split": `${split}%` } as React.CSSProperties}
              aria-label="Interactive before and after manga colorization slider"
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
              onPointerLeave={handlePointerUp}
              onKeyDown={handleKeyDown}
              tabIndex={0}
            >
              <div className="comp-layer comp-bw" aria-hidden="true">
                <svg viewBox="0 0 960 570" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" id="compareTemplate">
                  <defs>
                    <linearGradient id="shrineSky" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#1e2a5a" />
                      <stop offset="50%" stopColor="#315bea" />
                      <stop offset="82%" stopColor="#f04438" />
                      <stop offset="100%" stopColor="#f2c94c" />
                    </linearGradient>
                    <pattern id="shrineTone" width="6" height="6" patternUnits="userSpaceOnUse">
                      <circle cx="2" cy="2" r="1" fill="#111111" opacity="0.2" />
                    </pattern>
                  </defs>
                  <rect width="960" height="570" fill="url(#shrineSky)" />
                  <rect width="960" height="360" fill="url(#shrineTone)" />
                  <circle cx="480" cy="275" r="105" fill="#fff5d6" opacity="0.9" />
                  <path d="M-20 310 Q110 215 240 265 Q365 180 495 240 Q625 170 760 245 Q865 200 980 270 L980 410 L-20 410 Z" fill="#fde8c8" stroke="#111111" strokeWidth="2" />
                  <path d="M0 420 L185 280 L365 365 L580 250 L790 345 L960 275 L960 440 L0 440 Z" fill="#233158" stroke="#111111" strokeWidth="2" />
                  <path d="M180 570 L370 365 L590 365 L780 570 Z" fill="#cfc9be" stroke="#111111" strokeWidth="2.4" />
                  <g stroke="#111111" strokeWidth="1.8">
                    <line x1="215" y1="532" x2="745" y2="532" />
                    <line x1="255" y1="490" x2="705" y2="490" />
                    <line x1="295" y1="448" x2="665" y2="448" />
                    <line x1="335" y1="406" x2="625" y2="406" />
                  </g>
                  <path d="M0 570 L0 260 Q95 275 155 340 Q215 395 230 570 Z" fill="#16213e" stroke="#111111" strokeWidth="2.2" />
                  <path d="M960 570 L960 250 Q860 270 805 335 Q745 395 730 570 Z" fill="#16213e" stroke="#111111" strokeWidth="2.2" />
                  <g>
                    <rect x="275" y="340" width="28" height="75" fill="#9c968c" stroke="#111111" strokeWidth="2" />
                    <rect x="271" y="316" width="36" height="24" fill="#f2c94c" stroke="#111111" strokeWidth="2" />
                    <polygon points="262,316 289,296 316,316" fill="#7d7870" stroke="#111111" strokeWidth="2" />
                    <rect x="657" y="340" width="28" height="75" fill="#9c968c" stroke="#111111" strokeWidth="2" />
                    <rect x="653" y="316" width="36" height="24" fill="#f2c94c" stroke="#111111" strokeWidth="2" />
                    <polygon points="644,316 671,296 698,316" fill="#7d7870" stroke="#111111" strokeWidth="2" />
                  </g>
                  <path d="M325 148 Q480 182 635 148 L626 168 Q480 198 334 168 Z" fill="#f04438" stroke="#111111" strokeWidth="2.6" />
                  <rect x="355" y="212" width="250" height="18" fill="#f04438" stroke="#111111" strokeWidth="2.4" />
                  <rect x="378" y="166" width="26" height="202" fill="#f04438" stroke="#111111" strokeWidth="2.4" />
                  <rect x="556" y="166" width="26" height="202" fill="#f04438" stroke="#111111" strokeWidth="2.4" />
                  <path d="M446 476 L460 392 Q466 376 480 376 Q494 376 500 392 L514 476 Z" fill="#18223d" stroke="#111111" strokeWidth="2.4" />
                  <path d="M454 396 Q432 412 416 426 Q442 426 460 412 Z" fill="#f04438" stroke="#111111" strokeWidth="1.8" />
                  <circle cx="480" cy="360" r="14" fill="#111111" />
                  <line x1="510" y1="364" x2="492" y2="452" stroke="#111111" strokeWidth="3.2" strokeLinecap="round" />
                  <g fill="#f04438" stroke="#111111" strokeWidth="1.2">
                    <ellipse cx="195" cy="195" rx="8" ry="4" transform="rotate(-24 195 195)" />
                    <ellipse cx="755" cy="175" rx="8" ry="4" transform="rotate(32 755 175)" />
                    <ellipse cx="320" cy="275" rx="6.5" ry="3.5" transform="rotate(15 320 275)" />
                    <ellipse cx="640" cy="260" rx="7" ry="3.5" transform="rotate(-35 640 260)" />
                  </g>
                </svg>
              </div>
              <div className="comp-layer comp-color" id="compareColorLayer" aria-hidden="true" />
              <div className="comp-divider" id="compareDivider" />
              <span className="comp-tag comp-tag-left">ORIGINAL INK</span>
              <span className="comp-tag comp-tag-right">SUMI COLOR</span>
            </div>

            <div className="comparison-footer">
              <span className="mono-label">PLATE 01 // SHRINE AT DUSK — SCREENTONE PRESERVED</span>
              <div className="quick-splits">
                <button type="button" className="split-chip" onClick={() => setSplit(92)}>
                  Ink Only
                </button>
                <button type="button" className="split-chip" onClick={() => setSplit(50)}>
                  50 / 50
                </button>
                <button type="button" className="split-chip" onClick={() => setSplit(8)}>
                  Full Color
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Curated Manga Gallery */}
      <section className="gallery-section" id="gallery">
        <div className="container">
          <div className="section-top reveal">
            <div>
              <div className="section-index">
                <span className="index-dot" style={{ background: "var(--electric)" }} />
                <span className="mono-label">02 // Curated Exhibition</span>
              </div>
              <h2 className="section-heading">Selected <em>transformations</em>.</h2>
            </div>
            <div className="filter-row" role="tablist" aria-label="Filter gallery by category">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  className={`filter-btn ${filter === cat.id ? "is-active" : ""}`}
                  data-filter={cat.id}
                  onClick={() => setFilter(cat.id)}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          <div className="exhibition-grid">
            {exhibits
              .filter((e) => filter === "all" || e.cat === filter)
              .map((exhibit) => (
                <article key={exhibit.id} className={`exhibit-card exhibit-${exhibit.cat} reveal`} data-cat={exhibit.cat}>
                  <div className="exhibit-frame" tabIndex={0} role="button" aria-label={exhibit.title}>
                    <div className={`exhibit-art-box ${exhibit.ratio}`}>
                      <svg viewBox="0 0 420 520" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" className="exhibit-art">
                        <rect width="420" height="520" fill="#f7f5f0" />
                        <rect x="18" y="18" width="384" height="484" fill="#e8e5dc" stroke="#111111" strokeWidth="2" />
                        <text x="210" y="260" fontFamily="var(--font-mono)" fontSize="14" fill="#8c8982" textAnchor="middle">
                          {exhibit.title}
                        </text>
                      </svg>
                      <span className="exhibit-pill">
                        <span className="on-ink">Original Ink</span>
                        <span className="on-color">SUMI Color</span>
                      </span>
                    </div>
                  </div>
                  <div className="exhibit-info">
                    <h3 className="exhibit-title">{exhibit.title}</h3>
                    <span className="exhibit-cat">{exhibit.cat}</span>
                  </div>
                </article>
              ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="workflow-section" id="how-it-works">
        <div className="container">
          <div className="section-top reveal">
            <div>
              <div className="section-index">
                <span className="index-dot" style={{ background: "var(--saffron)" }} />
                <span className="mono-label">03 // Workflow</span>
              </div>
              <h2 className="section-heading">From ink plate to <em>finished</em> page.</h2>
            </div>
          </div>

          <div className="workflow-grid reveal">
            <div className="workflow-step">
              <div className="step-code">
                <span className="step-swatch" style={{ background: "var(--vermilion)" }} />
                01 — UPLOAD
              </div>
              <h3 className="step-heading">Upload your original manga pages.</h3>
              <p className="step-copy">
                Drop high-resolution monochrome scans or digital linework. SUMI automatically maps ink contours and screentone densities.
              </p>
            </div>
            <div className="workflow-step">
              <div className="step-code">
                <span className="step-swatch" style={{ background: "var(--electric)" }} />
                02 — COLORIZE
              </div>
              <h3 className="step-heading">Let SUMI transform your artwork.</h3>
              <p className="step-copy">
                Choose an editorial palette or lock character colors across chapters while keeping every original brushstroke intact.
              </p>
            </div>
            <div className="workflow-step">
              <div className="step-code">
                <span className="step-swatch" style={{ background: "var(--saffron)" }} />
                03 — EXPORT
              </div>
              <h3 className="step-heading">Download your finished colorized pages.</h3>
              <p className="step-copy">
                Export 600 DPI print-ready illustrations or layered PSD files ready for publishing and artbook production.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* About */}
      <section className="about-section" id="about">
        <div className="container about-grid reveal">
          <blockquote className="about-quote">
            “True colorization never erases the ink—it illuminates what the artist <em>already drew</em>.”
          </blockquote>
          <div className="about-body">
            <p>
              Named after traditional Japanese sumi ink (墨), SUMI is built for mangaka, colorists, and publishers who treat manga as fine visual literature.
            </p>
            <p>
              Unlike generic filters that blur linework or flatten halftone shading, our engine respects the deliberate contrast of black-and-white manga—bringing contemporary color depth to every panel.
            </p>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="final-cta">
        <div className="container final-cta-inner reveal">
          <div className="final-cta-left">
            <span className="final-eyebrow">04 // SUMI STUDIO</span>
            <h2 className="final-title">Give your manga a <em>new life</em>.</h2>
            <p className="final-sub">Step inside the studio and experience your black-and-white panels in full editorial color.</p>
          </div>
          <button type="button" className="btn-studio-final" onClick={() => {}}>
            Explore SUMI Studio →
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container footer-inner">
          <span>© 2026 SUMI (墨) — Color Beyond the Ink.</span>
          <div className="footer-links">
            <a href="#gallery">Gallery</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#about">About</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
