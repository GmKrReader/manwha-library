import streamlit as st
import pandas as pd
from supabase_client import supabase
from collections import defaultdict
from rapidfuzz import fuzz
import unicodedata


# =====================
# CONFIG
# =====================
st.set_page_config(
    page_title="Biblioteca Manhwa",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================
# AUTH
# =====================
def login_user(email, password):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if result.user:
            st.session_state["authenticated"] = True
            st.session_state["user"] = result.user.email
            return True

        return False

    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False


def logout_user():
    try:
        supabase.auth.sign_out()
    except:
        pass

    st.session_state.clear()
    st.rerun()


def show_login():
    st.title("📚 Biblioteca Manhwa")

    st.markdown("### 🔐 Iniciar sesión")

    email = st.text_input("Correo")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar", use_container_width=True):

        if not email or not password:
            st.warning("Completa todos los campos")
            return

        if login_user(email, password):
            st.success("Acceso concedido")
            st.rerun()
        else:
            st.error("Correo o contraseña incorrectos")


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "add_step" not in st.session_state:
    st.session_state["add_step"] = "input"

if "parsed_works_cache" not in st.session_state:
    st.session_state["parsed_works_cache"] = None

if not st.session_state["authenticated"]:
    show_login()
    st.stop()

# =====================
# CSS RESPONSIVO CON SOPORTE DARK MODE
# =====================
st.markdown("""
    <style>
    /* Variables que se adaptan al tema */
    :root {
        --bg-color: var(--streamlit-bg-color, #ffffff);
        --text-color: var(--streamlit-text-color, #000000);
        --border-color: var(--streamlit-border-color, #e0e0e0);
        --card-bg: var(--streamlit-card-bg, #f8f9fa);
    }
    
    /* Estilos base responsivos */
    .stApp {
        transition: all 0.3s ease;
    }
    
    /* Mejorar los botones */
    .stButton > button {
        border-radius: 8px;
        transition: all 0.3s;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Mejorar los expanders para dark mode */
    .streamlit-expanderHeader {
        background-color: transparent;
        border-radius: 8px;
        font-weight: 600;
        border: 1px solid var(--border-color);
    }
    
    .streamlit-expanderHeader:hover {
        background-color: rgba(128, 128, 128, 0.1);
    }
    
    /* Mejorar los text area */
    textarea {
        font-family: 'Courier New', monospace;
        font-size: 14px !important;
        line-height: 1.5 !important;
    }
    
    /* Mejorar los inputs en dark mode */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background-color: transparent;
    }
    
    /* Preview de imagen mejorado */
    .image-preview {
        border-radius: 8px;
        border: 2px solid var(--border-color);
        padding: 5px;
        background-color: var(--card-bg);
    }
    
    /* Badges y etiquetas */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px;
    }
    
    .badge-favorite {
        background-color: #ffd700;
        color: #000000;
    }
    
    .badge-smut {
        background-color: #dc2626;
        color: #ffffff;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--card-bg);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* Contenedor para agregar obras */
    .add-works-container {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 30px;
        border: 2px solid var(--border-color);
        animation: fadeIn 0.3s ease-out;
    }
    
    /* Contenedor de edición */
    .edit-form-container {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 30px;
        border: 2px solid var(--border-color);
        animation: fadeIn 0.3s ease-out;
    }
    </style>
""", unsafe_allow_html=True)
# =====================
# SAFE FUNCTIONS
# =====================
def safe_int(value, default=0):
    if pd.isna(value) or value is None:
        return default
    try:
        return int(value)
    except:
        return default

def clean(value):
    if value is None:
        return None
    if pd.isna(value):
        return None
    if str(value).lower() == "nan":
        return None
    return value

def safe_str(value):
    value = clean(value)
    return "" if value is None else str(value)

def normalize_text(text: str) -> str:
    """Normaliza texto para comparación (elimina acentos, espacios, convierte a minúsculas)"""
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text.lower())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = ''.join(c for c in text if c.isalnum() or c.isspace())
    return ' '.join(text.split())

