import os
import csv
import json
import streamlit as st
import pandas as pd

# Archivos de persistencia en disco
CONFIG_FILE = "config_cotizadora.json"
SESSION_FILE = "sesion_cotizadora.json"
HISTORIAL_FILE = "historial_cotizaciones.csv"

DEFAULT_CONFIG = {
    "moneda": "MXN",
    "costo_kwh": 3.50,         
    "consumo_w": 120.0,
    "desgaste_hora": 15.0,     
    "tarifa_mo_hora": 200.0,   
    "factor_fallas_pct": 10.0,
    "margen_ganancia_pct": 60.0
}

MATERIALES_PRESET_USD = {
    "PLA (Generic / CR)": 20.0,
    "Hyper PLA / Ender PLA+": 24.0,
    "PLA-Silk / Matte / Wood": 25.0,
    "PLA-CF (Fibra de Carbono)": 38.0,
    "PETG (Generic / CR)": 22.0,
    "Hyper PETG": 26.0,
    "PETG-CF (Fibra de Carbono)": 45.0,
    "PETG-GF (Fibra de Vidrio)": 42.0,
    "ABS (Generic / CR / Hyper)": 23.0,
    "ASA (Generic / HP)": 28.0,
    "TPU Flexible (95A / 85A)": 34.0,
    "PA (Nylon Genérico)": 48.0,
    "PA-CF / PA12-CF (Nylon Fibra Carbono)": 65.0,
    "PC (Policarbonato)": 45.0,
    "PP (Polipropileno)": 40.0,
    "PPS / PPS-CF (Súper Polímero)": 140.0,
    "PVA (Soporte Hidrosoluble)": 80.0,
    "BVOH (Soporte Soluble Pro)": 95.0,
    "HIPS (Soporte D-Limoneno)": 30.0
}

TIPO_CAMBIO_PRESET = 18.0

