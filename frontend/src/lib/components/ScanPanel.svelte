<script>
  import {
    scanId,
    isScanning,
    scanResults,
    consoleLines,
    activeTab,
  } from "$lib/stores";
  import { startScan } from "$lib/api";

  let target = "";
  let mode = "NORMAL";

  const modes = [
    {
      value: "NORMAL",
      label: "Normal",
      desc: "Équilibré",
      cls: "text-blue-400 border-blue-600/70",
    },
    {
      value: "STEALTH",
      label: "Stealth",
      desc: "Discret",
      cls: "text-green-400 border-green-600/70",
    },
    {
      value: "AGGRESSIVE",
      label: "Agressif",
      desc: "Complet",
      cls: "text-red-400 border-red-600/70",
    },
  ];

  function log(msg) {
    const t = new Date().toLocaleTimeString("fr-FR", { hour12: false });
    consoleLines.update((l) => [...l, `[${t}] ${msg}`]);
  }

  async function handleScan() {
    if (!target.trim() || $isScanning) return;

    const t = target
      .trim()
      .replace(/^https?:\/\//, "")
      .split("/")[0];

    isScanning.set(true);
    scanResults.set(null);
    scanId.set(null);
    consoleLines.set([]);
    activeTab.set("subdomains");

    log(`Démarrage du scan → ${t}  (mode: ${mode})`);
    log("Résolution DNS & énumération en cours...");

    try {
      const data = await startScan(t, mode);
      scanId.set(data.scan_id);
      scanResults.set(data.results);

      // Notifier si l'outil a extrait le domaine racine d'un sous-domaine
      if (data.results?.subdomain_input && data.results?.target !== t) {
        log(
          `ℹ Sous-domaine détecté — scan lancé sur le domaine racine : ${data.results.target}`,
        );
      }

      const count = data.results?.subdomains?.length ?? 0;
      log(
        `✓ Terminé — ${count} sous-domaine${count !== 1 ? "s" : ""} découvert${count !== 1 ? "s" : ""}`,
      );

      const waf = data.results?.waf_cdn ?? data.results?.cdn_waf;
      if (waf?.detected || (typeof waf === "string" && waf)) {
        log(`⚠ WAF/CDN détecté : ${waf?.name || waf}`);
      }
      if (data.results?.wildcard?.detected) {
        log("⚠ Wildcard DNS actif sur ce domaine");
      }
    } catch (e) {
      log(`✗ Erreur: ${e.message}`);
    } finally {
      isScanning.set(false);
    }
  }

  function onKeyDown(e) {
    if (e.key === "Enter") handleScan();
  }
</script>

<div class="panel space-y-4">
  <!-- Title -->
  <div class="section-title">
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#58a6ff"
      stroke-width="2"
    >
      <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
    </svg>
    Scanner un domaine
  </div>

  <!-- Target input -->
  <div>
    <label class="label" for="target">Cible</label>
    <input
      id="target"
      bind:value={target}
      on:keydown={onKeyDown}
      type="text"
      placeholder="example.com ou 192.168.1.1"
      class="input font-mono"
      disabled={$isScanning}
      autocomplete="off"
      spellcheck="false"
    />
  </div>

  <!-- Mode selector -->
  <div>
    <label class="label">Mode</label>
    <div class="grid grid-cols-3 gap-1.5">
      {#each modes as m}
        <button
          class="py-2 text-xs font-semibold rounded-md border transition-all
                 {mode === m.value
            ? m.cls + ' bg-elevated'
            : 'border-[#1c1c1c] text-[#555555] hover:border-[#272727] hover:text-[#b8b8b8]'}"
          on:click={() => (mode = m.value)}
          disabled={$isScanning}
          title={m.desc}
        >
          {m.label}
        </button>
      {/each}
    </div>
  </div>

  <!-- Scan button -->
  <button
    class="w-full py-2.5 text-sm font-semibold rounded-md border transition-all duration-200
           {$isScanning
      ? 'bg-blue-900/20 text-blue-400 border-blue-800/60 cursor-wait'
      : !target.trim()
        ? 'bg-elevated text-[#3a3a3a] border-[#1c1c1c] cursor-not-allowed'
        : 'bg-blue-600 hover:bg-blue-500 text-white border-transparent shadow-md shadow-blue-900/30'}"
    on:click={handleScan}
    disabled={$isScanning || !target.trim()}
  >
    {#if $isScanning}
      <span class="inline-flex items-center justify-center gap-2">
        <svg
          class="animate-spin"
          width="13"
          height="13"
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
        Analyse en cours…
      </span>
    {:else}
      Lancer le scan →
    {/if}
  </button>
</div>
