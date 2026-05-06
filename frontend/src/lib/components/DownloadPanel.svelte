<script>
  import { scanId } from "$lib/stores";
  import { downloadScan } from "$lib/api";

  let active = null; // fmt currently downloading
  let done = null; // fmt just downloaded

  const formats = [
    { fmt: "json", label: "JSON", icon: "{ }", color: "text-yellow-400" },
    { fmt: "txt", label: "TXT", icon: "≡", color: "text-[#555555]" },
    { fmt: "html", label: "HTML", icon: "</>", color: "text-orange-400" },
    { fmt: "csv", label: "CSV", icon: ",,,", color: "text-green-400" },
    { fmt: "pdf", label: "PDF", icon: "⬇", color: "text-red-400" },
  ];

  async function handle(fmt) {
    if (!$scanId || active) return;
    active = fmt;
    done = null;
    try {
      await downloadScan($scanId, fmt);
      done = fmt;
      setTimeout(() => (done = null), 2000);
    } catch (_) {
      /* silent */
    } finally {
      active = null;
    }
  }
</script>

<div class="panel space-y-3">
  <div class="section-title">
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#3fb950"
      stroke-width="2"
    >
      <path
        d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"
      />
    </svg>
    Exporter
  </div>

  <div class="flex flex-wrap gap-1.5">
    {#each formats as f}
      <button
        class="flex items-center gap-2 px-3 py-2 text-xs font-medium rounded-md border
               transition-all
               {$scanId
          ? 'border-[#1c1c1c] bg-elevated hover:bg-[#141414] hover:border-[#272727] text-[#b8b8b8]'
          : 'border-[#1c1c1c] bg-elevated text-[#3a3a3a] opacity-40 cursor-not-allowed'}"
        on:click={() => handle(f.fmt)}
        disabled={!$scanId || active !== null}
      >
        <span class="font-mono {f.color} w-5 text-center">{f.icon}</span>
        {#if done === f.fmt}
          <span class="text-green-400">✓ OK</span>
        {:else if active === f.fmt}
          <svg
            class="animate-spin text-[#555555]"
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
          {f.label}
        {/if}
      </button>
    {/each}
  </div>

  {#if !$scanId}
    <p class="text-[10px] text-[#3a3a3a] text-center">Scan requis</p>
  {/if}
</div>