def detect_smut(work_text: str) -> bool:
    """Detecta si una obra puede ser +18/smut basado en palabras clave"""
    smut_keywords = [
        "smut", "18+", "+18", "adult", "mature", "erotic", "ecchi", "hentai",
        "sexual", "desnudo", "sexo", "porn", "porno", "xxx", "nsfw",
        "manhwa 18", "adult manhwa", "mature content", "성인", "성인물", "19금"
    ]
    
    work_lower = work_text.lower()
    
    for keyword in smut_keywords:
        if keyword in work_lower:
            return True
    
    return False

def parse_bulk_input(input_text: str) -> list:
    """
    Parsea el input del usuario y retorna una lista de obras con sus aliases
    Formato esperado:
    - Obra1 / alias1 / alias2
    - Obra2
    - Obra3 / alias3
    
    Mejorado para manejar correctamente los separadores y espacios
    """
    works = []
    lines = input_text.strip().split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        # Dividir por '/' y limpiar cada parte
        # Importante: split('/') mantiene la integridad de cada parte
        parts = line.split('/')
        
        # Limpiar cada parte (eliminar espacios al inicio y final)
        cleaned_parts = [part.strip() for part in parts if part.strip()]
        
        if cleaned_parts:
            # La primera parte es el título principal
            title = cleaned_parts[0]
            # El resto son aliases (si hay más de una parte)
            aliases = cleaned_parts[1:] if len(cleaned_parts) > 1 else []
            
            # Validar que el título no esté vacío
            if title:
                work_info = {
                    "title": title,
                    "aliases": aliases
                }
                works.append(work_info)
            else:
                st.warning(f"Línea {line_num}: Título vacío después de limpiar")
    
    return works

# =====================
# LOAD DATA (MEJORADO)
# =====================
@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    with st.spinner("Cargando biblioteca..."):
        response = supabase.table("works").select("*").order("title").execute()
        df = pd.DataFrame(response.data)
        
        aliases_res = supabase.table("aliases").select("*").execute()
        aliases_df = pd.DataFrame(aliases_res.data)
        
        return df, aliases_df

def build_alias_map(aliases_df):
    """Construye el mapa de aliases desde el DataFrame"""
    alias_map = defaultdict(list)
    if not aliases_df.empty:
        for _, row in aliases_df.iterrows():
            wid = row["work_id"]
            alias_map[wid].append({
                "id": row["id"],
                "alias": row["alias"]
            })
    return alias_map

# Cargar datos iniciales
df, aliases_df = load_data()
alias_map = build_alias_map(aliases_df)

# =====================
# SCORE FUNCTION
# =====================
def score_work(row, query):
    if not query:
        return 1

    q = query.lower().strip()
    title = str(row.get("title") or "").lower()
    work_id = row.get("id")
    aliases = alias_map.get(work_id, [])
    alias_text = " ".join([a.get("alias", "") for a in aliases if isinstance(a, dict)]).lower()
    title_score = fuzz.partial_ratio(q, title)
    alias_score = fuzz.partial_ratio(q, alias_text)
    exact_boost = 100 if q == title else 0
    return max(title_score, alias_score) + exact_boost

