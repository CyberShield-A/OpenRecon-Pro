const BASE = "/api";

/** @param {Response} res */
async function handleError(res) {
  const body = await res.json().catch(() => ({ error: res.statusText }));
  throw new Error(body.error || `HTTP ${res.status}`);
}

/**
 * Lance un scan de reconnaissance.
 * @param {string} target
 * @param {'NORMAL'|'STEALTH'|'AGGRESSIVE'} mode
 */
export async function startScan(target, mode = "NORMAL") {
  const res = await fetch(`${BASE}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target, mode }),
  });
  if (!res.ok) await handleError(res);
  return res.json();
}

/**
 * Génère un rapport IA pour un scan existant.
 * @param {string} scanId
 * @param {string} userRole
 * @param {string} scanType
 * @param {string|null} model
 */
export async function generateReport(
  scanId,
  userRole,
  scanType = "complet",
  model = null,
) {
  const res = await fetch(`${BASE}/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      scan_id: scanId,
      user_role: userRole,
      scan_type: scanType,
      model,
    }),
  });
  if (!res.ok) await handleError(res);
  return res.json();
}

/**
 * Retrouve le domaine parent d'un sous-domaine.
 * @param {string} subdomain
 */
export async function lookupParentDomain(subdomain) {
  const res = await fetch(`${BASE}/parent-domain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subdomain }),
  });
  if (!res.ok) await handleError(res);
  return res.json();
}

/**
 * Déclenche le téléchargement d'un scan dans le format demandé.
 * @param {string} scanId
 * @param {'json'|'txt'|'html'|'csv'} fmt
 */
export async function downloadScan(scanId, fmt) {
  const res = await fetch(`${BASE}/download/${scanId}/${fmt}`);
  if (!res.ok) throw new Error("Échec du téléchargement");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const ext = fmt === "scan-pdf" ? "pdf" : fmt;
  const a = document.createElement("a");
  a.href = url;
  a.download = `openrecon_${scanId.slice(0, 8)}.${ext}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
