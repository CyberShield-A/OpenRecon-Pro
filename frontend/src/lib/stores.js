import { writable, derived } from "svelte/store";

// ── Core scan state ─────────────────────────────────────────
export const scanId = writable(/** @type {string|null} */ (null));
export const isScanning = writable(false);
export const scanResults = writable(/** @type {object|null} */ (null));
export const consoleLines = writable(/** @type {string[]} */ ([]));

// ── UI state ────────────────────────────────────────────────
export const activeTab = writable("subdomains");

// ── AI report state ─────────────────────────────────────────
export const aiReport = writable("");
export const isGeneratingReport = writable(false);

// ── Derived stats ────────────────────────────────────────────
export const stats = derived(scanResults, ($r) => {
  if (!$r) {
    return {
      subdomains: 0,
      waf: "—",
      wildcard: "—",
      score: "—",
      scoreColor: "text-[#555555]",
    };
  }

  const subdomains = ($r.subdomains || []).length;

  // Support both key names the backend may use
  const wafRaw = $r.waf_cdn ?? $r.cdn_waf;
  let waf;
  if (
    wafRaw &&
    typeof wafRaw === "object" &&
    ("cdn" in wafRaw || "waf" in wafRaw)
  ) {
    // Nouveau format : { cdn, waf, method }
    const parts = [];
    if (wafRaw.cdn && wafRaw.cdn !== "Aucun") parts.push(wafRaw.cdn);
    if (wafRaw.waf && wafRaw.waf !== "Aucun" && wafRaw.waf !== wafRaw.cdn)
      parts.push(wafRaw.waf);
    waf = parts.length ? parts.join(" / ") : "Aucun";
  } else if (wafRaw && typeof wafRaw === "object" && "detected" in wafRaw) {
    // Ancien format objet { detected, name }
    waf = wafRaw.detected ? wafRaw.name || "Détecté" : "Aucun";
  } else {
    waf = wafRaw || "—";
  }

  const wcRaw = $r.wildcard;
  let wildcard;
  if (wcRaw && typeof wcRaw === "object") {
    wildcard = wcRaw.detected ? "Oui" : "Non";
  } else if (typeof wcRaw === "boolean") {
    wildcard = wcRaw ? "Oui" : "Non";
  } else {
    wildcard = wcRaw ?? "—";
  }

  const rawScore = $r.security_score ?? $r.security_headers?.score ?? null;
  const score = rawScore !== null ? `${rawScore}/100` : "—";
  const scoreColor =
    rawScore === null
      ? "text-[#555555]"
      : rawScore >= 70
        ? "text-green-400"
        : rawScore >= 40
          ? "text-yellow-400"
          : "text-red-400";

  return { subdomains, waf, wildcard, score, scoreColor };
});
