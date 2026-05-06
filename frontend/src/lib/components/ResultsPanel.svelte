<script>
  import { scanResults, activeTab, scanId } from "$lib/stores";
  import { downloadScan } from "$lib/api";

  const tabs = [
    { id: "subdomains", label: "Sous-domaines" },
    { id: "whois", label: "WHOIS / RDAP" },
    { id: "tech", label: "Technologies" },
    { id: "headers", label: "En-têtes HTTP" },
  ];

  const exportFormats = [
    { fmt: "json", label: "JSON" },
    { fmt: "txt", label: "TXT" },
    { fmt: "html", label: "HTML" },
    { fmt: "csv", label: "CSV" },
    { fmt: "scan-pdf", label: "PDF" },
  ];

  let exportFmt = "json";
  let exporting = false;
  async function handleExport() {
    if (!$scanId || exporting) return;
    exporting = true;
    try {
      await downloadScan($scanId, exportFmt);
    } catch (_) {
      /* silent */
    } finally {
      exporting = false;
    }
  }

  let searchQuery = "";

  $: subdomains = $scanResults?.subdomains ?? [];
  $: rdap = $scanResults?.whois ?? {};
  $: {
    if (Object.keys(rdap).length) {
      console.log("[RDAP raw]", JSON.stringify(rdap, null, 2));
    }
  }

  // IP de secours : cherche le domaine racine dans la liste des sous-domaines
  $: fallbackIPs = (() => {
    const target = $scanResults?.target ?? "";
    if (!target) return [];
    const root = subdomains.find(
      (s) => s.subdomain === target || s.subdomain === "www." + target,
    );
    return root?.ips ?? [];
  })();

  // IPs finales : celles du RDAP en priorité, sinon fallback sous-domaines
  $: displayIPs = rdap.ip_addresses?.length ? rdap.ip_addresses : fallbackIPs;

  $: rawTech = $scanResults?.technologies;
  $: technologies = Array.isArray(rawTech)
    ? rawTech
    : (rawTech?.technologies ?? []);
  $: headers = $scanResults?.security_headers ?? {};
  $: presentHeaders = headers.present ?? {};
  $: missingHeaders = headers.missing ?? {};
  $: headerScore = headers.score ?? null;

  $: subscope_target = $scanResults?.subscope_target ?? null;
  $: subscope_count = subdomains.filter((s) => s.scope === "subscope").length;

  $: filtered = searchQuery.trim()
    ? subdomains.filter((s) =>
        s.subdomain?.toLowerCase().includes(searchQuery.toLowerCase()),
      )
    : subdomains;

  function confColor(c) {
    if (c >= 80) return "text-green-400 bg-green-900/20 border-green-900/40";
    if (c >= 50) return "text-yellow-400 bg-yellow-900/20 border-yellow-900/40";
    return "text-red-400 bg-red-900/20 border-red-900/40";
  }
</script>

