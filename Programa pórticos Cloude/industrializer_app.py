# -*- coding: utf-8 -*-
"""Industrializer: interfaz extendida sobre la aplicación estructural existente."""
from __future__ import annotations
from pathlib import Path
from tkinter import messagebox, PhotoImage
import customtkinter as ctk
from matplotlib.image import imread

from app_interface import MainStructuralApp
from frame_renderer_enhanced import EnhancedStructureRenderer
from pdf_exporter import export_preview_pdf

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
SEAL_PATH = ASSETS_DIR / "santos_corp_seal.png"
ICON_PATH = ASSETS_DIR / "industrializer.png"


class PdfContinueDialog(ctk.CTkToplevel):
    def __init__(self, master, on_continue):
        super().__init__(master)
        self.title("Industrializer — Control de calidad")
        self.geometry("520x300")
        self.resizable(False, False)
        self.on_continue = on_continue
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        ctk.CTkLabel(self, text="⚠  ADVERTENCIA MUY SERIA (más o menos)",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(28, 12))
        ctk.CTkLabel(self, text=(
            "Industrializer ha detectado que estás a punto de convertir\n"
            "una previsualización perfectamente normal en un PDF.\n\n"
            "El equipo de Santos Corp. recomienda pensarlo durante\n"
            "exactamente 3 segundos antes de continuar."),
            justify="center", text_color="gray80", font=ctk.CTkFont(size=12)).pack(padx=20, pady=8)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(pady=20)
        ctk.CTkButton(row, text="Cancelar", fg_color="gray40", command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(row, text="Continuar de todos modos", fg_color="#2f855a",
                      hover_color="#276749", command=self._continue).pack(side="left", padx=8)
        self.after(60, self._grab)

    def _grab(self):
        try: self.grab_set()
        except Exception: pass

    def _continue(self):
        try: self.grab_release()
        except Exception: pass
        self.destroy()
        self.on_continue()


class IndustrializerApp(MainStructuralApp):
    def __init__(self):
        super().__init__()
        self.title("Industrializer — Santos Corp.")
        self._set_icon()
        self._node_edit_original = None
        self._elem_edit_original = None

    def _set_icon(self):
        if not ICON_PATH.exists(): return
        try:
            self._tk_icon = PhotoImage(file=str(ICON_PATH))
            self.iconphoto(True, self._tk_icon)
        except Exception:
            pass

    def _build_editor_tab(self):
        super()._build_editor_tab()
        self.renderer = EnhancedStructureRenderer(self.ax, self.units)
        self._build_edit_controls()

    def _find_editor_left(self):
        for child in self.tab_editor.winfo_children():
            try:
                if str(child.grid_info().get("column")) == "0": return child
            except Exception: pass
        return None

    def _build_edit_controls(self):
        left = self._find_editor_left()
        if left is None: return
        ctk.CTkFrame(left, height=2, fg_color="gray40").grid(row=19, column=0, sticky="ew", padx=8, pady=6)
        ctk.CTkLabel(left, text="EDITAR / ELIMINAR", font=ctk.CTkFont(weight="bold")).grid(row=20, column=0, sticky="w", padx=8, pady=(4,2))
        ctk.CTkLabel(left, text="Nodo seleccionado:").grid(row=21, column=0, sticky="w", padx=8)
        self.node_selector = ctk.CTkOptionMenu(left, values=["—"], command=self._load_selected_node)
        self.node_selector.set("—"); self.node_selector.grid(row=22, column=0, sticky="ew", padx=8, pady=3)
        nb = ctk.CTkFrame(left, fg_color="transparent"); nb.grid(row=23, column=0, sticky="ew", padx=8, pady=2); nb.grid_columnconfigure((0,1), weight=1)
        ctk.CTkButton(nb, text="Actualizar Nodo", command=self._update_selected_node).grid(row=0,column=0,sticky="ew",padx=(0,3))
        ctk.CTkButton(nb, text="Eliminar Nodo", fg_color="#c53030", hover_color="#9b2c2c", command=self._delete_selected_node).grid(row=0,column=1,sticky="ew",padx=(3,0))
        ctk.CTkLabel(left, text="Elemento seleccionado:").grid(row=24, column=0, sticky="w", padx=8, pady=(6,1))
        self.elem_selector = ctk.CTkOptionMenu(left, values=["—"], command=self._load_selected_element)
        self.elem_selector.set("—"); self.elem_selector.grid(row=25, column=0, sticky="ew", padx=8, pady=3)
        eb = ctk.CTkFrame(left, fg_color="transparent"); eb.grid(row=26, column=0, sticky="ew", padx=8, pady=2); eb.grid_columnconfigure((0,1), weight=1)
        ctk.CTkButton(eb, text="Actualizar Elemento", command=self._update_selected_element).grid(row=0,column=0,sticky="ew",padx=(0,3))
        ctk.CTkButton(eb, text="Eliminar Elemento", fg_color="#c53030", hover_color="#9b2c2c", command=self._delete_selected_element).grid(row=0,column=1,sticky="ew",padx=(3,0))
        ctk.CTkLabel(left, text="Al eliminar un nodo también se eliminan los elementos conectados a él.", font=ctk.CTkFont(size=10), text_color="gray60").grid(row=27,column=0,sticky="w",padx=8,pady=(3,12))
        self._refresh_edit_selectors()

    @staticmethod
    def _entry_set(entry, value):
        entry.delete(0,"end"); entry.insert(0,str(value))

    def _refresh_edit_selectors(self):
        if not hasattr(self,"node_selector"): return
        nv=list(self.nodes.keys()) or ["—"]; ev=list(self.elements.keys()) or ["—"]
        self.node_selector.configure(values=nv); self.elem_selector.configure(values=ev)
        if self.node_selector.get() not in self.nodes: self.node_selector.set(nv[0])
        if self.elem_selector.get() not in self.elements: self.elem_selector.set(ev[0])

    def _load_selected_node(self,nid):
        if nid not in self.nodes: self._node_edit_original=None; return
        n=self.nodes[nid]; self._node_edit_original=nid
        for k in ("id","x","y","fx","fy"): self._entry_set(self.node_form[k],n[k])
        if "mz" in self.node_form: self._entry_set(self.node_form["mz"],n.get("mz",0.0))
        for k in ("rx","ry","rz"):
            if k in self.node_form:
                self.node_form[k].select() if n.get(k) else self.node_form[k].deselect()

    def _read_node_form(self):
        nid=self.node_form["id"].get().strip()
        if not nid: raise ValueError("El ID del nodo no puede estar vacío.")
        return nid,dict(x=self._get_float(self.node_form["x"],"X"),y=self._get_float(self.node_form["y"],"Y"),
            rx=bool(self.node_form["rx"].get()),ry=bool(self.node_form["ry"].get()),rz=bool(self.node_form["rz"].get()) if "rz" in self.node_form else False,
            fx=self._get_float(self.node_form["fx"],"Fx"),fy=self._get_float(self.node_form["fy"],"Fy"),mz=self._get_float(self.node_form["mz"],"Mz") if "mz" in self.node_form else 0.0)

    def _update_selected_node(self):
        old=self._node_edit_original or self.node_selector.get()
        if old not in self.nodes: messagebox.showinfo("Editar nodo","Selecciona primero un nodo existente."); return
        try:
            new,data=self._read_node_form()
            if new!=old and new in self.nodes: raise ValueError(f"Ya existe un nodo con ID '{new}'.")
            self.nodes.pop(old); self.nodes[new]=data
            if new!=old:
                for el in self.elements.values():
                    if el["ni"]==old: el["ni"]=new
                    if el["nj"]==old: el["nj"]=new
            self._node_edit_original=new; self._refresh_lists(); self._refresh_edit_selectors(); self.node_selector.set(new); self._invalidate_after_model_change(); self._redraw()
        except Exception as exc: messagebox.showerror("Error al actualizar nodo",str(exc))

    def _delete_selected_node(self):
        nid=self.node_selector.get()
        if nid not in self.nodes: messagebox.showinfo("Eliminar nodo","Selecciona primero un nodo existente."); return
        connected=[eid for eid,e in self.elements.items() if nid in (e["ni"],e["nj"])]
        msg=f"¿Eliminar el nodo '{nid}'?" + ("\n\nTambién se eliminarán los elementos conectados: "+", ".join(connected) if connected else "")
        if not messagebox.askyesno("Confirmar eliminación",msg): return
        del self.nodes[nid]
        for eid in connected: del self.elements[eid]
        self._node_edit_original=None; self._refresh_lists(); self._refresh_edit_selectors(); self._invalidate_after_model_change(); self._redraw()

    def _load_selected_element(self,eid):
        if eid not in self.elements: self._elem_edit_original=None; return
        e=self.elements[eid]; self._elem_edit_original=eid
        for k in ("id","ni","nj","A","E","fy"): self._entry_set(self.elem_form[k],e[k])
        if self.structure_type=="frame":
            for k in ("I","w1","w2"): self._entry_set(self.elem_form[k],e.get(k,0.0))

    def _read_element_form(self):
        eid=self.elem_form["id"].get().strip(); ni=self.elem_form["ni"].get().strip(); nj=self.elem_form["nj"].get().strip()
        if not eid: raise ValueError("El ID del elemento no puede estar vacío.")
        if ni not in self.nodes or nj not in self.nodes: raise ValueError("Los nodos i y j deben existir.")
        if ni==nj: raise ValueError("Los nodos i y j no pueden ser iguales.")
        A=self._get_float(self.elem_form["A"],"Área A"); E=self._get_float(self.elem_form["E"],"Módulo E"); fy=self._get_float(self.elem_form["fy"],"fy")
        if A<=0 or E<=0: raise ValueError("Área y E deben ser mayores que cero.")
        d=dict(ni=ni,nj=nj,A=A,E=E,fy=fy)
        if self.structure_type=="frame":
            I=self._get_float(self.elem_form["I"],"Inercia I"); w1=self._get_float(self.elem_form["w1"],"w1"); w2=self._get_float(self.elem_form["w2"],"w2")
            if I<=0: raise ValueError("La inercia I debe ser mayor que cero.")
            d.update(I=I,w1=w1,w2=w2)
        return eid,d

    def _update_selected_element(self):
        old=self._elem_edit_original or self.elem_selector.get()
        if old not in self.elements: messagebox.showinfo("Editar elemento","Selecciona primero un elemento existente."); return
        try:
            new,data=self._read_element_form()
            if new!=old and new in self.elements: raise ValueError(f"Ya existe un elemento con ID '{new}'.")
            self.elements.pop(old); self.elements[new]=data; self._elem_edit_original=new; self._refresh_lists(); self._refresh_edit_selectors(); self.elem_selector.set(new); self._invalidate_after_model_change(); self._redraw()
        except Exception as exc: messagebox.showerror("Error al actualizar elemento",str(exc))

    def _delete_selected_element(self):
        eid=self.elem_selector.get()
        if eid not in self.elements: messagebox.showinfo("Eliminar elemento","Selecciona primero un elemento existente."); return
        if not messagebox.askyesno("Confirmar eliminación",f"¿Eliminar el elemento '{eid}'?"): return
        del self.elements[eid]; self._elem_edit_original=None; self._refresh_lists(); self._refresh_edit_selectors(); self._invalidate_after_model_change(); self._redraw()

    def _invalidate_after_model_change(self):
        self.last_results=None; self.fs_label.configure(text="FS sistema: --",text_color="gray70"); self.current_diagram="structure"
        try: self._render_procedure_placeholder()
        except Exception: pass
        self._clear_container(self.results_scroll)
        ctk.CTkLabel(self.results_scroll,text="Los resultados quedaron invalidados por un cambio en la estructura.\nPresione 'Calcular Estructura' nuevamente.",font=ctk.CTkFont(size=13),text_color="gray60",justify="center").grid(row=0,column=0,pady=60)
        self._clear_container(self.pdf_scroll)
        ctk.CTkLabel(self.pdf_scroll,text="La previsualización debe actualizarse después de recalcular.",font=ctk.CTkFont(size=13),text_color="gray70").grid(row=0,column=0,pady=80)

    def _on_add_node(self): super()._on_add_node(); self._refresh_edit_selectors()
    def _on_add_element(self): super()._on_add_element(); self._refresh_edit_selectors()

    def _new_page_fig(self):
        fig,ax=super()._new_page_fig()
        if SEAL_PATH.exists():
            try:
                image=imread(str(SEAL_PATH))
                ax.imshow(image,extent=(0.02,0.98,0.02,0.985),aspect="auto",alpha=0.075,zorder=0)
            except Exception: pass
        return fig,ax

    def _on_convert_pdf(self):
        if self.last_results is None:
            messagebox.showinfo("Sin resultados","Calcula la estructura antes de convertir la previsualización a PDF."); return
        PdfContinueDialog(self,self._export_pdf_now)

    def _export_pdf_now(self):
        try:
            out=export_preview_pdf(self.last_results,self.nodes,self.elements,self.structure_type,self.units,SEAL_PATH if SEAL_PATH.exists() else None)
            messagebox.showinfo("PDF generado",f"La previsualización se convirtió correctamente en:\n\n{out}")
        except Exception as exc: messagebox.showerror("Error al generar PDF",str(exc))


def run_app():
    app=IndustrializerApp(); app.mainloop()
