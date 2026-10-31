import os
import uuid
from io import BytesIO
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


# ==========================================================
# 1. CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Pont - Sondage & Suivi",
    page_icon="🌉",
    layout="wide"
)

DATA_FILE = "pont_data_enhanced.csv"
UPLOAD_DIR = "uploads_pont"

os.makedirs(UPLOAD_DIR, exist_ok=True)

COLUMNS = [
    "ID", "Timestamp", "Nom", "Pont", "Ville",
    "Latitude", "Longitude", "Type_pont",
    "Etat_tablier", "Commentaire",
    "Note_Securite", "Note_Deformation",
    "Note_Corrosion", "Note_Tablier",
    "Indice_Etat", "Photos"
]

RATING_COLS = [
    "Note_Securite",
    "Note_Deformation",
    "Note_Corrosion",
    "Note_Tablier"
]


# ==========================================================
# 2. GESTION DES DONNEES
# ==========================================================

def load_data():

    if os.path.exists(DATA_FILE):

        try:
            data = pd.read_csv(DATA_FILE, dtype=str)

            for col in COLUMNS:
                if col not in data.columns:
                    data[col] = ""

            return data[COLUMNS]

        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=COLUMNS)

    return pd.DataFrame(columns=COLUMNS)


def save_data(data):

    data = data.reindex(columns=COLUMNS)

    data.to_csv(
        DATA_FILE,
        index=False,
        encoding="utf-8-sig"
    )


# ==========================================================
# 3. CALCUL DE L'INDICE D'ETAT
# ==========================================================

def compute_index(row):

    try:

        security = float(row["Note_Securite"])
        deformation = float(row["Note_Deformation"])
        corrosion = float(row["Note_Corrosion"])
        deck = float(row["Note_Tablier"])

        # Les notes de deformation et corrosion
        # sont inversees : une note faible indique
        # un meilleur etat.

        scores = np.array([
            security,
            6 - deformation,
            6 - corrosion,
            deck
        ], dtype=float)

        weights = np.array([
            0.4,
            0.2,
            0.2,
            0.2
        ])

        if not np.all(np.isfinite(scores)):
            return 0.0

        return round(float(np.sum(scores * weights)), 2)

    except (ValueError, TypeError, KeyError):
        return 0.0


def prepare_ratings(data):

    result = data.copy()

    for col in RATING_COLS:
        result[col] = pd.to_numeric(
            result[col],
            errors="coerce"
        )

    # Harmonisation : 5 représente toujours le meilleur score.
    result["Note_Deformation"] = (
        6 - result["Note_Deformation"]
    )

    result["Note_Corrosion"] = (
        6 - result["Note_Corrosion"]
    )

    return result


# ==========================================================
# 4. GESTION DES PHOTOS
# ==========================================================

def save_uploaded_files(uploaded_files):

    saved_names = []

    for uploaded_file in uploaded_files:

        if uploaded_file is None:
            continue

        ext = os.path.splitext(uploaded_file.name)[1].lower()

        if ext not in [".jpg", ".jpeg", ".png"]:
            continue

        filename = (
            datetime.now().strftime("%Y%m%d_%H%M%S")
            + "_"
            + uuid.uuid4().hex
            + ext
        )

        path = os.path.join(UPLOAD_DIR, filename)

        with open(path, "wb") as file:
            file.write(uploaded_file.getbuffer())

        saved_names.append(filename)

    return saved_names


# ==========================================================
# 5. GRAPHIQUES
# ==========================================================

def make_pie_chart(data, col, title):

    if data.empty or col not in data.columns:
        return None

    counts = data[col].dropna().value_counts()

    if counts.empty:
        return None

    fig, ax = plt.subplots(figsize=(6, 5))

    colors = plt.cm.tab20(
        np.linspace(0, 1, len(counts))
    )

    ax.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.1f%%",
        colors=colors,
        startangle=90
    )

    ax.set_title(title)

    plt.tight_layout()

    return fig


def make_bar_ratings(data, title):

    if data.empty:
        return None

    prepared = prepare_ratings(data)

    means = prepared[RATING_COLS].mean()

    if means.isna().all():
        return None

    labels = [
        "Sécurité",
        "Déformation",
        "Corrosion",
        "Tablier"
    ]

    fig, ax = plt.subplots(figsize=(7, 4))

    bars = ax.bar(
        labels,
        means.values,
        alpha=0.9
    )

    ax.set_ylim(0, 5.5)

    ax.set_ylabel("Note moyenne (1-5)")

    ax.set_title(title)

    ax.set_ylabel("Note moyenne harmonisée (1-5)")

    ax.grid(axis="y", alpha=0.25)

    for bar in bars:

        height = bar.get_height()

        if np.isfinite(height):

            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + 0.05,
                f"{height:.2f}",
                ha="center"
            )

    plt.xticks(rotation=15)

    plt.tight_layout()

    return fig


