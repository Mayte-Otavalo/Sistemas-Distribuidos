"""
Script para convertir WORKSHOP_7_REPORT.md a un documento PDF profesional (WORKSHOP_7_REPORT.pdf)
utilizando Python, Pygments (resaltado de sintaxis), renderizado SVG de diagramas y Chrome Headless.
"""

import os
import re
import subprocess
import markdown_it
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MD_PATH = os.path.join(BASE_DIR, "WORKSHOP_7_REPORT.md")
HTML_PATH = os.path.join(BASE_DIR, "WORKSHOP_7_REPORT.html")
PDF_PATH = os.path.join(BASE_DIR, "WORKSHOP_7_REPORT.pdf")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def generate_architecture_svg() -> str:
    """Genera un diagrama vectorial SVG profesional de la arquitectura distribuida del taller."""
    return """
    <div style="text-align: center; margin: 20px 0; page-break-inside: avoid;">
      <svg width="780" height="340" viewBox="0 0 780 340" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; font-family: 'Segoe UI', Roboto, sans-serif;">
        <defs>
          <linearGradient id="gradServer" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#1e3a8a"/>
            <stop offset="100%" stop-color="#2563eb"/>
          </linearGradient>
          <linearGradient id="gradClient1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#065f46"/>
            <stop offset="100%" stop-color="#059669"/>
          </linearGradient>
          <linearGradient id="gradClient2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#831843"/>
            <stop offset="100%" stop-color="#be185d"/>
          </linearGradient>
          <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
            <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#000" flood-opacity="0.12"/>
          </filter>
          <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#475569"/>
          </marker>
          <marker id="arrowhead-start" markerWidth="8" markerHeight="6" refX="1" refY="3" orient="auto">
            <polygon points="8 0, 0 3, 8 6" fill="#475569"/>
          </marker>
        </defs>

        <!-- Fondo del canvas -->
        <rect width="780" height="340" rx="12" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5"/>

        <!-- NODO 1: CLIENTE 1 (PC 2) -->
        <g filter="url(#shadow)">
          <rect x="30" y="30" width="230" height="125" rx="8" fill="#ffffff" stroke="#059669" stroke-width="2"/>
          <rect x="30" y="30" width="230" height="32" rx="8" fill="url(#gradClient1)"/>
          <rect x="30" y="54" width="230" height="8" fill="url(#gradClient1)"/>
          <text x="145" y="52" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">Nodo 1: Cliente 1 (PC)</text>
          <text x="45" y="80" fill="#1e293b" font-size="10.5" font-weight="600">• TCP Client Socket</text>
          <text x="45" y="98" fill="#1e293b" font-size="10.5">• Validador Esquemas / Código</text>
          <text x="45" y="116" fill="#1e293b" font-size="10.5">• Datos Locales (Partición 1)</text>
          <text x="45" y="134" fill="#64748b" font-size="9.5">IP: 192.168.1.101 | Windows/Linux</text>
        </g>

        <!-- NODO 2: CLIENTE 2 (Raspberry Pi Edge) -->
        <g filter="url(#shadow)">
          <rect x="30" y="185" width="230" height="125" rx="8" fill="#ffffff" stroke="#be185d" stroke-width="2"/>
          <rect x="30" y="185" width="230" height="32" rx="8" fill="url(#gradClient2)"/>
          <rect x="30" y="209" width="230" height="8" fill="url(#gradClient2)"/>
          <text x="145" y="207" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">Nodo 2: Cliente 2 (Raspberry Pi)</text>
          <text x="45" y="235" fill="#1e293b" font-size="10.5" font-weight="600">• TCP Client Socket</text>
          <text x="45" y="253" fill="#1e293b" font-size="10.5">• Validador Esquemas / Código</text>
          <text x="45" y="271" fill="#1e293b" font-size="10.5">• Nodo Edge Recursos Restringidos</text>
          <text x="45" y="289" fill="#64748b" font-size="9.5">IP: 192.168.1.102 | Raspberry Pi OS</text>
        </g>

        <!-- NODO 0: SERVIDOR COORDINADOR (PC 1) -->
        <g filter="url(#shadow)">
          <rect x="490" y="45" width="260" height="250" rx="8" fill="#ffffff" stroke="#2563eb" stroke-width="2"/>
          <rect x="490" y="45" width="260" height="34" rx="8" fill="url(#gradServer)"/>
          <rect x="490" y="71" width="260" height="8" fill="url(#gradServer)"/>
          <text x="620" y="68" fill="#ffffff" font-size="13" font-weight="bold" text-anchor="middle">Nodo 0: Coordinador / Servidor</text>
          
          <rect x="505" y="90" width="230" height="32" rx="4" fill="#eff6ff" stroke="#bfdbfe"/>
          <text x="620" y="110" fill="#1e3a8a" font-size="11" font-weight="bold" text-anchor="middle">TCP Server (0.0.0.0:5000)</text>

          <rect x="505" y="130" width="230" height="48" rx="4" fill="#f8fafc" stroke="#cbd5e1"/>
          <text x="515" y="148" fill="#0f172a" font-size="10" font-weight="bold">Validación de Esquemas:</text>
          <text x="515" y="165" fill="#475569" font-size="9.5">JSON Schema (Draft-07) &amp; XSD (lxml)</text>

          <rect x="505" y="186" width="230" height="48" rx="4" fill="#f8fafc" stroke="#cbd5e1"/>
          <text x="515" y="204" fill="#0f172a" font-size="10" font-weight="bold">Despacho de Servicios:</text>
          <text x="515" y="221" fill="#475569" font-size="9.5">1. get_global_model | 2. training_report</text>

          <rect x="505" y="242" width="230" height="42" rx="4" fill="#f8fafc" stroke="#cbd5e1"/>
          <text x="515" y="259" fill="#0f172a" font-size="10" font-weight="bold">Agregación &amp; Checkpoints:</text>
          <text x="515" y="274" fill="#475569" font-size="9">FedAvg, Idempotencia UUID, Logs</text>
        </g>

        <!-- ENLACES DE COMUNICACIÓN (FLECHAS BIDIRECCIONALES) -->
        <!-- Línea Cliente 1 <-> Servidor -->
        <path d="M 260 92 L 490 120" stroke="#475569" stroke-width="2.5" stroke-dasharray="6,4" marker-end="url(#arrowhead)" marker-start="url(#arrowhead-start)"/>
        <!-- Etiqueta Enlace 1 -->
        <rect x="290" y="76" width="170" height="26" rx="4" fill="#ffffff" stroke="#94a3b8" stroke-width="1"/>
        <text x="375" y="93" fill="#0f172a" font-size="9.5" font-weight="600" text-anchor="middle">TCP / JSON &amp; XML Framing</text>

        <!-- Línea Cliente 2 <-> Servidor -->
        <path d="M 260 248 L 490 220" stroke="#475569" stroke-width="2.5" stroke-dasharray="6,4" marker-end="url(#arrowhead)" marker-start="url(#arrowhead-start)"/>
        <!-- Etiqueta Enlace 2 -->
        <rect x="290" y="238" width="170" height="26" rx="4" fill="#ffffff" stroke="#94a3b8" stroke-width="1"/>
        <text x="375" y="255" fill="#0f172a" font-size="9.5" font-weight="600" text-anchor="middle">TCP / JSON &amp; XML Framing</text>
      </svg>
    </div>
    """

