<script>
  import {
    scanId,
    aiReport,
    isGeneratingReport,
    consoleLines,
  } from "$lib/stores";
  import { generateReport } from "$lib/api";
  import { markdownToHtml } from "$lib/markdown";

  let userRole = "chef_entreprise";
  let scanType = "complet";
  let error = "";

  const roles = [
    { value: "etudiant", label: "Étudiant", icon: "🎓" },
    { value: "chef_entreprise", label: "Chef d'entreprise", icon: "💼" },
    { value: "pentester", label: "Pentester", icon: "🎯" },
    { value: "admin_systeme", label: "Admin système", icon: "⚙️" },
    { value: "developpeur", label: "Développeur", icon: "👨‍💻" },
  ];

  const scanTypes = [
    { value: "complet", label: "Complet" },
    { value: "subdomain", label: "Sous-domaines" },
    { value: "web", label: "Web" },
    { value: "vulnerabilite", label: "Vulnérabilités" },
    { value: "rdap", label: "RDAP" },
  ];

  function log(msg) {
    const t = new Date().toLocaleTimeString("fr-FR", { hour12: false });
    consoleLines.update((l) => [...l, `[${t}] ${msg}`]);
  }

  async function handleGenerate() {
    if (!$scanId || $isGeneratingReport) return;
    error = "";
    aiReport.set("");
    isGeneratingReport.set(true);
    log(`Génération rapport IA… (rôle: ${userRole}, type: ${scanType})`);

    try {
      const data = await generateReport($scanId, userRole, scanType);
      aiReport.set(data.report ?? "");
      log("✓ Rapport IA généré avec succès");
    } catch (e) {
      error = e.message;
      log(`✗ Erreur rapport: ${e.message}`);
    } finally {
      isGeneratingReport.set(false);
    }
  }

  let copied = false;
  async function copyReport() {
    if (!$aiReport) return;
    await navigator.clipboard.writeText($aiReport);
    copied = true;
    setTimeout(() => (copied = false), 1800);
  }

  let downloading = false;
  async function downloadReport() {
    if (!$scanId || downloading) return;
    downloading = true;
    try {
      const { downloadScan } = await import("$lib/api");
      await downloadScan($scanId, "pdf");
    } catch (_) {
      /* silent */
    } finally {
      downloading = false;
    }
  }

  $: reportHtml = markdownToHtml($aiReport);
  $: activeRole = roles.find((r) => r.value === userRole);
  $: activeScanType = scanTypes.find((s) => s.value === scanType);
</script>

<div class="panel space-y-4">
  <!-- Header -->
  <div class="section-title">
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#a78bfa"
      stroke-width="2"
    >
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
    </svg>
    Rapport IA
    {#if $isGeneratingReport}
      <span
        class="badge bg-purple-900/30 text-purple-400 border border-purple-900/50 ml-auto animate-pulse"
      >
        Génération…
      </span>
    {/if}
  </div>

  <!-- Role buttons -->
  <div>
    <label class="label">Profil utilisateur</label>
    <div class="grid grid-cols-5 gap-1.5">
      {#each roles as role}
        <button
          class="flex flex-col items-center gap-1 py-2 px-1 rounded-md border transition-all
                 {userRole === role.value
            ? 'border-purple-600/80 bg-purple-900/20 text-purple-200'
            : 'border-[#1c1c1c] bg-elevated text-[#555555] hover:border-[#272727] hover:text-[#b8b8b8]'}"
          on:click={() => (userRole = role.value)}
          disabled={$isGeneratingReport}
          title={role.label}
        >
          <span class="text-base leading-none">{role.icon}</span>
          <span class="text-[9px] font-medium leading-tight text-center"
            >{role.label}</span
          >
        </button>
      {/each}
    </div>
  </div>

  <!-- Scan type + Generate button -->
  <div class="flex gap-2">
    <div class="flex-1">
      <label class="label" for="scan-type">Type d'analyse</label>
      <select
        id="scan-type"
        bind:value={scanType}
        class="input"
        disabled={$isGeneratingReport}
      >
        {#each scanTypes as st}
          <option value={st.value}>{st.label}</option>
        {/each}
      </select>
    </div>
    <div class="flex items-end">
      <button
        class="btn-primary px-4 py-2 text-xs"
        on:click={handleGenerate}
        disabled={!$scanId || $isGeneratingReport}
        title={!$scanId ? "Lancez d'abord un scan" : "Générer le rapport IA"}
      >
        {#if $isGeneratingReport}
          <svg
            class="animate-spin"
            width="11"
            height="11"
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
          En cours…
        {:else}
          <svg
            width="11"
            height="11"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
          </svg>
          Générer
        {/if}
      </button>
    </div>
  </div>

  <!-- Error -->
  {#if error}
    <div
      class="px-3 py-2 bg-red-900/20 border border-red-900/40 rounded-md text-xs text-red-400"
    >
      ✗ {error}
    </div>
  {/if}

  <!-- Report output -->
  {#if $aiReport}
    <div class="border border-[#1c1c1c] rounded-lg overflow-hidden">
      <!-- Report toolbar -->
      <div
        class="px-4 py-2 bg-elevated border-b border-[#1c1c1c] flex items-center justify-between"
      >
        <span class="text-xs text-[#555555]">
          {activeRole?.icon}
          {activeRole?.label} — {activeScanType?.label}
        </span>
        <div class="flex items-center gap-2">
          <!-- Copier -->
          <button
            class="text-xs text-[#555555] hover:text-[#e8e8e8] transition-colors flex items-center gap-1"
            on:click={copyReport}
            title="Copier le rapport"
          >
            {#if copied}
              <svg
                width="11"
                height="11"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#3fb950"
                stroke-width="2.5"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span class="text-green-400">Copié</span>
            {:else}
              <svg
                width="11"
                height="11"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <rect x="9" y="9" width="13" height="13" rx="2" />
                <path
                  d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                />
              </svg>
              Copier
            {/if}
          </button>
          <!-- Télécharger PDF -->
          <button
            class="text-xs flex items-center gap-1 transition-colors
                   {downloading
              ? 'text-[#3a3a3a] cursor-not-allowed'
              : 'text-[#555555] hover:text-red-400'}"
            on:click={downloadReport}
            disabled={downloading}
            title="Télécharger le rapport en PDF"
          >
            {#if downloading}
              <svg
                class="animate-spin"
                width="11"
                height="11"
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
                width="11"
                height="11"
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
            PDF
          </button>
        </div>
      </div>
      <!-- Report body -->
      <div class="report-content p-5 max-h-[480px] overflow-y-auto">
        {@html reportHtml}
      </div>
    </div>
  {:else if $scanId && !$isGeneratingReport}
    <div class="flex flex-col items-center py-8 text-center gap-2">
      <svg
        class="text-[#1c1c1c]"
        width="28"
        height="28"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
      </svg>
      <p class="text-sm text-[#3a3a3a]">
        Sélectionnez un profil et lancez la génération
      </p>
    </div>
  {:else if !$scanId}
    <div class="flex items-center justify-center py-8">
      <p class="text-sm text-[#3a3a3a]">
        Lancez d'abord un scan pour générer un rapport
      </p>
    </div>
  {/if}
</div>
