"""Load CSS themes for Streamlit."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

_STYLES_DIR = Path(__file__).resolve().parent.parent / "styles"


def load_css(theme: str = "retro") -> None:
    """Inject design system and theme CSS."""
    design = (_STYLES_DIR / "design_system.css").read_text()
    theme_file = "retro.css" if theme == "retro" else "modern.css"
    theme_css = (_STYLES_DIR / theme_file).read_text()
    st.markdown(f"<style>{design}\n{theme_css}</style>", unsafe_allow_html=True)
