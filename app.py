# ============================================================
#  ⚔️  RPG HABIT TRACKER — Multi-usuario + Gestión de Hábitos
#  pip install streamlit plotly pandas
#  streamlit run app.py
# ============================================================

import streamlit as st
import json, os
from datetime import date, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── CONFIGURACIÓN ────────────────────────────────────────────
st.set_page_config(page_title="⚔️ RPG Hábitos", page_icon="⚔️", layout="centered")
DATA_FILE = "rpg_usuarios.json"

# ── CONSTANTES ───────────────────────────────────────────────
CATEGORIAS = {
    "fisico":     {"label": "⚔️ Físico",      "color": "#ef5350", "stat": "fuerza"},
    "mental":     {"label": "🔮 Mental",      "color": "#42a5f5", "stat": "mente"},
    "salud":      {"label": "💚 Salud",        "color": "#66bb6a", "stat": "vitalidad"},
    "disciplina": {"label": "🏆 Disciplina",  "color": "#ab47bc", "stat": "disciplina"},
}

CLASES = ["Guerrero ⚔️", "Sabio 🔮", "Monje 🧘", "Explorador 🏹"]

ICONOS_CAT = {"fisico": "💪", "mental": "🧠", "salud": "💚", "disciplina": "🎯"}

EVOLUCIONES = [
    {"nivel": 1,  "titulo": "Aprendiz",  "clase": "Novato",     "tip": "Tu aventura comienza. ¡Completa hábitos hoy!"},
    {"nivel": 3,  "titulo": "Iniciado",  "clase": "Explorador", "tip": "¡Vas bien! Mantén tu racha y añade más hábitos."},
    {"nivel": 6,  "titulo": "Guerrero",  "clase": "Guerrero",   "tip": "Tu constancia se nota. Sube la dificultad."},
    {"nivel": 10, "titulo": "Veterano",  "clase": "Veterano",   "tip": "Intenta completar TODOS los hábitos cada día."},
    {"nivel": 15, "titulo": "Campeón",   "clase": "Campeón",    "tip": "Trabaja los stats más débiles."},
    {"nivel": 21, "titulo": "Héroe",     "clase": "Héroe",      "tip": "Eres inspiración. Crea hábitos que otros no se atreven."},
    {"nivel": 28, "titulo": "Leyenda",   "clase": "Leyenda",    "tip": "Has alcanzado la élite absoluta. ¡Nunca pares!"},
]

HABITOS_DEFAULT = [
    {"id": 1, "nombre": "Ejercicio 30 min",    "categoria": "fisico",     "xp": 30, "icono": "💪", "descripcion": "Cardio, pesas o cualquier actividad física"},
    {"id": 2, "nombre": "Leer 20 páginas",      "categoria": "mental",     "xp": 25, "icono": "📚", "descripcion": "Libros, artículos o material educativo"},
    {"id": 3, "nombre": "Meditación 10 min",    "categoria": "salud",      "xp": 20, "icono": "🧘", "descripcion": "Mindfulness o respiración consciente"},
    {"id": 4, "nombre": "Sin redes sociales",   "categoria": "disciplina", "xp": 35, "icono": "🎯", "descripcion": "Evitar Instagram, TikTok, Twitter por un día"},
    {"id": 5, "nombre": "Tomar 2L de agua",     "categoria": "salud",      "xp": 15, "icono": "💧", "descripcion": "Hidratación diaria completa"},
    {"id": 6, "nombre": "Escribir en diario",   "categoria": "mental",     "xp": 20, "icono": "✍️", "descripcion": "Reflexiones, metas o gratitud"},
    {"id": 7, "nombre": "Dormir 8 horas",       "categoria": "salud",      "xp": 25, "icono": "🌙", "descripcion": "Descanso reparador completo"},
    {"id": 8, "nombre": "Caminar 10,000 pasos", "categoria": "fisico",     "xp": 30, "icono": "🏃", "descripcion": "Actividad física diaria mínima"},
]

# ── PERSISTENCIA ─────────────────────────────────────────────
def cargar_todos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"usuarios": {}}

def guardar_todos(todos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2, default=str)

