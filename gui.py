# gui.py
from nicegui import ui
import asyncio
from core import engine
from modules.report import generate_report, export_html
from utils.config import get

class OpenReconGUI:
    def __init__(self):
        self.is_scanning = False
        self.is_generating_report = False
        self.last_results = None
        self.last_target = None
        self.last_report_text = None

    @staticmethod
    def _clean_domain(raw):
        """Supprime http://, https://, les slashs et espaces du domaine saisi."""
        domain = raw.strip()
        for prefix in ("https://", "http://"):
            if domain.lower().startswith(prefix):
                domain = domain[len(prefix):]
        domain = domain.split("/")[0].strip()  # retire le chemin éventuel
        return domain

    async def start_scan(self, target):
        target = self._clean_domain(target)
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
            self.last_results = results
            self.last_target = target
            self.report_btn.enable()
            
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
        whois_data = data.get('whois', {})
        headers_data = data.get('security_headers', {})
        tech_data = data.get('technologies', {})
        
        # Mise à jour des compteurs
        self.subdomain_count.set_text(str(len(subs)))
        self.waf_info.set_text(str(data.get('cdn_waf', 'Aucun')))
        self.wildcard_info.set_text(str(data.get('wildcard', 'N/A')))

        # Headers score
        score = headers_data.get('score', 0)
        grade = headers_data.get('grade', 'N/A')
        self.headers_score.set_text(f"{score}% ({grade})")

        # Nettoyage et remplissage de la liste des sous-domaines
        self.subdomain_list.clear()
        with self.subdomain_list:
            if not subs:
                ui.label("Aucun résultat trouvé.").classes('text-gray-500 italic p-2')
            
            for item in subs:
                name = item.get('subdomain', 'Inconnu')
                ips = ", ".join(item.get('ips', []))
                conf = item.get('confidence', 0)

                with ui.row().classes('w-full items-center gap-3 border-b border-slate-800 py-2 px-1'):
                    ui.label(name).classes('text-blue-400 font-mono font-bold flex-grow')
                    if ips:
                        ui.label(f"[{ips}]").classes('text-xs text-gray-500')
                    ui.badge(f"{conf}%", color='blue').props('outline')

        # Affichage WHOIS
        self.whois_area.clear()
        with self.whois_area:
            if whois_data.get('registrar'):
                items = [
                    ("Registrar", whois_data.get('registrar', 'N/A')),
                    ("Propriétaire", whois_data.get('registrant', 'N/A')),
                    ("Création", whois_data.get('creation_date', 'N/A')),
                    ("Expiration", whois_data.get('expiration_date', 'N/A')),
                    ("Vie privée", "Oui" if whois_data.get('privacy') else "Non"),
                ]
                for label, val in items:
                    with ui.row().classes('w-full gap-2 py-1'):
                        ui.label(label).classes('text-gray-500 text-xs w-24')
                        ui.label(str(val)).classes('text-sm')
            else:
                ui.label("WHOIS non disponible.").classes('text-gray-500 italic')

        # Affichage Technologies
        self.tech_area.clear()
        with self.tech_area:
            techs = tech_data.get('technologies', [])
            if techs:
                for t in techs:
                    ui.badge(t, color='indigo').props('outline').classes('mr-1 mb-1')
            else:
                ui.label("Aucune technologie identifiée.").classes('text-gray-500 italic')

        # Affichage Headers manquants
        self.headers_area.clear()
        with self.headers_area:
            missing = headers_data.get('missing', {})
            present = headers_data.get('present', {})
            if present:
                for h in present:
                    with ui.row().classes('items-center gap-2 py-1'):
                        ui.icon('check_circle', color='green').classes('text-sm')
                        ui.label(h).classes('text-green-400 text-xs font-mono')
            if missing:
                for h, details in missing.items():
                    with ui.row().classes('items-center gap-2 py-1'):
                        ui.icon('cancel', color='red').classes('text-sm')
                        ui.label(f"{h}").classes('text-red-400 text-xs font-mono')
                        ui.label(f"— {details['risk']}").classes('text-xs text-gray-500')
            if not present and not missing:
                ui.label("Non analysé.").classes('text-gray-500 italic')

    async def generate_ai_report(self):
        """Génère un rapport IA via Ollama."""
        if not self.last_results or self.is_generating_report:
            return

        self.is_generating_report = True
        self.log_area.push("🤖 Génération du rapport IA...")
        self.report_area.content = "*Analyse en cours... Veuillez patienter.*"

        try:
            loop = asyncio.get_event_loop()
            report = await loop.run_in_executor(
                None, generate_report, self.last_target, self.last_results
            )
            if report:
                self.report_area.content = report
                self.last_report_text = report
                self.export_html_btn.enable()
                self.log_area.push("✅ Rapport IA généré avec succès.")
                ui.notify("Rapport généré !", type="positive")
            else:
                self.report_area.content = "**Erreur** : Impossible de générer le rapport. Vérifiez Ollama."
                ui.notify("Échec de la génération du rapport.", type="negative")
        except Exception as e:
            self.report_area.content = f"**Erreur** : {str(e)}"
            ui.notify(f"Erreur : {str(e)}", type="negative")
        finally:
            self.is_generating_report = False

    def export_report_html(self):
        """Exporte le dernier rapport en HTML."""
        if not hasattr(self, 'last_report_text') or not self.last_report_text:
            ui.notify("Aucun rapport à exporter.", type="warning")
            return
        filepath = f"rapport_{self.last_target}.html"
        ok = export_html(self.last_report_text, self.last_target, filepath)
        if ok:
            ui.notify(f"Rapport HTML exporté : {filepath}", type="positive")
            self.log_area.push(f"📄 Rapport HTML sauvegardé : {filepath}")
        else:
            ui.notify("Échec de l'export HTML.", type="negative")

    def build(self):
        ui.query('body').style('background-color: #020617; color: white; font-family: "Inter", sans-serif;')
        
        # --- Header ---
        with ui.header().classes('bg-slate-900 border-b border-slate-800 p-4 justify-between items-center'):
            ui.label('OPENRECON PRO').classes('text-2xl font-black tracking-tighter text-blue-500')
            ui.badge('v3.13 - SECURE DEPLOY', color='blue')

        # --- Main Column ---
        with ui.column().classes('w-full max-w-5xl mx-auto p-6 gap-6'):
            
            # Input Section
            with ui.row().classes('w-full gap-4'):
                target_input = ui.input(label='Domaine cible', placeholder='google.com').classes('flex-grow').props('dark outlined')
                ui.button('DÉMARRER L\'ANALYSE', on_click=lambda: self.start_scan(target_input.value)).props('color=blue icon=bolt').classes('h-14 px-6')

            # Top Stats
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
                with ui.card().classes('flex-1 bg-slate-900 border border-slate-800'):
                    ui.label('SECURITY SCORE').classes('text-xs text-gray-500')
                    self.headers_score = ui.label('N/A').classes('text-xl text-yellow-400')

            # Main Results Table
            with ui.column().classes('w-full gap-4'):
                with ui.card().classes('w-full bg-slate-900 border border-slate-800 h-80'):
                    ui.label('CIBLES DÉCOUVERTES').classes('text-xs font-bold text-blue-300 border-b border-slate-800 w-full pb-1')
                    self.subdomain_list = ui.scroll_area().classes('w-full h-full')

                # Side by Side WHOIS and TECH
                with ui.row().classes('w-full gap-4'):
                    with ui.card().classes('flex-1 bg-slate-900 border border-slate-800'):
                        ui.label('WHOIS').classes('text-xs font-bold text-cyan-300 border-b border-slate-800 w-full pb-1')
                        self.whois_area = ui.column().classes('w-full py-2')
                    with ui.card().classes('flex-1 bg-slate-900 border border-slate-800'):
                        ui.label('TECHNOLOGIES').classes('text-xs font-bold text-indigo-300 border-b border-slate-800 w-full pb-1')
                        self.tech_area = ui.row().classes('w-full py-2 flex-wrap')

                # Headers Analysis
                with ui.card().classes('w-full bg-slate-900 border border-slate-800'):
                    ui.label('ANALYSE DES EN-TÊTES HTTP').classes('text-xs font-bold text-yellow-300 border-b border-slate-800 w-full pb-1')
                    self.headers_area = ui.column().classes('w-full py-2')

                # Logs
                with ui.card().classes('w-full bg-black border border-slate-800 h-48'):
                    ui.label('CONSOLES LOGS').classes('text-xs text-green-500 font-mono')
                    self.log_area = ui.log().classes('w-full h-full text-[11px] font-mono text-gray-400')

            # AI Section
            with ui.column().classes('w-full gap-4'):
                with ui.card().classes('w-full bg-slate-900 border border-slate-800'):
                    ui.label('RAPPORT IA').classes('text-xs font-bold text-purple-300 border-b border-slate-800 w-full pb-1')
                    with ui.row().classes('w-full gap-4 items-center py-2'):
                        self.report_btn = ui.button('GÉNÉRER', on_click=lambda: self.generate_ai_report()).props('color=purple icon=smart_toy').classes('h-10 px-4')
                        self.report_btn.disable()
                        self.export_html_btn = ui.button('EXPORT HTML', on_click=lambda: self.export_report_html()).props('color=teal icon=download').classes('h-10 px-4')
                        self.export_html_btn.disable()
                    self.report_area = ui.markdown("*Lancez un scan pour débloquer l'IA.*").classes('w-full text-sm text-gray-300 p-2')

if __name__ in {"__main__", "__mp_main__"}:
    gui = OpenReconGUI()
    gui.build()
    # On bind sur 0.0.0.0 pour Docker. # nosec bypass l'alerte Bandit B104.
    ui.run(title="OpenRecon Pro", dark=True, host='0.0.0.0', port=5000, reload=False) # nosec