{#if $scanResults}
  <div class="bg-panel border border-[#1c1c1c] rounded-lg overflow-hidden">
    <!-- Tab bar -->
    <div
      class="flex border-b border-[#1c1c1c] bg-surface overflow-x-auto items-center"
    >
      <div class="flex flex-1 overflow-x-auto">
        {#each tabs as t}
          <button
            class="tab {$activeTab === t.id ? 'tab-active' : 'tab-inactive'}"
            on:click={() => activeTab.set(t.id)}
          >
            {t.label}
            {#if t.id === "subdomains" && subdomains.length}
              <span class="ml-1.5 badge bg-blue-900/30 text-blue-400"
                >{subdomains.length}</span
              >
            {/if}
            {#if t.id === "headers" && headerScore !== null}
              <span
                class="ml-1.5 badge
                {headerScore >= 70
                  ? 'bg-green-900/30 text-green-400'
                  : headerScore >= 40
                    ? 'bg-yellow-900/30 text-yellow-400'
                    : 'bg-red-900/30 text-red-400'}"
              >
                {headerScore}
              </span>
            {/if}
          </button>
        {/each}
      </div>
      <!-- Export sélecteur -->
      {#if $scanId}
        <div class="flex items-center gap-1 px-2 shrink-0">
          <select
            bind:value={exportFmt}
            class="text-xs bg-elevated border border-[#1c1c1c] text-[#555555]
                   rounded-md px-2 py-1 focus:outline-none focus:border-[#272727]"
            disabled={exporting}
          >
            {#each exportFormats as f}
              <option value={f.fmt}>{f.label}</option>
            {/each}
          </select>
          <button
            class="flex items-center gap-1 text-xs px-2 py-1 rounded-md border
                   border-[#1c1c1c] bg-elevated text-[#555555]
                   hover:bg-[#141414] hover:border-[#272727] hover:text-[#b8b8b8]
                   transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            on:click={handleExport}
            disabled={exporting}
            title="Exporter l'analyse"
          >
            {#if exporting}
              <svg
                class="animate-spin"
                width="10"
                height="10"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="3"
                  stroke-dasharray="40"
                  stroke-dashoffset="15"
                  stroke-linecap="round"
                />
              </svg>
            {:else}
              <svg
                width="10"
                height="10"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"
                />
              </svg>
            {/if}
            Exporter
          </button>
        </div>
      {/if}
    </div>

    <!-- Tab content -->
    <div class="p-4">
      <!-- ── Subdomains ───────────────────────────── -->
      {#if $activeTab === "subdomains"}
        {#if subscope_target}
          <div
            class="mb-3 flex items-start gap-2 px-3 py-2 rounded-md bg-purple-900/20 border border-purple-500/30 text-xs text-purple-300"
          >
            <span class="shrink-0 mt-0.5">🔎</span>
            <span>
              Sous-domaine détecté en entrée — le scan a couvert <strong
                class="text-purple-200">{$scanResults?.target}</strong
              >
              (domaine racine)
              <em>et</em>
              <strong class="text-purple-200">{subscope_target}</strong>
              ({subscope_count} sous-sous-domaine{subscope_count !== 1
                ? "s"
                : ""} trouvé{subscope_count !== 1 ? "s" : ""}
              <span
                class="badge bg-purple-900/40 border-purple-500/40 text-purple-300"
                >⬇ sub</span
              >).
            </span>
          </div>
        {/if}
        <div class="mb-3">
          <input
            bind:value={searchQuery}
            type="text"
            placeholder="Filtrer les sous-domaines…"
            class="input"
          />
        </div>
        {#if filtered.length === 0}
          <p class="text-center text-sm text-[#3a3a3a] py-8">
            Aucun sous-domaine trouvé
          </p>
        {:else}
          <div class="space-y-1 max-h-64 overflow-y-auto pr-1">
            {#each filtered as sub}
              <div
                class="flex items-center justify-between px-3 py-2 bg-elevated
                          rounded-md hover:bg-[#141414] transition-colors group"
              >
                <div class="flex items-center gap-2 min-w-0">
                  <svg
                    class="shrink-0 text-blue-400/60"
                    width="11"
                    height="11"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <path
                      d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10
                             15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"
                    />
                  </svg>
                  <span class="mono text-[#e8e8e8] truncate"
                    >{sub.subdomain ?? sub}</span
                  >
                </div>
                <div class="flex items-center gap-1.5 shrink-0 ml-2">
                  {#if sub.ips?.length}
                    <span
                      class="badge bg-elevated text-[#555555] border border-[#1c1c1c] mono"
                    >
                      {sub.ips[0]}{sub.ips.length > 1
                        ? ` +${sub.ips.length - 1}`
                        : ""}
                    </span>
                  {/if}
                  {#if sub.confidence != null}
                    <span class="badge border {confColor(sub.confidence)}"
                      >{sub.confidence}%</span
                    >
                  {/if}
                  {#if sub.scope === "subscope"}
                    <span
                      class="badge bg-purple-900/40 border border-purple-500/40 text-purple-300"
                      title="Sous-domaine du scope saisi">⬇ sub</span
                    >
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}

        <!-- ── WHOIS / RDAP ─────────────────────────── -->
      {:else if $activeTab === "whois"}
        {#if Object.keys(rdap).length === 0}
          <p class="text-center text-sm text-[#3a3a3a] py-8">
            Aucune donnée RDAP
          </p>
        {:else}
          <div class="space-y-3 max-h-80 overflow-y-auto pr-1">
            <!-- Adresses IP -->
            <div class="rdap-row">
              <span class="rdap-key">
                <svg
                  width="11"
                  height="11"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  class="inline mr-1 text-blue-400"
                  ><circle cx="12" cy="12" r="10" /><path d="M2 12h20" /></svg
                >
                Adresses IP
              </span>
              <div class="flex flex-wrap gap-1">
                {#if displayIPs.length}
                  {#each displayIPs as ip}
                    <span
                      class="badge bg-blue-900/20 text-blue-300 border border-blue-900/40 mono"
                      >{ip}</span
                    >
                  {/each}
                  {#if !rdap.ip_addresses?.length && fallbackIPs.length}
                    <span class="text-[10px] text-[#3a3a3a] ml-1 self-center"
                      >(via sous-domaines)</span
                    >
                  {/if}
                {:else}
                  <span class="text-[#3a3a3a] text-xs">Non résolu</span>
                {/if}
              </div>
            </div>

            <!-- Registrar -->
            {#if rdap.registrar}
              <div class="rdap-row">
                <span class="rdap-key">Registrar</span>
                <span class="rdap-val">{rdap.registrar}</span>
              </div>
            {/if}

            <!-- Registrant -->
            {#if rdap.registrant}
              <div class="rdap-row">
                <span class="rdap-key">Registrant</span>
                <div class="flex items-center gap-2">
                  <span class="rdap-val">{rdap.registrant}</span>
                  {#if rdap.privacy}
                    <span
                      class="badge bg-yellow-900/20 text-yellow-400 border border-yellow-900/40"
                    >
                      🔒 Protégé
                    </span>
                  {/if}
                </div>
              </div>
            {/if}

            <!-- Dates -->
            {#if rdap.creation_date}
              <div class="rdap-row">
                <span class="rdap-key">Création</span>
                <span class="rdap-val">{rdap.creation_date}</span>
              </div>
            {/if}
            {#if rdap.expiration_date}
              <div class="rdap-row">
                <span class="rdap-key">Expiration</span>
                <span
                  class="rdap-val {new Date(rdap.expiration_date) < new Date()
                    ? 'text-red-400'
                    : ''}">{rdap.expiration_date}</span
                >
              </div>
            {/if}

            <!-- DNSSEC -->
            {#if rdap.dnssec}
              <div class="rdap-row">
                <span class="rdap-key">DNSSEC</span>
                <span
                  class="badge {rdap.dnssec === 'signed'
                    ? 'bg-green-900/20 text-green-400 border-green-900/40'
                    : 'bg-[#1c1c1c] text-[#555555] border-[#1c1c1c]'} border"
                >
                  {rdap.dnssec}
                </span>
              </div>
            {/if}

            <!-- Emails -->
            <div class="rdap-row items-start">
              <span class="rdap-key pt-0.5">
                <svg
                  width="11"
                  height="11"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  class="inline mr-1 text-purple-400"
                >
                  <path
                    d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"
                  />
                  <polyline points="22,6 12,13 2,6" />
                </svg>
                Emails
              </span>
              <div class="flex flex-wrap gap-1.5">
                {#if rdap.emails?.length}
                  {#each rdap.emails as email}
                    <a
                      href="mailto:{email}"
                      class="badge bg-purple-900/20 text-purple-300 border border-purple-900/40 mono hover:bg-purple-900/30 transition-colors"
                    >
                      {email}
                    </a>
                  {/each}
                {:else}
                  <span class="text-[#3a3a3a] text-xs italic">
                    {rdap.privacy
                      ? "🔒 Masqués (protection vie privée)"
                      : "Aucun email public"}
                  </span>
                {/if}
              </div>
            </div>

            <!-- Name servers -->
            {#if rdap.name_servers?.length}
              <div class="rdap-row items-start">
                <span class="rdap-key pt-0.5">Name servers</span>
                <div class="flex flex-wrap gap-1">
                  {#each rdap.name_servers as ns}
                    <span
                      class="badge bg-elevated text-[#555555] border border-[#1c1c1c] mono"
                      >{ns}</span
                    >
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        {/if}

        <!-- ── Technologies ─────────────────────────── -->
      {:else if $activeTab === "tech"}
        {#if technologies.length === 0}
          <p class="text-center text-sm text-[#3a3a3a] py-8">
            Aucune technologie détectée
          </p>
        {:else}
          <div class="flex flex-wrap gap-2">
            {#each technologies as tech}
              <span
                class="badge bg-elevated text-[#b8b8b8] border border-[#1c1c1c] px-2.5 py-1 text-xs"
              >
                {tech}
              </span>
            {/each}
          </div>
        {/if}

        <!-- ── HTTP Headers ─────────────────────────── -->
      {:else if $activeTab === "headers"}
        {#if headerScore !== null}
          <div class="flex items-center gap-2 mb-4">
            <span class="text-xs text-[#555555]">Score global</span>
            <span
              class="font-bold
              {headerScore >= 70
                ? 'text-green-400'
                : headerScore >= 40
                  ? 'text-yellow-400'
                  : 'text-red-400'}"
            >
              {headerScore}/100
            </span>
            <div
              class="flex-1 h-1.5 bg-elevated rounded-full overflow-hidden ml-2"
            >
              <div
                class="h-full rounded-full transition-all
                {headerScore >= 70
                  ? 'bg-green-500'
                  : headerScore >= 40
                    ? 'bg-yellow-500'
                    : 'bg-red-500'}"
                style="width: {headerScore}%"
              ></div>
            </div>
          </div>
        {/if}

        {#if Object.keys(missingHeaders).length > 0}
          <div class="mb-4">
            <p class="label text-red-400 mb-2">En-têtes manquants</p>
            <div class="space-y-1.5">
              {#each Object.entries(missingHeaders) as [h, info]}
                <div
                  class="px-3 py-2.5 bg-red-900/10 border border-red-900/30 rounded-md"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-red-500 text-xs font-bold">✗</span>
                    <span class="mono text-[#e8e8e8] font-medium">{h}</span>
                    {#if info?.risk}
                      <span
                        class="badge bg-red-900/30 text-red-400 border border-red-900/50 ml-auto"
                      >
                        {info.risk}
                      </span>
                    {/if}
                  </div>
                  {#if info?.impact}
                    <p class="text-xs text-[#555555] mt-1 ml-4">
                      {info.impact}
                    </p>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {/if}

        {#if Object.keys(presentHeaders).length > 0}
          <div>
            <p class="label text-green-400 mb-2">En-têtes présents</p>
            <div class="space-y-1">
              {#each Object.entries(presentHeaders) as [h, v]}
                <div
                  class="flex items-center gap-2 px-3 py-2
                            bg-green-900/10 border border-green-900/20 rounded-md"
                >
                  <span class="text-green-400 text-xs">✓</span>
                  <span class="mono text-[#e8e8e8]">{h}</span>
                  {#if v}
                    <span
                      class="mono text-[#555555] text-[10px] ml-auto truncate max-w-xs"
                      >{v}</span
                    >
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {/if}

        {#if Object.keys(missingHeaders).length === 0 && Object.keys(presentHeaders).length === 0}
          <p class="text-center text-sm text-[#3a3a3a] py-8">
            Aucune donnée d'en-têtes
          </p>
        {/if}
      {/if}
    </div>
  </div>
{/if}
