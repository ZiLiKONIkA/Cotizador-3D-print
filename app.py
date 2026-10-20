import os
import csv
import json
import sys
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import customtkinter as ctk

# Función helper para resolver la ruta de recursos en el ejecutable empaquetado (_MEIPASS)
def resource_path(relative_path):
    """ Obtiene la ruta absoluta para recursos, funciona en dev y en PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Configuración del tema global CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

CONFIG_FILE = "config_cotizadora.json"
SESSION_FILE = "sesion_cotizadora.json"
HISTORIAL_FILE = "historial_cotizaciones.csv"
ICON_FILE = "app_icon.ico"

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

class AppCotizadoraModern(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cotizadora 3D Pro - ZKN Dark Edition")
        self.geometry("1120x800")
        self.minsize(980, 720)
        
        # Cargar icono de ventana compatible tanto en dev como en .exe empaquetado
        icon_path = resource_path(ICON_FILE)
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
            
            try:
                # Método reforzado mediante PhotoImage para forzar reemplazo en Tkinter/CustomTkinter
                self.img_icon_app = tk.PhotoImage(file=icon_path)
                self.iconphoto(False, self.img_icon_app)
            except Exception:
                pass
        
        self.config_data = self.cargar_configuracion()
        self.session_data = self.cargar_sesion()
        
        self.create_layout()
        self.restaurar_sesion_ui()
        self.calcular_costos()
        self.cargar_historial_en_tabla()

        self.protocol("WM_DELETE_WINDOW", self.al_cerrar)

    def cargar_configuracion(self):
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

    def guardar_configuracion_disco(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}")

    def cargar_sesion(self):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def guardar_sesion_disco(self):
        try:
            sesion = {
                "moneda": self.cb_moneda_rapida.get(),
                "cliente": self.entry_cliente.get(),
                "pieza": self.entry_pieza.get(),
                "preset": self.cb_preset.get(),
                "precio_kg": self.entry_precio_kg.get(),
                "peso_g": self.entry_peso_g.get(),
                "tiempo_h": self.entry_tiempo_h.get(),
                "mo_min": self.entry_mo_min.get(),
                "cantidad": self.entry_cantidad.get(),
                "descuento_pct": self.entry_descuento_pct.get()
            }
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(sesion, f, indent=4)
        except Exception:
            pass

    def create_layout(self):
        # Header Superior
        self.header_frame = ctk.CTkFrame(self, fg_color="#18181c", corner_radius=0, height=60)
        self.header_frame.pack(fill="x", side="top")
        
        self.lbl_titulo = ctk.CTkLabel(
            self.header_frame, 
            text="⚡ Cotizadora & Calculadora de Impresión 3D Pro (K1C)", 
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#ffffff"
        )
        self.lbl_titulo.pack(side="left", padx=20, pady=15)
        
        # Tabview (Pestañas)
        self.tabview = ctk.CTkTabview(
            self, 
            corner_radius=12, 
            fg_color="#18181c", 
            segmented_button_selected_color="#bb86fc", 
            segmented_button_selected_hover_color="#9955e8"
        )
        self.tabview.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.tab_cotizador = self.tabview.add("📊 Cotizador de Piezas")
        self.tab_config = self.tabview.add("⚙️ Configuración del Taller")
        self.tab_historial = self.tabview.add("📜 Historial de Cotizaciones")
        
        self.build_tab_cotizador()
        self.build_tab_config()
        self.build_tab_historial()

    def build_tab_cotizador(self):
        self.tab_cotizador.grid_columnconfigure(0, weight=1)
        self.tab_cotizador.grid_columnconfigure(1, weight=1)
        self.tab_cotizador.grid_rowconfigure(0, weight=1)

        self.left_panel = ctk.CTkScrollableFrame(self.tab_cotizador, fg_color="#212126", corner_radius=12)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.right_panel = ctk.CTkFrame(self.tab_cotizador, fg_color="#212126", corner_radius=12)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Proyecto y Moneda
        header_proj_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        header_proj_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.lbl_sec_proj = ctk.CTkLabel(header_proj_frame, text="Información del Proyecto", font=ctk.CTkFont(size=14, weight="bold"), text_color="#bb86fc")
        self.lbl_sec_proj.pack(side="left")

        self.cb_moneda_rapida = ctk.CTkSegmentedButton(
            header_proj_frame, 
            values=["MXN", "USD"], 
            command=self.on_moneda_change,
            selected_color="#bb86fc",
            selected_hover_color="#9955e8"
        )
        self.cb_moneda_rapida.set(self.config_data.get("moneda", "MXN"))
        self.cb_moneda_rapida.pack(side="right")

        self.entry_cliente = ctk.CTkEntry(self.left_panel, placeholder_text="Nombre del Cliente", corner_radius=8)
        self.entry_cliente.insert(0, "Cliente General")
        self.entry_cliente.pack(fill="x", padx=10, pady=5)

        self.entry_pieza = ctk.CTkEntry(self.left_panel, placeholder_text="Nombre de la Pieza", corner_radius=8)
        self.entry_pieza.insert(0, "Soporte_Rack_2020")
        self.entry_pieza.pack(fill="x", padx=10, pady=5)

        # Parámetros Técnicos
        self.lbl_sec_tech = ctk.CTkLabel(self.left_panel, text="Parámetros del Slicer", font=ctk.CTkFont(size=14, weight="bold"), text_color="#bb86fc")
        self.lbl_sec_tech.pack(anchor="w", padx=10, pady=(15, 5))

        ctk.CTkLabel(self.left_panel, text="Preset de Filamento:").pack(anchor="w", padx=10)
        self.cb_preset = ctk.CTkOptionMenu(
            self.left_panel, 
            values=list(MATERIALES_PRESET_USD.keys()), 
            command=self.on_preset_change, 
            corner_radius=8,
            fg_color="#33333e",
            button_color="#bb86fc",
            button_hover_color="#9955e8"
        )
        self.cb_preset.set("PA-CF / PA12-CF (Nylon Fibra Carbono)")
        self.cb_preset.pack(fill="x", padx=10, pady=5)

        self.lbl_precio_kg_title = ctk.CTkLabel(self.left_panel, text="Precio Filamento ($/kg):")
        self.lbl_precio_kg_title.pack(anchor="w", padx=10)
        
        self.entry_precio_kg = ctk.CTkEntry(self.left_panel, corner_radius=8)
        precio_init = MATERIALES_PRESET_USD["PA-CF / PA12-CF (Nylon Fibra Carbono)"] * TIPO_CAMBIO_PRESET
        self.entry_precio_kg.insert(0, str(precio_init))
        self.entry_precio_kg.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.left_panel, text="Peso Pieza + Soportes (Gramos):").pack(anchor="w", padx=10)
        self.entry_peso_g = ctk.CTkEntry(self.left_panel, corner_radius=8)
        self.entry_peso_g.insert(0, "85.0")
        self.entry_peso_g.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.left_panel, text="Tiempo de Impresión (Horas):").pack(anchor="w", padx=10)
        self.entry_tiempo_h = ctk.CTkEntry(self.left_panel, corner_radius=8)
        self.entry_tiempo_h.insert(0, "4.5")
        self.entry_tiempo_h.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.left_panel, text="Mano de Obra (Minutos dedicados):").pack(anchor="w", padx=10)
        self.entry_mo_min = ctk.CTkEntry(self.left_panel, corner_radius=8)
        self.entry_mo_min.insert(0, "20.0")
        self.entry_mo_min.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.left_panel, text="Cantidad de Piezas (Lote):").pack(anchor="w", padx=10)
        self.entry_cantidad = ctk.CTkEntry(self.left_panel, corner_radius=8)
        self.entry_cantidad.insert(0, "1")
        self.entry_cantidad.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.left_panel, text="Descuento Mayoreo / Volumen (%):", text_color="#00e676").pack(anchor="w", padx=10)
        self.entry_descuento_pct = ctk.CTkEntry(self.left_panel, corner_radius=8, placeholder_text="Ej. 10.0")
        self.entry_descuento_pct.insert(0, "0.0")
        self.entry_descuento_pct.pack(fill="x", padx=10, pady=5)

        self.btn_calc = ctk.CTkButton(
            self.left_panel, 
            text="⚡ CALCULAR Y DESGLOSAR", 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#bb86fc", 
            hover_color="#9955e8", 
            text_color="#000000",
            corner_radius=8,
            command=self.calcular_costos
        )
        self.btn_calc.pack(fill="x", padx=10, pady=20)

        for entry in [self.entry_cliente, self.entry_pieza, self.entry_precio_kg, self.entry_peso_g, self.entry_tiempo_h, self.entry_mo_min, self.entry_cantidad, self.entry_descuento_pct]:
            entry.bind("<KeyRelease>", lambda e: self.on_input_changed())

        # Panel Derecho
        self.lbl_sec_res = ctk.CTkLabel(self.right_panel, text="Desglose de Costos", font=ctk.CTkFont(size=14, weight="bold"), text_color="#bb86fc")
        self.lbl_sec_res.pack(anchor="w", padx=15, pady=(15, 5))

        self.desglose_frame = ctk.CTkFrame(self.right_panel, fg_color="#18181c", corner_radius=8)
        self.desglose_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.lbl_desglose_text = ctk.CTkLabel(
            self.desglose_frame, 
            text="", 
            font=ctk.CTkFont(family="Consolas", size=12),
            justify="left",
            anchor="nw"
        )
        self.lbl_desglose_text.pack(fill="both", expand=True, padx=12, pady=12)

        self.card_total = ctk.CTkFrame(self.right_panel, fg_color="#2b2b36", corner_radius=10, border_width=1, border_color="#bb86fc")
        self.card_total.pack(fill="x", padx=15, pady=(0, 10))

        self.lbl_costo_unitario = ctk.CTkLabel(self.card_total, text="Costo Base / Unid: $0.00", font=ctk.CTkFont(size=11), text_color="#aaaaaa")
        self.lbl_costo_unitario.pack(anchor="w", padx=12, pady=(8, 0))

        self.lbl_precio_unitario = ctk.CTkLabel(self.card_total, text="Precio Sugerido / Unid: $0.00", font=ctk.CTkFont(size=13, weight="bold"), text_color="#00e676")
        self.lbl_precio_unitario.pack(anchor="w", padx=12, pady=(2, 0))

        self.lbl_precio_total_lote = ctk.CTkLabel(self.card_total, text="TOTAL LOTE (1 pcs): $0.00", font=ctk.CTkFont(size=15, weight="bold"), text_color="#ffffff")
        self.lbl_precio_total_lote.pack(anchor="w", padx=12, pady=(4, 8))

        self.btn_guardar_historial = ctk.CTkButton(
            self.right_panel, 
            text="💾 Registrar en Historial (CSV)", 
            fg_color="#00e676", 
            hover_color="#00b359", 
            text_color="#000000",
            corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=self.registrar_historial
        )
        self.btn_guardar_historial.pack(fill="x", padx=15, pady=(0, 15))

    def build_tab_config(self):
        self.config_container = ctk.CTkFrame(self.tab_config, fg_color="#212126", corner_radius=12)
        self.config_container.pack(fill="x", padx=20, pady=20)

        self.entries_cfg = {}
        fields = [
            ("moneda", "Moneda de Trabajo Predeterminada:", self.config_data["moneda"]),
            ("costo_kwh", "Costo de Energía ($ / kWh):", str(self.config_data["costo_kwh"])),
            ("consumo_w", "Consumo Promedio Impresora (Watts):", str(self.config_data["consumo_w"])),
            ("desgaste_hora", "Depreciación Hardware ($ / Hora):", str(self.config_data["desgaste_hora"])),
            ("tarifa_mo_hora", "Costo de Mano de Obra ($ / Hora):", str(self.config_data["tarifa_mo_hora"])),
            ("factor_fallas_pct", "Margen por Merma / Fallas (%):", str(self.config_data["factor_fallas_pct"])),
            ("margen_ganancia_pct", "Margen de Ganancia Objetivo (%):", str(self.config_data["margen_ganancia_pct"])),
        ]

        for key, label_text, val_default in fields:
            row_frame = ctk.CTkFrame(self.config_container, fg_color="transparent")
            row_frame.pack(fill="x", padx=15, pady=8)

            lbl = ctk.CTkLabel(row_frame, text=label_text)
            lbl.pack(side="left")

            entry = ctk.CTkEntry(row_frame, width=150, corner_radius=8)
            entry.insert(0, str(val_default))
            entry.pack(side="right")

            self.entries_cfg[key] = entry

        self.btn_save_config = ctk.CTkButton(
            self.tab_config, 
            text="💾 Guardar Configuración Global", 
            fg_color="#bb86fc", 
            hover_color="#9955e8", 
            text_color="#000000",
            corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            command=self.guardar_configuracion_ui
        )
        self.btn_save_config.pack(anchor="e", padx=20, pady=10)

    def build_tab_historial(self):
        self.hist_container = ctk.CTkFrame(self.tab_historial, fg_color="#212126", corner_radius=12)
        self.hist_container.pack(fill="both", expand=True, padx=15, pady=15)

        top_bar = ctk.CTkFrame(self.hist_container, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=10)

        lbl_hist_title = ctk.CTkLabel(top_bar, text="Cotizaciones Guardadas", font=ctk.CTkFont(size=14, weight="bold"), text_color="#bb86fc")
        lbl_hist_title.pack(side="left")

        btn_export = ctk.CTkButton(
            top_bar, text="📥 Exportar / Descargar CSV", fg_color="#007acc", hover_color="#005999", corner_radius=8, command=self.exportar_csv_dialogo
        )
        btn_export.pack(side="right", padx=5)

        btn_delete = ctk.CTkButton(
            top_bar, text="🗑️ Eliminar Seleccionado", fg_color="#d32f2f", hover_color="#9a0007", corner_radius=8, command=self.eliminar_cotizacion_seleccionada
        )
        btn_delete.pack(side="right", padx=5)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#18181c", foreground="#ffffff", fieldbackground="#18181c", rowheight=26, borderwidth=0)
        style.configure("Treeview.Heading", background="#2b2b36", foreground="#00e676", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#bb86fc")], foreground=[("selected", "#000000")])

        cols = ("Cliente", "Pieza", "Material", "Peso (g)", "Tiempo (h)", "Cant.", "Desc.", "Total Lote", "Moneda")
        self.tree_historial = ttk.Treeview(self.hist_container, columns=cols, show="headings", selectmode="browse")
        
        widths = [130, 140, 160, 70, 70, 50, 60, 100, 60]
        for col, w in zip(cols, widths):
            self.tree_historial.heading(col, text=col)
            self.tree_historial.column(col, width=w, anchor="center" if w < 100 else "w")

        scrollbar = ttk.Scrollbar(self.hist_container, orient="vertical", command=self.tree_historial.yview)
        self.tree_historial.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self.tree_historial.pack(fill="both", expand=True, padx=(10, 0), pady=10)

    def cargar_historial_en_tabla(self):
        for item in self.tree_historial.get_children():
            self.tree_historial.delete(item)

        if not os.path.exists(HISTORIAL_FILE):
            return

        try:
            with open(HISTORIAL_FILE, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if row:
                        self.tree_historial.insert("", tk.END, values=row)
        except Exception:
            pass

    def eliminar_cotizacion_seleccionada(self):
        selected_item = self.tree_historial.selection()
        if not selected_item:
            messagebox.showwarning("Atención", "Por favor selecciona una cotización de la lista para eliminar.")
            return

        values_to_remove = list(self.tree_historial.item(selected_item[0])["values"])

        if os.path.exists(HISTORIAL_FILE):
            rows = []
            with open(HISTORIAL_FILE, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if [str(x) for x in row] != [str(x) for x in values_to_remove]:
                        rows.append(row)

            with open(HISTORIAL_FILE, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if header:
                    writer.writerow(header)
                writer.writerows(rows)

        self.cargar_historial_en_tabla()
        messagebox.showinfo("Eliminado", "La cotización fue eliminada del historial.")

    def exportar_csv_dialogo(self):
        if not os.path.exists(HISTORIAL_FILE):
            messagebox.showwarning("Historial Vacío", "Aún no hay cotizaciones registradas para exportar.")
            return

        path_destino = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv"), ("Todos los archivos", "*.*")],
            title="Guardar archivo de historial como..."
        )

        if path_destino:
            try:
                import shutil
                shutil.copyfile(HISTORIAL_FILE, path_destino)
                messagebox.showinfo("Éxito", f"Historial guardado exitosamente en:\n{path_destino}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")

    def restaurar_sesion_ui(self):
        s = self.session_data
        if not s:
            return
            
        if "moneda" in s:
            self.cb_moneda_rapida.set(s["moneda"])
        if "cliente" in s:
            self.entry_cliente.delete(0, tk.END)
            self.entry_cliente.insert(0, s["cliente"])
        if "pieza" in s:
            self.entry_pieza.delete(0, tk.END)
            self.entry_pieza.insert(0, s["pieza"])
        if "preset" in s and s["preset"] in MATERIALES_PRESET_USD:
            self.cb_preset.set(s["preset"])
        if "precio_kg" in s:
            self.entry_precio_kg.delete(0, tk.END)
            self.entry_precio_kg.insert(0, s["precio_kg"])
        if "peso_g" in s:
            self.entry_peso_g.delete(0, tk.END)
            self.entry_peso_g.insert(0, s["peso_g"])
        if "tiempo_h" in s:
            self.entry_tiempo_h.delete(0, tk.END)
            self.entry_tiempo_h.insert(0, s["tiempo_h"])
        if "mo_min" in s:
            self.entry_mo_min.delete(0, tk.END)
            self.entry_mo_min.insert(0, s["mo_min"])
        if "cantidad" in s:
            self.entry_cantidad.delete(0, tk.END)
            self.entry_cantidad.insert(0, s["cantidad"])
        if "descuento_pct" in s:
            self.entry_descuento_pct.delete(0, tk.END)
            self.entry_descuento_pct.insert(0, s["descuento_pct"])

    def on_input_changed(self):
        self.calcular_costos()
        self.guardar_sesion_disco()

    def on_moneda_change(self, nueva_moneda):
        if "moneda" in self.entries_cfg:
            self.entries_cfg["moneda"].delete(0, tk.END)
            self.entries_cfg["moneda"].insert(0, nueva_moneda)
        
        self.on_preset_change(self.cb_preset.get())

    def on_preset_change(self, choice):
        if choice in MATERIALES_PRESET_USD:
            precio_base = MATERIALES_PRESET_USD[choice]
            moneda_actual = self.cb_moneda_rapida.get()
            
            if moneda_actual == "MXN":
                precio_final = precio_base * TIPO_CAMBIO_PRESET
            else:
                precio_final = precio_base
                
            self.entry_precio_kg.delete(0, tk.END)
            self.entry_precio_kg.insert(0, f"{precio_final:.2f}")
            self.on_input_changed()

    def get_float(self, entry_widget, default=0.0):
        try:
            val = float(entry_widget.get().strip())
            return val
        except ValueError:
            return default

    def calcular_costos(self):
        moneda = self.cb_moneda_rapida.get()
        
        precio_kg = self.get_float(self.entry_precio_kg, 20.0)
        peso_g = self.get_float(self.entry_peso_g, 0.0)
        tiempo_h = self.get_float(self.entry_tiempo_h, 0.0)
        mo_min = self.get_float(self.entry_mo_min, 0.0)
        cant = max(1, int(self.get_float(self.entry_cantidad, 1.0)))
        pct_descuento = max(0.0, min(100.0, self.get_float(self.entry_descuento_pct, 0.0)))

        costo_kwh = self.get_float(self.entries_cfg["costo_kwh"], self.config_data["costo_kwh"]) if "costo_kwh" in self.entries_cfg else self.config_data["costo_kwh"]
        watts = self.get_float(self.entries_cfg["consumo_w"], self.config_data["consumo_w"]) if "consumo_w" in self.entries_cfg else self.config_data["consumo_w"]
        desgaste_h = self.get_float(self.entries_cfg["desgaste_hora"], self.config_data["desgaste_hora"]) if "desgaste_hora" in self.entries_cfg else self.config_data["desgaste_hora"]
        tarifa_mo_h = self.get_float(self.entries_cfg["tarifa_mo_hora"], self.config_data["tarifa_mo_hora"]) if "tarifa_mo_hora" in self.entries_cfg else self.config_data["tarifa_mo_hora"]
        pct_fallas = self.get_float(self.entries_cfg["factor_fallas_pct"], self.config_data["factor_fallas_pct"]) if "factor_fallas_pct" in self.entries_cfg else self.config_data["factor_fallas_pct"]
        pct_margen = self.get_float(self.entries_cfg["margen_ganancia_pct"], self.config_data["margen_ganancia_pct"]) if "margen_ganancia_pct" in self.entries_cfg else self.config_data["margen_ganancia_pct"]

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

        precio_total_lote = precio_final_unitario * cant
        ganancia_neta_total = (precio_final_unitario - costo_total_unitario) * cant

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

        self.lbl_desglose_text.configure(text=desglose_str)

        self.lbl_costo_unitario.configure(text=f"Costo Base / Unid: {moneda} ${costo_total_unitario:.2f}")
        
        if pct_descuento > 0:
            self.lbl_precio_unitario.configure(
                text=f"Precio Final / Unid: {moneda} ${precio_final_unitario:.2f}  (Desc: -${monto_descuento_unitario:.2f})"
            )
        else:
            self.lbl_precio_unitario.configure(
                text=f"Precio Sugerido / Unid: {moneda} ${precio_final_unitario:.2f}"
            )

        self.lbl_precio_total_lote.configure(
            text=f"TOTAL LOTE ({cant} pcs): {moneda} ${precio_total_lote:.2f}"
        )

        self.ultimo_calculo = {
            "cliente": self.entry_cliente.get(),
            "pieza": self.entry_pieza.get(),
            "material": self.cb_preset.get(),
            "peso_g": peso_g,
            "tiempo_h": tiempo_h,
            "cantidad": cant,
            "descuento_pct": pct_descuento,
            "costo_unitario": costo_total_unitario,
            "precio_unitario": precio_final_unitario,
            "precio_total": precio_total_lote,
            "moneda": moneda
        }

    def guardar_configuracion_ui(self):
        try:
            for key, entry in self.entries_cfg.items():
                if key == "moneda":
                    self.config_data[key] = entry.get()
                else:
                    self.config_data[key] = float(entry.get())

            self.guardar_configuracion_disco()
            self.calcular_costos()
            messagebox.showinfo("Configuración", "¡Parámetros globales guardados exitosamente!")
        except Exception as e:
            messagebox.showerror("Error", f"Verifique los datos ingresados: {e}")

    def registrar_historial(self):
        if not hasattr(self, 'ultimo_calculo'):
            return

        calc = self.ultimo_calculo
        archivo_existe = os.path.exists(HISTORIAL_FILE)

        try:
            with open(HISTORIAL_FILE, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not archivo_existe:
                    writer.writerow(["Cliente", "Pieza", "Material", "Peso (g)", "Tiempo (h)", "Cantidad", "Descuento (%)", "Costo Unitario", "Precio Unitario Final", "Total Lote", "Moneda"])

                writer.writerow([
                    calc["cliente"],
                    calc["pieza"],
                    calc["material"],
                    calc["peso_g"],
                    calc["tiempo_h"],
                    calc["cantidad"],
                    f"{calc['descuento_pct']:.1f}%",
                    f"{calc['costo_unitario']:.2f}",
                    f"{calc['precio_unitario']:.2f}",
                    f"{calc['precio_total']:.2f}",
                    calc["moneda"]
                ])
            
            self.cargar_historial_en_tabla()
            messagebox.showinfo("Historial", "Cotización registrada y agregada a la lista de historial.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar en historial: {e}")

    def al_cerrar(self):
        self.guardar_sesion_disco()
        self.destroy()

if __name__ == "__main__":
    app = AppCotizadoraModern()
    app.mainloop()
