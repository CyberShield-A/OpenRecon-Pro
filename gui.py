# gui.py
from nicegui import ui
import asyncio
from core import engine

class OpenReconGUI:
    def __init__(self):
        self.is_scanning = False

    async def start_scan(self, target):
        if not target or "." not in target:
            ui.notify('Veuillez entrer un domaine valide (ex: google.com)', type='warning')
            return

        if self.is_scanning:
            return

        self.is_scanning = True
        self.log_area.push(f"🔎 Lancement du scan : {target}")
        
        try:
            # Exécution dans un thread séparé pour ne pas figer l'UI
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, engine.run, target)
            
            # Mise à jour de l'affichage
            self.display_results(results)
            
            self.log_area.push(f"✅ Scan terminé : {len(results.get('subdomains', []))} résultats.")
            ui.notify('Scan terminé avec succès !', type='positive')
            
        except Exception as e:
            ui.notify(f'Erreur : {str(e)}', type='negative')
            self.log_area.push(f"❌ ERREUR : {str(e)}")
        finally:
            self.is_scanning = False

    def display_results(self, data):
        """Met à jour les cartes et la liste avec les dictionnaires reçus"""
        subs = data.get('subdomains', [])
        
        # Mise à jour des compteurs
        self.subdomain_count.set_text(str(len(subs)))
        self.waf_info.set_text(str(data.get('cdn_waf', 'Aucun')))
        self.wildcard_info.set_text(str(data.get('wildcard', 'N/A')))

        # Nettoyage et remplissage de la liste
        self.subdomain_list.clear()
        with self.subdomain_list:
            if not subs:
                ui.label("Aucun résultat trouvé.").classes('text-gray-500 italic p-2')
            
            for item in subs:
                # 'item' est un dictionnaire {'subdomain': '...', 'ips': [...]}
                name = item.get('subdomain', 'Inconnu')
                ips = ", ".join(item.get('ips', []))
                conf = item.get('confidence', 0)

                with ui.row().classes('w-full items-center gap-3 border-b border-slate-800 py-2 px-1'):
                    ui.label(name).classes('text-blue-400 font-mono font-bold flex-grow')
                    if ips:
                        ui.label(f"[{ips}]").classes('text-xs text-gray-500')
                    ui.badge(f"{conf}%", color='blue').props('outline')

    def build(self):
        ui.query('body').style('background-color: #020617; color: white; font-family: "Inter", sans-serif;')
        
        # --- Header ---
        with ui.header().classes('bg-slate-900 border-b border-slate-800 p-4 justify-between items-center'):
            ui.label('OPENRECON PRO').classes('text-2xl font-black tracking-tighter text-blue-500')
            ui.badge('v3.13', color='blue')

        # --- Main Layout ---
        with ui.column().classes('w-full max-w-5xl mx-auto p-6 gap-6'):
            
            # Input
            with ui.row().classes('w-full gap-4'):
                target_input = ui.input(label='Domaine cible', placeholder='google.com').classes('flex-grow').props('dark outlined')
                ui.button('DÉMARRER L\'ANALYSE', on_click=lambda: self.start_scan(target_input.value)).props('color=blue icon=bolt').classes('h-14 px-6')

            # Stats Cards
            with ui.row().classes('w-full gap-4'):
                with ui.card().classes('flex-1 bg-slate-900 border border-slate-800'):
                    ui.label('SOUS-DOMAINES').classes('text-xs text-gray-500')
                    self.subdomain_count = ui.label('0').classes('text-3xl font-bold')
                with ui.card().classes('flex-1 bg-slate-900 border border-slate-800'):
                    ui.label('WAF / CDN').classes('text-xs text-gray-500')
                    self.waf_info = ui.label('Aucun').classes('text-xl text-orange-400')
                with ui.card().classes('flex-1 bg-slate-900 border border-slate-800'):
                    ui.label('JOKER (Wildcard)').classes('text-xs text-gray-500')
                    self.wildcard_info = ui.label('N / A').classes('text-xl text-green-400')

            # Results
            with ui.column().classes('w-full gap-4'):
                with ui.card().classes('w-full bg-slate-900 border border-slate-800 h-80'):
                    ui.label('CIBLES DÉCOUVERTES').classes('text-xs font-bold text-blue-300 border-b border-slate-800 w-full pb-1')
                    self.subdomain_list = ui.scroll_area().classes('w-full h-full')

                with ui.card().classes('w-full bg-black border border-slate-800 h-48'):
                    ui.label('JOURNAUX SYSTÈME').classes('text-xs text-green-500 font-mono')
                    self.log_area = ui.log().classes('w-full h-full text-[11px] font-mono text-gray-400')

if __name__ in {"__main__", "__mp_main__"}:
    gui = OpenReconGUI()
    gui.build()
    ui.run(title="OpenRecon Pro", dark=True, port=8080)