# =====================
# FUNCIÓN PARA VERIFICAR EXISTENCIA DE OBRA (MEJORADA)
# =====================
def check_work_exists(title: str, aliases: list, alias_map: dict, df: pd.DataFrame) -> tuple:
    """
    Verifica si una obra ya existe en la base de datos
    Verifica tanto el título como TODOS los aliases
    Retorna: (existe, id, nombre_encontrado, tipo_match)
    """
    # Normalizar título principal
    normalized_title = normalize_text(title)
    
    # 1. Verificar si el título principal ya existe
    for _, work in df.iterrows():
        if normalize_text(work.get("title", "")) == normalized_title:
            return True, work["id"], work["title"], "título"
    
    # 2. Verificar si el título principal coincide con algún alias existente
    for work_id, existing_aliases in alias_map.items():
        for alias_data in existing_aliases:
            if normalize_text(alias_data.get("alias", "")) == normalized_title:
                work = df[df["id"] == work_id].iloc[0]
                return True, work_id, work["title"], f"alias '{alias_data.get('alias')}'"
    
    # 3. Verificar si ALGUNO de los aliases ingresados ya existe en la BD
    for alias in aliases:
        normalized_alias = normalize_text(alias)
        
        # 3a. Verificar si el alias coincide con algún título existente
        for _, work in df.iterrows():
            if normalize_text(work.get("title", "")) == normalized_alias:
                return True, work["id"], work["title"], f"título (alias '{alias}' coincide con título)"
        
        # 3b. Verificar si el alias coincide con algún alias existente
        for work_id, existing_aliases in alias_map.items():
            for alias_data in existing_aliases:
                if normalize_text(alias_data.get("alias", "")) == normalized_alias:
                    work = df[df["id"] == work_id].iloc[0]
                    return True, work_id, work["title"], f"alias '{alias_data.get('alias')}' (coincide con alias ingresado)"
    
    # 4. Búsqueda difusa (para títulos muy similares)
    best_match = None
    best_score = 0
    
    # Verificar todos los textos (título + aliases ingresados)
    texts_to_check = [normalized_title] + [normalize_text(a) for a in aliases]
    
    for text_to_check in texts_to_check:
        for _, work in df.iterrows():
            # Comparar con títulos existentes
            title_score = fuzz.ratio(text_to_check, normalize_text(work.get("title", "")))
            if title_score > 85 and title_score > best_score:
                best_score = title_score
                best_match = (work["id"], work["title"], "título (similar)")
            
            # Comparar con aliases existentes
            for alias_data in alias_map.get(work["id"], []):
                alias_score = fuzz.ratio(text_to_check, normalize_text(alias_data.get("alias", "")))
                if alias_score > 85 and alias_score > best_score:
                    best_score = alias_score
                    best_match = (work["id"], work["title"], f"alias similar '{alias_data.get('alias')}'")
    
    if best_match:
        return True, best_match[0], best_match[1], best_match[2]
    
    return False, None, None, None

# =====================
# FUNCIÓN PARA ACTUALIZAR DATOS (NUEVA)
# =====================
def refresh_data():
    """Recarga los datos desde Supabase y actualiza las variables globales"""
    global df, aliases_df, alias_map
    df, aliases_df = load_data()
    alias_map = build_alias_map(aliases_df)
    st.cache_data.clear()

