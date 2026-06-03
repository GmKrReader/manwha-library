import streamlit as st
import pandas as pd
from supabase_client import supabase

# =====================
# CONFIG
# =====================
st.set_page_config(
    page_title="Biblioteca Manhwa",
    layout="wide"
)

def safe_int(value, default=0):
    if pd.isna(value) or value is None:
        return default
    try:
        return int(value)
    except:
        return default

# =====================
# UTILIDAD PARA LIMPIEZA
# =====================
def clean(value):
    if pd.isna(value):
        return None
    return value

# =====================
# CARGA DE DATOS
# =====================
response = (
    supabase
    .table("works")
    .select("*")
    .order("title")
    .execute()
)

df = pd.DataFrame(response.data)

# =====================
# SIDEBAR
# =====================
st.sidebar.title("📚 Biblioteca")

search = st.sidebar.text_input("Buscar obra")

favorite_only = st.sidebar.checkbox("Solo favoritos")

status_filter = st.sidebar.selectbox(
    "Estado personal",
    options=["Todos", "READING", "PLANNED", "COMPLETED"]
)

items_per_page = st.sidebar.selectbox(
    "Obras por página",
    [25, 50, 100],
    index=1
)

# =====================
# FILTROS
# =====================
if search:
    df = df[
        df["title"]
        .str.contains(search, case=False, na=False)
    ]

if favorite_only:
    df = df[df["favorite"] == True]

if status_filter != "Todos":
    df = df[df["personal_status"] == status_filter]

# =====================
# PAGINACIÓN
# =====================
total_records = len(df)

total_pages = max(
    1,
    (total_records + items_per_page - 1) // items_per_page
)

page = st.sidebar.number_input(
    "Página",
    min_value=1,
    max_value=total_pages,
    value=1
)

start = (page - 1) * items_per_page
end = start + items_per_page

df = df.iloc[start:end]

# =====================
# HEADER
# =====================
st.title("📚 Mi Biblioteca")
st.caption(f"{total_records} obras encontradas | Página {page}/{total_pages}")

# =====================
# LISTA DE OBRAS
# =====================
for _, work in df.iterrows():

    st.divider()

    col_cover, col_info = st.columns([1, 4])

    # =====================
    # PORTADA
    # =====================
    with col_cover:

        cover_url = clean(work.get("cover_url"))

        has_cover = (
            cover_url is not None
            and str(cover_url).strip() != ""
        )

        if has_cover:
            st.image(str(cover_url), use_container_width=True)
        else:
            st.image("assets/missing_cover.png", width=150)

    # =====================
    # INFO
    # =====================
    with col_info:

        
        favorite = work.get("favorite", False)

        star = "⭐" if favorite else ""

        st.subheader(f"{star} {work.get('title', 'Sin título')}")

        st.write(f"**Rating:** {clean(work.get('personal_rating')) or '-'}")
        st.write(f"**Estado:** {clean(work.get('personal_status')) or '-'}")
        st.write(f"**Capítulos:** {clean(work.get('chapter_count')) or '-'}")
        st.write(f"**+18:** {'Sí' if work.get('smut') else 'No'}")

        # =====================
        # REVIEW COMPLETA
        # =====================
        review = clean(work.get("review"))

        if isinstance(review, str) and review.strip():

            with st.expander("📖 Ver review completo"):

                st.text_area(
                    "",
                    value=review,
                    height=250,
                    disabled=True,
                    key=f"review_{work.get('id')}"
                )

        # =====================
        # BOTÓN DETALLES (FUTURO)
        # =====================
        st.button(
            "Ver detalles",
            key=f"details_{work.get('id')}"
        )

        if st.button("✏️ Editar", key=f"edit_{work.get('id')}"):
            st.session_state["edit_id"] = work.get("id")


        # =====================
        # FUNCION DE EDICION
        # =====================
if "edit_id" in st.session_state:

    edit_id = st.session_state["edit_id"]

    work = df[df["id"] == edit_id].iloc[0]

    st.divider()
    st.subheader("✏️ Editar obra")

    with st.form("edit_form"):

        title = st.text_input(
            "Título",
            value=work.get("title") or ""
        )

        rating = st.number_input(
            "Rating",
            min_value=1,
            max_value=10,
            value=safe_int(work.get("personal_rating"), 1)
        )

        status = st.selectbox(
            "Estado personal",
            ["READING", "PLANNED", "COMPLETED"],
            index=0
        )

        chapters = st.number_input(
            "Capítulos",
            value=safe_int(work.get("chapter_count"), 0)
        )

        cover_url = st.text_input(
            "Cover URL",
            value=work.get("cover_url") or ""
        )

        favorite = st.checkbox(
            "Favorito",
            value=bool(work.get("favorite"))
        )

        review = st.text_area(
            "Review",
            value=work.get("review") or "",
            height=200
        )

        # =========================
        # BOTONES
        # =========================
        col1, col2 = st.columns(2)

        with col1:
            submitted = st.form_submit_button("Guardar cambios")
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancelar")

        if submitted:

            supabase.table("works").update({
                "title": title,
                "personal_rating": rating,
                "personal_status": status,
                "chapter_count": chapters,
                "cover_url": cover_url,
                "favorite": favorite,
                "review": review
            }).eq("id", edit_id).execute()

            st.success("Actualizado correctamente")

            del st.session_state["edit_id"]

            st.rerun()
    # =========================
    # LOGICA CANCELAR
    # =========================
    if cancelled:

        del st.session_state["edit_id"]

        st.rerun()       