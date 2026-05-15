import streamlit as st
import requests
import anthropic
from datetime import datetime, date
import json

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Mundial 2026 Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Estilos personalizados ───────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700&family=Inter:wght@400;500&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

  .stApp { background: #0a0e1a; color: #e8eaf0; }

  .hero-banner {
    background: linear-gradient(135deg, #0d1b3e 0%, #1a2d5a 50%, #0d3320 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
  }
  .hero-banner::before {
    content: "⚽";
    position: absolute;
    right: 2rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 5rem;
    opacity: 0.08;
  }
  .hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 0.3rem;
  }
  .hero-sub {
    color: #7a8aaa;
    font-size: 0.95rem;
    margin: 0;
  }

  .metric-card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    text-align: center;
  }
  .metric-number {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: #4ade80;
    line-height: 1;
  }
  .metric-label {
    font-size: 0.78rem;
    color: #6b7280;
    margin-top: 0.3rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .match-card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.7rem;
  }
  .match-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.8rem;
  }
  .match-meta { font-size: 0.75rem; color: #6b7280; }
  .match-teams {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .team-name { font-weight: 500; font-size: 1rem; color: #e8eaf0; }
  .score-center { font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 700; color: #4ade80; padding: 0 1rem; }
  .badge-live { background: #7f1d1d; color: #fca5a5; border-radius: 20px; padding: 2px 10px; font-size: 0.7rem; font-weight: 600; }
  .badge-upcoming { background: #1a2d5a; color: #93c5fd; border-radius: 20px; padding: 2px 10px; font-size: 0.7rem; }
  .badge-done { background: #1f2937; color: #6b7280; border-radius: 20px; padding: 2px 10px; font-size: 0.7rem; }

  .group-card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
  }
  .group-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    color: #4ade80;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.7rem;
  }

  .ai-box {
    background: linear-gradient(135deg, #0d1b3e, #0d2a1a);
    border: 1px solid rgba(74,222,128,0.2);
    border-radius: 12px;
    padding: 1.4rem;
    margin-bottom: 1rem;
  }
  .ai-box p { color: #cbd5e1; font-size: 0.92rem; line-height: 1.65; }

  .prob-bar-bg {
    background: #1f2937;
    border-radius: 4px;
    height: 8px;
    margin: 4px 0 10px;
    overflow: hidden;
  }
  .prob-bar-fill {
    height: 100%;
    border-radius: 4px;
    background: #4ade80;
    transition: width 0.5s ease;
  }
  .prob-bar-fill.draw { background: #6b7280; }
  .prob-bar-fill.away { background: #f87171; }

  [data-testid="stTab"] button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
  }

  .stButton > button {
    background: #4ade80 !important;
    color: #0a0e1a !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.4rem !important;
  }
  .stButton > button:hover { background: #22c55e !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers API ──────────────────────────────────────────────────────────────
def get_api_key(name: str) -> str:
    """Lee API keys desde st.secrets o variables de entorno."""
    try:
        return st.secrets[name]
    except Exception:
        import os
        return os.environ.get(name, "")

def football_request(endpoint: str, params: dict) -> dict | None:
    """Llama a la API-Football. Devuelve None si hay error."""
    api_key = get_api_key("FOOTBALL_API_KEY")
    if not api_key:
        return None
    headers = {"x-apisports-key": api_key}
    url = f"https://v3.football.api-sports.io/{endpoint}"
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error conectando con API-Football: {e}")
        return None

def claude_analyze(prompt: str) -> str:
    """Genera análisis con Claude."""
    api_key = get_api_key("ANTHROPIC_API_KEY")
    if not api_key:
        return "⚠️ Configura tu ANTHROPIC_API_KEY en secrets.toml para activar los análisis con IA."
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=(
                "Eres un analista deportivo experto en fútbol mundial especializado en la Copa del Mundo 2026. "
                "El torneo se juega del 11 de junio al 19 de julio de 2026 en Estados Unidos, México y Canadá. "
                "Participan 48 selecciones en 12 grupos. Argentina es la vigente campeona (Qatar 2022). "
                "Los grupos correctos son: A(México,Sudáfrica,Corea Sur,Rep.Checa), B(Canadá,Bosnia,Qatar,Suiza), "
                "C(Brasil,Marruecos,Haití,Escocia), D(EE.UU.,Paraguay,Australia,Turquía), "
                "E(Alemania,Curazao,Costa de Marfil,Ecuador), F(Países Bajos,Japón,Suecia,Túnez), "
                "G(Bélgica,Irán,Nueva Zelanda,Portugal·), H(España,Cabo Verde,Arabia Saudita,Uruguay), "
                "I(Francia,Senegal,Irak,Noruega), J(Argentina,Argelia,Austria,Jordania), "
                "K(Portugal,R.D.Congo,Uzbekistán,Colombia), L(Inglaterra,Croacia,Ghana,Panamá). "
                "Das análisis precisos, entretenidos y con datos concretos del torneo real. "
                "Responde siempre en español, de forma concisa (máx 4 párrafos)."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        return f"Error con Claude API: {e}"

# ── Datos del Mundial 2026 (fuente fija para fase pre-torneo) ────────────────
GRUPOS = {
    "A": [("🇲🇽", "México"), ("🇿🇦", "Sudáfrica"), ("🇰🇷", "Corea del Sur"), ("🇨🇿", "Rep. Checa")],
    "B": [("🇨🇦", "Canadá"), ("🇧🇦", "Bosnia-Herz."), ("🇶🇦", "Qatar"), ("🇨🇭", "Suiza")],
    "C": [("🇧🇷", "Brasil"), ("🇲🇦", "Marruecos"), ("🇭🇹", "Haití"), ("SCO", "Escocia")],
    "D": [("🇺🇸", "EE.UU."), ("🇵🇾", "Paraguay"), ("🇦🇺", "Australia"), ("🇹🇷", "Turquía")],
    "E": [("🇩🇪", "Alemania"), ("🇨🇼", "Curazao"), ("🇨🇮", "Costa de Marfil"), ("🇪🇨", "Ecuador")],
    "F": [("🇳🇱", "Países Bajos"), ("🇯🇵", "Japón"), ("🇸🇪", "Suecia"), ("🇹🇳", "Túnez")],
    "G": [("🇧🇪", "Bélgica"), ("🇮🇷", "Irán"), ("🇳🇿", "Nueva Zelanda"), ("🇵🇹", "Portugal·")],
    "H": [("🇪🇸", "España"), ("🇨🇻", "Cabo Verde"), ("🇸🇦", "Arabia Saudita"), ("🇺🇾", "Uruguay")],
    "I": [("🇫🇷", "Francia"), ("🇸🇳", "Senegal"), ("🇮🇶", "Irak"), ("🇳🇴", "Noruega")],
    "J": [("🇦🇷", "Argentina"), ("🇩🇿", "Argelia"), ("🇦🇹", "Austria"), ("🇯🇴", "Jordania")],
    "K": [("🇵🇹", "Portugal"), ("🇨🇩", "R.D. Congo"), ("🇺🇿", "Uzbekistán"), ("🇨🇴", "Colombia")],
    "L": [("ENG", "Inglaterra"), ("🇭🇷", "Croacia"), ("🇬🇭", "Ghana"), ("🇵🇦", "Panamá")],
}

PARTIDOS_INICIALES = [
    # Jueves 11 junio
    {"local": ("🇲🇽", "México"), "visita": ("🇿🇦", "Sudáfrica"), "fecha": "Jue 11 jun", "hora": "15:00", "estadio": "Est. Azteca, Ciudad de México", "grupo": "A", "estado": "próximo"},
    {"local": ("🇰🇷", "Corea del Sur"), "visita": ("🇨🇿", "Rep. Checa"), "fecha": "Jue 11 jun", "hora": "22:00", "estadio": "Est. Akron, Guadalajara", "grupo": "A", "estado": "próximo"},
    # Viernes 12 junio
    {"local": ("🇨🇦", "Canadá"), "visita": ("🇧🇦", "Bosnia-Herz."), "fecha": "Vie 12 jun", "hora": "15:00", "estadio": "BMO Field, Toronto", "grupo": "B", "estado": "próximo"},
    {"local": ("🇺🇸", "EE.UU."), "visita": ("🇵🇾", "Paraguay"), "fecha": "Vie 12 jun", "hora": "21:00", "estadio": "SoFi Stadium, Los Ángeles", "grupo": "D", "estado": "próximo"},
    # Sábado 13 junio
    {"local": ("🇶🇦", "Qatar"), "visita": ("🇨🇭", "Suiza"), "fecha": "Sáb 13 jun", "hora": "15:00", "estadio": "Levi's Stadium, San Francisco", "grupo": "B", "estado": "próximo"},
    {"local": ("🇧🇷", "Brasil"), "visita": ("🇲🇦", "Marruecos"), "fecha": "Sáb 13 jun", "hora": "18:00", "estadio": "MetLife Stadium, Nueva Jersey", "grupo": "C", "estado": "próximo"},
    {"local": ("🇭🇹", "Haití"), "visita": ("SCO", "Escocia"), "fecha": "Sáb 13 jun", "hora": "21:00", "estadio": "Gillette Stadium, Boston", "grupo": "C", "estado": "próximo"},
    # Domingo 14 junio
    {"local": ("🇦🇺", "Australia"), "visita": ("🇹🇷", "Turquía"), "fecha": "Dom 14 jun", "hora": "00:00", "estadio": "BC Place, Vancouver", "grupo": "D", "estado": "próximo"},
    {"local": ("🇩🇪", "Alemania"), "visita": ("🇨🇼", "Curazao"), "fecha": "Dom 14 jun", "hora": "13:00", "estadio": "NRG Stadium, Houston", "grupo": "E", "estado": "próximo"},
    {"local": ("🇳🇱", "Países Bajos"), "visita": ("🇯🇵", "Japón"), "fecha": "Dom 14 jun", "hora": "16:00", "estadio": "AT&T Stadium, Dallas", "grupo": "F", "estado": "próximo"},
    {"local": ("🇨🇮", "Costa de Marfil"), "visita": ("🇪🇨", "Ecuador"), "fecha": "Dom 14 jun", "hora": "19:00", "estadio": "Lincoln Financial, Filadelfia", "grupo": "E", "estado": "próximo"},
    {"local": ("🇸🇪", "Suecia"), "visita": ("🇹🇳", "Túnez"), "fecha": "Dom 14 jun", "hora": "22:00", "estadio": "Est. BBVA, Monterrey", "grupo": "F", "estado": "próximo"},
    # Lunes 15 junio
    {"local": ("🇪🇸", "España"), "visita": ("🇨🇻", "Cabo Verde"), "fecha": "Lun 15 jun", "hora": "12:00", "estadio": "Mercedes-Benz Stadium, Atlanta", "grupo": "H", "estado": "próximo"},
    {"local": ("🇧🇪", "Bélgica"), "visita": ("🇪🇬", "Egipto"), "fecha": "Lun 15 jun", "hora": "15:00", "estadio": "Gillette Stadium, Boston", "grupo": "G", "estado": "próximo"},
    {"local": ("🇸🇦", "Arabia Saudita"), "visita": ("🇺🇾", "Uruguay"), "fecha": "Lun 15 jun", "hora": "18:00", "estadio": "Hard Rock Stadium, Miami", "grupo": "H", "estado": "próximo"},
    {"local": ("🇮🇷", "Irán"), "visita": ("🇳🇿", "Nueva Zelanda"), "fecha": "Lun 15 jun", "hora": "21:00", "estadio": "SoFi Stadium, Los Ángeles", "grupo": "G", "estado": "próximo"},
    # Martes 16 junio
    {"local": ("🇫🇷", "Francia"), "visita": ("🇸🇳", "Senegal"), "fecha": "Mar 16 jun", "hora": "15:00", "estadio": "MetLife Stadium, Nueva Jersey", "grupo": "I", "estado": "próximo"},
    {"local": ("🇮🇶", "Irak"), "visita": ("🇳🇴", "Noruega"), "fecha": "Mar 16 jun", "hora": "18:00", "estadio": "Gillette Stadium, Boston", "grupo": "I", "estado": "próximo"},
    {"local": ("🇦🇷", "Argentina"), "visita": ("🇩🇿", "Argelia"), "fecha": "Mar 16 jun", "hora": "21:00", "estadio": "Arrowhead Stadium, Kansas City", "grupo": "J", "estado": "próximo"},
    # Miércoles 17 junio
    {"local": ("🇦🇹", "Austria"), "visita": ("🇯🇴", "Jordania"), "fecha": "Mié 17 jun", "hora": "00:00", "estadio": "Levi's Stadium, San Francisco", "grupo": "J", "estado": "próximo"},
    {"local": ("🇵🇹", "Portugal"), "visita": ("🇨🇩", "R.D. Congo"), "fecha": "Mié 17 jun", "hora": "13:00", "estadio": "NRG Stadium, Houston", "grupo": "K", "estado": "próximo"},
    {"local": ("ENG", "Inglaterra"), "visita": ("🇭🇷", "Croacia"), "fecha": "Mié 17 jun", "hora": "16:00", "estadio": "AT&T Stadium, Dallas", "grupo": "L", "estado": "próximo"},
    {"local": ("🇬🇭", "Ghana"), "visita": ("🇵🇦", "Panamá"), "fecha": "Mié 17 jun", "hora": "19:00", "estadio": "BMO Field, Toronto", "grupo": "L", "estado": "próximo"},
    {"local": ("🇺🇿", "Uzbekistán"), "visita": ("🇨🇴", "Colombia"), "fecha": "Mié 17 jun", "hora": "19:00", "estadio": "Est. Azteca, Ciudad de México", "grupo": "K", "estado": "próximo"},
]

FAVORITOS = [
    ("🇦🇷", "Argentina", 28),
    ("🇧🇷", "Brasil", 18),
    ("🇫🇷", "Francia", 15),
    ("🇪🇸", "España", 12),
    ("ENG", "Inglaterra", 10),
    ("🇩🇪", "Alemania", 8),
    ("🇵🇹", "Portugal", 5),
    ("Otros", "Otros", 4),
]

# ── Componentes UI ───────────────────────────────────────────────────────────
def render_match_card(p: dict):
    estado_badge = {
        "en vivo": '<span class="badge-live">🔴 EN VIVO</span>',
        "próximo": '<span class="badge-upcoming">🗓 Próximo</span>',
        "finalizado": '<span class="badge-done">✓ Finalizado</span>',
    }.get(p["estado"], "")

    score = p.get("score", "– : –")

    st.markdown(f"""
    <div class="match-card">
      <div class="match-header">
        <span class="match-meta">Grupo {p["grupo"]} · {p["fecha"]} {p["hora"]} · {p["estadio"]}</span>
        {estado_badge}
      </div>
      <div class="match-teams">
        <span class="team-name">{p["local"][0]} {p["local"][1]}</span>
        <span class="score-center">{score}</span>
        <span class="team-name">{p["visita"][0]} {p["visita"][1]}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_prob_bars(home_pct: int, draw_pct: int, away_pct: int, home: str, away: str):
    st.markdown(f"""
    <div style="margin: 0.8rem 0;">
      <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#9ca3af; margin-bottom:2px;">
        <span>{home}</span><span>Empate</span><span>{away}</span>
      </div>
      <div style="display:flex; gap:4px;">
        <div style="flex:{home_pct}; background:#4ade80; height:8px; border-radius:4px;"></div>
        <div style="flex:{draw_pct}; background:#6b7280; height:8px; border-radius:4px;"></div>
        <div style="flex:{away_pct}; background:#f87171; height:8px; border-radius:4px;"></div>
      </div>
      <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#e8eaf0; margin-top:2px; font-weight:500;">
        <span>{home_pct}%</span><span>{draw_pct}%</span><span>{away_pct}%</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── HERO ─────────────────────────────────────────────────────────────────────
dias_restantes = max((date(2026, 6, 11) - date.today()).days, 0)

st.markdown(f"""
<div class="hero-banner">
  <p class="hero-title">Mundial 2026 Dashboard</p>
  <p class="hero-sub">🇨🇦 Canadá · 🇺🇸 Estados Unidos · 🇲🇽 México &nbsp;|&nbsp; 11 junio – 19 julio 2026</p>
</div>
""", unsafe_allow_html=True)

# Métricas principales
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-number">{dias_restantes}</div><div class="metric-label">Días para el inicio</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="metric-card"><div class="metric-number">48</div><div class="metric-label">Selecciones</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="metric-card"><div class="metric-number">104</div><div class="metric-label">Partidos totales</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="metric-card"><div class="metric-number">39</div><div class="metric-label">Días de torneo</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["⚽ Partidos", "📊 Grupos", "🤖 Análisis IA", "🏆 Predictor"])

# ── TAB 1: PARTIDOS ──────────────────────────────────────────────────────────
with tab1:
    st.subheader("Próximos partidos — Jornada 1")

    # Si hay API key, intenta traer datos en vivo
    api_key = get_api_key("FOOTBALL_API_KEY")
    if api_key:
        with st.spinner("Cargando resultados en vivo..."):
            data = football_request("fixtures", {"league": "1", "season": "2026"})
            if data and data.get("response"):
                fixtures = data["response"]
                for f in fixtures[:8]:
                    home = f["teams"]["home"]
                    away = f["teams"]["away"]
                    score_h = f["goals"]["home"] if f["goals"]["home"] is not None else "–"
                    score_a = f["goals"]["away"] if f["goals"]["away"] is not None else "–"
                    status = f["fixture"]["status"]["short"]
                    estado = "en vivo" if status in ("1H","2H","HT","ET","P") else ("finalizado" if status == "FT" else "próximo")
                    fecha_dt = datetime.fromisoformat(f["fixture"]["date"].replace("Z","+00:00"))
                    partido = {
                        "local": ("", home["name"]),
                        "visita": ("", away["name"]),
                        "fecha": fecha_dt.strftime("%d %b"),
                        "hora": fecha_dt.strftime("%H:%M"),
                        "estadio": f["fixture"]["venue"]["name"] or "Por confirmar",
                        "grupo": f.get("league", {}).get("round", "–"),
                        "estado": estado,
                        "score": f"{score_h} : {score_a}",
                    }
                    render_match_card(partido)
            else:
                st.info("API conectada pero sin partidos disponibles aún. Mostrando datos de ejemplo.")
                for p in PARTIDOS_INICIALES:
                    render_match_card(p)
    else:
        st.info("💡 Agrega tu FOOTBALL_API_KEY en `.streamlit/secrets.toml` para ver resultados en tiempo real.")
        for p in PARTIDOS_INICIALES:
            render_match_card(p)

# ── TAB 2: GRUPOS ────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Fase de grupos — Mundial 2026")
    st.caption("El torneo se juega con 12 grupos de 4 equipos. Clasifican los 2 primeros de cada grupo + 8 mejores terceros.")

    # Mostrar grupos en filas de 3
    grupos_lista = list(GRUPOS.items())
    for fila in range(0, len(grupos_lista), 3):
        cols = st.columns(3)
        for col_idx, (grupo, equipos) in enumerate(grupos_lista[fila:fila+3]):
            with cols[col_idx]:
                html = f"""<div class="group-card"><div class="group-title">Grupo {grupo}</div><table style="width:100%;font-size:0.82rem;border-collapse:collapse;"><tr><th style="text-align:left;color:#4b5563;font-size:0.7rem;padding-bottom:6px;">Selección</th><th style="text-align:right;color:#4b5563;font-size:0.7rem;padding-bottom:6px;">PJ</th><th style="text-align:right;color:#4b5563;font-size:0.7rem;padding-bottom:6px;">GD</th><th style="text-align:right;color:#4b5563;font-size:0.7rem;padding-bottom:6px;">Pts</th></tr>"""
                for j, (bandera, nombre) in enumerate(equipos):
                    color = "#4ade80" if j < 2 else "#9ca3af"
                    fw = "600" if j < 2 else "400"
                    html += f"""<tr><td style="color:{color};font-weight:{fw};padding:5px 4px;">{bandera} {nombre}</td><td style="text-align:right;color:#6b7280;padding:5px 4px;">0</td><td style="text-align:right;color:#6b7280;padding:5px 4px;">0</td><td style="text-align:right;color:{color};font-weight:{fw};padding:5px 4px;">0</td></tr>"""
                html += "</table></div>"
                st.markdown(html, unsafe_allow_html=True)


# ── TAB 3: ANÁLISIS IA ───────────────────────────────────────────────────────
with tab3:
    st.subheader("Análisis pre-partido con Claude IA")

    partidos_analizar = [
        ("México vs Sudáfrica", "🇲🇽", "🇿🇦", "México", "Sudáfrica", 55, 25, 20),
        ("Argentina vs Argelia", "🇦🇷", "🇩🇿", "Argentina", "Argelia", 75, 15, 10),
        ("Brasil vs Marruecos", "🇧🇷", "🇲🇦", "Brasil", "Marruecos", 60, 22, 18),
        ("Francia vs Senegal", "🇫🇷", "🇸🇳", "Francia", "Senegal", 62, 22, 16),
        ("España vs Cabo Verde", "🇪🇸", "🇨🇻", "España", "Cabo Verde", 82, 12, 6),
        ("Inglaterra vs Croacia", "🏴", "🇭🇷", "Inglaterra", "Croacia", 55, 25, 20),
        ("Alemania vs Curazao", "🇩🇪", "🇨🇼", "Alemania", "Curazao", 88, 8, 4),
        ("EE.UU. vs Paraguay", "🇺🇸", "🇵🇾", "EE.UU.", "Paraguay", 48, 28, 24),
    ]

    for nombre, f1, f2, local, visita, ph, pd, pa in partidos_analizar:
        with st.expander(f"{f1} {local}  vs  {f2} {visita}"):
            st.markdown(f"**Probabilidades estimadas — {nombre}**")
            render_prob_bars(ph, pd, pa, local, visita)

            col_btn, _ = st.columns([1, 3])
            with col_btn:
                if st.button(f"🤖 Analizar con IA", key=f"btn_{nombre}"):
                    with st.spinner("Claude está analizando el partido..."):
                        prompt = (
                            f"Analiza el partido {local} vs {visita} del Mundial 2026. "
                            f"Incluye: forma reciente de ambos equipos, jugadores clave a seguir, "
                            f"historial de enfrentamientos y tu predicción del resultado. "
                            f"Sé específico y entretenido."
                        )
                        analysis = claude_analyze(prompt)
                        st.markdown(f'<div class="ai-box"><p>{analysis}</p></div>', unsafe_allow_html=True)

# ── TAB 4: PREDICTOR ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("¿Quién ganará el Mundial 2026?")

    st.markdown("**Probabilidades según modelos estadísticos y rendimiento reciente:**")

    for bandera, nombre, pct in FAVORITOS:
        col_name, col_bar, col_pct = st.columns([2, 6, 1])
        with col_name:
            st.markdown(f"<span style='font-size:0.9rem; color:#e8eaf0;'>{bandera} {nombre}</span>", unsafe_allow_html=True)
        with col_bar:
            st.progress(pct / 100)
        with col_pct:
            st.markdown(f"<span style='font-size:0.9rem; font-weight:600; color:#4ade80;'>{pct}%</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("**Pide un análisis personalizado a Claude:**")
    seleccion = st.selectbox(
        "Selecciona una selección para analizar",
        ["Argentina", "Brasil", "Francia", "España", "Inglaterra", "Alemania", "Portugal", "México", "Chile", "Uruguay"],
    )
    if st.button(f"🤖 Analizar chances de {seleccion}"):
        with st.spinner(f"Claude analiza las posibilidades de {seleccion}..."):
            prompt = (
                f"Analiza en detalle las posibilidades de {seleccion} de ganar el Mundial 2026. "
                f"Considera: rendimiento en clasificatorias, plantel actual, entrenador, "
                f"rivales en el grupo y posibles cruces en eliminatorias. "
                f"Da una predicción fundamentada."
            )
            analysis = claude_analyze(prompt)
            st.markdown(f'<div class="ai-box"><p>{analysis}</p></div>', unsafe_allow_html=True)

    st.markdown("<br>")
    st.markdown("**Pregunta libre a Claude sobre el Mundial:**")
    pregunta = st.text_input("¿Qué quieres saber del Mundial 2026?", placeholder="Ej: ¿Quién es el mejor delantero del torneo?")
    if st.button("🤖 Preguntar a Claude") and pregunta:
        with st.spinner("Analizando..."):
            analysis = claude_analyze(pregunta)
            st.markdown(f'<div class="ai-box"><p>{analysis}</p></div>', unsafe_allow_html=True)
