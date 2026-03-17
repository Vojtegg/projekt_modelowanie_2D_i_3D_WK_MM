import streamlit as st

st.set_page_config(page_title="Generator Torów Wyścigowych", layout="wide")

st.title("🏎️ Projekt: Analiza terenu pod tory wyścigowe")
st.write("Witajcie w naszym projekcie! Tutaj wkrótce pojawi się mapa.")

# Przykładowy suwak
nachylenie = st.slider("Wybierz maksymalne nachylenie terenu (w stopniach):", 0, 15, 5)
st.write(f"Wybrane nachylenie: **{nachylenie} stopni**")
