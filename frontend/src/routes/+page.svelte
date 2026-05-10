<script>
  import ScanPanel from "$lib/components/ScanPanel.svelte";
  import StatsBar from "$lib/components/StatsBar.svelte";
  import ConsoleLog from "$lib/components/ConsoleLog.svelte";
  import ResultsPanel from "$lib/components/ResultsPanel.svelte";
  import AIReport from "$lib/components/AIReport.svelte";
</script>

<div class="flex h-[calc(100vh-49px)] overflow-hidden">
  <!-- ── Left sidebar ──────────────────────────────────── -->
  <aside
    class="w-72 shrink-0 border-r border-[#1c1c1c] flex flex-col
                overflow-y-auto bg-surface p-3 gap-3"
  >
    <ScanPanel />
  </aside>

  <!-- ── Main content ──────────────────────────────────── -->
  <div class="flex-1 overflow-y-auto p-3 space-y-3 min-w-0">
    <StatsBar />
    <ConsoleLog />
    <ResultsPanel />
    <AIReport />
  </div>
</div>