# ==========================================================
# 6. GENERATION DU RAPPORT PDF
# ==========================================================

def generate_pdf_report(selected_data, bridge_name=None):

    buffer = BytesIO()

    with PdfPages(buffer) as pdf:

        # PAGE 1 : PRESENTATION

        fig = plt.figure(figsize=(8.27, 11.69))

        fig.text(
            0.05, 0.95,
            "RAPPORT D'ANALYSE DES EVALUATIONS DES PONTS",
            fontsize=16,
            weight="bold"
        )

        fig.text(
            0.05, 0.91,
            f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            fontsize=11
        )

        if bridge_name:

            fig.text(
                0.05, 0.87,
                f"Pont : {bridge_name}",
                fontsize=12
            )

        fig.text(
            0.05, 0.83,
            f"Nombre d'evaluations : {len(selected_data)}",
            fontsize=12
        )

        if not selected_data.empty:

            mean_index = pd.to_numeric(
                selected_data["Indice_Etat"],
                errors="coerce"
            ).mean()

            fig.text(
                0.05, 0.78,
                f"Indice moyen : {mean_index:.2f}/5"
                if pd.notna(mean_index)
                else "Indice moyen : Non disponible",
                fontsize=12
            )

        pdf.savefig(fig)
        plt.close(fig)

        # PAGE 2 : ETAT DES TABLIERS

        fig = make_pie_chart(
            selected_data,
            "Etat_tablier",
            "Repartition des etats des tabliers"
        )

        if fig is not None:
            pdf.savefig(fig)
            plt.close(fig)

        # PAGE 3 : NOTES MOYENNES

        fig = make_bar_ratings(
            selected_data,
            "Moyennes des evaluations harmonisees"
        )

        if fig is not None:
            pdf.savefig(fig)
            plt.close(fig)

        # PAGES PHOTOS

        photos = []

        for photo_field in selected_data["Photos"].dropna():

            for filename in str(photo_field).split(";"):

                filename = filename.strip()

                if filename and filename not in photos:
                    photos.append(filename)

        for filename in photos[:8]:

            path = os.path.join(UPLOAD_DIR, filename)

            if os.path.exists(path):

                try:

                    fig, ax = plt.subplots(figsize=(8.27, 6))

                    image = plt.imread(path)

                    ax.imshow(image)
                    ax.axis("off")
                    ax.set_title(filename)

                    pdf.savefig(fig)
                    plt.close(fig)

                except Exception:
                    continue

    buffer.seek(0)

    return buffer


# ==========================================================
# 7. CHARGEMENT INITIAL
# ==========================================================

df = load_data()

# Initialisation des variables de session

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

if "edit_comment" not in st.session_state:
    st.session_state.edit_comment = ""


# ==========================================================
# 8. TITRE DE L'APPLICATION
# ==========================================================

st.title("🌉 Application de sondage et suivi des ponts")

st.markdown(
    """
    Cette plateforme permet de collecter les évaluations
    des ouvrages d'art, de suivre leur état et de produire
    des rapports d'analyse.
    """
)

col1, col2 = st.columns([1, 2])


# ==========================================================
# 9. FORMULAIRE D'EVALUATION
# ==========================================================

