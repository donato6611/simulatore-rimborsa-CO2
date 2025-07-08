# --- Import necessari ---
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# --- Funzione di simulazione ---
def simulazione_rimborso_co2(
    p_gas=36.0,                # €/MWh gas medio annuo
    pun=109.0,                 # €/MWh PUN medio annuo
    prezzo_co2=65.0,           # €/tCO2 quota ETS
    fattore_emissione=0.36,    # tCO2/MWh elettrico (CCGT tipico)
    energia_borsa=285_000_000, # MWh annui scambiati in borsa
    frazione_gas=0.4,          # quota energia da gas
    rendimento_gas=0.56        # rendimento medio centrali gas
):
    mwh_gas_per_mwh_elettrico = 1 / rendimento_gas
    incidenza_gas_pun = p_gas * mwh_gas_per_mwh_elettrico
    incidenza_co2_pun = prezzo_co2 * fattore_emissione
    altri_costi = pun - (incidenza_gas_pun + incidenza_co2_pun)
    # PUN "scontato" del rimborso CO2
    pun_scontato_co2 = incidenza_gas_pun + altri_costi
    energia_gas = frazione_gas * energia_borsa
    costo_rimborso_co2 = prezzo_co2 * fattore_emissione * energia_gas
    psoc = costo_rimborso_co2 / energia_borsa
    pun_eq = pun_scontato_co2 + psoc
    vantaggio = (pun - pun_eq) * energia_borsa
    leva = vantaggio / costo_rimborso_co2 if costo_rimborso_co2 != 0 else float('inf')
    return {
        "Incidenza gas su PUN": incidenza_gas_pun,
        "Incidenza CO2 su PUN": incidenza_co2_pun,
        "Altri costi/spreads": altri_costi,
        "PUN senza CO2": pun_scontato_co2,
        "Costo annuo rimborso CO2 (mld €)": costo_rimborso_co2 / 1e9,
        "Psoc (€/MWh)": psoc,
        "PUN equivalente": pun_eq,
        "Vantaggio sistema (mld €)": vantaggio / 1e9,
        "Leva": leva
    }

# --- UI Streamlit ---
st.set_page_config(page_title="Simulazione rimborso CO₂", layout="centered")
st.title("Simulazione rimborso CO₂ ai produttori termoelettrici")
st.markdown("""
<span style='color:#e76f51'><b>ATTENZIONE:</b> I valori di default/precaricati in questa simulazione sono riferiti all'anno solare 2024 (fonti: GME, Terna, ARERA).<br>
In questo scenario, si simula l'effetto di un rimborso del costo delle quote CO₂ (ETS) ai produttori a gas.</span>
""", unsafe_allow_html=True)
st.markdown("""
Analisi semplificata dell'effetto di un rimborso del costo delle quote CO₂ per la generazione elettrica a gas, con socializzazione del costo su tutti i kWh scambiati in borsa. Modifica i parametri e osserva i risultati.
""")

# --- Input utente con chiavi univoche ---
p_gas = st.number_input("Prezzo medio gas (€/MWh)", value=36.0, min_value=0.0, key="p_gas_rimborso")
pun = st.number_input("PUN medio annuo (€/MWh)", value=109.0, min_value=0.0, key="pun_rimborso")
prezzo_co2 = st.number_input("Prezzo quota CO₂ ETS (€/tCO₂)", value=65.0, min_value=0.0, key="prezzo_co2_rimborso")
fattore_emissione = st.number_input("Fattore di emissione centrali gas (tCO₂/MWh elettrico)", value=0.36, min_value=0.0, max_value=1.0, key="fattore_emissione_rimborso")
energia_borsa = st.number_input("Energia annua in borsa (MWh)", value=285_000_000.0, min_value=1.0, key="energia_borsa_rimborso")
frazione_gas = st.slider("Frazione energia da gas (%)", min_value=0, max_value=100, value=40, key="frazione_gas_rimborso") / 100
rendimento_gas = st.number_input("Rendimento medio centrali gas (%)", value=56.0, min_value=1.0, max_value=100.0, key="rendimento_gas_rimborso") / 100

if st.button("Calcola risultati", key="calcola_rimborso"):
    risultati = simulazione_rimborso_co2(
        p_gas=p_gas,
        pun=pun,
        prezzo_co2=prezzo_co2,
        fattore_emissione=fattore_emissione,
        energia_borsa=energia_borsa,
        frazione_gas=frazione_gas,
        rendimento_gas=rendimento_gas
    )
    st.subheader("Risultati della simulazione")
    pun_eq = risultati["PUN equivalente"]
    risparmio_perc = 100 * (pun - pun_eq) / pun if pun > 0 else 0
    for k, v in risultati.items():
        if "mld" in k:
            st.write(f"{k}: {v:.2f}")
        else:
            st.write(f"{k}: {v:.2f}")
    st.success(f"Risparmio percentuale sul PUN equivalente rispetto al PUN reale: {risparmio_perc:.2f}%")
    st.markdown("""
    **Nota:**
    - La leva è inversamente proporzionale alla quota di energia prodotta da gas.
    - I risultati sono indicativi e dipendono fortemente dai parametri inseriti.
    """)

    # --- Grafico 1: Confronto PUN ---
    fig1, ax1 = plt.subplots(figsize=(5,3))
    labels = ["PUN attuale", "PUN senza CO2", "PUN equivalente"]
    values = [pun, risultati["PUN senza CO2"], risultati["PUN equivalente"]]
    colors = ["#888", "#2a9d8f", "#f4a261"]
    ax1.bar(labels, values, color=colors)
    for i, v in enumerate(values):
        ax1.text(i, v+2, f"{v:.1f}", ha='center')
    ax1.set_ylabel("€/MWh")
    ax1.set_title("Confronto PUN e scenari rimborso CO₂")
    st.pyplot(fig1)

    # --- Grafico 2: Ripartizione costi in PUN ---
    fig2, ax2 = plt.subplots(figsize=(5,3))
    ax2.bar(["PUN attuale"], [pun], color="#888", label="Totale")
    ax2.bar(["PUN attuale"], [risultati["Incidenza gas su PUN"]], color="#457b9d", label="Quota gas")
    ax2.bar(["PUN attuale"], [risultati["Incidenza CO2 su PUN"]], bottom=[risultati["Incidenza gas su PUN"]], color="#e76f51", label="Quota CO₂")
    ax2.bar(["PUN attuale"], [risultati["Altri costi/spreads"]], bottom=[risultati["Incidenza gas su PUN"]+risultati["Incidenza CO2 su PUN"]], color="#e9c46a", label="Altri costi/spreads")
    ax2.set_ylabel("€/MWh")
    ax2.set_title("Composizione PUN attuale")
    ax2.legend()
    st.pyplot(fig2)

    # --- Grafico 3: Effetto leva ---
    leva = risultati["Leva"]
    fig3, ax3 = plt.subplots(figsize=(5,3))
    ax3.bar(["Vantaggio sistema"], [risultati["Vantaggio sistema (mld €)"]], color="#2a9d8f", label="Vantaggio")
    ax3.bar(["Costo rimborso CO2"], [risultati["Costo annuo rimborso CO2 (mld €)"]], color="#e76f51", label="Costo rimborso CO2")
    ax3.set_ylabel("Miliardi €/anno")
    ax3.set_title(f"Effetto leva (Leva = {leva:.2f})")
    ax3.legend()
    st.pyplot(fig3)