# --- FUNCIONES DE PERSISTENCIA DE ARCHIVOS ---
def cargar_configuracion():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def guardar_configuracion_disco(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception as e:
        st.error(f"No se pudo guardar la configuración: {e}")

def cargar_sesion():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_sesion_disco(sesion_dict):
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(sesion_dict, f, indent=4)
    except Exception:
        pass

# --- INICIALIZACIÓN DE LA APLICACIÓN ---
st.set_page_config(
    page_title="Cotizadora 3D Pro - ZKN Dark Edition",
    page_icon="⚡",
    layout="wide"
)

# Cargar archivos de configuración y sesión
config_data = cargar_configuracion()
session_data = cargar_sesion()

# Estado de sesión inicial
if "moneda_prev" not in st.session_state:
    st.session_state.moneda_prev = session_data.get("moneda", config_data.get("moneda", "MXN"))
if "preset_prev" not in st.session_state:
    st.session_state.preset_prev = session_data.get("preset", "PA-CF / PA12-CF (Nylon Fibra Carbono)")

# Título Principal
st.title("⚡ Cotizadora & Calculadora de Impresión 3D Pro (K1C)")

# Pestañas Principales
tab_cotizador, tab_config, tab_historial = st.tabs([
    "📊 Cotizador de Piezas", 
    "⚙️ Configuración del Taller", 
    "📜 Historial de Cotizaciones"
])

# --- PESTAÑA 1: COTIZADOR ---
with tab_cotizador:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Información del Proyecto")
        
        moneda = st.radio(
            "Moneda de Trabajo:", 
            ["MXN", "USD"], 
            index=0 if session_data.get("moneda", config_data["moneda"]) == "MXN" else 1,
            horizontal=True
        )
        
        cliente = st.text_input("Nombre del Cliente:", value=session_data.get("cliente", "Cliente General"))
        pieza = st.text_input("Nombre de la Pieza:", value=session_data.get("pieza", "Soporte_Rack_2020"))

        st.subheader("Parámetros del Slicer")
        
        presets_list = list(MATERIALES_PRESET_USD.keys())
        default_preset_idx = presets_list.index(session_data.get("preset", "PA-CF / PA12-CF (Nylon Fibra Carbono)")) if session_data.get("preset") in presets_list else 12
        
        preset_choice = st.selectbox("Preset de Filamento:", presets_list, index=default_preset_idx)

        # Cálculo dinámico de precio base sugerido si cambia el preset o la moneda
        precio_base_usd = MATERIALES_PRESET_USD.get(preset_choice, 65.0)
        precio_sugerido_init = precio_base_usd * TIPO_CAMBIO_PRESET if moneda == "MXN" else precio_base_usd

        # Si el usuario cambió moneda o preset en la UI, forzar recálculo del precio sugerido del preset
        if st.session_state.moneda_prev != moneda or st.session_state.preset_prev != preset_choice:
            val_precio_kg = float(precio_sugerido_init)
            st.session_state.moneda_prev = moneda
            st.session_state.preset_prev = preset_choice
        else:
            try:
                val_precio_kg = float(session_data.get("precio_kg", precio_sugerido_init))
            except ValueError:
                val_precio_kg = float(precio_sugerido_init)

        precio_kg = st.number_input(f"Precio Filamento (${moneda}/kg):", value=val_precio_kg, step=10.0)
        peso_g = st.number_input("Peso Pieza + Soportes (Gramos):", value=float(session_data.get("peso_g", 85.0)), step=1.0)
        tiempo_h = st.number_input("Tiempo de Impresión (Horas):", value=float(session_data.get("tiempo_h", 4.5)), step=0.1)
        mo_min = st.number_input("Mano de Obra (Minutos dedicados):", value=float(session_data.get("mo_min", 20.0)), step=1.0)
        cantidad = st.number_input("Cantidad de Piezas (Lote):", value=int(session_data.get("cantidad", 1)), min_value=1, step=1)
        pct_descuento = st.number_input("Descuento Mayoreo / Volumen (%):", value=float(session_data.get("descuento_pct", 0.0)), min_value=0.0, max_value=100.0, step=0.5)

        # Guardar sesión activa automáticamente a disco
        sesion_actual = {
            "moneda": moneda,
            "cliente": cliente,
            "pieza": pieza,
            "preset": preset_choice,
            "precio_kg": str(precio_kg),
            "peso_g": str(peso_g),
            "tiempo_h": str(tiempo_h),
            "mo_min": str(mo_min),
            "cantidad": str(cantidad),
            "descuento_pct": str(pct_descuento)
        }
        guardar_sesion_disco(sesion_actual)

    # --- FÓRMULAS EXACTAS DE CÁLCULO DE COSTOS ---
    costo_kwh = float(config_data.get("costo_kwh", 3.50))
    watts = float(config_data.get("consumo_w", 120.0))
    desgaste_h = float(config_data.get("desgaste_hora", 15.0))
    tarifa_mo_h = float(config_data.get("tarifa_mo_hora", 200.0))
    pct_fallas = float(config_data.get("factor_fallas_pct", 10.0))
    pct_margen = float(config_data.get("margen_ganancia_pct", 60.0))

    costo_mat = (precio_kg / 1000.0) * peso_g
    costo_luz = (watts / 1000.0) * tiempo_h * costo_kwh
    costo_desgaste = desgaste_h * tiempo_h
    costo_mo = (mo_min / 60.0) * tarifa_mo_h

    subtotal_operativo = costo_mat + costo_luz + costo_desgaste
    costo_con_merma = subtotal_operativo * (1.0 + (pct_fallas / 100.0))
    costo_total_unitario = costo_con_merma + costo_mo

    if pct_margen < 100:
        precio_lista_unitario = costo_total_unitario / (1.0 - (pct_margen / 100.0))
    else:
        precio_lista_unitario = costo_total_unitario * 2.0

    monto_descuento_unitario = precio_lista_unitario * (pct_descuento / 100.0)
    precio_final_unitario = precio_lista_unitario - monto_descuento_unitario

    precio_total_lote = precio_final_unitario * cantidad
    ganancia_neta_total = (precio_final_unitario - costo_total_unitario) * cantidad

    with col_right:
        st.subheader("Desglose de Costos")

        desglose_str = (
            f"Concepto                     Monto (x1 unid)\n"
            f"--------------------------------------------\n"
            f"Costo Filamento        : {moneda} ${costo_mat:.2f}\n"
            f"Energía Eléctrica      : {moneda} ${costo_luz:.2f}\n"
            f"Desgaste Impresora     : {moneda} ${costo_desgaste:.2f}\n"
            f"Merma/Fallas ({pct_fallas:.0f}%)   : {moneda} ${(costo_con_merma - subtotal_operativo):.2f}\n"
            f"Mano de Obra           : {moneda} ${costo_mo:.2f}\n"
            f"--------------------------------------------\n"
            f"Costo Base Total       : {moneda} ${costo_total_unitario:.2f}\n"
            f"Precio Lista (bruto)   : {moneda} ${precio_lista_unitario:.2f}\n"
            f"Desc. Mayoreo ({pct_descuento:.1f}%) : - {moneda} ${monto_descuento_unitario:.2f}\n"
            f"--------------------------------------------\n"
            f"Ganancia Neta Total Lote: {moneda} ${ganancia_neta_total:.2f}"
        )

        st.code(desglose_str, language="text")

        st.caption(f"Costo Base / Unid: {moneda} ${costo_total_unitario:.2f}")

        if pct_descuento > 0:
            st.markdown(f"**Precio Final / Unid:** :green[{moneda} ${precio_final_unitario:.2f}] *(Desc: -${monto_descuento_unitario:.2f})*")
        else:
            st.markdown(f"**Precio Sugerido / Unid:** :green[{moneda} ${precio_final_unitario:.2f}]")

        st.markdown(f"### **TOTAL LOTE ({cantidad} pcs): {moneda} ${precio_total_lote:.2f}**")

        # Botón para registrar cotización en CSV
        if st.button("💾 Registrar en Historial (CSV)", type="primary", use_container_width=True):
            archivo_existe = os.path.exists(HISTORIAL_FILE)
            try:
                with open(HISTORIAL_FILE, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if not archivo_existe:
                        writer.writerow(["Cliente", "Pieza", "Material", "Peso (g)", "Tiempo (h)", "Cantidad", "Descuento (%)", "Costo Unitario", "Precio Unitario Final", "Total Lote", "Moneda"])

                    writer.writerow([
                        cliente,
                        pieza,
                        preset_choice,
                        peso_g,
                        tiempo_h,
                        cantidad,
                        f"{pct_descuento:.1f}%",
                        f"{costo_total_unitario:.2f}",
                        f"{precio_final_unitario:.2f}",
                        f"{precio_total_lote:.2f}",
                        moneda
                    ])
                st.success("¡Cotización registrada y agregada al historial CSV!")
            except Exception as e:
                st.error(f"No se pudo guardar en el historial: {e}")

# --- PESTAÑA 2: CONFIGURACIÓN DEL TALLER ---
with tab_config:
    st.subheader("⚙️ Configuración Global del Taller")

    with st.form("form_config"):
        cfg_moneda = st.text_input("Moneda de Trabajo Predeterminada:", value=str(config_data.get("moneda", "MXN")))
        cfg_kwh = st.number_input("Costo de Energía ($ / kWh):", value=float(config_data.get("costo_kwh", 3.50)), step=0.1)
        cfg_watts = st.number_input("Consumo Promedio Impresora (Watts):", value=float(config_data.get("consumo_w", 120.0)), step=5.0)
        cfg_desgaste = st.number_input("Depreciación Hardware ($ / Hora):", value=float(config_data.get("desgaste_hora", 15.0)), step=1.0)
        cfg_mo = st.number_input("Costo de Mano de Obra ($ / Hora):", value=float(config_data.get("tarifa_mo_hora", 200.0)), step=10.0)
        cfg_fallas = st.number_input("Margen por Merma / Fallas (%):", value=float(config_data.get("factor_fallas_pct", 10.0)), step=1.0)
        cfg_margen = st.number_input("Margen de Ganancia Objetivo (%):", value=float(config_data.get("margen_ganancia_pct", 60.0)), step=1.0)

        btn_guardar_cfg = st.form_submit_button("💾 Guardar Configuración Global")

        if btn_guardar_cfg:
            nuevos_datos_cfg = {
                "moneda": cfg_moneda,
                "costo_kwh": cfg_kwh,
                "consumo_w": cfg_watts,
                "desgaste_hora": cfg_desgaste,
                "tarifa_mo_hora": cfg_mo,
                "factor_fallas_pct": cfg_fallas,
                "margen_ganancia_pct": cfg_margen
            }
            guardar_configuracion_disco(nuevos_datos_cfg)
            st.success("¡Parámetros globales guardados exitosamente!")

# --- PESTAÑA 3: HISTORIAL DE COTIZACIONES ---
with tab_historial:
    st.subheader("📜 Cotizaciones Guardadas")

    if os.path.exists(HISTORIAL_FILE):
        try:
            df_historial = pd.read_csv(HISTORIAL_FILE)
            if not df_historial.empty:
                st.dataframe(df_historial, use_container_width=True)

                col_actions_1, col_actions_2 = st.columns([1, 1])

                with col_actions_1:
                    # Descargar CSV directamente
                    csv_bytes = df_historial.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Exportar / Descargar CSV",
                        data=csv_bytes,
                        file_name="historial_cotizaciones.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                with col_actions_2:
                    # Selección de fila para eliminar
                    opciones_filas = [f"{i}: {row['Cliente']} - {row['Pieza']} ({row['Total Lote']} {row['Moneda']})" for i, row in df_historial.iterrows()]
                    fila_a_eliminar = st.selectbox("Selecciona cotización para eliminar:", opciones_filas)

                    if st.button("🗑️ Eliminar Seleccionado", type="primary", use_container_width=True):
                        idx_eliminar = int(fila_a_eliminar.split(":")[0])
                        df_actualizado = df_historial.drop(idx_eliminar)
                        df_actualizado.to_csv(HISTORIAL_FILE, index=False, encoding="utf-8")
                        st.success("Cotización eliminada correctamente.")
                        st.rerun()
            else:
                st.info("El historial de cotizaciones está vacío.")
        except Exception as e:
            st.error(f"Error al leer el historial CSV: {e}")
    else:
        st.info("Aún no se ha registrado ninguna cotización.")