# =====================
# FUNCIÓN PARA AGREGAR OBRAS (MEJORADA)
# =====================
def show_add_works_modal():
    """Muestra el formulario para agregar obras (VERSIÓN FIXED + FLOW ESTABLE)"""

    st.markdown('<div class="add-works-container fade-in">', unsafe_allow_html=True)

    st.markdown("## ➕ Agregar nuevas obras")

    # =========================
    # INIT STATE
    # =========================
    
    if "add_step" not in st.session_state:
        st.session_state["add_step"] = "input"

    if "parsed_works_cache" not in st.session_state:
        st.session_state["parsed_works_cache"] = None

    # =========================
    # INPUT STEP
    # =========================
    if st.session_state["add_step"] == "input":

        works_input = st.text_area(
            "**Lista de obras a agregar**",
            height=200,
            placeholder="Ejemplo:\nSolo Leveling\nDeja que te enseñe / Asi no se hace / The Carry\nEl héroe ha regresado / Hero Has Returned",
            help="Cada línea es una obra. Usa '/' para aliases"
        )

        st.markdown("### ⚙️ Opciones")

        col1, col2 = st.columns(2)

        with col1:
            auto_detect_smut = st.checkbox(
                "🔞 Detectar automáticamente si es +18",
                value=True
            )

        with col2:
            default_status = st.selectbox(
                "📌 Estado por defecto",
                options=["PLANNED", "READING", "COMPLETED"],
                index=0
            )

        col_btn1, col_btn2 = st.columns(2)

        # =========================
        # PROCESS BUTTON
        # =========================
        with col_btn1:
            if st.button("🔍 Procesar y verificar", use_container_width=True, type="primary"):

                if not works_input.strip():
                    st.warning("Por favor ingresa obras")
                else:
                    parsed = parse_bulk_input(works_input)

                    st.session_state["parsed_works_cache"] = {
                        "data": parsed,
                        "auto_detect_smut": auto_detect_smut,
                        "default_status": default_status
                    }

                    st.session_state["add_step"] = "preview"
                    st.rerun()

        with col_btn2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.pop("show_add_works", None)
                st.rerun()

    # =========================
    # PREVIEW STEP
    # =========================
    elif st.session_state["add_step"] == "preview":

        cache = st.session_state["parsed_works_cache"]

        if not cache:
            st.error("No hay datos procesados")
            st.session_state["add_step"] = "input"
            st.rerun()

        parsed_works = cache["data"]
        auto_detect_smut = cache["auto_detect_smut"]
        default_status = cache["default_status"]

        st.markdown("## 📊 Preview de agregación")

        existing_works = []
        new_works = []
        duplicates_in_list = []
        seen_titles = set()

        for work_info in parsed_works:

            title = work_info["title"]
            aliases = work_info["aliases"]
            normalized_title = normalize_text(title)

            # duplicados internos
            if normalized_title in seen_titles:
                duplicates_in_list.append(title)
                continue

            seen_titles.add(normalized_title)

            # check BD
            exists, work_id, found_name, match_type = check_work_exists(
                title, aliases, alias_map, df
            )

            if exists:
                existing_works.append({
                    "input": title,
                    "aliases": aliases,
                    "found_as": found_name,
                    "match_type": match_type
                })
            else:
                is_smut = False

                if auto_detect_smut:
                    is_smut = detect_smut(title)
                    for a in aliases:
                        if detect_smut(a):
                            is_smut = True

                new_works.append({
                    "title": title,
                    "aliases": aliases,
                    "smut": is_smut
                })

        # =========================
        # RESULTS
        # =========================

        if existing_works:
            st.error(f"❌ Ya existentes ({len(existing_works)}):")
            for w in existing_works:
                aliases_txt = ", ".join(w["aliases"]) if w["aliases"] else "-"
                st.write(f"- {w['input']} → {w['found_as']} ({w['match_type']})")

        if duplicates_in_list:
            st.warning(f"🔄 Duplicados en lista ({len(duplicates_in_list)}):")
            for d in duplicates_in_list:
                st.write(f"- {d}")

        # En la sección de resultados, mejora la visualización:
        if new_works:
            st.success(f"✅ Nuevas obras ({len(new_works)}):")
            
            for w in new_works:
                smut_badge = " 🔞" if w["smut"] else ""
                
                # Mostrar título y aliases correctamente formateados
                if w["aliases"]:
                    aliases_display = f" → Aliases: {', '.join(w['aliases'])}"
                else:
                    aliases_display = ""
                
                st.write(f"- **{w['title']}**{smut_badge}{aliases_display}")

        # =========================
        # ACTIONS
        # =========================

        st.markdown("---")

        col1, col2 = st.columns(2)

        # CONFIRM
        with col1:
            if st.button("✅ Confirmar inserción", type="primary", use_container_width=True):

                if not new_works:
                    st.warning("No hay obras nuevas para insertar")
                    return

                with st.spinner("Insertando obras..."):

                    added = 0

                    for w in new_works:

                        try:
                            res = supabase.table("works").insert({
                                "title": w["title"],
                                "title_normalized": normalize_text(w["title"]),
                                "smut": w["smut"],
                                "favorite": False,
                                "personal_status": default_status,
                                "personal_rating": None,
                                "chapter_count": 0,
                                "publication_status": "ONGOING",
                                "cover_url": None,
                                "synopsis": None,
                                "review": None
                            }).execute()

                            if res.data:
                                wid = res.data[0]["id"]
                                added += 1

                                for a in w["aliases"]:
                                    if a.strip():
                                        supabase.table("aliases").insert({
                                            "work_id": wid,
                                            "alias": a.strip(),
                                            "alias_normalized": normalize_text(a)
                                        }).execute()

                        except Exception as e:
                            st.error(f"Error en {w['title']}: {e}")

                    refresh_data()

                st.success(f"✅ Agregadas {added} obras")
                st.balloons()

                st.session_state["add_step"] = "input"
                st.session_state["parsed_works_cache"] = None
                st.session_state.pop("show_add_works", None)

                st.rerun()

        # BACK
        with col2:
            if st.button("🔙 Volver", use_container_width=True):
                st.session_state["add_step"] = "input"
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# =====================
# FUNCIÓN PARA EDITAR OBRA (MEJORADA)
# =====================
def show_edit_form(work, edit_id):
    """Muestra el formulario de edición mejorado en la parte superior"""
    
    st.markdown('<div class="edit-form-container fade-in">', unsafe_allow_html=True)
    
    col_close1, col_close2, col_close3 = st.columns([6, 1, 1])
    with col_close1:
        st.markdown(f"## ✏️ Editando: {work.get('title')}")
    with col_close3:
        if st.button("❌ Cerrar", key="close_edit_btn", use_container_width=True):
            if "edit_work" in st.session_state:
                del st.session_state["edit_work"]
                st.rerun()
    
    st.markdown("---")
    
    with st.form(f"edit_form_{edit_id}", clear_on_submit=False):
        
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown("### 📖 Información Principal")
            title = st.text_input(
                "**Título**",
                value=work.get("title") or "",
                placeholder="Ingresa el título de la obra"
            )
            
            st.markdown("### 📝 Review / Reseña")
            review = st.text_area(
                "**Review**",
                value=safe_str(work.get("review")),
                height=350,
                placeholder="Escribe tu reseña detallada aquí..."
            )
        
        with col_right:
            st.markdown("### ⭐ Calificación")
            
            rating_value = work.get("personal_rating")
            rating_value = None if pd.isna(rating_value) else rating_value
            
            rating = st.number_input(
                "**Rating (0-10)**",
                min_value=0,
                max_value=10,
                value=int(rating_value) if rating_value is not None else 0,
                step=1,
                key=f"rating_{edit_id}"
            )
            
            favorite = st.checkbox(
                "⭐ **Marcar como favorito**",
                value=bool(work.get("favorite"))
            )
            
            smut_value = work.get("smut", False)
            smut = st.checkbox(
                "🔞 **Smut / +18**",
                value=bool(smut_value)
            )
            
            st.markdown("---")
            st.markdown("### 📌 Estado y Progreso")
            
            status_options = ["", "READING", "PLANNED", "COMPLETED"]
            current_status = work.get("personal_status")
            current_status = None if pd.isna(current_status) else current_status
            default_index = status_options.index(current_status) if current_status in status_options else 0
            
            status = st.selectbox(
                "**Estado personal**",
                options=status_options,
                index=default_index,
                key=f"status_{edit_id}"
            )
            
            chapters_value = work.get("chapter_count")
            chapters_value = None if pd.isna(chapters_value) else chapters_value
            
            chapters = st.number_input(
                "**Capítulos leídos**",
                min_value=0,
                value=int(chapters_value) if chapters_value is not None else 0,
                key=f"chapters_{edit_id}"
            )
            
            st.markdown("---")
            st.markdown("### 📊 Estado de Publicación")
            
            # Obtener el valor actual de publication_status
            current_publication_status = work.get("publication_status", "ONGOING")
            # Si es None o está vacío, por defecto ONGOING
            if pd.isna(current_publication_status) or not current_publication_status:
                current_publication_status = "ONGOING"
            
            # Checkbox: True = COMPLETED, False = ONGOING
            is_completed = current_publication_status == "COMPLETED"
            
            publication_completed = st.checkbox(
                "✅ **Obra completada** (marcar si la publicación ha finalizado)",
                value=is_completed,
                help="Si la obra ya no se publica más capítulos, marca esta casilla",
                key=f"publication_{edit_id}"
            )
            
            # Mostrar el estado actual de forma visual
            if publication_completed:
                st.success("📗 Estado: COMPLETED - La publicación de la obra ha finalizado")
            else:
                st.info("📘 Estado: ONGOING - La obra sigue en publicación")
            
            st.markdown("---")
            st.markdown("### 🖼️ Portada")
            
            cover_url = st.text_input(
                "**Cover URL**",
                value=safe_str(work.get("cover_url")),
                placeholder="https://ejemplo.com/portada.jpg",
                key=f"cover_{edit_id}"
            )
            
            if cover_url and cover_url.strip():
                try:
                    st.markdown('<div class="image-preview">', unsafe_allow_html=True)
                    st.image(cover_url, width=150, caption="Vista previa")
                    st.markdown('</div>', unsafe_allow_html=True)
                except:
                    st.warning("⚠️ No se pudo cargar la vista previa")
        
        st.markdown("---")
        st.markdown("### 🏷️ Aliases / Nombres Alternativos")
        st.caption("💡 Cada alias en una línea nueva")
        
        current_aliases = alias_map.get(edit_id, [])
        alias_text = "\n".join([a.get("alias", "") for a in current_aliases])
        
        new_aliases = st.text_area(
            "**Aliases (uno por línea)**",
            value=alias_text,
            height=150,
            placeholder="Asi no se hace\nDeja que te enseñe\nThe Carry",
            key=f"aliases_{edit_id}"
        )
        
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
        
        with col_btn1:
            save = st.form_submit_button("💾 Guardar Cambios", use_container_width=True, type="primary")
        
        with col_btn2:
            cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if save:
            try:
                with st.spinner("Guardando cambios..."):
                    # Determinar el publication_status basado en el checkbox
                    publication_status = "COMPLETED" if publication_completed else "ONGOING"
                    
                    supabase.table("works").update({
                        "title": title,
                        "personal_rating": rating,
                        "personal_status": status if status else None,
                        "chapter_count": chapters,
                        "cover_url": cover_url if cover_url else None,
                        "favorite": favorite,
                        "review": review if review else None,
                        "smut": smut,
                        "publication_status": publication_status  # Nuevo campo
                    }).eq("id", edit_id).execute()
                    
                    supabase.table("aliases").delete().eq("work_id", edit_id).execute()
                    
                    aliases_inserted = 0
                    for a in new_aliases.split("\n"):
                        alias_clean = a.strip()
                        if alias_clean:
                            supabase.table("aliases").insert({
                                "work_id": edit_id,
                                "alias": alias_clean,
                                "alias_normalized": normalize_text(alias_clean)
                            }).execute()
                            aliases_inserted += 1
                    
                    if "edit_work" in st.session_state:
                        del st.session_state["edit_work"]
                    
                    # Recargar datos después de editar
                    refresh_data()
                    
                    st.success(f"✅ ¡Guardado correctamente! ({aliases_inserted} aliases actualizados)")
                    st.balloons()
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error al guardar: {str(e)}")
        
        if cancel:
            if "edit_work" in st.session_state:
                del st.session_state["edit_work"]
            st.info("Edición cancelada")
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# =====================
# SIDEBAR
# =====================
st.sidebar.title("📚 Biblioteca")
st.sidebar.success(
    f"👤 {st.session_state.get('user','Usuario')}"
)