def convert_markdown_to_styled_html(md_content: str) -> str:
    # 1. Reemplazar bloques mermaid con SVG nativo
    mermaid_pattern = re.compile(r'```mermaid[\s\S]*?```', re.MULTILINE)
    md_content = mermaid_pattern.sub(generate_architecture_svg(), md_content)

    # 2. Configurar markdown-it
    md = markdown_it.MarkdownIt("commonmark").enable("table").enable("strikethrough")

    # Renderizador personalizado para bloques de código con Pygments
    formatter = HtmlFormatter(style="friendly", noclasses=True)

    def highlight_code_block(code: str, lang: str) -> str:
        lang = lang.strip().lower() if lang else "text"
        if lang in ["text", "txt", "output", "console"]:
            # Estilo terminal oscuro limpio
            escaped_code = (
                code.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
            )
            return f"""
            <div style="background: #0f172a; border-radius: 6px; padding: 12px 16px; margin: 14px 0; border: 1px solid #1e293b; page-break-inside: avoid;">
              <div style="color: #64748b; font-size: 8pt; margin-bottom: 6px; text-transform: uppercase; font-family: monospace; letter-spacing: 0.5px;">Terminal Output</div>
              <pre style="margin: 0; font-family: 'Cascadia Code', Consolas, monospace; font-size: 8.5pt; color: #38bdf8; line-height: 1.45; overflow-x: auto;">{escaped_code}</pre>
            </div>
            """
        try:
            lexer = get_lexer_by_name(lang)
        except Exception:
            lexer = TextLexer()
        highlighted = highlight(code, lexer, formatter)
        return f'<div style="margin: 12px 0; border-radius: 6px; overflow: hidden; border: 1px solid #e2e8f0; page-break-inside: avoid;">{highlighted}</div>'

    # Reemplazar bloques de código manualmente antes o procesar
    code_pattern = re.compile(r'```([a-zA-Z0-9_-]*)\n([\s\S]*?)```', re.MULTILINE)
    placeholders = {}

    def code_replacer(match):
        lang = match.group(1)
        code = match.group(2)
        idx = f"###CODE_BLOCK_{len(placeholders)}###"
        placeholders[idx] = highlight_code_block(code, lang)
        return idx

    md_processed = code_pattern.sub(code_replacer, md_content)
    raw_html = md.render(md_processed)

    for idx, snippet in placeholders.items():
        raw_html = raw_html.replace(f"<p>{idx}</p>", snippet).replace(idx, snippet)

    # 3. Ensamblar documento HTML final con estilos de reporte profesional
    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Workshop 7: Data-Interchange using JSON/XML - Report</title>
  <style>
    @page {{
      size: A4;
      margin: 18mm 18mm 20mm 18mm;
      @bottom-right {{
        content: "Página " counter(page);
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 8.5pt;
        color: #64748b;
      }}
    }}
    body {{
      font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', Arial, sans-serif;
      font-size: 10pt;
      line-height: 1.6;
      color: #1e293b;
      margin: 0;
      padding: 0;
      background: #ffffff;
    }}
    .header-banner {{
      background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 50%, #2563eb 100%);
      color: #ffffff;
      padding: 24px 28px;
      border-radius: 8px;
      margin-bottom: 24px;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }}
    .header-banner h1 {{
      margin: 0 0 6px 0;
      font-size: 18pt;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: #ffffff;
      border-bottom: none;
    }}
    .header-banner h2 {{
      margin: 0 0 14px 0;
      font-size: 12pt;
      font-weight: 400;
      color: #bfdbfe;
      border-bottom: none;
    }}
    .header-meta {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      font-size: 8.5pt;
      border-top: 1px solid rgba(255,255,255,0.25);
      padding-top: 10px;
    }}
    .header-meta div span {{
      color: #93c5fd;
      font-weight: 600;
    }}
    h1 {{
      font-size: 15pt;
      font-weight: 700;
      color: #0f172a;
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 6px;
      margin-top: 26px;
      margin-bottom: 12px;
      page-break-after: avoid;
    }}
    h2 {{
      font-size: 12.5pt;
      font-weight: 700;
      color: #1e3a8a;
      border-bottom: 1px solid #cbd5e1;
      padding-bottom: 4px;
      margin-top: 20px;
      margin-bottom: 10px;
      page-break-after: avoid;
    }}
    h3 {{
      font-size: 11pt;
      font-weight: 600;
      color: #334155;
      margin-top: 14px;
      margin-bottom: 8px;
      page-break-after: avoid;
    }}
    p {{
      margin: 0 0 10px 0;
      text-align: justify;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      font-size: 8.5pt;
      page-break-inside: avoid;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
      border: 1px solid #cbd5e1;
    }}
    th {{
      background: #1e3a8a;
      color: #ffffff;
      font-weight: 600;
      text-align: left;
      padding: 8px 10px;
      border: 1px solid #1e3a8a;
    }}
    td {{
      padding: 7px 10px;
      border: 1px solid #e2e8f0;
    }}
    tr:nth-child(even) {{
      background: #f8fafc;
    }}
    tr:hover {{
      background: #f1f5f9;
    }}
    ul, ol {{
      margin: 0 0 12px 0;
      padding-left: 24px;
    }}
    li {{
      margin-bottom: 4px;
    }}
    code {{
      background: #f1f5f9;
      color: #b91c1c;
      font-family: 'Cascadia Code', Consolas, Monaco, monospace;
      font-size: 9pt;
      padding: 2px 5px;
      border-radius: 4px;
      border: 1px solid #e2e8f0;
    }}
    pre code {{
      background: transparent;
      color: inherit;
      border: none;
      padding: 0;
    }}
    hr {{
      border: none;
      border-top: 1px solid #e2e8f0;
      margin: 20px 0;
    }}
    .callout {{
      background: #eff6ff;
      border-left: 4px solid #3b82f6;
      padding: 10px 14px;
      margin: 14px 0;
      border-radius: 0 6px 6px 0;
      font-size: 9.5pt;
    }}
  </style>
</head>
<body>
  {raw_html}
</body>
</html>
"""
    return html_doc

def build_pdf():
    print(f"Leyendo {MD_PATH}...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    print("Generando HTML estilizado...")
    html_content = convert_markdown_to_styled_html(md_text)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Archivo HTML intermedio guardado en: {HTML_PATH}")

    file_uri = "file:///" + HTML_PATH.replace("\\", "/")

    print(f"Invocando Chrome Headless ({CHROME_PATH})...")
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        f"--print-to-pdf={PDF_PATH}",
        "--no-pdf-header-footer",
        file_uri
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(PDF_PATH):
        size_kb = os.path.getsize(PDF_PATH) / 1024.0
        print(f"[ÉXITO] Documento PDF generado correctamente: {PDF_PATH} ({size_kb:.1f} KB)")
    else:
        print(f"[ERROR] No se pudo generar el PDF. Salida: {res.stderr} | {res.stdout}")

if __name__ == "__main__":
    build_pdf()