with col1:

    st.header("➤ Soumettre une évaluation")

    with st.form("evaluation_form"):

        name = st.text_input(
            "Votre nom",
            key="name_input"
        )

        bridge = st.text_input(
            "Nom du pont",
            key="bridge_input"
        )

        city = st.text_input(
            "Ville / Localisation",
            key="city_input"
        )

        lat = st.text_input(
            "Latitude (optionnelle)",
            key="lat_input"
        )

        lon = st.text_input(
            "Longitude (optionnelle)",
            key="lon_input"
        )

        type_bridge = st.selectbox(
            "Type de pont",
            [
                "Pont en béton",
                "Pont métallique",
                "Pont mixte",
                "Pont en bois",
                "Autre"
            ]
        )

        state = st.selectbox(
            "État général du tablier",
            [
                "Très Bon",
                "Bon",
                "Moyen",
                "Mauvais",
                "Très Mauvais"
            ]
        )

        st.markdown("### Notes d'évaluation")

        st.caption(
            "Pour la sécurité et le tablier : 5 = excellent. "
            "Pour les déformations et la corrosion : 5 = très important."
        )

        note_sec = st.slider(
            "Sécurité",
            1, 5, 3
        )

        note_def = st.slider(
            "Déformation observée",
            1, 5, 3
        )

        note_cor = st.slider(
            "Corrosion observée",
            1, 5, 3
        )

        note_tab = st.slider(
            "État du tablier",
            1, 5, 3
        )

        comment = st.text_area(
            "Commentaire"
        )

        uploaded_files = st.file_uploader(
            "Photos (JPG / PNG)",
            accept_multiple_files=True,
            type=["png", "jpg", "jpeg"]
        )

        submit_btn = st.form_submit_button(
            "📥 Soumettre l'évaluation",
            use_container_width=True
        )

    # TRAITEMENT DE L'EVALUATION

    if submit_btn:

        if (
            not name.strip()
            or not bridge.strip()
            or not comment.strip()
        ):

            st.error(
                "Les champs Nom, Pont et Commentaire sont obligatoires."
            )

        else:

            saved_photos = save_uploaded_files(
                uploaded_files or []
            )

            photos_field = ";".join(saved_photos)

            row = {

                "ID": uuid.uuid4().hex,

                "Timestamp": datetime.now().isoformat(),

                "Nom": name.strip(),

                "Pont": bridge.strip(),

                "Ville": city.strip(),

                "Latitude": lat.strip(),

                "Longitude": lon.strip(),

                "Type_pont": type_bridge,

                "Etat_tablier": state,

                "Commentaire": comment.strip(),

                "Note_Securite": note_sec,

                "Note_Deformation": note_def,

                "Note_Corrosion": note_cor,

                "Note_Tablier": note_tab,

                "Photos": photos_field
            }

            row["Indice_Etat"] = compute_index(row)

            # CORRECTION DE PANDAS APPEND

            new_row = pd.DataFrame(
                [row],
                columns=COLUMNS
            )

            df = pd.concat(
                [df, new_row],
                ignore_index=True
            )

            save_data(df)

            st.success(
                "✅ Évaluation enregistrée avec succès !"
            )

            st.rerun()

    st.divider()

    # ======================================================
    # 10. MODIFICATION DU COMMENTAIRE
    # ======================================================

    st.subheader("✏ Modifier un commentaire")

    edit_name = st.text_input(
        "Nom de l'évaluateur",
        key="edit_name_input"
    )

    if st.button("Rechercher mon dernier commentaire"):

        if not edit_name.strip():

            st.warning("Entrez votre nom.")

        else:

            matches = df[
                df["Nom"].astype(str).str.strip().str.lower()
                == edit_name.strip().lower()
            ]

            if matches.empty:

                st.info("Aucune évaluation trouvée sous ce nom.")

            else:

                last_record = matches.iloc[-1]

                st.session_state.edit_id = last_record["ID"]

                st.session_state.edit_comment = (
                    last_record["Commentaire"]
                )

                st.rerun()

    if st.session_state.edit_id is not None:

        st.markdown("**Modification du commentaire sélectionné**")

        # Vérifier que l'enregistrement existe toujours

        selected = df[
            df["ID"] == st.session_state.edit_id
        ]

        if selected.empty:

            st.warning("Cet enregistrement n'existe plus.")

            st.session_state.edit_id = None

        else:

            st.text_area(
                "Nouveau commentaire",
                key="edit_comment"
            )

            if st.button("💾 Valider la modification"):

                new_comment = st.session_state.edit_comment.strip()

                if not new_comment:

                    st.error("Le commentaire ne peut pas être vide.")

                else:

                    mask = (
                        df["ID"] == st.session_state.edit_id
                    )

                    df.loc[mask, "Commentaire"] = new_comment

                    save_data(df)

                    st.session_state.edit_id = None
                    st.session_state.edit_comment = ""

                    st.success("Commentaire modifié avec succès.")

                    st.rerun()


# ==========================================================
# 11. VISUALISATION ET EXPLORATION
# ==========================================================

