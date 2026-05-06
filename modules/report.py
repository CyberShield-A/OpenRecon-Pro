# modules/report.py
import re as _re
from datetime import datetime
from utils.logger import info, warning, success
from utils.config import get
from modules.prompts import get_system_prompt, build_full_prompt, USER_ROLES, SCAN_TYPES

OLLAMA_MODEL = get('OLLAMA_MODEL', 'llama3.1:8b')


def generate_report(target, results, user_role='chef_entreprise', scan_type='complet', model=None):
    if model is None:
        model = OLLAMA_MODEL
    if user_role not in USER_ROLES:
        warning('Role inconnu, fallback chef_entreprise')
        user_role = 'chef_entreprise'
    if scan_type not in SCAN_TYPES:
        scan_type = 'complet'
    try:
        import ollama
    except ImportError:
        warning('Installez ollama: pip install ollama')
        return None
    system_prompt = get_system_prompt(user_role)
    user_prompt = build_full_prompt(target, results, user_role, scan_type)
    role_label = USER_ROLES[user_role]
    info('Generation rapport profil: ' + role_label + ', modele: ' + model)
    info('Cela peut prendre quelques instants...')
    try:
        response = ollama.chat(model=model, messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user',   'content': user_prompt},
        ])
        report_text = response['message']['content']
        success('Rapport genere pour profil: ' + role_label)
        return report_text
    except Exception as e:
        err = str(e)
        if 'connection' in err.lower() or 'refused' in err.lower():
            warning('Ollama non accessible. Lancez: ollama serve')
        elif 'not found' in err.lower() or 'model' in err.lower():
            warning('Modele ' + model + ' introuvable. ollama pull ' + model)
        else:
            warning('Erreur rapport: ' + err)
        return None


def save_report(report_text, filepath):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_text)
        success('Rapport sauvegarde: ' + filepath)
    except IOError as e:
        warning('Impossible sauvegarder: ' + str(e))


def _markdown_to_html(text):
    html = text
    html = _re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=_re.MULTILINE)
    html = _re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=_re.MULTILINE)
    html = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = _re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=_re.MULTILINE)
    html = _re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    html = html.replace('\n\n', '</p><p>')
    return '<p>' + html + '</p>'


def export_html_string(report_text, target, user_role=''):
    html_body = _markdown_to_html(report_text)
    date_str = datetime.now().strftime('%d/%m/%Y a %H:%M')
    role_label = USER_ROLES.get(user_role, '')
    role_badge = ('<span class="role-badge">' + role_label + '</span>') if role_label else ''
    return (
        '<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        '<title>Rapport OpenRecon Pro - ' + target + '</title>'
        '<style>'
        '*{margin:0;padding:0;box-sizing:border-box}'
        'body{background:#0f172a;color:#e2e8f0;font-family:sans-serif;line-height:1.7;padding:40px 20px}'
        '.container{max-width:900px;margin:0 auto}'
        '.header{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:30px;margin-bottom:30px;text-align:center}'
        '.header h1{color:#3b82f6;font-size:28px;margin-bottom:8px}'
        '.header .meta{color:#94a3b8;font-size:14px}'
        '.role-badge{display:inline-block;background:#1d4ed8;color:#bfdbfe;padding:3px 12px;border-radius:99px;font-size:12px;font-weight:600;margin-top:8px}'
        '.content{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:30px}'
        'h2{color:#3b82f6;margin:25px 0 12px;padding-bottom:6px;border-bottom:1px solid #334155;font-size:20px}'
        'h3{color:#60a5fa;margin:18px 0 8px;font-size:16px}'
        'p{margin:8px 0}li{margin:4px 0 4px 20px}'
        'strong{color:#f1f5f9}'
        'code{background:#0f172a;color:#34d399;padding:2px 6px;border-radius:4px;font-family:monospace;font-size:13px}'
        '.footer{text-align:center;margin-top:30px;color:#64748b;font-size:12px}'
        '@media print{body{background:white;color:#1e293b}'
        '.header{background:#f1f5f9;border-color:#cbd5e1}'
        '.header h1{color:#1e40af}'
        '.content{background:white;border-color:#cbd5e1}'
        'h2{color:#1e40af;border-color:#cbd5e1}h3{color:#2563eb}'
        'code{background:#f1f5f9;color:#059669}}'
        '</style></head><body>'
        '<div class="container">'
        '<div class="header"><h1>OPENRECON PRO</h1>'
        '<div class="meta">Rapport d audit de reconnaissance passive<br>'
        'Cible : <strong>' + target + '</strong> - ' + date_str + '<br>' + role_badge + '</div></div>'
        '<div class="content">' + html_body + '</div>'
        '<div class="footer">Genere par OpenRecon Pro - Rapport confidentiel</div>'
        '</div></body></html>'
    )


