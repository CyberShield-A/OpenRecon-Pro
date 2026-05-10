/**
 * Minimal Markdown → HTML converter (escapes input first to prevent XSS).
 * Handles: h1–h3, bold, italic, inline code, fenced code blocks,
 *          unordered lists, horizontal rules, paragraphs.
 * @param {string} md
 * @returns {string}
 */
export function markdownToHtml(md) {
  if (!md) return "";

  // 1. Escape raw HTML from LLM output
  let out = md
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // 2. Fenced code blocks
  out = out.replace(
    /```[\w]*\n([\s\S]*?)```/g,
    (_, code) => `<pre class="rpt-pre"><code>${code.trimEnd()}</code></pre>`,
  );

  // 3. Headings
  out = out.replace(/^### (.+)$/gm, '<h3 class="rpt-h3">$1</h3>');
  out = out.replace(/^## (.+)$/gm, '<h2 class="rpt-h2">$1</h2>');
  out = out.replace(/^# (.+)$/gm, '<h1 class="rpt-h1">$1</h1>');

  // 4. Horizontal rule
  out = out.replace(/^---+$/gm, '<hr class="rpt-hr">');

  // 5. Bold + italic (combined first)
  out = out.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
  out = out.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/\*(.+?)\*/g, "<em>$1</em>");
  out = out.replace(/_(.+?)_/g, "<em>$1</em>");

  // 6. Inline code
  out = out.replace(/`([^`\n]+)`/g, '<code class="rpt-code">$1</code>');

  // 7. Unordered lists — group consecutive items
  out = out.replace(/^[-*] (.+)$/gm, "<li>$1</li>");
  out = out.replace(
    /(<li>[\s\S]*?<\/li>\n?)+/g,
    (m) => `<ul class="rpt-ul">${m}</ul>`,
  );

  // 8. Paragraphs (split on blank lines; skip block-level elements)
  const blockTags = /^<(h[1-3]|ul|pre|hr)/;
  out = out
    .split(/\n{2,}/)
    .map((block) => {
      block = block.trim();
      if (!block || blockTags.test(block)) return block;
      return `<p class="rpt-p">${block.replace(/\n/g, "<br>")}</p>`;
    })
    .filter(Boolean)
    .join("\n");

  return out;
}
