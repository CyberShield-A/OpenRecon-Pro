<script>
  import { lookupParentDomain } from '$lib/api';

  let input   = '';
  let loading = false;
  let result  = null;
  let error   = '';

  async function handleLookup() {
    if (!input.trim() || loading) return;
    loading = true;
    error   = '';
    result  = null;

    try {
      result = await lookupParentDomain(input.trim());
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function onKeyDown(e) {
    if (e.key === 'Enter') handleLookup();
  }
</script>

<div class="panel space-y-3">
  <div class="section-title">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#22d3ee" stroke-width="2">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
    </svg>
    Domaine parent
  </div>

  <div class="flex gap-1.5">
    <input
      bind:value={input}
      on:keydown={onKeyDown}
      type="text"
      placeholder="api.v2.example.com"
      class="input font-mono text-xs"
      disabled={loading}
      autocomplete="off"
      spellcheck="false"
    />
    <button
      class="btn-ghost shrink-0 px-2.5"
      on:click={handleLookup}
      disabled={!input.trim() || loading}
      title="Rechercher le domaine parent"
    >
      {#if loading}
        <svg class="animate-spin" width="12" height="12" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"
                  stroke-dasharray="40" stroke-dashoffset="15" stroke-linecap="round"/>
        </svg>
      {:else}
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
      {/if}
    </button>
  </div>

  {#if error}
    <p class="text-xs text-red-400">✗ {error}</p>
  {/if}

  {#if result}
    <div class="bg-elevated border border-[#1c1c1c] rounded-md p-3 space-y-2.5">
      <div>
        <span class="label mb-0.5">Domaine parent</span>
        <div class="mono text-blue-400 font-semibold text-sm">{result.parent_domain}</div>
      </div>
      <div class="grid grid-cols-2 gap-2 text-xs border-t border-[#1c1c1c] pt-2">
        <div>
          <span class="text-[#555555]">Méthode</span>
          <div class="text-[#b8b8b8] font-medium capitalize">{result.method}</div>
        </div>
        <div>
          <span class="text-[#555555]">DNS vérifié</span>
          <div class="{result.dns_verified ? 'text-green-400' : 'text-[#3a3a3a]'}">
            {result.dns_verified ? '✓ Oui' : '— Non'}
          </div>
        </div>
        {#if result.levels_removed != null}
          <div>
            <span class="text-[#555555]">Niveaux supprimés</span>
            <div class="text-[#b8b8b8] font-medium">{result.levels_removed}</div>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>
