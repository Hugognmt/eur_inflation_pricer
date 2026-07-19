"""Tab: Params — mirrors the Excel "Params" sheet (feeds, seaso, correspondence)."""

import pandas as pd
import streamlit as st

from instance import config, exports


def render(provider) -> None:
    st.subheader("Params")

    if provider.is_available():
        st.success(f"Bloomberg: {provider.message}")
    else:
        st.warning(f"Bloomberg: {provider.message}")

    p = config.PARAMS
    c1, c2 = st.columns(2)
    with c1:
        feeds = pd.DataFrame(
            {
                "setting": [
                    "Reuters enabled",
                    "Bro feed available",
                    "Fixings bro feed available",
                    "Source",
                ],
                "value": [
                    p["reuters_enabled"],
                    p["bro_feed_available"],
                    p["fixings_bro_feed_available"],
                    p["source"],
                ],
            }
        )
        st.dataframe(feeds.astype(str), hide_index=True, width="stretch")
    with c2:
        calc = pd.DataFrame(
            {
                "setting": [
                    "Roll market",
                    "Seaso",
                    "Seaso calc type",
                    "ESTR fixing",
                    "Start histo date",
                ],
                "value": [
                    p["roll_market"] or "-",
                    p["seaso"],
                    p["seaso_calc_type"],
                    p["estr_fixing"],
                    p["start_histo_date"],
                ],
            }
        )
        st.dataframe(calc.astype(str), hide_index=True, width="stretch")

    st.caption(
        "MVP: only Bloomberg is wired. Reuters / broker feeds and KDB paths are "
        "shown for parity with the Excel and come later."
    )

    st.markdown("**Linker ↔ Nominal correspondence** (edit in `instance/config.py`):")
    st.dataframe(
        pd.DataFrame(config.correspondence()),
        hide_index=True,
        width="stretch",
    )

    _render_exports(provider)

    # TODO(workspace): source feed flags, ESTR fixing and histo paths from
    # Workspace / KDB once those providers exist.


def _render_exports(provider) -> None:
    """CSV exports feeding the pricers (linker pricer, ...) — Excel DatasToImport."""
    st.divider()
    st.markdown("**Exports CSV (pour les pricers)**")

    out_dir = exports.resolved_dir()
    st.caption(f"Dossier de sortie : `{out_dir}` — éditable dans `instance/settings.toml`.")

    data = exports.collect(provider)
    refs = pd.DataFrame(
        [
            {
                "Dataset": key,
                "Fichier": config.EXPORT_FILES[key],
                "Lignes": len(df),
                "Chemin cible": str(out_dir / config.EXPORT_FILES[key]),
            }
            for key, df in data.items()
        ]
    )
    st.dataframe(refs, hide_index=True, width="stretch")

    if st.button("💾 Sauvegarder tout en CSV", width="stretch"):
        written = exports.write_all(data)
        st.success(f"{len(written)} fichier(s) écrits dans {out_dir}")

    st.caption("Ou télécharger un fichier directement :")
    cols = st.columns(len(data))
    for col, (key, df) in zip(cols, data.items()):
        with col:
            st.download_button(
                config.EXPORT_FILES[key],
                exports.to_csv_bytes(df),
                file_name=config.EXPORT_FILES[key],
                mime="text/csv",
                width="stretch",
                key=f"dl_{key}",
            )
