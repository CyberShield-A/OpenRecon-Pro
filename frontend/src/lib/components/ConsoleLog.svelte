<script>
  import { consoleLines } from '$lib/stores';
  import { afterUpdate } from 'svelte';

  let el;
  let collapsed = false;

  afterUpdate(() => {
    if (el && !collapsed) el.scrollTop = el.scrollHeight;
  });

  function lineClass(line) {
    if (line.includes('✓')) return 'text-green-400';
    if (line.includes('✗') || line.includes('Erreur')) return 'text-red-400';
    if (line.includes('⚠')) return 'text-yellow-400';
    return 'text-[#555555]';
  }
</script>

<div class="bg-panel border border-[#1c1c1c] rounded-lg overflow-hidden">
  <!-- Terminal chrome bar -->
  <button
    class="w-full flex items-center justify-between px-4 py-2 border-b border-[#1c1c1c]
           hover:bg-elevated/50 transition-colors cursor-pointer"
    on:click={() => (collapsed = !collapsed)}
    aria-expanded={!collapsed}
  >
    <div class="flex items-center gap-3">
      <div class="flex gap-1.5">
        <div class="w-2.5 h-2.5 rounded-full bg-[#f85149]/60"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-[#d29922]/60"></div>
        <div class="w-2.5 h-2.5 rounded-full bg-[#3fb950]/60"></div>
      </div>
      <span class="font-mono text-xs text-[#3a3a3a]">openrecon — console</span>
    </div>
    <div class="flex items-center gap-2">
      <span class="text-[10px] text-[#3a3a3a]">
        {$consoleLines.length} ligne{$consoleLines.length !== 1 ? 's' : ''}
      </span>
      <svg
        class="text-[#3a3a3a] transition-transform {collapsed ? 'rotate-180' : ''}"
        width="11" height="11" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2"
      >
        <polyline points="18 15 12 9 6 15"/>
      </svg>
    </div>
  </button>

  {#if !collapsed}
    <div
      bind:this={el}
      class="h-28 overflow-y-auto bg-surface p-3 font-mono text-xs leading-5"
    >
      {#if $consoleLines.length === 0}
        <span class="text-[#3a3a3a]">En attente de scan…</span>
      {:else}
        {#each $consoleLines as line}
          <div class={lineClass(line)}>{line}</div>
        {/each}
        <span class="inline-block w-1.5 h-3.5 bg-blue-400 align-middle animate-pulse ml-0.5"></span>
      {/if}
    </div>
  {/if}
</div>
