<script>
  import '../app.css';
</script>

<div class="min-h-screen bg-surface flex flex-col">
  <!-- ── Navbar ─────────────────────────────────────────── -->
  <header class="sticky top-0 z-50 bg-panel border-b border-[#1c1c1c] px-4 py-2.5
                 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="flex items-center justify-center w-8 h-8 bg-blue-600/20
                  border border-blue-600/40 rounded-md shrink-0">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
             stroke="#58a6ff" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83
                   M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
        </svg>
      </div>
      <div>
        <h1 class="text-sm font-bold text-[#e8e8e8] leading-none tracking-tight">
          OpenRecon Pro
        </h1>
        <span class="text-[10px] text-[#3a3a3a]">Reconnaissance & OSINT</span>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <span class="badge bg-blue-900/30 text-blue-400 border border-blue-900/50">v2.0</span>
      <span class="badge bg-green-900/30 text-green-400 border border-green-900/50">
        <span class="w-1.5 h-1.5 bg-green-400 rounded-full mr-1.5 animate-pulse"></span>
        Online
      </span>
    </div>
  </header>

  <!-- ── Page content ───────────────────────────────────── -->
  <main class="flex-1 overflow-hidden">
    <slot />
  </main>
</div>