if st.sidebar.button("🚪 Cerrar sesión"):
    logout_user()
    
st.sidebar.markdown("---")

# Botón para agregar obras
if st.sidebar.button("➕ Agregar obras", use_container_width=True, type="secondary"):
    st.session_state["show_add_works"] = True
    st.rerun()

# Botón para refrescar datos (NUEVO)
if st.sidebar.button("🔄 Refrescar datos", use_container_width=True):
    refresh_data()
    st.rerun()

st.sidebar.markdown("---")

def update_search():
    st.session_state["search"] = st.session_state["search_input"]

search_input = st.sidebar.text_input(
    "🔎 Buscar obra",
    key="search_input",
    on_change=update_search,
    placeholder="Escribe el nombre de una obra..."
)

search = st.session_state.get("search", "")

favorite_only = st.sidebar.checkbox("⭐ Solo favoritos")

smut_filter = st.sidebar.checkbox("🔞 Solo +18")


status_filter = st.sidebar.selectbox(
    "📌 Estado personal",
    options=["Todos", "READING", "PLANNED", "COMPLETED"],
    help="Filtrar por estado de lectura"
)

publication_filter = st.sidebar.selectbox(
    "📌📄 Estado de publicación",
    options=["Todos", "ONGOING", "COMPLETED"],
    help="Filtrar por estado de publicación"
)