def export_pdf_html_string(report_text, target, user_role=''):
    """Génère un HTML optimisé pour l'export PDF WeasyPrint.
    Fond blanc, texte noir, full-width, typographie professionnelle.
    """
    html_body = _markdown_to_html(report_text)
    date_str = datetime.now().strftime('%d/%m/%Y à %H:%M')
    role_label = USER_ROLES.get(user_role, '')
    role_badge = ('<span class="role-badge">' + role_label + '</span>') if role_label else ''
    return (
        '<!DOCTYPE html><html lang="fr"><head>'
        '<meta charset="UTF-8">'
        '<title>Rapport OpenRecon Pro – ' + target + '</title>'
        '<style>'
        '@page{size:A4;margin:2.5cm 3cm}'
        'body{background:white;color:#1a1a1a;font-family:Arial,Helvetica,sans-serif;'
        'font-size:11pt;line-height:1.65;margin:0;padding:0}'
        '.header{border-bottom:3px solid #1e3a8a;padding-bottom:18px;margin-bottom:28px}'
        '.header h1{color:#1e3a8a;font-size:22pt;font-weight:700;margin:0 0 6px}'
        '.header .meta{color:#374151;font-size:10pt;margin-top:4px}'
        '.role-badge{display:inline-block;background:#1e3a8a;color:white;'
        'padding:2px 10px;border-radius:99px;font-size:9pt;font-weight:600;margin-top:6px}'
        'h2{color:#1e3a8a;font-size:14pt;font-weight:700;'
        'border-bottom:1.5px solid #cbd5e1;padding-bottom:5px;margin:26px 0 12px}'
        'h3{color:#1d4ed8;font-size:12pt;font-weight:600;margin:18px 0 8px}'
        'p{margin:8px 0;color:#1a1a1a}'
        'ul,ol{margin:8px 0;padding-left:0}'
        'li{margin:5px 0;padding-left:18px;color:#1a1a1a;list-style:none;position:relative}'
        'li::before{content:"▸";position:absolute;left:0;color:#1d4ed8;font-size:9pt}'
        'strong{color:#0f172a;font-weight:700}'
        'em{color:#374151;font-style:italic}'
        'code{background:#f1f5f9;color:#065f46;padding:1px 5px;border-radius:3px;'
        'font-family:"Courier New",monospace;font-size:9.5pt;border:1px solid #e2e8f0}'
        '.footer{border-top:1px solid #cbd5e1;padding-top:10px;margin-top:40px;'
        'color:#64748b;font-size:9pt;text-align:center}'
        '</style></head><body>'
        '<div class="header">'
        '<h1>OpenRecon Pro — Rapport d\'audit</h1>'
        '<div class="meta">'
        'Cible&nbsp;: <strong>' + target + '</strong>&ensp;·&ensp;' + date_str +
        ('&ensp;·&ensp;' + role_badge if role_badge else '') +
        '</div></div>'
        + html_body +
        '<div class="footer">Généré par OpenRecon Pro — Document confidentiel</div>'
        '</body></html>'
    )


def export_html(report_text, target, filepath, user_role=''):
    try:
        html = export_html_string(report_text, target, user_role)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        success('Rapport HTML exporte: ' + filepath)
        return True
    except Exception as e:
        warning('Impossible exporter HTML: ' + str(e))
        return False