def usuario_default(nombre, clase):
    return {
        "personaje": {
            "nombre": nombre, "clase": clase, "nivel": 1, "xp": 0,
            "stats": {"fuerza": 0, "mente": 0, "vitalidad": 0, "disciplina": 0},
            "racha": 0, "ultimo_dia": None, "total_completados": 0,
        },
        "habitos": HABITOS_DEFAULT,
        "registro": [],
        "next_id": 9,
    }

# ── HELPERS ──────────────────────────────────────────────────
def xp_necesario(nivel): return nivel * 100

def get_evolucion(nivel):
    ev = EVOLUCIONES[0]
    for e in EVOLUCIONES:
        if nivel >= e["nivel"]: ev = e
    return ev

def get_siguiente_ev(nivel):
    for e in EVOLUCIONES:
        if nivel < e["nivel"]: return e
    return None

def calcular_racha(registro):
    dias = sorted({r["fecha"] for r in registro}, reverse=True)
    if not dias: return 0
    racha = 0
    hoy = date.today()
    for i, d in enumerate(dias):
        if d == str(hoy - timedelta(days=i)): racha += 1
        else: break
    return racha

def registros_hoy(data):
    return [r for r in data["registro"] if r["fecha"] == str(date.today())]

def xp_hoy(data):
    return sum(r["xp"] for r in registros_hoy(data))

def completados_hoy(data):
    return {r["habito_id"] for r in registros_hoy(data)}