with col2:

    st.header("📊 Visualisation et exploration")

    # FILTRES

    st.subheader("Filtres")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:

        unique_cities = sorted(
            df["Ville"].dropna().unique().tolist()
        )

        city_filter = st.selectbox(
            "Ville",
            ["Toutes"] + unique_cities
        )

    with filter_col2:

        unique_types = sorted(
            df["Type_pont"].dropna().unique().tolist()
        )

        type_filter = st.selectbox(
            "Type de pont",
            ["Tous"] + unique_types
        )

    with filter_col3:

        unique_states = sorted(
            df["Etat_tablier"].dropna().unique().tolist()
        )

        state_filter = st.selectbox(
            "État",
            ["Tous"] + unique_states
        )

    date_col1, date_col2 = st.columns(2)

    with date_col1:

        date_min = st.date_input(
            "Date minimale",
            value=None
        )

    with date_col2:

        date_max = st.date_input(
            "Date maximale",
            value=None
        )

    # APPLICATION DES FILTRES

    df_vis = df.copy()

    if city_filter != "Toutes":

        df_vis = df_vis[
            df_vis["Ville"] == city_filter
        ]

    if type_filter != "Tous":

        df_vis = df_vis[
            df_vis["Type_pont"] == type_filter
        ]

    if state_filter != "Tous":

        df_vis = df_vis[
            df_vis["Etat_tablier"] == state_filter
        ]

    dates = pd.to_datetime(
        df_vis["Timestamp"],
        errors="coerce"
    )

    if date_min is not None:

        df_vis = df_vis[
            dates.dt.date >= date_min
        ]

    if date_max is not None:

        dates = pd.to_datetime(
            df_vis["Timestamp"],
            errors="coerce"
        )

        df_vis = df_vis[
            dates.dt.date <= date_max
        ]

    st.divider()

    # INDICATEURS PRINCIPAUX

    st.subheader("Indicateurs clés")

    total_evaluations = len(df_vis)

    total_bridges = df_vis["Pont"].nunique()

    average_index = pd.to_numeric(
        df_vis["Indice_Etat"],
        errors="coerce"
    ).mean()

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "Évaluations",
        total_evaluations
    )

    metric2.metric(
        "Ponts évalués",
        total_bridges
    )

    metric3.metric(
        "Indice moyen",
        f"{average_index:.2f}/5"
        if pd.notna(average_index)
        else "N/A"
    )

    st.divider()

    # GRAPHIQUE CIRCULAIRE

    st.subheader("Répartition des états des tabliers")

    pie_fig = make_pie_chart(
        df_vis,
        "Etat_tablier",
        "Répartition des états"
    )

    if pie_fig is not None:

        st.pyplot(pie_fig)

        plt.close(pie_fig)

    else:

        st.info("Aucune donnée disponible pour ce graphique.")

    st.divider()

    # GRAPHIQUE DES NOTES

    st.subheader("Moyennes des évaluations")

    bar_fig = make_bar_ratings(
        df_vis,
        "Moyennes des notes harmonisées"
    )

    if bar_fig is not None:

        st.pyplot(bar_fig)

        plt.close(bar_fig)

    else:

        st.info("Aucune note disponible.")

    st.divider()

    # TABLEAU DES DONNEES

    st.subheader("Données des évaluations")

    if not df_vis.empty:

        display_df = df_vis.copy()

        display_df["Timestamp"] = pd.to_datetime(
            display_df["Timestamp"],
            errors="coerce"
        )

        display_df = display_df.sort_values(
            by="Timestamp",
            ascending=False
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("Aucune donnée ne correspond aux filtres.")

    # TELECHARGEMENT CSV

    csv_bytes = df_vis.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "⬇ Télécharger les données CSV",
        data=csv_bytes,
        file_name="ponts_filtered.csv",
        mime="text/csv"
    )

    st.divider()

    # ======================================================
    # 12. RAPPORT PDF
    # ======================================================

    st.subheader("📄 Générer un rapport PDF")

    bridge_options = [
        "Tous"
    ] + sorted(
        df["Pont"].dropna().unique().tolist()
    )

    bridge_select = st.selectbox(
        "Choisir un pont",
        bridge_options
    )

    if st.button("🖨️ Générer le rapport PDF"):

        if bridge_select != "Tous":

            selected_df = df[
                df["Pont"] == bridge_select
            ]

        else:

            selected_df = df_vis

        if selected_df.empty:

            st.error(
                "Aucune donnée disponible pour générer le rapport."
            )

        else:

            pdf_buffer = generate_pdf_report(
                selected_df,
                bridge_name=(
                    None if bridge_select == "Tous"
                    else bridge_select
                )
            )

            st.download_button(
                "⬇ Télécharger le rapport PDF",
                data=pdf_buffer,
                file_name="rapport_ponts.pdf",
                mime="application/pdf",
                key="download_pdf"
            )

    st.divider()

    # ======================================================
    # 13. PHOTOS RECENTES
    # ======================================================

    st.subheader("📸 Photos récentes")

    recent_photos = []

    for photo_field in df["Photos"].dropna().astype(str):

        for filename in photo_field.split(";"):

            filename = filename.strip()

            if filename:
                recent_photos.append(filename)

    if recent_photos:

        photo_columns = st.columns(3)

        for i, filename in enumerate(
            recent_photos[-6:][::-1]
        ):

            path = os.path.join(
                UPLOAD_DIR,
                filename
            )

            if os.path.exists(path):

                try:

                    photo_columns[i % 3].image(
                        path,
                        width="stretch",
                        caption=filename
                    )

                except Exception:

                    photo_columns[i % 3].write(filename)

    else:

        st.info("Aucune photo disponible.")


# ==========================================================
# 14. PIED DE PAGE
# ==========================================================

st.divider()

st.caption(
    "Application de sondage et de suivi des ponts | "
    "Collecte, évaluation, visualisation et rapports."
)