items_per_page = st.sidebar.selectbox(
    "📄 Obras por página",
    [10, 20, 30, 50, 100],
    index=2
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Estadísticas")
total_works = len(df)
completed = len(df[df["personal_status"] == "COMPLETED"])
reading = len(df[df["personal_status"] == "READING"])
planned = len(df[df["personal_status"] == "PLANNED"])
favorites = len(df[df["favorite"] == True])
smut_count = len(df[df["smut"] == True])

col1, col2 = st.sidebar.columns(2)
with col1:
    st.metric("Total obras", total_works)
    st.metric("Leyendo", reading)
    st.metric("Favoritos", favorites)
with col2:
    st.metric("Completados", completed)
    st.metric("Planeados", planned)
    st.metric("🔞 +18", smut_count)

st.sidebar.markdown("---")
st.sidebar.caption("💡 **Tips:**")
st.sidebar.caption("• Haz clic en ✏️ para editar")
st.sidebar.caption("• Usa el buscador con nombres o aliases")
st.sidebar.caption("• Usa '🔄 Refrescar datos' para actualizar")
st.sidebar.caption("• Los datos se sincronizan automáticamente")

# =====================
# SHOW ADD WORKS MODAL (ARRIBA)
# =====================
if st.session_state.get("show_add_works", False):
    show_add_works_modal()
    st.markdown("---")

# =====================
# FILTERS
# =====================
df_filtered = df.copy()

if search:
    with st.spinner("Buscando..."):
        df_filtered["score"] = df_filtered.apply(lambda row: score_work(row, search), axis=1)
        df_filtered = df_filtered[df_filtered["score"] > 30]
        df_filtered = df_filtered.sort_values("score", ascending=False)

if favorite_only:
    df_filtered = df_filtered[df_filtered["favorite"] == True]

if smut_filter:
    df_filtered = df_filtered[df_filtered["smut"] == True]

if status_filter != "Todos":
    df_filtered = df_filtered[df_filtered["personal_status"] == status_filter]

if publication_filter != "Todos":
    df_filtered = df_filtered[df_filtered["publication_status"] == publication_filter]    

# =====================
# EDIT SECTION (ARRIBA)
# =====================
if "edit_work" in st.session_state:
    edit_id = st.session_state["edit_work"]
    
    work_row = df[df["id"] == edit_id]
    
    if not work_row.empty:
        work = work_row.iloc[0]
        show_edit_form(work, edit_id)
        st.markdown("---")
        st.markdown("### 📚 Listado de obras")

# =====================
# PAGINATION
# =====================
total_records = len(df_filtered)
total_pages = max(1, (total_records + items_per_page - 1) // items_per_page)

current_page = st.sidebar.number_input(
    "📖 Página",
    min_value=1,
    max_value=total_pages,
    value=min(st.session_state.get("current_page", 1), total_pages),
    key="page_input"
)
st.session_state["current_page"] = current_page

start = (current_page - 1) * items_per_page
end = start + items_per_page

df_page = df_filtered.iloc[start:end]

# =====================
# HEADER
# =====================
st.markdown(f"### 📚 Mi Biblioteca de Manhwas")
st.markdown(f"**{total_records} obras encontradas** | Página {current_page}/{total_pages}")

if search:
    st.info(f"🔍 Resultados para: '{search}' - {total_records} obras encontradas")

if favorite_only:
    st.success(f"⭐ Mostrando solo obras favoritas ({total_records})")

if smut_filter:
    st.warning(f"🔞 Mostrando solo obras +18 ({total_records})")

# =====================
# LISTA DE OBRAS
# =====================
if len(df_page) == 0:
    st.warning("No se encontraron obras con los filtros seleccionados.")
else:
    for idx, work in df_page.iterrows():
        
        with st.container(border=True):
            
            col_cover, col_info = st.columns([1, 4])
            
            with col_cover:
                cover_url = clean(work.get("cover_url"))
                
                if cover_url and str(cover_url).strip():
                    try:
                        st.image(str(cover_url), use_container_width=True)
                    except:
                        st.image("assets/missing_cover.png", use_container_width=True)
                else:
                    st.image("assets/missing_cover.png", use_container_width=True)
            
            with col_info:
                col_title, col_rating = st.columns([4, 1])
                with col_title:
                    st.subheader(work.get("title", "Sin título"))
                    if work.get("favorite"):
                        st.markdown('<span class="badge badge-favorite">⭐ Favorito</span>', unsafe_allow_html=True)
                    if work.get("smut"):
                        st.markdown('<span class="badge badge-smut">🔞 +18</span>', unsafe_allow_html=True)
                    
                    # Badge para estado de publicación (NUEVO)
                    publication_status = work.get("publication_status", "ONGOING")
                    if pd.isna(publication_status) or not publication_status:
                        publication_status = "ONGOING"
                    
                    if publication_status == "COMPLETED":
                        st.markdown('<span class="badge" style="background-color: #10b981; color: white;">✅ Publicación Completada</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge" style="background-color: #3b82f6; color: white;">🔄 En publicación</span>', unsafe_allow_html=True)
                
                with col_rating:
                    rating_display = clean(work.get('personal_rating'))
                    if rating_display:
                        st.markdown(f"### ⭐ {rating_display}/10")
                    else:
                        st.markdown("### ⭐ -/10")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    status_display = clean(work.get('personal_status'))
                    if status_display:
                        status_emoji = {
                            "READING": "📖",
                            "PLANNED": "📅", 
                            "COMPLETED": "✅"
                        }.get(status_display, "📌")
                        st.markdown(f"**{status_emoji} Estado personal:** {status_display}")
                    else:
                        st.markdown("**📌 Estado personal:** Sin especificar")
                
                with col2:
                    chapters_count = clean(work.get('chapter_count'))
                    st.markdown(f"**📑 Capítulos leídos:** {chapters_count if chapters_count else '0'}")
                
                with col3:
                    # Mostrar también el publication_status en texto para claridad
                    pub_status_text = "Completada" if publication_status == "COMPLETED" else "En publicación"
                    st.markdown(f"**📅 Publicación:** {pub_status_text}")
                
                review = clean(work.get("review"))
                if isinstance(review, str) and review.strip():
                    with st.expander("📖 Ver reseña completa"):
                        st.markdown(review)
                
                with st.expander(f"📋 Detalles y aliases"):
                    
                    st.markdown("**📝 Sinopsis**")
                    synopsis = work.get("synopsis")
                    if synopsis and not pd.isna(synopsis):
                        st.write(synopsis)
                    else:
                        st.write("*Sinopsis no disponible*")
                    
                    st.markdown("**🏷️ Aliases**")
                    wid = work.get("id")
                    current_aliases = alias_map.get(wid, [])
                    
                    if current_aliases:
                        cols = st.columns(3)
                        for i, alias_data in enumerate(current_aliases):
                            with cols[i % 3]:
                                st.markdown(f"- {alias_data.get('alias')}")
                    else:
                        st.write("*Sin aliases registrados*")
                
                if st.button("✏️ Editar obra", key=f"edit_{work.get('id')}", use_container_width=True):
                    st.session_state["edit_work"] = work.get("id")
                    st.session_state["current_page"] = current_page
                    st.rerun()
# =====================
# FOOTER
# =====================
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)
with col_footer2:
    st.caption(f"📚 Biblioteca personal de Manhwas | Total: {total_works} obras")
    st.caption("🔄 Datos sincronizados con Supabase")