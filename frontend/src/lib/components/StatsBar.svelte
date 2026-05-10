<script>
  import { stats, scanResults } from "$lib/stores";

  $: hasData = !!$scanResults;

  // Décompose CDN / WAF séparément pour un affichage plus précis
  $: wafRaw = $scanResults?.waf_cdn ?? $scanResults?.cdn_waf ?? null;
  $: cdnLabel =
    wafRaw && typeof wafRaw === "object" && "cdn" in wafRaw
      ? wafRaw.cdn !== "Aucun"
        ? wafRaw.cdn
        : null
      : null;
  $: wafLabel =
    wafRaw && typeof wafRaw === "object" && "waf" in wafRaw
      ? wafRaw.waf !== "Aucun"
        ? wafRaw.waf
        : null
      : null;
  $: wafMethodBadge =
    wafRaw?.method === "ip_range"
      ? "IP"
      : wafRaw?.method === "ip_range+header"
        ? "IP+HDR"
        : wafRaw?.method === "header"
          ? "HDR"
          : null;
</script>

<div class="grid grid-cols-4 gap-3">
  <!-- Subdomains -->
  <div
    class="bg-panel border border-blue-900/40 bg-blue-900/10 rounded-lg p-3 space-y-1"
  >
    <div class="flex items-center justify-between">
      <span
        class="text-[10px] font-semibold text-[#555555] uppercase tracking-widest"
        >Sous-domaines</span
      >
      <svg
        class="text-blue-400 opacity-70"
        width="13"
        height="13"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"
        />
      </svg>
    </div>
    <div class="text-2xl font-bold text-blue-400 {hasData ? '' : 'opacity-30'}">
      {$stats.subdomains}
    </div>
  </div>

  <!-- WAF / CDN -->
  <div
    class="bg-panel border border-orange-900/40 bg-orange-900/10 rounded-lg p-3 space-y-1"
  >
    <div class="flex items-center justify-between">
      <span
        class="text-[10px] font-semibold text-[#555555] uppercase tracking-widest"
        >WAF / CDN</span
      >
      <svg
        class="text-orange-400 opacity-70"
        width="13"
        height="13"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    </div>
    {#if hasData && (cdnLabel || wafLabel)}
      <div class="space-y-0.5 pt-0.5">
        {#if cdnLabel}
          <div class="flex items-center gap-1">
            <span
              class="text-[9px] font-semibold text-orange-500/70 uppercase w-7 shrink-0"
              >CDN</span
            >
            <span class="text-xs font-bold text-orange-400 truncate"
              >{cdnLabel}</span
            >
          </div>
        {/if}
        {#if wafLabel}
          <div class="flex items-center gap-1">
            <span
              class="text-[9px] font-semibold text-red-500/70 uppercase w-7 shrink-0"
              >WAF</span
            >
            <span class="text-xs font-bold text-red-400 truncate"
              >{wafLabel}</span
            >
          </div>
        {/if}
        {#if wafMethodBadge}
          <span class="text-[9px] text-[#3a3a3a] mono">{wafMethodBadge}</span>
        {/if}
      </div>
    {:else}
      <div
        class="text-sm font-bold text-orange-400 {hasData
          ? ''
          : 'opacity-30'} truncate leading-8"
      >
        {$stats.waf}
      </div>
    {/if}
  </div>

  <!-- Wildcard DNS -->
  <div
    class="bg-panel border border-yellow-900/40 bg-yellow-900/10 rounded-lg p-3 space-y-1"
  >
    <div class="flex items-center justify-between">
      <span
        class="text-[10px] font-semibold text-[#555555] uppercase tracking-widest"
        >Wildcard DNS</span
      >
      <svg
        class="text-yellow-400 opacity-70"
        width="13"
        height="13"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
      </svg>
    </div>
    <div
      class="text-sm font-bold text-yellow-400 {hasData
        ? ''
        : 'opacity-30'} leading-8"
    >
      {$stats.wildcard}
    </div>
  </div>

  <!-- Security Score -->
  <div class="bg-panel border border-[#1c1c1c] rounded-lg p-3 space-y-1">
    <div class="flex items-center justify-between">
      <span
        class="text-[10px] font-semibold text-[#555555] uppercase tracking-widest"
        >Sécurité</span
      >
      <svg
        class="{$stats.scoreColor} opacity-70"
        width="13"
        height="13"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    </div>
    <div
      class="text-2xl font-bold {$stats.scoreColor} {hasData
        ? ''
        : 'opacity-30'}"
    >
      {$stats.score}
    </div>
  </div>
</div>
