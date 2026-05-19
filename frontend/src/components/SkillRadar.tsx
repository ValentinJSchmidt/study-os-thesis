/**
 * SVG hexagonal radar chart.
 * All data is mock — replace with API data when available.
 *
 * Axes (6): Programming, Statistics, Databases, Projects, Web, Versioning
 * Levels: Unaware (0) → Aware (1) → Working (2) → Practitioner (3) → Expert (4)
 */

const SIZE = 400;
const CX = SIZE / 2;
const CY = SIZE / 2;
const LEVELS = 4; // rings
const MAX_R = 160; // radius at outermost ring

const AXES = [
  "Programming",
  "Statistics",
  "Databases",
  "Projects",
  "Web",
  "Versioning",
];
const N = AXES.length;

// Mock data (0–4 scale, matching levels above)
const CURRENT_DATA = [3.5, 3.8, 2.5, 2.8, 1.5, 2.2]; // red polygon
const TARGET_DATA  = [4.0, 3.5, 3.5, 3.5, 3.0, 3.5]; // blue polygon

/** Convert polar (angle, radius) to Cartesian. 0° = top. */
function polar(angle: number, r: number): [number, number] {
  const rad = (angle - 90) * (Math.PI / 180);
  return [CX + r * Math.cos(rad), CY + r * Math.sin(rad)];
}

/** Build a polygon points string from data array (values 0–4). */
function buildPoints(data: number[]): string {
  return data
    .map((v, i) => {
      const angle = (360 / N) * i;
      const r = (v / LEVELS) * MAX_R;
      const [x, y] = polar(angle, r);
      return `${x},${y}`;
    })
    .join(" ");
}

/** Build ring polygon at a given level. */
function ringPoints(level: number): string {
  const r = (level / LEVELS) * MAX_R;
  return Array.from({ length: N }, (_, i) => {
    const [x, y] = polar((360 / N) * i, r);
    return `${x},${y}`;
  }).join(" ");
}

const LEVEL_LABELS = ["Unaware", "Aware", "Working", "Practitioner", "Expert"];

export default function SkillRadar() {
  return (
    <div className="flex flex-col lg:flex-row gap-8 items-center">
      {/* SVG radar */}
      <div className="w-full lg:w-2/3 aspect-square max-w-[480px] relative">
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="w-full h-full"
        >
          {/* Grid rings */}
          {Array.from({ length: LEVELS }, (_, i) => i + 1).map((level) => (
            <polygon
              key={level}
              points={ringPoints(level)}
              fill="none"
              stroke="#e3e2e6"
              strokeWidth="1"
            />
          ))}

          {/* Axis lines */}
          {AXES.map((_, i) => {
            const angle = (360 / N) * i;
            const [x, y] = polar(angle, MAX_R);
            return (
              <line
                key={i}
                x1={CX}
                y1={CY}
                x2={x}
                y2={y}
                stroke="#e3e2e6"
                strokeWidth="1"
              />
            );
          })}

          {/* Target polygon (blue) */}
          <polygon
            points={buildPoints(TARGET_DATA)}
            fill="rgba(134,160,205,0.15)"
            stroke="#455f88"
            strokeWidth="2"
          />

          {/* Current polygon (red) */}
          <polygon
            points={buildPoints(CURRENT_DATA)}
            fill="rgba(186,26,26,0.15)"
            stroke="#ba1a1a"
            strokeWidth="2"
          />

          {/* Axis labels */}
          {AXES.map((label, i) => {
            const angle = (360 / N) * i;
            const r = MAX_R + 22;
            const [x, y] = polar(angle, r);
            const anchor =
              Math.abs(x - CX) < 5 ? "middle" : x > CX ? "start" : "end";
            const dy = y < CY ? "-0.3em" : y > CY ? "1em" : "0.4em";
            return (
              <text
                key={label}
                x={x}
                y={y}
                textAnchor={anchor}
                dy={dy}
                fontSize="12"
                fontFamily="Inter, sans-serif"
                fontWeight="600"
                fill="#43474e"
              >
                {label}
              </text>
            );
          })}

          {/* Level labels along the top axis */}
          {Array.from({ length: LEVELS + 1 }, (_, i) => {
            const r = (i / LEVELS) * MAX_R;
            const [x, y] = polar(0, r); // straight up
            if (i === 0) return null;
            return (
              <text
                key={i}
                x={x + 4}
                y={y}
                fontSize="9"
                fontFamily="Inter, sans-serif"
                fill="#74777f"
                dominantBaseline="middle"
              >
                {LEVEL_LABELS[i]}
              </text>
            );
          })}
        </svg>
      </div>

      {/* Legend + insight */}
      <div className="flex-1 flex flex-col gap-6">
        <div className="flex flex-col gap-4 bg-surface-container-low p-6 rounded-lg">
          <span className="font-title-lg text-primary font-semibold">Legende</span>
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 rounded bg-error border border-error shrink-0" />
              <div>
                <span className="block font-label-md text-on-surface">Aktueller Stand</span>
                <span className="text-body-sm text-on-surface-variant">
                  Basierend auf deinem Transcript
                </span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 rounded bg-primary-container border border-surface-tint shrink-0" />
              <div>
                <span className="block font-label-md text-on-surface">Zielprofil</span>
                <span className="text-body-sm text-on-surface-variant">
                  Anforderung für Master-Forschung
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-tertiary-container/10 border border-tertiary-container/20 p-4 rounded-lg flex items-start gap-3">
          <span className="material-symbols-outlined text-tertiary-container mt-0.5">
            info
          </span>
          <p className="text-body-sm text-on-tertiary-container font-medium">
            Dein Fokus in Statistiken und Programmierung ist bereits auf
            Experten-Niveau. Ergänze Web-Technologien, um das Zielprofil zu
            vervollständigen.
          </p>
        </div>
      </div>
    </div>
  );
}