def subir_niveles(p):
    subio = False
    while p["xp"] >= xp_necesario(p["nivel"]):
        p["xp"] -= xp_necesario(p["nivel"])
        p["nivel"] += 1
        subio = True
    return subio

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #1a2329; }
  [data-testid="stSidebar"]          { background: #0f1923; border-right: 1px solid #263238; }
  .stTabs [data-baseweb="tab-list"]  { background: #263238; border-radius: 12px; padding: 4px; }
  .stTabs [data-baseweb="tab"]       { color: #90a4ae; border-radius: 8px; }
  .stTabs [aria-selected="true"]     { background: #F5B800 !important; color: #000 !important; font-weight: bold; }
  .hero-card { background: linear-gradient(135deg,#1a2f1a,#0f1923); border: 2px solid #F5B800; border-radius:16px; padding:20px; margin-bottom:16px; }
  .nivel-badge { background:#F5B800; color:#000; font-weight:bold; padding:3px 12px; border-radius:20px; display:inline-block; }
  .xp-badge { background:#3a3000; color:#F5B800; font-size:12px; font-weight:bold; padding:2px 10px; border-radius:20px; border:1px solid #7B5E00; display:inline-block; }
  .tip-box { background:#263238; border-left:4px solid #F5B800; border-radius:8px; padding:12px 16px; color:#FFF8DC; font-style:italic; }
  .habit-row { background:#2E3B43; border:1px solid #37474F; border-radius:10px; padding:10px 14px; margin-bottom:6px; }
  .habit-row-done { background:#1B3A1F; border:1px solid #2E7D32; border-radius:10px; padding:10px 14px; margin-bottom:6px; opacity:0.65; }
  .ev-active { background:#2a2000; border:2px solid #F5B800; border-radius:12px; padding:14px; margin-bottom:10px; }
  .ev-done   { background:#1B3A1F; border:1px solid #2E7D32;  border-radius:12px; padding:14px; margin-bottom:10px; opacity:0.7; }
  .ev-lock   { background:#1c1c1c; border:1px solid #37474F;  border-radius:12px; padding:14px; margin-bottom:10px; opacity:0.35; }
  .user-card { background:#263238; border:1px solid #37474F; border-radius:12px; padding:14px; margin-bottom:8px; cursor:pointer; }
  .user-card:hover { border-color:#F5B800; }
  .section-title { color:#F5B800; font-size:13px; font-weight:bold; text-transform:uppercase; letter-spacing:1px; border-left:4px solid #F5B800; padding-left:8px; margin:16px 0 10px; }
  .cat-label { font-size:11px; font-weight:bold; text-transform:uppercase; letter-spacing:1px; padding:4px 10px; border-radius:4px; margin:12px 0 6px; }
  .stButton > button { background:linear-gradient(135deg,#F5B800,#ff9800); color:#000; font-weight:bold; border:none; border-radius:10px; }
  .stButton > button:hover { opacity:0.88; }
  div[data-testid="stMetricValue"] { color:#F5B800 !important; }
  h1,h2,h3 { color:#F5B800 !important; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
#  SIDEBAR — SELECTOR DE USUARIO
# ════════════════════════════════════════════════════════════
def sidebar_usuarios():
    todos = st.session_state.todos
    usuarios = todos.get("usuarios", {})

    with st.sidebar:
        st.markdown("<h2 style='color:#F5B800;margin-bottom:0'>⚔️ Héroes</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#90a4ae;font-size:12px;margin-top:0'>Selecciona o crea un perfil</p>", unsafe_allow_html=True)
        st.markdown("---")

        # Lista de usuarios existentes
        if usuarios:
            for uid, udata in usuarios.items():
                p   = udata["personaje"]
                ev  = get_evolucion(p["nivel"])
                sel = st.session_state.get("usuario_id") == uid
                borde = "#F5B800" if sel else "#37474F"
                st.markdown(f"""
                <div style="background:{'#2a2000' if sel else '#263238'};border:2px solid {borde};
                     border-radius:12px;padding:12px;margin-bottom:6px">
                  <div style="font-weight:bold;color:#F5B800">{p['nombre']}</div>
                  <div style="color:#90a4ae;font-size:11px">Nv.{p['nivel']} · {ev['titulo']}</div>
                  <div style="color:#FF6D00;font-size:11px">🔥 {calcular_racha(udata['registro'])} días</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Jugar como {p['nombre']}", key=f"sel_{uid}"):
                    st.session_state.usuario_id = uid
                    st.session_state.pantalla   = "main"
                    st.rerun()
        else:
            st.info("Aún no hay héroes. ¡Crea el primero!")

        st.markdown("---")
        if st.button("➕ Crear nuevo héroe", use_container_width=True):
            st.session_state.pantalla = "crear"
            st.rerun()

        # Eliminar usuario activo
        if st.session_state.get("usuario_id") and st.session_state.get("pantalla") == "main":
            st.markdown("---")
            with st.expander("⚠️ Zona peligrosa"):
                st.warning("Esto borrará permanentemente este héroe.")
                if st.button("🗑️ Eliminar este héroe", key="del_user"):
                    uid = st.session_state.usuario_id
                    del todos["usuarios"][uid]
                    guardar_todos(todos)
                    st.session_state.todos      = todos
                    st.session_state.usuario_id = None
                    st.session_state.pantalla   = "crear"
                    st.rerun()

# ════════════════════════════════════════════════════════════
#  PANTALLA: CREAR PERSONAJE
# ════════════════════════════════════════════════════════════
def pantalla_crear():
    st.markdown("<h1 style='text-align:center'>⚔️ Nuevo Héroe</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#90a4ae'>Crea tu personaje y comienza tu aventura</p>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        nombre = st.text_input("🧙 Nombre del héroe", placeholder="¿Cómo te llamas?", key="inp_nombre")
        clase  = st.selectbox("⚔️ Clase", CLASES, key="inp_clase")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 ¡Crear héroe!", use_container_width=True):
            if not nombre.strip():
                st.error("Escribe un nombre para continuar.")
            else:
                todos    = st.session_state.todos
                uid      = nombre.strip().lower().replace(" ", "_") + f"_{len(todos['usuarios'])}"
                todos["usuarios"][uid] = usuario_default(nombre.strip(), clase)
                guardar_todos(todos)
                st.session_state.todos      = todos
                st.session_state.usuario_id = uid
                st.session_state.pantalla   = "main"
                st.rerun()

# ════════════════════════════════════════════════════════════
#  PANTALLA: MAIN
# ════════════════════════════════════════════════════════════
def pantalla_main():
    todos = st.session_state.todos
    uid   = st.session_state.usuario_id
    data  = todos["usuarios"][uid]
    p     = data["personaje"]
    ev    = get_evolucion(p["nivel"])
    sig   = get_siguiente_ev(p["nivel"])
    xp_n  = xp_necesario(p["nivel"])
    pct   = min(p["xp"] / xp_n, 1.0)
    racha = calcular_racha(data["registro"])
    p["racha"] = racha

    # ── HEADER HÉROE ─────────────────────────────────────────
    st.markdown(f"""
    <div class="hero-card">
      <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
        <div style="font-size:52px">⚔️</div>
        <div style="flex:1">
          <div style="font-size:22px;font-weight:bold;color:#F5B800">{p['nombre']}</div>
          <div style="color:#90a4ae;font-size:13px">{p['clase']} · {ev['titulo']}</div>
          <div style="margin-top:6px">
            <span class="nivel-badge">Nv. {p['nivel']}</span>
            <span style="color:#FF6D00;margin-left:10px;font-size:13px">🔥 {racha} días de racha</span>
          </div>
        </div>
        <div style="text-align:right">
          <div style="color:#F5B800;font-size:24px;font-weight:bold">+{xp_hoy(data)}</div>
          <div style="color:#90a4ae;font-size:11px">XP hoy</div>
        </div>
      </div>
      <div style="margin-top:12px">
        <div style="display:flex;justify-content:space-between;color:#90a4ae;font-size:11px;margin-bottom:4px">
          <span>{p['xp']} / {xp_n} XP</span><span>{int(pct*100)}%</span>
        </div>
        <div style="background:#37474F;border-radius:10px;height:10px">
          <div style="background:linear-gradient(90deg,#F5B800,#ff9800);width:{int(pct*100)}%;height:10px;border-radius:10px"></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if sig:
        st.markdown(f"<p style='color:#546e7a;font-size:12px;margin-top:-8px'>⬆️ Próxima evolución: <b style='color:#F5B800'>{sig['titulo']}</b> en nivel {sig['nivel']} · {sig['nivel']-p['nivel']} niveles más</p>", unsafe_allow_html=True)

    # ── TABS ─────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚔️ Hábitos", "🛠️ Mis Hábitos", "📊 Stats", "📈 Progreso", "🌟 Evolución"])

    # ══ TAB 1: REGISTRAR HÁBITOS DEL DÍA ════════════════════
    with tab1:
        completados = completados_hoy(data)
        hoy_str     = str(date.today())
        total_h     = len(data["habitos"])

        st.markdown(f"<p style='color:#90a4ae'>📅 {date.today().strftime('%d/%m/%Y')} &nbsp;·&nbsp; {len(completados)}/{total_h} completados hoy</p>", unsafe_allow_html=True)

        if not data["habitos"]:
            st.warning("No tienes hábitos todavía. Ve a la pestaña **🛠️ Mis Hábitos** y añade los tuyos.")
        else:
            for cat_key, cat_info in CATEGORIAS.items():
                habs_cat = [h for h in data["habitos"] if h["categoria"] == cat_key]
                if not habs_cat: continue

                st.markdown(f"<div class='cat-label' style='color:{cat_info['color']};border-left:4px solid {cat_info['color']};padding-left:8px'>{cat_info['label']}</div>", unsafe_allow_html=True)

                for h in habs_cat:
                    done = h["id"] in completados
                    css  = "habit-row-done" if done else "habit-row"
                    c1,c2,c3,c4 = st.columns([0.07, 0.55, 0.22, 0.16])
                    with c1:
                        st.markdown(f"<div style='font-size:20px;margin-top:6px'>{h.get('icono','⚡')}</div>", unsafe_allow_html=True)
                    with c2:
                        tachado = "text-decoration:line-through;color:#546e7a" if done else "color:#eceff1"
                        desc    = h.get("descripcion","")
                        st.markdown(f"<div style='{tachado};margin-top:4px;font-size:13px'>{h['nombre']}</div>{'<div style=\"color:#546e7a;font-size:11px\">'+desc+'</div>' if desc and not done else ''}", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"<div style='margin-top:8px'><span class='xp-badge'>+{h['xp']} XP</span></div>", unsafe_allow_html=True)
                    with c4:
                        if done:
                            st.markdown("<div style='color:#66bb6a;font-size:22px;text-align:center;margin-top:4px'>✓</div>", unsafe_allow_html=True)
                        else:
                            if st.button("✓ Hecho", key=f"done_{h['id']}"):
                                stat = CATEGORIAS[h["categoria"]]["stat"]
                                data["registro"].append({
                                    "fecha": hoy_str, "habito_id": h["id"],
                                    "nombre": h["nombre"], "categoria": h["categoria"], "xp": h["xp"]
                                })
                                p["xp"] += h["xp"]
                                p["stats"][stat] += 1
                                p["total_completados"] += 1
                                p["ultimo_dia"] = hoy_str
                                subio = subir_niveles(p)
                                guardar_todos(todos)
                                if subio:
                                    st.session_state.nivel_up = get_evolucion(p["nivel"])
                                st.rerun()

        # NIVEL UP
        if "nivel_up" in st.session_state and st.session_state.nivel_up:
            ev_up = st.session_state.nivel_up
            st.balloons()
            st.success(f"🌟 ¡SUBISTE AL NIVEL {p['nivel']}! — Ahora eres **{ev_up['titulo']} · {ev_up['clase']}**\n\n💡 {ev_up['tip']}")
            if st.button("¡Seguir adelante! ⚔️"):
                del st.session_state.nivel_up
                st.rerun()

    # ══ TAB 2: GESTIÓN DE HÁBITOS ════════════════════════════
    with tab2:
        st.markdown("<div class='section-title'>➕ Crear nuevo hábito</div>", unsafe_allow_html=True)

        with st.form("form_crear_habito", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                n_nombre = st.text_input("Nombre del hábito *", placeholder="Ej: Correr 5km")
            with c2:
                n_cat = st.selectbox("Categoría *", list(CATEGORIAS.keys()),
                                     format_func=lambda k: CATEGORIAS[k]["label"])
            c3, c4, c5 = st.columns(3)
            with c3:
                n_xp   = st.number_input("XP (recompensa)", min_value=5, max_value=100, value=20, step=5)
            with c4:
                n_icono = st.text_input("Icono (emoji)", value=ICONOS_CAT.get(n_cat,"⚡"), max_chars=2)
            with c5:
                n_desc = st.text_input("Descripción (opcional)", placeholder="Breve descripción")

            submitted = st.form_submit_button("➕ Crear hábito", use_container_width=True)
            if submitted:
                if not n_nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    data["habitos"].append({
                        "id":          data["next_id"],
                        "nombre":      n_nombre.strip(),
                        "categoria":   n_cat,
                        "xp":          n_xp,
                        "icono":       n_icono or ICONOS_CAT.get(n_cat,"⚡"),
                        "descripcion": n_desc.strip(),
                    })
                    data["next_id"] += 1
                    guardar_todos(todos)
                    st.success(f"✅ Hábito **{n_nombre}** creado con +{n_xp} XP")
                    st.rerun()

        st.markdown("<div class='section-title'>📋 Tus hábitos actuales</div>", unsafe_allow_html=True)

        if not data["habitos"]:
            st.info("Aún no tienes hábitos. ¡Crea tu primero arriba!")
        else:
            # Editar y eliminar
            for cat_key, cat_info in CATEGORIAS.items():
                habs_cat = [h for h in data["habitos"] if h["categoria"] == cat_key]
                if not habs_cat: continue
                st.markdown(f"<div class='cat-label' style='color:{cat_info['color']};border-left:4px solid {cat_info['color']};padding-left:8px'>{cat_info['label']}</div>", unsafe_allow_html=True)

                for h in habs_cat:
                    with st.expander(f"{h.get('icono','⚡')} {h['nombre']}  ·  +{h['xp']} XP"):
                        with st.form(f"edit_{h['id']}"):
                            ec1, ec2 = st.columns(2)
                            with ec1: e_nombre = st.text_input("Nombre", value=h["nombre"], key=f"en_{h['id']}")
                            with ec2: e_cat    = st.selectbox("Categoría", list(CATEGORIAS.keys()),
                                                               index=list(CATEGORIAS.keys()).index(h["categoria"]),
                                                               format_func=lambda k: CATEGORIAS[k]["label"],
                                                               key=f"ec_{h['id']}")
                            ec3, ec4, ec5 = st.columns(3)
                            with ec3: e_xp    = st.number_input("XP", 5, 100, int(h["xp"]), 5, key=f"ex_{h['id']}")
                            with ec4: e_icono = st.text_input("Icono", value=h.get("icono","⚡"), max_chars=2, key=f"ei_{h['id']}")
                            with ec5: e_desc  = st.text_input("Descripción", value=h.get("descripcion",""), key=f"ed_{h['id']}")

                            bc1, bc2 = st.columns(2)
                            with bc1:
                                if st.form_submit_button("💾 Guardar cambios", use_container_width=True):
                                    for hab in data["habitos"]:
                                        if hab["id"] == h["id"]:
                                            hab["nombre"]      = e_nombre.strip() or hab["nombre"]
                                            hab["categoria"]   = e_cat
                                            hab["xp"]          = e_xp
                                            hab["icono"]       = e_icono or "⚡"
                                            hab["descripcion"] = e_desc.strip()
                                    guardar_todos(todos)
                                    st.success("Guardado ✅"); st.rerun()
                            with bc2:
                                if st.form_submit_button("🗑️ Eliminar", use_container_width=True):
                                    data["habitos"] = [hab for hab in data["habitos"] if hab["id"] != h["id"]]
                                    guardar_todos(todos)
                                    st.success("Eliminado"); st.rerun()

    # ══ TAB 3: STATS ═════════════════════════════════════════
    with tab3:
        stats    = p["stats"]
        max_stat = max(max(stats.values(), default=1), 1)

        vals = [stats["fuerza"], stats["mente"], stats["vitalidad"], stats["disciplina"]]
        cats_r = ["Fuerza ⚔️","Mente 🔮","Vitalidad 💚","Disciplina 🏆"]
        fig_r = go.Figure(go.Scatterpolar(
            r=vals+[vals[0]], theta=cats_r+[cats_r[0]],
            fill='toself', fillcolor='rgba(245,184,0,0.15)',
            line=dict(color='#F5B800',width=2), marker=dict(color='#F5B800',size=6),
        ))
        fig_r.update_layout(
            polar=dict(bgcolor='#263238',
                radialaxis=dict(visible=True,color='#546e7a',gridcolor='#37474F'),
                angularaxis=dict(color='#90a4ae',gridcolor='#37474F')),
            paper_bgcolor='#1a2329', margin=dict(l=30,r=30,t=30,b=30), height=300, showlegend=False,
        )
        st.plotly_chart(fig_r, use_container_width=True, config={'displayModeBar':False})

        colores_s = {"fuerza":"#ef5350","mente":"#42a5f5","vitalidad":"#66bb6a","disciplina":"#ab47bc"}
        labels_s  = {"fuerza":"⚔️ Fuerza","mente":"🔮 Mente","vitalidad":"💚 Vitalidad","disciplina":"🏆 Disciplina"}
        for stat, val in stats.items():
            pct_s = min(val / max(max_stat, 50), 1.0)
            st.markdown(f"""
            <div style='margin-bottom:10px'>
              <div style='display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px'>
                <span style='color:{colores_s[stat]}'>{labels_s[stat]}</span>
                <span style='color:#fff;font-weight:bold'>{val} pts</span>
              </div>
              <div style='background:#37474F;border-radius:10px;height:10px'>
                <div style='background:{colores_s[stat]};width:{int(pct_s*100)}%;height:10px;border-radius:10px'></div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🏆 Nivel",   p["nivel"])
        c2.metric("✅ Total",   p["total_completados"])
        c3.metric("🔥 Racha",   f"{racha} días")
        c4.metric("⭐ Clase",   ev["clase"])
        st.markdown(f"<div class='tip-box' style='margin-top:16px'>💡 {ev['tip']}</div>", unsafe_allow_html=True)

    # ══ TAB 4: PROGRESO ══════════════════════════════════════
    with tab4:
        if not data["registro"]:
            st.info("Aún no hay registros. ¡Completa tu primer hábito!")
        else:
            df = pd.DataFrame(data["registro"])
            df["fecha"] = pd.to_datetime(df["fecha"])
            hoy_d = date.today()
            fechas = [str(hoy_d - timedelta(days=i)) for i in range(13,-1,-1)]
            xp_dia = df.groupby(df["fecha"].dt.strftime("%Y-%m-%d"))["xp"].sum().to_dict()
            y_xp   = [xp_dia.get(f,0) for f in fechas]
            labels = [(hoy_d - timedelta(days=13-i)).strftime("%d/%m") for i in range(14)]

            fig_l = go.Figure()
            fig_l.add_trace(go.Scatter(
                x=labels, y=y_xp, mode='lines+markers',
                line=dict(color='#F5B800',width=2), marker=dict(color='#F5B800',size=7),
                fill='tozeroy', fillcolor='rgba(245,184,0,0.1)',
            ))
            fig_l.update_layout(
                title=dict(text='⭐ XP por día (últimas 2 semanas)',font=dict(color='#F5B800')),
                paper_bgcolor='#1a2329', plot_bgcolor='#263238',
                xaxis=dict(color='#90a4ae',gridcolor='#37474F'),
                yaxis=dict(color='#90a4ae',gridcolor='#37474F'),
                margin=dict(l=10,r=10,t=40,b=10), height=240, showlegend=False,
            )
            st.plotly_chart(fig_l, use_container_width=True, config={'displayModeBar':False})

            cat_counts = df.groupby("categoria")["xp"].sum().reset_index()
            cat_counts["label"] = cat_counts["categoria"].map(lambda k: CATEGORIAS.get(k,{}).get("label",k))
            fig_p = px.pie(cat_counts, values="xp", names="label",
                           color_discrete_sequence=[CATEGORIAS.get(c,{}).get("color","#aaa") for c in cat_counts["categoria"]],
                           hole=0.4)
            fig_p.update_layout(title=dict(text='📊 XP por categoría',font=dict(color='#F5B800')),
                                 paper_bgcolor='#1a2329',font=dict(color='#eceff1'),
                                 margin=dict(l=10,r=10,t=40,b=10),height=270)
            st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar':False})

            st.markdown("<div class='section-title'>📋 Historial reciente</div>", unsafe_allow_html=True)
            df_show = df.sort_values("fecha",ascending=False).head(20).copy()
            df_show["fecha"] = df_show["fecha"].dt.strftime("%d/%m/%Y")
            df_show["xp"]   = df_show["xp"].astype(str)+" XP"
            df_show = df_show.rename(columns={"fecha":"Fecha","nombre":"Hábito","categoria":"Categoría","xp":"XP"})
            st.dataframe(df_show[["Fecha","Hábito","Categoría","XP"]], use_container_width=True, hide_index=True)

            csv_b = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Exportar CSV", csv_b, f"habitos_{p['nombre']}.csv", "text/csv")

    # ══ TAB 5: EVOLUCIÓN ═════════════════════════════════════
    with tab5:
        st.markdown("<p style='color:#90a4ae'>Tu camino de transformación como héroe</p>", unsafe_allow_html=True)
        for e in EVOLUCIONES:
            desbloq = p["nivel"] >= e["nivel"]
            actual  = ev["nivel"] == e["nivel"]
            css = "ev-active" if actual else "ev-done" if desbloq else "ev-lock"
            ico = "🌟" if actual else "✅" if desbloq else "🔒"
            badge = "<span style='background:#F5B800;color:#000;font-size:11px;font-weight:bold;padding:2px 8px;border-radius:20px;margin-left:8px'>ACTUAL</span>" if actual else ""
            tip   = f"<p style='color:#90a4ae;font-size:12px;margin-top:6px'>{e['tip']}</p>" if desbloq else ""
            color = "#F5B800" if actual else "#81C784" if desbloq else "#546e7a"
            st.markdown(f"""
            <div class="{css}">
              <div style="display:flex;align-items:center;gap:10px">
                <span style="font-size:26px">{ico}</span>
                <div>
                  <span style="font-weight:bold;color:{color}">{e['titulo']} — {e['clase']}</span>{badge}
                  <div style="color:#546e7a;font-size:11px">Nivel {e['nivel']}+</div>
                </div>
              </div>
              {tip}
            </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════
if "todos" not in st.session_state:
    st.session_state.todos = cargar_todos()

if "pantalla" not in st.session_state:
    usuarios = st.session_state.todos.get("usuarios", {})
    st.session_state.pantalla   = "main" if usuarios else "crear"
    st.session_state.usuario_id = next(iter(usuarios), None)

sidebar_usuarios()

if st.session_state.pantalla == "crear":
    pantalla_crear()
elif st.session_state.pantalla == "main" and st.session_state.get("usuario_id"):
    pantalla_main()
else:
    pantalla_crear()
