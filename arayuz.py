from __future__ import annotations

import calendar
import ctypes
import json
import os
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime, date, timedelta
from typing import Optional, Any, Callable

from modeller import format_zaman, TIME_FMT
from motor import RezervasyonMotoru, _id_num


HATA_ACIKLAMALARI: dict[str, str] = {
    "BULUNAMADI": "Kullanıcı, kaynak veya rezervasyon sistemde bulunamadı.",
    "ZAMAN_ADIMI_HATASI": "Saatler 15 dakikalık adımlara (:00, :15, :30, :45) oturmalı ve bitiş başlangıçtan sonra olmalıdır.",
    "GECMIS_ZAMAN": "Başlangıç saati mevcut simüle saatten önce olamaz.",
    "CALISMA_SAATI_DISI": "Rezervasyon aynı gün içinde ve 08:00 - 22:00 saatleri arasında kalmalıdır.",
    "SURE_SINIRI": "Süre en az 30 dakika ve rolün izin verdiği azami süre sınırında olmalıdır.",
    "ILERI_TARIH_SINIRI": "Seçilen tarih, rolün izin verdiği ileri tarih sınırını aşmaktadır (Güvenilirlik < 50 ise sınır 1 gündür).",
    "ROL_IZNI_YOK": "Kullanıcının rolü, seçilen kaynağı rezerve etmeye yetkili değildir.",
    "SERTIFIKA_YOK": "Kaynak türünün gerektirdiği sertifika kullanıcıda bulunmamaktadır.",
    "BAKIM": "Talep edilen zaman aralığı kaynağın bakım penceresi ile kesişmektedir.",
    "KESISME": "Kaynak belirtilen saat aralığında başka bir rezervasyon tarafından kullanılmaktadır.",
    "HAZIRLIK_IHLALI": "Kaynağın önceki rezervasyondan sonraki hazırlık (soğuma/havalandırma) süresi henüz dolmamıştır.",
    "ARDISIK_KULLANIM": "Aynı kullanıcının aynı kaynakta art arda iki rezervasyonu arasında en az 60 dakika boşluk olmalıdır.",
    "BAKIYE_YETERSIZ": "Kullanıcının KP bakiyesi bu rezervasyonun ücretini karşılamaya yetmemektedir.",
    "BEKLEME_GEREKSIZ": "Talep edilen aralık zaten müsaittir; bekleme kaydı açılmasına gerek yoktur.",
    "DURUM_HATASI": "Rezervasyonun mevcut durumu bu eylem için uygun değildir (Giriş/İptal için ONAYLI, Çıkış için KULLANIMDA olmalıdır).",
    "GIRIS_PENCERESI_DISI": "Giriş işlemi yalnızca başlangıçtan 10 dakika önce ile 15 dakika sonra arasındaki pencerede yapılabilir.",
    "ID_MEVCUT": "Bu ID ile kayıtlı bir kullanıcı veya kaynak zaten mevcuttur.",
    "TANIMSIZ_DEGER": "Girilen rol veya kaynak türü başlangıç dosyasında tanımlı değildir.",
    "GECERSIZ_DEGER": "ID/Ad boş bırakılamaz; bakiye (0 ile kota arası olmalı) ve güvenilirlik puanı (0-100 arası tamsayı) geçerli olmalıdır.",
    "PAKET_BOYUTU": "Paket rezervasyon en az 2, en fazla 4 kalem içerebilir.",
    "GUVENILIRLIK_DUSUK": "Güvenilirlik puanı 50'nin altında olan kullanıcılar paket rezervasyon yapamaz.",
    "PAKET_RED": "Paketteki kalemlerden en az biri doğrulama kurallarını geçemedi.",
    "PAKET_ICI_KESISME": "Paket içerisindeki kalemler kendi aralarında çakışmakta veya hazırlık/ardışık kurallarını ihlal etmektedir.",
    "SAAT_GERI": "Simüle saat geriye alınamaz.",
    "BILINMEYEN_KOMUT": "Bilinmeyen bir komut istendi.",
}

TEMALAR: dict[str, dict[str, str]] = {
    "light": {
        "bg": "#f8fafc",
        "panel": "#ffffff",
        "surface_alt": "#f1f5f9",
        "sidebar_bg": "#ffffff",
        "sidebar_hover": "#f1f5f9",
        "sidebar_active": "#eff6ff",
        "sidebar_active_fg": "#1d4ed8",
        "topbar_bg": "#ffffff",
        "topbar_fg": "#0f172a",
        "topbar_muted": "#64748b",
        "clock_bg": "#f1f5f9",
        "clock_label": "#0284c7",
        "clock_fg": "#0f172a",
        "notice_bg": "#f1f5f9",
        "notice_fg": "#334155",
        "panel_border": "#e2e8f0",
        "input_border": "#cbd5e1",
        "input_bg": "#ffffff",
        "text_dark": "#0f172a",
        "text_muted": "#64748b",
        "primary": "#2563eb",
        "primary_hover": "#1d4ed8",
        "primary_fg": "#ffffff",
        "btn_neutral_bg": "#f1f5f9",
        "btn_neutral_fg": "#334155",
        "btn_neutral_hover": "#e2e8f0",
        "btn_accent_bg": "#dbeafe",
        "btn_accent_fg": "#1d4ed8",
        "btn_accent_hover": "#bfdbfe",
        "btn_warn_bg": "#fef3c7",
        "btn_warn_fg": "#b45309",
        "btn_warn_hover": "#fde68a",
        "btn_disabled_bg": "#e2e8f0",
        "btn_disabled_fg": "#94a3b8",
        "code_bg": "#0f172a",
        "code_fg": "#38bdf8",
        "canvas_bg": "#ffffff",
        "canvas_row_even": "#ffffff",
        "canvas_row_odd": "#f8fafc",
        "canvas_header_bg": "#f1f5f9",
        "canvas_grid_hour": "#e2e8f0",
        "canvas_grid_quarter": "#f1f5f9",
        "tooltip_bg": "#0f172a",
        "tooltip_fg": "#f8fafc",
        "ONAYLI": "#3b82f6",
        "ONAYLI_BORDER": "#1d4ed8",
        "ONAYLI_FG": "#ffffff",
        "KULLANIMDA": "#10b981",
        "KULLANIMDA_BORDER": "#047857",
        "KULLANIMDA_FG": "#ffffff",
        "TAMAMLANDI": "#94a3b8",
        "TAMAMLANDI_BORDER": "#475569",
        "TAMAMLANDI_FG": "#0f172a",
        "IPTAL": "#ef4444",
        "IPTAL_BORDER": "#b91c1c",
        "IPTAL_FG": "#ffffff",
        "GELMEDI": "#f97316",
        "GELMEDI_BORDER": "#c2410c",
        "GELMEDI_FG": "#ffffff",
        "BAKIM": "#fef08a",
        "BAKIM_BORDER": "#ca8a04",
        "BAKIM_FG": "#854d0e",
        "HAZIRLIK": "#f3e8ff",
        "HAZIRLIK_BORDER": "#7e22ce",
        "HAZIRLIK_FG": "#6b21a8",
        "SIMULE_SAAT": "#ef4444",
        "SELECTION": "#facc15",
        "success": "#16a34a",
        "success_hover": "#15803d",
        "error": "#dc2626",
        "error_hover": "#b91c1c",
        "info": "#0284c7",
        "info_hover": "#0369a1",
        "warn": "#d97706",
        "tree_sel_bg": "#dbeafe",
        "tree_sel_fg": "#1e3a8a",
        "combobox_sel_bg": "#2563eb",
        "switch_track_off": "#cbd5e1",
        "switch_track_on": "#2563eb",
        "switch_knob": "#ffffff",
    },
    "dark": {
        "bg": "#0d1117",
        "panel": "#161b22",
        "surface_alt": "#21262d",
        "sidebar_bg": "#11141a",
        "sidebar_hover": "#1c2128",
        "sidebar_active": "#1f2d42",
        "sidebar_active_fg": "#60a5fa",
        "topbar_bg": "#11141a",
        "topbar_fg": "#e6edf3",
        "topbar_muted": "#8b949e",
        "clock_bg": "#161b22",
        "clock_label": "#38bdf8",
        "clock_fg": "#f0f6fc",
        "notice_bg": "#161b22",
        "notice_fg": "#cbd5e1",
        "panel_border": "#30363d",
        "input_border": "#30363d",
        "input_bg": "#0d1117",
        "text_dark": "#e6edf3",
        "text_muted": "#8b949e",
        "primary": "#2f81f7",
        "primary_hover": "#58a6ff",
        "primary_fg": "#ffffff",
        "btn_neutral_bg": "#21262d",
        "btn_neutral_fg": "#e6edf3",
        "btn_neutral_hover": "#30363d",
        "btn_accent_bg": "#1f2d42",
        "btn_accent_fg": "#60a5fa",
        "btn_accent_hover": "#263b57",
        "btn_warn_bg": "#3b2c0c",
        "btn_warn_fg": "#fbbf24",
        "btn_warn_hover": "#523e12",
        "btn_disabled_bg": "#21262d",
        "btn_disabled_fg": "#484f58",
        "code_bg": "#090c10",
        "code_fg": "#79c0ff",
        "canvas_bg": "#0d1117",
        "canvas_row_even": "#0d1117",
        "canvas_row_odd": "#12171f",
        "canvas_header_bg": "#161b22",
        "canvas_grid_hour": "#262c36",
        "canvas_grid_quarter": "#181d24",
        "tooltip_bg": "#21262d",
        "tooltip_fg": "#f0f6fc",
        "ONAYLI": "#1d4ed8",
        "ONAYLI_BORDER": "#60a5fa",
        "ONAYLI_FG": "#f8fafc",
        "KULLANIMDA": "#059669",
        "KULLANIMDA_BORDER": "#34d399",
        "KULLANIMDA_FG": "#f8fafc",
        "TAMAMLANDI": "#475569",
        "TAMAMLANDI_BORDER": "#94a3b8",
        "TAMAMLANDI_FG": "#f1f5f9",
        "IPTAL": "#b91c1c",
        "IPTAL_BORDER": "#f87171",
        "IPTAL_FG": "#fef2f2",
        "GELMEDI": "#c2410c",
        "GELMEDI_BORDER": "#fb923c",
        "GELMEDI_FG": "#fff7ed",
        "BAKIM": "#42300b",
        "BAKIM_BORDER": "#eab308",
        "BAKIM_FG": "#fde047",
        "HAZIRLIK": "#2e1065",
        "HAZIRLIK_BORDER": "#a855f7",
        "HAZIRLIK_FG": "#d8b4fe",
        "SIMULE_SAAT": "#f87171",
        "SELECTION": "#facc15",
        "success": "#34d399",
        "success_hover": "#10b981",
        "error": "#f87171",
        "error_hover": "#ef4444",
        "info": "#38bdf8",
        "info_hover": "#0ea5e9",
        "warn": "#fbbf24",
        "tree_sel_bg": "#1f2d42",
        "tree_sel_fg": "#60a5fa",
        "combobox_sel_bg": "#2f81f7",
        "switch_track_off": "#30363d",
        "switch_track_on": "#2f81f7",
        "switch_knob": "#f0f6fc",
    },
}

TUR_PALETLERI: dict[str, list[tuple[str, str, str, str]]] = {
    "light": [
        ("#eff6ff", "#2563eb", "#1e3a8a", "#2563eb"),
        ("#ecfdf5", "#059669", "#064e3b", "#047857"),
        ("#fffbeb", "#d97706", "#78350f", "#b45309"),
        ("#f5f3ff", "#7c3aed", "#4c1d95", "#6d28d9"),
        ("#fff1f2", "#e11d48", "#881337", "#be123c"),
        ("#ecfeff", "#0891b2", "#164e63", "#0e7490"),
    ],
    "dark": [
        ("#132036", "#3b82f6", "#bfdbfe", "#60a5fa"),
        ("#0d261f", "#10b981", "#a7f3d0", "#34d399"),
        ("#2b210e", "#f59e0b", "#fde68a", "#fbbf24"),
        ("#201538", "#8b5cf6", "#ddd6fe", "#a78bfa"),
        ("#2e131d", "#f43f5e", "#fecdd3", "#fb7185"),
        ("#0e262e", "#06b6d4", "#a5f3fc", "#22d3ee"),
    ],
}

TURKCE_AYLAR: list[str] = [
    "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


class SidebarToggleButonu(tk.Canvas):

    def __init__(self, parent: tk.Widget, on_toggle: Callable[[], None], tema_adi: str = "light") -> None:
        super().__init__(parent, width=34, height=28, highlightthickness=0, bd=0, cursor="hand2")
        self.on_toggle = on_toggle
        self.tema_adi = tema_adi
        self.acik = True
        self.hover = False
        self.bind("<Button-1>", lambda e: self.on_toggle())
        self.bind("<Enter>", lambda e: self._hover_degisti(True))
        self.bind("<Leave>", lambda e: self._hover_degisti(False))
        self.ciz()

    def _hover_degisti(self, durum: bool) -> None:
        self.hover = durum
        self.ciz()

    def tema_degistir(self, tema_adi: str, acik: bool) -> None:
        self.tema_adi = tema_adi
        self.acik = acik
        self.ciz()

    def ciz(self) -> None:
        t = TEMALAR[self.tema_adi]
        bg = t["btn_neutral_hover"] if self.hover else t["topbar_bg"]
        fg = t["primary"] if self.hover else t["topbar_fg"]
        self.configure(bg=bg)
        self.delete("all")
        self.create_rectangle(3, 3, 31, 25, outline=t["input_border"], fill=t["btn_neutral_bg"] if self.hover else "", width=1)
        self.create_rectangle(7, 7, 27, 21, outline=fg, width=1.4)
        self.create_line(14, 7, 14, 21, fill=fg, width=1.4)
        if self.acik:
            self.create_rectangle(8, 8, 13, 20, fill=fg, outline="")
        else:
            self.create_line(9, 11, 12, 11, fill=fg, width=1.4)
            self.create_line(9, 14, 12, 14, fill=fg, width=1.4)
            self.create_line(9, 17, 12, 17, fill=fg, width=1.4)


class TemaSwitch(tk.Canvas):

    def __init__(self, parent: tk.Widget, acik: bool, on_toggle: Callable[[bool], None], tema_adi: str = "light") -> None:
        super().__init__(parent, width=46, height=24, highlightthickness=0, bd=0, cursor="hand2")
        self.acik = acik
        self.on_toggle = on_toggle
        self.tema_adi = tema_adi
        self.bind("<Button-1>", self._tiklandi)
        self.ciz()

    def _tiklandi(self, event=None) -> None:
        self.acik = not self.acik
        self.ciz()
        self.on_toggle(self.acik)

    def set_durum(self, acik: bool, tema_adi: str) -> None:
        self.acik = acik
        self.tema_adi = tema_adi
        self.ciz()

    def ciz(self) -> None:
        t = TEMALAR[self.tema_adi]
        self.configure(bg=t["topbar_bg"])
        self.delete("all")
        track_col = t["switch_track_on"] if self.acik else t["switch_track_off"]
        r = 10
        x1, y1, x2, y2 = 3, 2, 43, 22
        self.create_oval(x1, y1, x1 + 2 * r, y2, fill=track_col, outline="")
        self.create_oval(x2 - 2 * r, y1, x2, y2, fill=track_col, outline="")
        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=track_col, outline="")
        kx = 24 if self.acik else 5
        self.create_oval(kx, 4, kx + 16, 20, fill=t["switch_knob"], outline="")


class TakvimSeciciPopup(tk.Toplevel):

    def __init__(
        self,
        parent: tk.Misc,
        baslangic_tarih: Any,
        simule_bugun: date,
        on_select: Callable[[date], None],
        anchor_widget: Optional[tk.Widget] = None,
        tema_adi: str = "light",
    ) -> None:
        super().__init__(parent)
        self.withdraw()
        self.overrideredirect(True)
        self.on_select = on_select
        self.simule_bugun = simule_bugun
        self.tema_adi = tema_adi
        self.secili_tarih = self._tarih_cozumle(baslangic_tarih, simule_bugun)
        self.gorunen_yil = self.secili_tarih.year
        self.gorunen_ay = self.secili_tarih.month

        t = TEMALAR[self.tema_adi]
        self.configure(bg=t["panel_border"])

        self.kasa = tk.Frame(self, bg=t["panel"], padx=10, pady=10, highlightthickness=1, highlightbackground=t["panel_border"])
        self.kasa.pack(fill=tk.BOTH, expand=True)

        ust = tk.Frame(self.kasa, bg=t["panel"])
        ust.pack(fill=tk.X, pady=(0, 8))

        tk.Button(
            ust, text="<", width=3, font=("Segoe UI", 9, "bold"),
            bg=t["btn_neutral_bg"], fg=t["btn_neutral_fg"],
            activebackground=t["btn_neutral_hover"], activeforeground=t["btn_neutral_fg"],
            relief="flat", bd=0, cursor="hand2",
            command=lambda: self._ay_degistir(-1)
        ).pack(side=tk.LEFT)

        self.lbl_baslik = tk.Label(
            ust, text="", font=("Segoe UI", 10, "bold"),
            bg=t["panel"], fg=t["text_dark"]
        )
        self.lbl_baslik.pack(side=tk.LEFT, expand=True)

        tk.Button(
            ust, text=">", width=3, font=("Segoe UI", 9, "bold"),
            bg=t["btn_neutral_bg"], fg=t["btn_neutral_fg"],
            activebackground=t["btn_neutral_hover"], activeforeground=t["btn_neutral_fg"],
            relief="flat", bd=0, cursor="hand2",
            command=lambda: self._ay_degistir(1)
        ).pack(side=tk.RIGHT)

        self.izgara = tk.Frame(self.kasa, bg=t["panel"])
        self.izgara.pack()

        for col, gun_adi in enumerate(["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]):
            tk.Label(
                self.izgara, text=gun_adi, width=4, font=("Segoe UI", 8, "bold"),
                bg=t["panel"], fg=t["text_muted"], pady=3
            ).grid(row=0, column=col, padx=1, pady=1)

        alt = tk.Frame(self.kasa, bg=t["panel"])
        alt.pack(fill=tk.X, pady=(8, 0))
        tk.Button(
            alt,
            text=f"Simüle Bugün ({self.simule_bugun.strftime('%Y-%m-%d')})",
            font=("Segoe UI", 8, "bold"),
            bg=t["btn_accent_bg"], fg=t["btn_accent_fg"],
            activebackground=t["btn_accent_hover"], activeforeground=t["btn_accent_fg"],
            relief="flat", bd=0, padx=8, pady=4, cursor="hand2",
            command=lambda: self._gun_sec(self.simule_bugun)
        ).pack(fill=tk.X)

        self._gunleri_ciz()
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<FocusOut>", self._focus_disina_cikti)

        self.update_idletasks()
        self._konumlandir(anchor_widget)
        self.deiconify()
        self.lift()
        self.focus_force()

    def _tarih_cozumle(self, val: Any, varsayilan: date) -> date:
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val
        if isinstance(val, str):
            s = val.strip()
            if len(s) >= 10:
                try:
                    return datetime.strptime(s[:10], "%Y-%m-%d").date()
                except ValueError:
                    pass
        return varsayilan

    def _konumlandir(self, anchor_widget: Optional[tk.Widget]) -> None:
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        if anchor_widget is not None:
            x = anchor_widget.winfo_rootx()
            y = anchor_widget.winfo_rooty() + anchor_widget.winfo_height() + 4
        else:
            x = (sw - w) // 2
            y = (sh - h) // 2
        if x + w > sw - 8:
            x = max(8, sw - w - 8)
        if y + h > sh - 40:
            if anchor_widget is not None:
                y = max(8, anchor_widget.winfo_rooty() - h - 4)
            else:
                y = max(8, sh - h - 40)
        self.geometry(f"+{x}+{y}")

    def _focus_disina_cikti(self, event=None) -> None:
        self.after(20, self._focus_kontrol)

    def _focus_kontrol(self) -> None:
        try:
            if not self.winfo_exists():
                return
            odak = self.focus_get()
            if odak is None or odak.winfo_toplevel() != self:
                self.destroy()
        except Exception:
            pass

    def _ay_degistir(self, delta: int) -> None:
        toplam_ay = self.gorunen_yil * 12 + (self.gorunen_ay - 1) + delta
        self.gorunen_yil = toplam_ay // 12
        self.gorunen_ay = (toplam_ay % 12) + 1
        self._gunleri_ciz()

    def _gunleri_ciz(self) -> None:
        for w in list(self.izgara.winfo_children()):
            info = w.grid_info()
            if int(info.get("row", 0)) >= 1:
                w.destroy()

        t = TEMALAR[self.tema_adi]
        self.lbl_baslik.configure(text=f"{TURKCE_AYLAR[self.gorunen_ay]} {self.gorunen_yil}")

        cal = calendar.Calendar(firstweekday=0)
        haftalar = cal.monthdatescalendar(self.gorunen_yil, self.gorunen_ay)

        for r_idx, hafta in enumerate(haftalar, start=1):
            for c_idx, g in enumerate(hafta):
                secili_mi = g == self.secili_tarih
                bugun_mu = g == self.simule_bugun
                bu_ay_mi = g.month == self.gorunen_ay

                if secili_mi:
                    bg = t["primary"]
                    fg = t["primary_fg"]
                    font = ("Segoe UI", 9, "bold")
                elif bugun_mu:
                    bg = t["btn_accent_bg"]
                    fg = t["btn_accent_fg"]
                    font = ("Segoe UI", 9, "bold")
                else:
                    bg = t["panel"] if bu_ay_mi else t["surface_alt"]
                    fg = t["text_dark"] if bu_ay_mi else t["text_muted"]
                    font = ("Segoe UI", 9)

                btn = tk.Button(
                    self.izgara,
                    text=str(g.day),
                    width=3,
                    font=font,
                    bg=bg,
                    fg=fg,
                    activebackground=t["primary_hover"] if secili_mi else t["sidebar_hover"],
                    activeforeground=t["primary_fg"] if secili_mi else t["text_dark"],
                    relief="flat",
                    bd=0,
                    padx=2,
                    pady=3,
                    cursor="hand2",
                    command=lambda sec_g=g: self._gun_sec(sec_g),
                )
                btn.grid(row=r_idx, column=c_idx, padx=1, pady=1, sticky="nsew")

    def _gun_sec(self, g: date) -> None:
        self.on_select(g)
        self.destroy()


class KaynakTakvimiCanvas(tk.Frame):

    def __init__(self, parent: tk.Widget, on_select_callback, tema_adi: str = "light") -> None:
        self.tema_adi = tema_adi
        t = TEMALAR[self.tema_adi]
        super().__init__(parent, bg=t["bg"])
        self.on_select_callback = on_select_callback

        self.header_height = 40
        self.label_width = 180
        self.row_height = 64
        self.split_row_height = 80
        self.start_hour = 8
        self.end_hour = 22
        self.total_hours = self.end_hour - self.start_hour
        self.hour_width = 70
        self.timeline_width = self.total_hours * self.hour_width

        self.canvas = tk.Canvas(
            self,
            bg=t["canvas_bg"],
            highlightthickness=1,
            highlightbackground=t["panel_border"],
        )
        self.v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_hover)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.items_map: dict[int, dict[str, Any]] = {}
        self.selected_item_id: Optional[str] = None
        self.gun = datetime.now().date()
        self.tooltip = None
        self._son_cizim_args: Optional[tuple[Any, ...]] = None

    def tema_degistir(self, tema_adi: str) -> None:
        self.tema_adi = tema_adi
        t = TEMALAR[self.tema_adi]
        self.configure(bg=t["bg"])
        self.canvas.configure(bg=t["canvas_bg"], highlightbackground=t["panel_border"])
        if self._son_cizim_args is not None:
            self.ciz(*self._son_cizim_args)

    def _on_canvas_configure(self, event) -> None:
        avail_w = max(520, event.width - self.label_width - 24)
        if abs(avail_w - self.timeline_width) > 1:
            self.timeline_width = avail_w
            self.hour_width = self.timeline_width / self.total_hours
            if self._son_cizim_args is not None:
                self.ciz(*self._son_cizim_args)

    def _dakika_to_x(self, saat: int, dakika: int) -> float:
        total_mins = (saat - self.start_hour) * 60 + dakika
        return self.label_width + (total_mins / (self.total_hours * 60)) * self.timeline_width

    def _time_to_x(self, dt: datetime) -> float:
        return self._dakika_to_x(dt.hour, dt.minute)

    def ciz(
        self,
        gun: datetime.date,
        simule_saat: datetime,
        kaynaklar: list[Any],
        rezervasyonlar: list[Any],
        bakimlar: list[Any],
        kaynak_turleri: dict[str, Any],
        secili_rez_id: Optional[str] = None,
    ) -> None:
        self._son_cizim_args = (
            gun, simule_saat, kaynaklar, rezervasyonlar, bakimlar, kaynak_turleri, secili_rez_id
        )
        self.gun = gun
        self.selected_item_id = secili_rez_id
        self.canvas.delete("all")
        self.items_map.clear()

        t = TEMALAR[self.tema_adi]
        tur_listesi = list(kaynak_turleri.keys())
        tur_paleti = TUR_PALETLERI[self.tema_adi]
        total_width = self.label_width + self.timeline_width + 24

        row_heights: dict[str, int] = {}
        row_lanes: dict[str, tuple[int, dict[str, int]]] = {}
        for k in kaynaklar:
            k_tur_obj = kaynak_turleri.get(k.tur)
            h_dk = k_tur_obj.hazirlik_dk if k_tur_obj else 0
            serit_sayisi, serit_haritasi = self._hesapla_alt_seritler(k.id, gun, rezervasyonlar, h_dk)
            row_lanes[k.id] = (serit_sayisi, serit_haritasi)
            if serit_sayisi <= 1:
                row_heights[k.id] = self.row_height
            elif serit_sayisi == 2:
                row_heights[k.id] = self.split_row_height
            else:
                row_heights[k.id] = max(self.split_row_height, 32 * serit_sayisi + 10)

        total_height = self.header_height + sum(row_heights.values()) + 30
        self.canvas.configure(scrollregion=(0, 0, total_width, total_height))

        satir_konumlari: list[tuple[Any, float, int]] = []
        cur_y = self.header_height
        for idx, k in enumerate(kaynaklar):
            r_h = row_heights[k.id]
            bg_col = t["canvas_row_even"] if idx % 2 == 0 else t["canvas_row_odd"]
            self.canvas.create_rectangle(
                self.label_width, cur_y, total_width, cur_y + r_h,
                fill=bg_col, outline=t["panel_border"], width=1
            )

            tur_adi = k.tur
            if tur_adi in tur_listesi:
                tur_idx = tur_listesi.index(tur_adi)
            else:
                tur_idx = sum(ord(c) for c in tur_adi)
            tur_bg, tur_accent, tur_title, tur_sub = tur_paleti[tur_idx % len(tur_paleti)]

            self.canvas.create_rectangle(
                0, cur_y, self.label_width, cur_y + r_h,
                fill=tur_bg, outline=t["panel_border"], width=1
            )
            self.canvas.create_rectangle(
                0, cur_y, 5, cur_y + r_h,
                fill=tur_accent, outline=""
            )
            self.canvas.create_text(
                14, cur_y + r_h / 2 - 9,
                text=k.id, anchor="w",
                font=("Segoe UI", 10, "bold"), fill=tur_title
            )
            self.canvas.create_text(
                14, cur_y + r_h / 2 + 10,
                text=f"{k.ad} ({tur_adi})", anchor="w",
                font=("Segoe UI", 8), fill=tur_sub
            )

            satir_konumlari.append((k, cur_y, r_h))
            cur_y += r_h

        self._ciz_cetvel(total_height)

        for k, row_y, r_h in satir_konumlari:
            serit_sayisi, serit_haritasi = row_lanes[k.id]
            for bp in bakimlar:
                if bp.kaynak != k.id:
                    continue
                if bp.baslangic.date() > gun or bp.bitis.date() < gun:
                    continue
                self._ciz_bakim(bp, row_y, r_h)

            k_tur_obj = kaynak_turleri.get(k.tur)
            hazirlik_dk = k_tur_obj.hazirlik_dk if k_tur_obj else 0

            self._ciz_kaynak_rezervasyonlari(
                k.id, gun, row_y, r_h, serit_sayisi, serit_haritasi, hazirlik_dk, rezervasyonlar
            )

        if simule_saat.date() == gun:
            if 8 <= simule_saat.hour <= 22:
                sim_x = self._time_to_x(simule_saat)
                self.canvas.create_line(
                    sim_x, self.header_height, sim_x, cur_y,
                    fill=t["SIMULE_SAAT"], width=2, dash=(4, 2)
                )
                saat_str = simule_saat.strftime("%H:%M")
                self.canvas.create_rectangle(
                    sim_x - 22, 10, sim_x + 22, 28,
                    fill=t["SIMULE_SAAT"], outline=""
                )
                self.canvas.create_text(
                    sim_x, 19, text=saat_str,
                    fill="#ffffff", font=("Segoe UI", 8, "bold")
                )

    def _ciz_cetvel(self, total_height: float) -> None:
        t = TEMALAR[self.tema_adi]
        total_width = self.label_width + self.timeline_width + 24
        self.canvas.create_rectangle(
            0, 0, total_width, self.header_height,
            fill=t["canvas_header_bg"], outline=t["panel_border"], width=1
        )
        self.canvas.create_line(
            self.label_width, 0, self.label_width, total_height,
            fill=t["panel_border"], width=1
        )
        self.canvas.create_text(
            14, self.header_height / 2,
            text="KAYNAK / SAAT", anchor="w",
            font=("Segoe UI", 9, "bold"), fill=t["text_dark"]
        )

        for h in range(self.start_hour, self.end_hour + 1):
            x = self._dakika_to_x(h, 0)
            self.canvas.create_line(
                x, self.header_height, x, total_height,
                fill=t["canvas_grid_hour"], width=1
            )
            self.canvas.create_text(
                x, self.header_height / 2,
                text=f"{h:02d}:00", anchor="center",
                font=("Segoe UI", 9, "bold"), fill=t["text_dark"]
            )
            if h < self.end_hour:
                for m in (15, 30, 45):
                    sub_x = self._dakika_to_x(h, m)
                    self.canvas.create_line(
                        sub_x, self.header_height, sub_x, total_height,
                        fill=t["canvas_grid_quarter"], width=1, dash=(2, 4)
                    )

    def _hesapla_alt_seritler(
        self,
        kaynak_id: str,
        gun: datetime.date,
        rezervasyonlar: list[Any],
        hazirlik_dk: int = 0,
    ) -> tuple[int, dict[str, int]]:
        gunluk = [
            r for r in rezervasyonlar
            if r.kaynak == kaynak_id and r.baslangic.date() == gun
        ]
        if not gunluk:
            return 1, {}

        aktif = [r for r in gunluk if r.durum in ("ONAYLI", "KULLANIMDA", "TAMAMLANDI")]
        pasif = [r for r in gunluk if r.durum in ("IPTAL", "GELMEDI")]

        if not pasif:
            return 1, {r.id: 0 for r in gunluk}

        h_delta = timedelta(minutes=hazirlik_dk)
        aktif.sort(key=lambda r: (r.baslangic, _id_num(r.id)))
        pasif.sort(key=lambda r: (r.baslangic, _id_num(r.id)))

        serit_araliklari: list[list[tuple[datetime, datetime]]] = []
        serit_haritasi: dict[str, int] = {}

        for rez in aktif + pasif:
            bas = min(rez.baslangic, rez.bitis)
            bit_efektif = (
                rez.bitis + h_delta
                if rez.durum in ("ONAYLI", "KULLANIMDA", "TAMAMLANDI")
                else rez.bitis
            )

            atanan_serit = None
            for idx, araliklar in enumerate(serit_araliklari):
                if all(not (bas < a_bit and bit_efektif > a_bas) for a_bas, a_bit in araliklar):
                    atanan_serit = idx
                    araliklar.append((bas, bit_efektif))
                    break

            if atanan_serit is None:
                atanan_serit = len(serit_araliklari)
                serit_araliklari.append([(bas, bit_efektif)])

            serit_haritasi[rez.id] = atanan_serit

        return max(1, len(serit_araliklari)), serit_haritasi

    def _ciz_bakim(self, bp: Any, y: float, r_h: float) -> None:
        t = TEMALAR[self.tema_adi]
        x1 = max(self.label_width, self._time_to_x(bp.baslangic))
        x2 = min(self.label_width + self.timeline_width, self._time_to_x(bp.bitis))
        if x2 <= x1:
            return

        tag_id = self.canvas.create_rectangle(
            x1, y + 6, x2, y + r_h - 6,
            fill=t["BAKIM"], outline=t["BAKIM_BORDER"], width=1,
            stipple="gray25"
        )
        bakim_w = x2 - x1
        if bakim_w >= 120:
            bakim_yazi = f"BAKIM ({bp.baslangic.strftime('%H:%M')}-{bp.bitis.strftime('%H:%M')})"
        elif bakim_w >= 44:
            bakim_yazi = "BAKIM"
        else:
            bakim_yazi = ""

        info = {
            "tur": "BAKIM",
            "kaynak": bp.kaynak,
            "baslangic": format_zaman(bp.baslangic),
            "bitis": format_zaman(bp.bitis),
        }
        self.items_map[tag_id] = info

        if bakim_yazi:
            mid_x = (x1 + x2) / 2
            mid_y = y + r_h / 2
            text_id = self.canvas.create_text(
                mid_x, mid_y,
                text=bakim_yazi,
                fill=t["BAKIM_FG"], font=("Segoe UI", 8, "bold")
            )
            self.items_map[text_id] = info

    def _ciz_kaynak_rezervasyonlari(
        self,
        kaynak_id: str,
        gun: datetime.date,
        y: float,
        r_h: float,
        serit_sayisi: int,
        serit_haritasi: dict[str, int],
        hazirlik_dk: int,
        rezervasyonlar: list[Any],
    ) -> None:
        gunluk = [
            r for r in rezervasyonlar
            if r.kaynak == kaynak_id and r.baslangic.date() == gun
        ]

        for rez in gunluk:
            if serit_sayisi > 1:
                lane = serit_haritasi.get(rez.id, 0)
                pad = 4
                gap = 4
                lane_h = (r_h - 2 * pad - (serit_sayisi - 1) * gap) / serit_sayisi
                box_y1 = y + pad + lane * (lane_h + gap)
                box_y2 = box_y1 + lane_h
            else:
                box_y1 = y + 6
                box_y2 = y + r_h - 6

            bas_dt = min(rez.baslangic, rez.bitis)
            x1 = self._time_to_x(bas_dt)
            x2 = max(x1 + 4, self._time_to_x(rez.bitis))

            t = TEMALAR[self.tema_adi]
            fill_col = t.get(rez.durum, t["TAMAMLANDI"])
            border_col = t.get(f"{rez.durum}_BORDER", t["panel_border"])
            fg_col = t.get(f"{rez.durum}_FG", "#ffffff")
            dash = (3, 3) if rez.durum in ("IPTAL", "GELMEDI") else ()

            width = 3 if rez.id == self.selected_item_id else 1
            if rez.id == self.selected_item_id:
                border_col = t["SELECTION"]

            box_id = self.canvas.create_rectangle(
                x1, box_y1, x2, box_y2,
                fill=fill_col, outline=border_col, width=width, dash=dash
            )

            box_w = x2 - x1
            if box_w < 68:
                text_str = rez.id
            elif serit_sayisi > 1 or box_w < 130:
                text_str = f"{rez.id}:{rez.durum}"
            else:
                text_str = f"{rez.id} ({rez.kullanici}) {rez.ucret}KP"

            mid_x = (x1 + x2) / 2
            mid_y = (box_y1 + box_y2) / 2
            text_id = self.canvas.create_text(
                mid_x, mid_y,
                text=text_str, fill=fg_col,
                font=("Segoe UI", 8, "bold")
            )

            if hazirlik_dk > 0 and rez.durum in ("ONAYLI", "KULLANIMDA", "TAMAMLANDI"):
                hx1 = x2
                hx2 = min(
                    self.label_width + self.timeline_width,
                    self._time_to_x(rez.bitis + timedelta(minutes=hazirlik_dk))
                )
                if hx2 > hx1:
                    h_box = self.canvas.create_rectangle(
                        hx1, box_y1 + 2, hx2, box_y2 - 2,
                        fill=t["HAZIRLIK"], outline=t["HAZIRLIK_BORDER"],
                        width=1, dash=(1, 2)
                    )
                    h_info = {
                        "tur": "HAZIRLIK",
                        "kaynak": kaynak_id,
                        "dakika": hazirlik_dk,
                        "baslangic": format_zaman(rez.bitis),
                        "bitis": format_zaman(rez.bitis + timedelta(minutes=hazirlik_dk)),
                    }
                    self.items_map[h_box] = h_info
                    hw = hx2 - hx1
                    if hw >= 26:
                        h_yazi = f"h:{hazirlik_dk}"
                    elif hw >= 12:
                        h_yazi = "h"
                    else:
                        h_yazi = ""
                    if h_yazi:
                        h_text = self.canvas.create_text(
                            (hx1 + hx2) / 2, mid_y,
                            text=h_yazi, fill=t["HAZIRLIK_FG"],
                            font=("Segoe UI", 7)
                        )
                        self.items_map[h_text] = h_info

            info = {
                "tur": "REZERVASYON",
                "id": rez.id,
                "kullanici": rez.kullanici,
                "kaynak": rez.kaynak,
                "baslangic": format_zaman(rez.baslangic),
                "bitis": format_zaman(rez.bitis),
                "durum": rez.durum,
                "ucret": rez.ucret,
                "paket": rez.paket,
            }
            self.items_map[box_id] = info
            self.items_map[text_id] = info

    def _on_click(self, event) -> None:
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        clicked = self.canvas.find_overlapping(canvas_x - 1, canvas_y - 1, canvas_x + 1, canvas_y + 1)
        for c in reversed(clicked):
            if c in self.items_map:
                info = self.items_map[c]
                if info.get("tur") == "REZERVASYON":
                    self.selected_item_id = info["id"]
                    if self.on_select_callback:
                        self.on_select_callback(info)
                    return

    def _on_hover(self, event) -> None:
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        clicked = self.canvas.find_overlapping(canvas_x - 1, canvas_y - 1, canvas_x + 1, canvas_y + 1)
        info = None
        for c in reversed(clicked):
            if c in self.items_map:
                info = self.items_map[c]
                break

        if info:
            text = ""
            if info["tur"] == "REZERVASYON":
                paket_bilgi = f"\nPaket: {info['paket']}" if info.get("paket") else ""
                text = (
                    f"Rezervasyon: {info['id']}\n"
                    f"Durum: {info['durum']}\n"
                    f"Kullanıcı: {info['kullanici']}\n"
                    f"Kaynak: {info['kaynak']}\n"
                    f"Saat: {info['baslangic'][11:]} - {info['bitis'][11:]}\n"
                    f"Ücret: {info['ucret']} KP{paket_bilgi}"
                )
            elif info["tur"] == "BAKIM":
                text = (
                    f"BAKIM PENCERESİ\n"
                    f"Kaynak: {info['kaynak']}\n"
                    f"Aralık: {info['baslangic'][11:]} - {info['bitis'][11:]}"
                )
            elif info["tur"] == "HAZIRLIK":
                text = (
                    f"HAZIRLIK / SOĞUMA SÜRESİ\n"
                    f"Kaynak: {info['kaynak']}\n"
                    f"Süre: {info['dakika']} dk\n"
                    f"Aralık: {info['baslangic'][11:]} - {info['bitis'][11:]}"
                )
            self._goster_tooltip(event.x_root, event.y_root, text)
        else:
            self._gizle_tooltip()

    def _goster_tooltip(self, x: int, y: int, text: str) -> None:
        if self.tooltip:
            self.tooltip.destroy()
        t = TEMALAR[self.tema_adi]
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x + 12}+{y + 12}")
        lbl = tk.Label(
            self.tooltip, text=text, justify="left",
            background=t["tooltip_bg"], foreground=t["tooltip_fg"],
            font=("Segoe UI", 8), padx=8, pady=6, relief="flat",
            highlightthickness=1, highlightbackground=t["panel_border"]
        )
        lbl.pack()

    def _gizle_tooltip(self) -> None:
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class MasaustuUygulamasi(tk.Tk):

    def __init__(self) -> None:
        if os.name == "nt":
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass
        super().__init__()
        self.title("Kampüs Kaynak Rezervasyon Sistemi")
        self.geometry("1440x900")
        self.minsize(1100, 700)
        try:
            self.state("zoomed")
        except Exception:
            pass

        self.tema_adi: str = "light"
        self.sidebar_acik: bool = True
        self.aktif_sayfa: str = "takvim"
        self._aktif_takvim_popup: Optional[TakvimSeciciPopup] = None

        self._tema_baglantilari: list[tuple[tk.Widget, dict[str, str]]] = []
        self._durum_etiket_rolleri: dict[tk.Widget, str] = {}
        self._sidebar_ogeleri: dict[str, tuple[tk.Frame, tk.Frame, tk.Label]] = {}

        self.configure(bg=self._tema()["bg"])

        self.motor = RezervasyonMotoru()
        self.baslangic_dosyasi: str = "baslangic.json"
        self.olay_gunlugu: list[dict[str, Any]] = []

        self.goruntulenen_gun: date = datetime.now().date()
        self.secili_rezervasyon: Optional[dict[str, Any]] = None
        self.son_red_edilen_talep: Optional[dict[str, Any]] = None
        self.vars_ekle_sert: dict[str, tk.BooleanVar] = {}
        self.vars_ekle_roller: dict[str, tk.BooleanVar] = {}

        self._stil_yapilandir()
        self._arayuz_olustur()
        self.bind("<Control-b>", lambda e: self._sidebar_toggle())
        self.bind("<Control-B>", lambda e: self._sidebar_toggle())
        self._otomatik_baslat()

    def _tema(self) -> dict[str, str]:
        return TEMALAR[self.tema_adi]

    def _tek_widget_tema_uygula(self, w: tk.Widget, esleme: dict[str, str], t: dict[str, str]) -> None:
        w.configure(**{k: t[v] for k, v in esleme.items()})

    def _tema_bagla(self, widget: tk.Widget, **esleme: str) -> tk.Widget:
        self._tema_baglantilari.append((widget, esleme))
        self._tek_widget_tema_uygula(widget, esleme, self._tema())
        return widget

    def _etiket_durum_yaz(self, lbl: tk.Label, metin: str, rol: str = "text_muted") -> None:
        self._durum_etiket_rolleri[lbl] = rol
        lbl.configure(text=metin, fg=self._tema()[rol])

    def _tema_switch_tiklandi(self, koyu_acik: bool) -> None:
        self.tema_adi = "dark" if koyu_acik else "light"
        self._tema_uygula()

    def _tema_uygula(self) -> None:
        t = self._tema()
        self.configure(bg=t["bg"])
        self._stil_yapilandir()

        gecerli_baglantilar: list[tuple[tk.Widget, dict[str, str]]] = []
        for w, esleme in self._tema_baglantilari:
            try:
                if w.winfo_exists():
                    self._tek_widget_tema_uygula(w, esleme, t)
                    gecerli_baglantilar.append((w, esleme))
            except Exception:
                pass
        self._tema_baglantilari = gecerli_baglantilar

        silinecek_etiketler = []
        for lbl, rol in self._durum_etiket_rolleri.items():
            try:
                if lbl.winfo_exists():
                    lbl.configure(fg=t[rol])
                else:
                    silinecek_etiketler.append(lbl)
            except Exception:
                silinecek_etiketler.append(lbl)
        for lbl in silinecek_etiketler:
            del self._durum_etiket_rolleri[lbl]

        if hasattr(self, "takvim"):
            self.takvim.tema_degistir(self.tema_adi)
        if hasattr(self, "btn_sidebar_toggle"):
            self.btn_sidebar_toggle.tema_degistir(self.tema_adi, self.sidebar_acik)
        if hasattr(self, "tema_switch"):
            self.tema_switch.set_durum(self.tema_adi == "dark", self.tema_adi)
        self._sidebar_aktif_gorunumu_guncelle()
        self._eylem_butonlarini_guncelle()

        if self._aktif_takvim_popup is not None:
            try:
                if self._aktif_takvim_popup.winfo_exists():
                    self._aktif_takvim_popup.destroy()
            except Exception:
                pass
            self._aktif_takvim_popup = None

    def _stil_yapilandir(self) -> None:
        t = self._tema()
        self.option_add("*TCombobox*Listbox.background", t["input_bg"])
        self.option_add("*TCombobox*Listbox.foreground", t["text_dark"])
        self.option_add("*TCombobox*Listbox.selectBackground", t["combobox_sel_bg"])
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.option_add("*TCombobox*Listbox.font", ("Segoe UI", 9))

        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", font=("Segoe UI", 9), background=t["bg"], foreground=t["text_dark"])
        style.configure("TLabel", background=t["panel"], foreground=t["text_dark"])
        style.configure("TFrame", background=t["panel"])
        style.configure(
            "TCombobox",
            fieldbackground=t["input_bg"],
            background=t["btn_neutral_bg"],
            foreground=t["text_dark"],
            insertcolor=t["text_dark"],
            bordercolor=t["input_border"],
            lightcolor=t["input_bg"],
            darkcolor=t["input_bg"],
            arrowcolor=t["text_muted"],
            padding=5,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", t["input_bg"]), ("disabled", t["surface_alt"])],
            selectbackground=[("readonly", t["input_bg"])],
            selectforeground=[("readonly", t["text_dark"])],
            foreground=[("readonly", t["text_dark"]), ("disabled", t["text_muted"])],
            bordercolor=[("focus", t["primary"]), ("hover", t["text_muted"])],
            background=[("active", t["btn_neutral_hover"])],
        )
        style.configure(
            "TEntry",
            fieldbackground=t["input_bg"],
            foreground=t["text_dark"],
            insertcolor=t["text_dark"],
            bordercolor=t["input_border"],
            lightcolor=t["input_bg"],
            darkcolor=t["input_bg"],
            padding=5,
        )
        style.map("TEntry", bordercolor=[("focus", t["primary"])])
        style.configure(
            "Treeview",
            rowheight=26,
            background=t["input_bg"],
            fieldbackground=t["input_bg"],
            foreground=t["text_dark"],
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background=t["surface_alt"],
            foreground=t["text_dark"],
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            padding=[6, 5],
        )
        style.map("Treeview", background=[("selected", t["tree_sel_bg"])], foreground=[("selected", t["tree_sel_fg"])])
        style.configure(
            "TScrollbar",
            background=t["input_border"],
            troughcolor=t["bg"],
            bordercolor=t["bg"],
            arrowcolor=t["text_muted"],
            relief="flat",
        )
        style.map("TScrollbar", background=[("active", t["text_muted"])])

    def _arayuz_olustur(self) -> None:
        self._olustur_ust_panel()

        t = self._tema()
        self.govde_konteyner = self._tema_bagla(tk.Frame(self, bg=t["bg"]), bg="bg")
        self.govde_konteyner.pack(fill=tk.BOTH, expand=True)

        self._olustur_sidebar(self.govde_konteyner)

        self.icerik_alani = self._tema_bagla(
            tk.Frame(self.govde_konteyner, bg=t["bg"], padx=12, pady=10),
            bg="bg"
        )
        self.icerik_alani.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.sayfa_takvim_talep = self._tema_bagla(
            tk.PanedWindow(self.icerik_alani, orient=tk.HORIZONTAL, bg=t["bg"], sashwidth=6, bd=0, relief="flat"),
            bg="bg"
        )
        self.panel_takvim = self._tema_bagla(tk.Frame(self.sayfa_takvim_talep, bg=t["bg"]), bg="bg")
        self._olustur_sol_kolon(self.panel_takvim)

        self.panel_talep = self._tema_bagla(
            tk.Frame(self.sayfa_takvim_talep, bg=t["panel"], highlightthickness=1, highlightbackground=t["panel_border"]),
            bg="panel", highlightbackground="panel_border"
        )
        self._olustur_sekme_talep(self.panel_talep)

        self.panel_kullanici = self._tema_bagla(
            tk.Frame(self.icerik_alani, bg=t["panel"], highlightthickness=1, highlightbackground=t["panel_border"]),
            bg="panel", highlightbackground="panel_border"
        )
        self._olustur_sekme_kullanici(self.panel_kullanici)

        self.panel_gunluk = self._tema_bagla(
            tk.Frame(self.icerik_alani, bg=t["panel"], highlightthickness=1, highlightbackground=t["panel_border"]),
            bg="panel", highlightbackground="panel_border"
        )
        self._olustur_sekme_gunluk(self.panel_gunluk)

        self.panel_ekle = self._tema_bagla(tk.Frame(self.icerik_alani, bg=t["bg"]), bg="bg")
        self._olustur_sekme_ekle(self.panel_ekle)

        self._sayfa_sec("takvim")

    def _olustur_sidebar(self, parent: tk.Widget) -> None:
        t = self._tema()
        self.sidebar_cerceve = self._tema_bagla(
            tk.Frame(parent, bg=t["sidebar_bg"], width=215, highlightthickness=1, highlightbackground=t["panel_border"]),
            bg="sidebar_bg", highlightbackground="panel_border"
        )
        self.sidebar_cerceve.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_cerceve.pack_propagate(False)

        baslik = self._tema_bagla(
            tk.Label(self.sidebar_cerceve, text="MENÜ", font=("Segoe UI", 8, "bold"), bg=t["sidebar_bg"], fg=t["text_muted"], anchor="w", padx=16, pady=12),
            bg="sidebar_bg", fg="text_muted"
        )
        baslik.pack(fill=tk.X)

        menuler = [
            ("takvim", "Kaynak Takvimi"),
            ("talep", "Talep Formu"),
            ("kullanici", "Kullanıcı Paneli"),
            ("gunluk", "Olay Günlüğü"),
            ("ekle", "Üye / Kaynak Ekle"),
        ]
        for anahtar, metin in menuler:
            row = tk.Frame(self.sidebar_cerceve, bg=t["sidebar_bg"], cursor="hand2")
            row.pack(fill=tk.X, padx=8, pady=2)

            accent = tk.Frame(row, width=4, bg=t["sidebar_bg"])
            accent.pack(side=tk.LEFT, fill=tk.Y)

            lbl = tk.Label(
                row, text=metin, font=("Segoe UI", 9, "bold"),
                bg=t["sidebar_bg"], fg=t["text_dark"],
                anchor="w", padx=12, pady=10, cursor="hand2"
            )
            lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            self._sidebar_ogeleri[anahtar] = (row, accent, lbl)
            for w in (row, accent, lbl):
                w.bind("<Button-1>", lambda e, a=anahtar: self._sayfa_sec(a))
                w.bind("<Enter>", lambda e, a=anahtar: self._sidebar_hover(a, True))
                w.bind("<Leave>", lambda e, a=anahtar: self._sidebar_hover(a, False))

        alt_ipucu = self._tema_bagla(
            tk.Label(self.sidebar_cerceve, text="Kenar Çubuğu: Ctrl+B", font=("Segoe UI", 8), bg=t["sidebar_bg"], fg=t["text_muted"], anchor="w", padx=16, pady=12),
            bg="sidebar_bg", fg="text_muted"
        )
        alt_ipucu.pack(side=tk.BOTTOM, fill=tk.X)

    def _sidebar_hover(self, anahtar: str, icerde: bool) -> None:
        if anahtar == self.aktif_sayfa:
            return
        t = self._tema()
        row, accent, lbl = self._sidebar_ogeleri[anahtar]
        bg = t["sidebar_hover"] if icerde else t["sidebar_bg"]
        row.configure(bg=bg)
        accent.configure(bg=bg)
        lbl.configure(bg=bg)

    def _sidebar_aktif_gorunumu_guncelle(self) -> None:
        t = self._tema()
        for anahtar, (row, accent, lbl) in self._sidebar_ogeleri.items():
            if anahtar == self.aktif_sayfa:
                row.configure(bg=t["sidebar_active"])
                accent.configure(bg=t["primary"])
                lbl.configure(bg=t["sidebar_active"], fg=t["sidebar_active_fg"])
            else:
                row.configure(bg=t["sidebar_bg"])
                accent.configure(bg=t["sidebar_bg"])
                lbl.configure(bg=t["sidebar_bg"], fg=t["text_dark"])

    def _sidebar_toggle(self) -> None:
        if self.sidebar_acik:
            self.sidebar_cerceve.pack_forget()
            self.sidebar_acik = False
        else:
            self.sidebar_cerceve.pack(side=tk.LEFT, fill=tk.Y, before=self.icerik_alani)
            self.sidebar_acik = True
        self.btn_sidebar_toggle.tema_degistir(self.tema_adi, self.sidebar_acik)

    def _takvim_talep_cekmece_degistir(self) -> None:
        if self.aktif_sayfa == "talep":
            self._sayfa_sec("takvim")
        else:
            self._sayfa_sec("talep")

    def _sayfa_sec(self, sayfa_adi: str) -> None:
        self.aktif_sayfa = sayfa_adi

        for w in (self.sayfa_takvim_talep, self.panel_kullanici, self.panel_gunluk, self.panel_ekle):
            w.pack_forget()

        if sayfa_adi in ("takvim", "talep"):
            for p in list(self.sayfa_takvim_talep.panes()):
                self.sayfa_takvim_talep.forget(p)
            self.sayfa_takvim_talep.add(self.panel_takvim, minsize=560, stretch="always")
            if sayfa_adi == "talep":
                self.sayfa_takvim_talep.add(self.panel_talep, minsize=430, stretch="never")
            self.sayfa_takvim_talep.pack(fill=tk.BOTH, expand=True)

            if hasattr(self, "btn_takvim_talep_cekmece"):
                if sayfa_adi == "talep":
                    self.btn_takvim_talep_cekmece.configure(text="Tam Ekran Takvim")
                else:
                    self.btn_takvim_talep_cekmece.configure(text="Yeni Talep Oluştur")
        elif sayfa_adi == "kullanici":
            self.panel_kullanici.pack(fill=tk.BOTH, expand=True)
        elif sayfa_adi == "gunluk":
            self.panel_gunluk.pack(fill=tk.BOTH, expand=True)
        elif sayfa_adi == "ekle":
            self.panel_ekle.pack(fill=tk.BOTH, expand=True)

        self._sidebar_aktif_gorunumu_guncelle()

    def _takvim_popup_ac(self, mevcut_val: Any, anchor: Optional[tk.Widget], on_sec: Callable[[date], None]) -> None:
        if self._aktif_takvim_popup is not None:
            try:
                if self._aktif_takvim_popup.winfo_exists():
                    self._aktif_takvim_popup.destroy()
            except Exception:
                pass
            self._aktif_takvim_popup = None

        bugun = self.motor.saat.date() if self.motor.saat != datetime.min else self.goruntulenen_gun
        self._aktif_takvim_popup = TakvimSeciciPopup(
            self,
            baslangic_tarih=mevcut_val,
            simule_bugun=bugun,
            on_select=on_sec,
            anchor_widget=anchor,
            tema_adi=self.tema_adi,
        )

    def _takvim_ust_tarih_ac(self) -> None:
        self._takvim_popup_ac(self.goruntulenen_gun, self.lbl_takvim_gun, self._takvim_tarih_secildi)

    def _takvim_tarih_secildi(self, g: date) -> None:
        self.goruntulenen_gun = g
        if hasattr(self, "var_talep_tarih"):
            self.var_talep_tarih.set(self.goruntulenen_gun.strftime("%Y-%m-%d"))
        self._tum_arayuzu_guncelle()

    def _olustur_ust_panel(self) -> None:
        t = self._tema()
        ust_konteyner = self._tema_bagla(
            tk.Frame(self, bg=t["topbar_bg"], highlightthickness=1, highlightbackground=t["panel_border"]),
            bg="topbar_bg", highlightbackground="panel_border"
        )
        ust_konteyner.pack(fill=tk.X, side=tk.TOP)

        ust_cerceve = self._tema_bagla(
            tk.Frame(ust_konteyner, bg=t["topbar_bg"], padx=14, pady=8),
            bg="topbar_bg"
        )
        ust_cerceve.pack(fill=tk.X)

        sol_box = self._tema_bagla(tk.Frame(ust_cerceve, bg=t["topbar_bg"]), bg="topbar_bg")
        sol_box.pack(side=tk.LEFT)

        self.btn_sidebar_toggle = SidebarToggleButonu(sol_box, on_toggle=self._sidebar_toggle, tema_adi=self.tema_adi)
        self.btn_sidebar_toggle.pack(side=tk.LEFT, padx=(0, 12))

        self.lbl_dosya_durumu = self._tema_bagla(
            tk.Label(sol_box, text="Dosya: baslangic.json", font=("Segoe UI", 8, "bold"), bg=t["topbar_bg"], fg=t["topbar_muted"]),
            bg="topbar_bg", fg="topbar_muted"
        )
        self.lbl_dosya_durumu.pack(side=tk.LEFT)

        self._tema_bagla(
            tk.Button(
                sol_box, text="Dosya Seç", font=("Segoe UI", 8, "bold"),
                bg=t["btn_neutral_bg"], fg=t["btn_neutral_fg"],
                activebackground=t["btn_neutral_hover"], activeforeground=t["btn_neutral_fg"],
                relief="flat", padx=8, pady=3, cursor="hand2",
                command=self._dosya_sec
            ),
            bg="btn_neutral_bg", fg="btn_neutral_fg", activebackground="btn_neutral_hover", activeforeground="btn_neutral_fg"
        ).pack(side=tk.LEFT, padx=(8, 4))

        self._tema_bagla(
            tk.Button(
                sol_box, text="Sıfırla", font=("Segoe UI", 8),
                bg=t["btn_neutral_bg"], fg=t["btn_neutral_fg"],
                activebackground=t["btn_neutral_hover"], activeforeground=t["btn_neutral_fg"],
                relief="flat", padx=8, pady=3, cursor="hand2",
                command=self._dosyayi_yeniden_yukle
            ),
            bg="btn_neutral_bg", fg="btn_neutral_fg", activebackground="btn_neutral_hover", activeforeground="btn_neutral_fg"
        ).pack(side=tk.LEFT)

        orta_box = self._tema_bagla(
            tk.Frame(
                ust_cerceve, bg=t["clock_bg"], padx=14, pady=4,
                relief="flat", bd=0, highlightthickness=1, highlightbackground=t["panel_border"]
            ),
            bg="clock_bg", highlightbackground="panel_border"
        )
        orta_box.pack(side=tk.LEFT, expand=True, padx=12)

        self._tema_bagla(
            tk.Label(orta_box, text="SİMÜLASYON SAATİ", font=("Segoe UI", 7, "bold"), fg=t["clock_label"], bg=t["clock_bg"]),
            fg="clock_label", bg="clock_bg"
        ).pack()
        self.lbl_simule_saat = self._tema_bagla(
            tk.Label(orta_box, text="2027-03-08 08:00 (Pazartesi)", font=("Segoe UI", 11, "bold"), fg=t["clock_fg"], bg=t["clock_bg"]),
            fg="clock_fg", bg="clock_bg"
        )
        self.lbl_simule_saat.pack()

        sag_box = self._tema_bagla(tk.Frame(ust_cerceve, bg=t["topbar_bg"]), bg="topbar_bg")
        sag_box.pack(side=tk.RIGHT)

        self._tema_bagla(
            tk.Label(sag_box, text="Zaman:", font=("Segoe UI", 8, "bold"), fg=t["topbar_muted"], bg=t["topbar_bg"]),
            fg="topbar_muted", bg="topbar_bg"
        ).pack(side=tk.LEFT, padx=(0, 4))

        for metin, delta_dk in [("+15dk", 15), ("+30dk", 30), ("+1sa", 60), ("+2sa", 120), ("+1gün", 1440)]:
            self._tema_bagla(
                tk.Button(
                    sag_box, text=metin, font=("Segoe UI", 8, "bold"),
                    bg=t["btn_neutral_bg"], fg=t["btn_neutral_fg"],
                    activebackground=t["btn_neutral_hover"], activeforeground=t["btn_neutral_fg"],
                    relief="flat", padx=6, pady=3, cursor="hand2",
                    command=lambda d=delta_dk: self._hizli_saat_ilerlet(d)
                ),
                bg="btn_neutral_bg", fg="btn_neutral_fg", activebackground="btn_neutral_hover", activeforeground="btn_neutral_fg"
            ).pack(side=tk.LEFT, padx=2)

        self._tema_bagla(
            tk.Label(sag_box, text="Hedef:", font=("Segoe UI", 8), fg=t["topbar_muted"], bg=t["topbar_bg"]),
            fg="topbar_muted", bg="topbar_bg"
        ).pack(side=tk.LEFT, padx=(8, 2))

        self.cb_hedef_saat = ttk.Combobox(sag_box, width=16)
        self.cb_hedef_saat.pack(side=tk.LEFT, padx=2)

        self._tema_bagla(
            tk.Button(
                sag_box, text="Saati İlerlet", font=("Segoe UI", 8, "bold"),
                bg=t["primary"], fg=t["primary_fg"],
                activebackground=t["primary_hover"], activeforeground=t["primary_fg"],
                relief="flat", padx=8, pady=3, cursor="hand2",
                command=self._ozel_saat_ilerlet_uygula
            ),
            bg="primary", fg="primary_fg", activebackground="primary_hover", activeforeground="primary_fg"
        ).pack(side=tk.LEFT, padx=(4, 12))

        self._tema_bagla(
            tk.Label(sag_box, text="Koyu Mod", font=("Segoe UI", 8, "bold"), fg=t["topbar_fg"], bg=t["topbar_bg"]),
            fg="topbar_fg", bg="topbar_bg"
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.tema_switch = TemaSwitch(sag_box, acik=False, on_toggle=self._tema_switch_tiklandi, tema_adi=self.tema_adi)
        self.tema_switch.pack(side=tk.LEFT)

        self.lbl_saat_olay_bildirimi = self._tema_bagla(
            tk.Label(
                ust_konteyner,
                text="Simülasyon saati hazır.",
                font=("Segoe UI", 8),
                fg=t["notice_fg"],
                bg=t["notice_bg"],
                anchor="w",
                padx=16,
                pady=4,
                justify="left",
            ),
            bg="notice_bg"
        )
        self._durum_etiket_rolleri[self.lbl_saat_olay_bildirimi] = "notice_fg"
        self.lbl_saat_olay_bildirimi.pack(fill=tk.X)

    def _olustur_sol_kolon(self, parent: tk.Widget) -> None:
        t = self._tema()
        ust_bar = self._tema_bagla(
            tk.Frame(parent, bg=t["panel"], padx=10, pady=8, highlightthickness=1, highlightbackground=t["panel_border"]),
            bg="panel", highlightbackground="panel_border"
        )
        ust_bar.pack(fill=tk.X, side=tk.TOP, pady=(0, 6))

        self._tema_bagla(
            tk.Label(ust_bar, text="Kaynak Takvimi", font=("Segoe UI", 10, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).pack(side=tk.LEFT)

        btn_box = self._tema_bagla(tk.Frame(ust_bar, bg=t["panel"]), bg="panel")
        btn_box.pack(side=tk.RIGHT)

        self._tema_bagla(
            tk.Button(
                btn_box, text="<", font=("Segoe UI", 8, "bold"),
                bg=t["btn_neutral_bg"], fg=t["btn_neutral_fg"],
                activebackground=t["btn_neutral_hover"], activeforeground=t["btn_neutral_fg"],
                relief="flat", padx=7, pady=3, cursor="hand2",
                command=lambda: self._gun_degistir(-1)
            ),
            bg="btn_neutral_bg", fg="btn_neutral_fg", activebackground="btn_neutral_hover", activeforeground="btn_neutral_fg"
        ).pack(side=tk.LEFT, padx=2)

        self.lbl_takvim_gun = self._tema_bagla(
            tk.Button(
                btn_box, text="2027-03-08 Pazartesi", font=("Segoe UI", 9, "bold"),
                bg=t["surface_alt"], fg=t["text_dark"],
                activebackground=t["btn_accent_bg"], activeforeground=t["btn_accent_fg"],
                relief="flat", padx=8, pady=3, cursor="hand2",
                command=self._takvim_ust_tarih_ac
            ),
            bg="surface_alt", fg="text_dark", activebackground="btn_accent_bg", activeforeground="btn_accent_fg"
        )
        self.lbl_takvim_gun.pack(side=tk.LEFT, padx=2)

        self._tema_bagla(
            tk.Button(
                btn_box, text=">", font=("Segoe UI", 8, "bold"),
                bg=t["btn_neutral_bg"], fg=t["btn_neutral_fg"],
                activebackground=t["btn_neutral_hover"], activeforeground=t["btn_neutral_fg"],
                relief="flat", padx=7, pady=3, cursor="hand2",
                command=lambda: self._gun_degistir(1)
            ),
            bg="btn_neutral_bg", fg="btn_neutral_fg", activebackground="btn_neutral_hover", activeforeground="btn_neutral_fg"
        ).pack(side=tk.LEFT, padx=2)

        self._tema_bagla(
            tk.Button(
                btn_box, text="Bugün", font=("Segoe UI", 8, "bold"),
                bg=t["btn_accent_bg"], fg=t["btn_accent_fg"],
                activebackground=t["btn_accent_hover"], activeforeground=t["btn_accent_fg"],
                relief="flat", padx=7, pady=3, cursor="hand2",
                command=self._takvimi_simule_gune_getir
            ),
            bg="btn_accent_bg", fg="btn_accent_fg", activebackground="btn_accent_hover", activeforeground="btn_accent_fg"
        ).pack(side=tk.LEFT, padx=(4, 4))

        self.btn_takvim_talep_cekmece = self._tema_bagla(
            tk.Button(
                btn_box, text="Yeni Talep Oluştur", font=("Segoe UI", 8, "bold"),
                bg=t["primary"], fg=t["primary_fg"],
                activebackground=t["primary_hover"], activeforeground=t["primary_fg"],
                relief="flat", padx=8, pady=3, cursor="hand2",
                command=self._takvim_talep_cekmece_degistir
            ),
            bg="primary", fg="primary_fg", activebackground="primary_hover", activeforeground="primary_fg"
        )
        self.btn_takvim_talep_cekmece.pack(side=tk.LEFT, padx=(2, 0))

        legend_bar = self._tema_bagla(
            tk.Frame(parent, bg=t["panel"], padx=8, pady=5, highlightthickness=1, highlightbackground=t["panel_border"]),
            bg="panel", highlightbackground="panel_border"
        )
        legend_bar.pack(fill=tk.X, side=tk.TOP, pady=(0, 6))

        items = [
            ("ONAYLI", "ONAYLI"),
            ("KULLANIMDA", "KULLANIMDA"),
            ("TAMAMLANDI", "TAMAMLANDI"),
            ("GELMEDI", "GELMEDI"),
            ("IPTAL", "IPTAL"),
            ("BAKIM", "BAKIM"),
            ("HAZIRLIK", "HAZIRLIK"),
        ]
        for etiket, anahtar in items:
            swatch = self._tema_bagla(
                tk.Label(
                    legend_bar, text="  ", bg=t[anahtar],
                    relief="flat", bd=0, highlightthickness=1, highlightbackground=t[f"{anahtar}_BORDER"]
                ),
                bg=anahtar, highlightbackground=f"{anahtar}_BORDER"
            )
            swatch.pack(side=tk.LEFT, padx=(2, 2))
            self._tema_bagla(
                tk.Label(legend_bar, text=etiket, font=("Segoe UI", 7, "bold"), bg=t["panel"], fg=t["text_muted"]),
                bg="panel", fg="text_muted"
            ).pack(side=tk.LEFT, padx=(0, 5))

        sorgu_box = self._tema_bagla(tk.Frame(legend_bar, bg=t["panel"]), bg="panel")
        sorgu_box.pack(side=tk.RIGHT)
        self._tema_bagla(
            tk.Label(sorgu_box, text="Kaynak:", font=("Segoe UI", 8, "bold"), bg=t["panel"], fg=t["text_muted"]),
            bg="panel", fg="text_muted"
        ).pack(side=tk.LEFT, padx=(0, 4))
        self.cb_takvim_kaynak = ttk.Combobox(sorgu_box, width=7, state="readonly")
        self.cb_takvim_kaynak.pack(side=tk.LEFT, padx=2)
        self._tema_bagla(
            tk.Button(
                sorgu_box, text="Kaynak Sorgula", font=("Segoe UI", 8, "bold"),
                bg=t["btn_accent_bg"], fg=t["btn_accent_fg"],
                activebackground=t["btn_accent_hover"], activeforeground=t["btn_accent_fg"],
                relief="flat", padx=6, pady=2, cursor="hand2",
                command=self._kaynak_sorgu_gonder
            ),
            bg="btn_accent_bg", fg="btn_accent_fg", activebackground="btn_accent_hover", activeforeground="btn_accent_fg"
        ).pack(side=tk.LEFT, padx=(4, 0))

        self.takvim = KaynakTakvimiCanvas(parent, on_select_callback=self._rezervasyon_secildi, tema_adi=self.tema_adi)
        self.takvim.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.eylem_konteyner = self._tema_bagla(
            tk.Frame(parent, bg=t["panel"], padx=12, pady=8, highlightthickness=1, highlightbackground=t["panel_border"]),
            bg="panel", highlightbackground="panel_border"
        )
        self.eylem_konteyner.pack(fill=tk.X, side=tk.BOTTOM)

        self.eylem_bari = self._tema_bagla(tk.Frame(self.eylem_konteyner, bg=t["panel"]), bg="panel")
        self.eylem_bari.pack(fill=tk.X)

        self.lbl_secili_rez = self._tema_bagla(
            tk.Label(
                self.eylem_bari, text="Seçili Rezervasyon: (Takvimden veya tablodan bir rezervasyona tıklayın)",
                font=("Segoe UI", 9, "bold"), bg=t["panel"], fg=t["text_muted"]
            ),
            bg="panel"
        )
        self._durum_etiket_rolleri[self.lbl_secili_rez] = "text_muted"
        self.lbl_secili_rez.pack(side=tk.LEFT)

        self.btn_giris = tk.Button(
            self.eylem_bari, text="Giriş Yap", font=("Segoe UI", 8, "bold"),
            bg=t["btn_disabled_bg"], fg="#ffffff", disabledforeground=t["btn_disabled_fg"],
            activebackground=t["success_hover"], activeforeground="#ffffff",
            relief="flat", padx=10, pady=4, cursor="hand2", state="disabled",
            command=self._eylem_giris
        )
        self.btn_giris.pack(side=tk.RIGHT, padx=4)

        self.btn_cikis = tk.Button(
            self.eylem_bari, text="Çıkış Yap", font=("Segoe UI", 8, "bold"),
            bg=t["btn_disabled_bg"], fg="#ffffff", disabledforeground=t["btn_disabled_fg"],
            activebackground=t["info_hover"], activeforeground="#ffffff",
            relief="flat", padx=10, pady=4, cursor="hand2", state="disabled",
            command=self._eylem_cikis
        )
        self.btn_cikis.pack(side=tk.RIGHT, padx=4)

        self.btn_iptal = tk.Button(
            self.eylem_bari, text="İptal Et", font=("Segoe UI", 8, "bold"),
            bg=t["btn_disabled_bg"], fg="#ffffff", disabledforeground=t["btn_disabled_fg"],
            activebackground=t["error_hover"], activeforeground="#ffffff",
            relief="flat", padx=10, pady=4, cursor="hand2", state="disabled",
            command=self._eylem_iptal
        )
        self.btn_iptal.pack(side=tk.RIGHT, padx=4)

        self.lbl_eylem_sonuc = self._tema_bagla(
            tk.Label(
                self.eylem_konteyner,
                text="",
                font=("Segoe UI", 8, "bold"),
                bg=t["panel"],
                fg=t["text_muted"],
                anchor="w",
                justify="left",
            ),
            bg="panel"
        )
        self._durum_etiket_rolleri[self.lbl_eylem_sonuc] = "text_muted"
        self.lbl_eylem_sonuc.pack(fill=tk.X, pady=(4, 0))

    def _olustur_sekme_talep(self, parent: tk.Widget) -> None:
        t = self._tema()
        canvas = self._tema_bagla(tk.Canvas(parent, bg=t["panel"], highlightthickness=0), bg="panel")
        scroll = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        icerik = self._tema_bagla(tk.Frame(canvas, bg=t["panel"], padx=14, pady=12), bg="panel")

        icerik.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win_id = canvas.create_window((0, 0), window=icerik, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win_id, width=e.width))
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._tema_bagla(
            tk.Label(icerik, text="Talep Formu", font=("Segoe UI", 11, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).pack(anchor="w", pady=(0, 8))

        self.var_talep_modu = tk.StringVar(value="tekil")
        mod_bar = self._tema_bagla(
            tk.Frame(
                icerik, bg=t["surface_alt"], padx=6, pady=4,
                relief="flat", bd=0, highlightthickness=1, highlightbackground=t["panel_border"]
            ),
            bg="surface_alt", highlightbackground="panel_border"
        )
        mod_bar.pack(fill=tk.X, pady=(0, 10))

        self._tema_bagla(
            tk.Radiobutton(
                mod_bar, text="Tekil Rezervasyon", variable=self.var_talep_modu, value="tekil",
                bg=t["surface_alt"], fg=t["text_dark"], selectcolor=t["input_bg"],
                activebackground=t["surface_alt"], activeforeground=t["text_dark"],
                highlightthickness=0, bd=0, font=("Segoe UI", 9, "bold"),
                command=self._talep_modu_degisti
            ),
            bg="surface_alt", fg="text_dark", selectcolor="input_bg", activebackground="surface_alt", activeforeground="text_dark"
        ).pack(side=tk.LEFT, padx=10)
        self._tema_bagla(
            tk.Radiobutton(
                mod_bar, text="Paket Rezervasyon (2-4 Kalem)", variable=self.var_talep_modu, value="paket",
                bg=t["surface_alt"], fg=t["text_dark"], selectcolor=t["input_bg"],
                activebackground=t["surface_alt"], activeforeground=t["text_dark"],
                highlightthickness=0, bd=0, font=("Segoe UI", 9, "bold"),
                command=self._talep_modu_degisti
            ),
            bg="surface_alt", fg="text_dark", selectcolor="input_bg", activebackground="surface_alt", activeforeground="text_dark"
        ).pack(side=tk.LEFT, padx=10)

        kull_box = self._tema_bagla(tk.Frame(icerik, bg=t["panel"]), bg="panel")
        kull_box.pack(fill=tk.X, pady=(0, 8))
        self._tema_bagla(
            tk.Label(kull_box, text="Kullanıcı:", font=("Segoe UI", 9, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).pack(anchor="w")
        self.cb_talep_kullanici = ttk.Combobox(kull_box, state="readonly")
        self.cb_talep_kullanici.pack(fill=tk.X, pady=(2, 0))

        self.frm_tekil = self._tema_bagla(tk.Frame(icerik, bg=t["panel"]), bg="panel")
        self.frm_tekil.pack(fill=tk.X)

        self._tema_bagla(
            tk.Label(self.frm_tekil, text="Kaynak:", font=("Segoe UI", 9, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).pack(anchor="w", pady=(4, 0))
        self.cb_talep_kaynak = ttk.Combobox(self.frm_tekil, state="readonly")
        self.cb_talep_kaynak.pack(fill=tk.X, pady=(2, 6))

        self._tema_bagla(
            tk.Label(self.frm_tekil, text="Tarih (YYYY-AA-GG):", font=("Segoe UI", 9, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).pack(anchor="w")

        tarih_satir = self._tema_bagla(tk.Frame(self.frm_tekil, bg=t["panel"]), bg="panel")
        tarih_satir.pack(fill=tk.X, pady=(2, 6))
        self.var_talep_tarih = tk.StringVar()
        self.var_talep_tarih.trace_add("write", lambda *_: self._canli_json_guncelle())
        self.ent_talep_tarih = ttk.Entry(tarih_satir, textvariable=self.var_talep_tarih)
        self.ent_talep_tarih.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn_talep_tarih_sec = self._tema_bagla(
            tk.Button(
                tarih_satir, text="Takvim", font=("Segoe UI", 8, "bold"),
                bg=t["btn_accent_bg"], fg=t["btn_accent_fg"],
                activebackground=t["btn_accent_hover"], activeforeground=t["btn_accent_fg"],
                relief="flat", padx=10, pady=4, cursor="hand2",
                command=lambda: self._takvim_popup_ac(
                    self.var_talep_tarih.get(),
                    self.ent_talep_tarih,
                    lambda g: self.var_talep_tarih.set(g.strftime("%Y-%m-%d")),
                )
            ),
            bg="btn_accent_bg", fg="btn_accent_fg", activebackground="btn_accent_hover", activeforeground="btn_accent_fg"
        )
        self.btn_talep_tarih_sec.pack(side=tk.LEFT, padx=(6, 0))

        zaman_grid = self._tema_bagla(tk.Frame(self.frm_tekil, bg=t["panel"]), bg="panel")
        zaman_grid.pack(fill=tk.X, pady=(0, 8))

        self._tema_bagla(
            tk.Label(zaman_grid, text="Başlangıç (SS:DD):", font=("Segoe UI", 8, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).grid(row=0, column=0, sticky="w")
        self._tema_bagla(
            tk.Label(zaman_grid, text="Bitiş (SS:DD):", font=("Segoe UI", 8, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        saatler = [f"{h:02d}:{m:02d}" for h in range(8, 23) for m in (0, 15, 30, 45) if not (h == 22 and m > 0)]
        self.cb_talep_bas = ttk.Combobox(zaman_grid, values=saatler, width=12)
        self.cb_talep_bas.set("10:00")
        self.cb_talep_bas.grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.cb_talep_bit = ttk.Combobox(zaman_grid, values=saatler, width=12)
        self.cb_talep_bit.set("12:00")
        self.cb_talep_bit.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(2, 0))

        btn_bar = self._tema_bagla(tk.Frame(self.frm_tekil, bg=t["panel"]), bg="panel")
        btn_bar.pack(fill=tk.X, pady=(4, 10))

        self._tema_bagla(
            tk.Button(
                btn_bar, text="Fiyat Hesapla (fiyat)", font=("Segoe UI", 8, "bold"),
                bg=t["btn_neutral_bg"], fg=t["btn_neutral_fg"],
                activebackground=t["btn_neutral_hover"], activeforeground=t["btn_neutral_fg"],
                relief="flat", padx=4, pady=5, cursor="hand2",
                command=self._fiyat_hesapla
            ),
            bg="btn_neutral_bg", fg="btn_neutral_fg", activebackground="btn_neutral_hover", activeforeground="btn_neutral_fg"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self._tema_bagla(
            tk.Button(
                btn_bar, text="Bekleme Aç (bekleme)", font=("Segoe UI", 8, "bold"),
                bg=t["btn_warn_bg"], fg=t["btn_warn_fg"],
                activebackground=t["btn_warn_hover"], activeforeground=t["btn_warn_fg"],
                relief="flat", padx=4, pady=5, cursor="hand2",
                command=self._talep_bekleme_gonder
            ),
            bg="btn_warn_bg", fg="btn_warn_fg", activebackground="btn_warn_hover", activeforeground="btn_warn_fg"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self._tema_bagla(
            tk.Button(
                btn_bar, text="Rezervasyon Yap", font=("Segoe UI", 8, "bold"),
                bg=t["primary"], fg=t["primary_fg"],
                activebackground=t["primary_hover"], activeforeground=t["primary_fg"],
                relief="flat", padx=4, pady=5, cursor="hand2",
                command=self._rezervasyon_gonder
            ),
            bg="primary", fg="primary_fg", activebackground="primary_hover", activeforeground="primary_fg"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        self.frm_paket = self._tema_bagla(tk.Frame(icerik, bg=t["panel"]), bg="panel")
        self.paket_kalem_satirlari: list[dict[str, Any]] = []

        self._tema_bagla(
            tk.Label(self.frm_paket, text="Paket Kalemleri:", font=("Segoe UI", 9, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).pack(anchor="w")
        self.frm_kalem_listesi = self._tema_bagla(tk.Frame(self.frm_paket, bg=t["panel"]), bg="panel")
        self.frm_kalem_listesi.pack(fill=tk.X, pady=(4, 6))

        p_btn_bar = self._tema_bagla(tk.Frame(self.frm_paket, bg=t["panel"]), bg="panel")
        p_btn_bar.pack(fill=tk.X, pady=(2, 6))
        self._tema_bagla(
            tk.Button(
                p_btn_bar, text="+ Kalem Ekle", font=("Segoe UI", 8, "bold"),
                bg=t["btn_neutral_bg"], fg=t["btn_neutral_fg"],
                activebackground=t["btn_neutral_hover"], activeforeground=t["btn_neutral_fg"],
                relief="flat", padx=8, pady=3, cursor="hand2",
                command=self._paket_kalem_ekle
            ),
            bg="btn_neutral_bg", fg="btn_neutral_fg", activebackground="btn_neutral_hover", activeforeground="btn_neutral_fg"
        ).pack(side=tk.LEFT)
        self._tema_bagla(
            tk.Button(
                p_btn_bar, text="- Kalem Çıkar", font=("Segoe UI", 8),
                bg=t["btn_neutral_bg"], fg=t["btn_neutral_fg"],
                activebackground=t["btn_neutral_hover"], activeforeground=t["btn_neutral_fg"],
                relief="flat", padx=8, pady=3, cursor="hand2",
                command=self._paket_kalem_cikar
            ),
            bg="btn_neutral_bg", fg="btn_neutral_fg", activebackground="btn_neutral_hover", activeforeground="btn_neutral_fg"
        ).pack(side=tk.LEFT, padx=6)

        self._tema_bagla(
            tk.Button(
                self.frm_paket, text="Paket Fiyatını Hesapla", font=("Segoe UI", 8, "bold"),
                bg=t["btn_neutral_bg"], fg=t["btn_neutral_fg"],
                activebackground=t["btn_neutral_hover"], activeforeground=t["btn_neutral_fg"],
                relief="flat", pady=5, cursor="hand2",
                command=self._paket_fiyat_hesapla
            ),
            bg="btn_neutral_bg", fg="btn_neutral_fg", activebackground="btn_neutral_hover", activeforeground="btn_neutral_fg"
        ).pack(fill=tk.X, pady=(2, 4))

        self._tema_bagla(
            tk.Button(
                self.frm_paket, text="Paket Talebi Gönder", font=("Segoe UI", 9, "bold"),
                bg=t["primary"], fg=t["primary_fg"],
                activebackground=t["primary_hover"], activeforeground=t["primary_fg"],
                relief="flat", pady=5, cursor="hand2",
                command=self._paket_gonder
            ),
            bg="primary", fg="primary_fg", activebackground="primary_hover", activeforeground="primary_fg"
        ).pack(fill=tk.X, pady=(2, 10))

        self._paket_kalem_ekle()
        self._paket_kalem_ekle()

        self.frm_json_onizleme = self._tema_bagla(
            tk.Frame(
                icerik, bg=t["surface_alt"], padx=8, pady=8,
                highlightthickness=1, highlightbackground=t["panel_border"]
            ),
            bg="surface_alt", highlightbackground="panel_border"
        )
        self.frm_json_onizleme.pack(fill=tk.X, pady=(4, 6))
        self._tema_bagla(
            tk.Label(self.frm_json_onizleme, text="Canlı Komut JSON Önizlemesi", font=("Segoe UI", 8, "bold"), bg=t["surface_alt"], fg=t["text_dark"]),
            bg="surface_alt", fg="text_dark"
        ).pack(anchor="w", pady=(0, 4))
        self.lbl_canli_json = self._tema_bagla(
            tk.Label(
                self.frm_json_onizleme, text="", font=("Consolas", 8),
                bg=t["code_bg"], fg=t["code_fg"], padx=8, pady=6,
                anchor="w", justify="left", wraplength=390
            ),
            bg="code_bg", fg="code_fg"
        )
        self.lbl_canli_json.pack(fill=tk.X)

        self.frm_sonuc = self._tema_bagla(
            tk.Frame(
                icerik, bg=t["surface_alt"], padx=8, pady=8,
                highlightthickness=1, highlightbackground=t["panel_border"]
            ),
            bg="surface_alt", highlightbackground="panel_border"
        )
        self.frm_sonuc.pack(fill=tk.X, pady=(4, 4))
        self._tema_bagla(
            tk.Label(self.frm_sonuc, text="Sonuç ve Geri Bildirim", font=("Segoe UI", 8, "bold"), bg=t["surface_alt"], fg=t["text_dark"]),
            bg="surface_alt", fg="text_dark"
        ).pack(anchor="w", pady=(0, 4))

        self.lbl_sonuc_durum = self._tema_bagla(
            tk.Label(
                self.frm_sonuc, text="Henüz talep gönderilmedi.", font=("Segoe UI", 9),
                bg=t["surface_alt"], fg=t["text_muted"], wraplength=390, justify="left", anchor="w"
            ),
            bg="surface_alt"
        )
        self._durum_etiket_rolleri[self.lbl_sonuc_durum] = "text_muted"
        self.lbl_sonuc_durum.pack(fill=tk.X)

        self.btn_hizli_bekleme = self._tema_bagla(
            tk.Button(
                self.frm_sonuc, text="Bu Talep İçin Bekleme Kaydı Aç",
                font=("Segoe UI", 9, "bold"), bg=t["warn"], fg="#ffffff",
                activebackground=t["btn_warn_fg"], activeforeground="#ffffff",
                relief="flat", pady=5, cursor="hand2",
                command=self._hizli_bekleme_ac
            ),
            bg="warn", activebackground="btn_warn_fg"
        )

        for w in (self.cb_talep_kullanici, self.cb_talep_kaynak, self.ent_talep_tarih, self.cb_talep_bas, self.cb_talep_bit):
            w.bind("<<ComboboxSelected>>", lambda e: self._canli_json_guncelle())
            w.bind("<KeyRelease>", lambda e: self._canli_json_guncelle())

    def _canli_json_guncelle(self) -> None:
        if not hasattr(self, "lbl_canli_json"):
            return
        try:
            kullanici = self.cb_talep_kullanici.get()
            if self.var_talep_modu.get() == "tekil":
                kaynak = self.cb_talep_kaynak.get()
                tarih = self.ent_talep_tarih.get().strip()
                bas = self.cb_talep_bas.get().strip()
                bit = self.cb_talep_bit.get().strip()
                cmd = {
                    "komut": "rezervasyon",
                    "kullanici": kullanici,
                    "kaynak": kaynak,
                    "baslangic": f"{tarih}T{bas}",
                    "bitis": f"{tarih}T{bit}",
                }
            else:
                kalemler = []
                for k in self.paket_kalem_satirlari:
                    tarih = k["tarih"].get().strip()
                    kalemler.append({
                        "kaynak": k["kaynak"].get(),
                        "baslangic": f"{tarih}T{k['bas'].get().strip()}",
                        "bitis": f"{tarih}T{k['bit'].get().strip()}",
                    })
                cmd = {
                    "komut": "paket",
                    "kullanici": kullanici,
                    "kalemler": kalemler,
                }
            self.lbl_canli_json.configure(text=json.dumps(cmd, ensure_ascii=False))
        except Exception:
            pass

    def _talep_modu_degisti(self) -> None:
        if self.var_talep_modu.get() == "tekil":
            self.frm_paket.pack_forget()
            self.frm_tekil.pack(fill=tk.X, before=self.frm_json_onizleme)
        else:
            self.frm_tekil.pack_forget()
            self.frm_paket.pack(fill=tk.X, before=self.frm_json_onizleme)
        self._canli_json_guncelle()

    def _paket_kalem_ekle(self) -> None:
        if len(self.paket_kalem_satirlari) >= 6:
            return
        t = self._tema()
        idx = len(self.paket_kalem_satirlari)
        outer_frame = self._tema_bagla(
            tk.Frame(
                self.frm_kalem_listesi, bg=t["surface_alt"], padx=6, pady=5,
                relief="flat", bd=0, highlightthickness=1, highlightbackground=t["panel_border"]
            ),
            bg="surface_alt", highlightbackground="panel_border"
        )
        outer_frame.pack(fill=tk.X, pady=3)

        row_frame = self._tema_bagla(tk.Frame(outer_frame, bg=t["surface_alt"]), bg="surface_alt")
        row_frame.pack(fill=tk.X)

        self._tema_bagla(
            tk.Label(row_frame, text=f"Kalem {idx+1}", font=("Segoe UI", 8, "bold"), bg=t["surface_alt"], fg=t["text_dark"]),
            bg="surface_alt", fg="text_dark"
        ).pack(side=tk.LEFT)
        cb_kaynak = ttk.Combobox(row_frame, width=8, state="readonly", values=list(self.motor.kaynaklar.keys()))
        if self.motor.kaynaklar:
            cb_kaynak.current(min(idx, len(self.motor.kaynaklar) - 1))
        cb_kaynak.pack(side=tk.LEFT, padx=4)

        var_tarih = tk.StringVar(value=self.goruntulenen_gun.strftime("%Y-%m-%d"))
        var_tarih.trace_add("write", lambda *_: self._canli_json_guncelle())
        ent_tarih = ttk.Entry(row_frame, width=11, textvariable=var_tarih)
        ent_tarih.pack(side=tk.LEFT, padx=(2, 2))

        self._tema_bagla(
            tk.Button(
                row_frame, text="Seç", font=("Segoe UI", 7, "bold"),
                bg=t["btn_accent_bg"], fg=t["btn_accent_fg"],
                activebackground=t["btn_accent_hover"], activeforeground=t["btn_accent_fg"],
                relief="flat", padx=5, pady=2, cursor="hand2",
                command=lambda v=var_tarih, e_w=ent_tarih: self._takvim_popup_ac(
                    v.get(),
                    e_w,
                    lambda g, sv=v: sv.set(g.strftime("%Y-%m-%d")),
                )
            ),
            bg="btn_accent_bg", fg="btn_accent_fg", activebackground="btn_accent_hover", activeforeground="btn_accent_fg"
        ).pack(side=tk.LEFT, padx=(0, 3))

        saatler = [f"{h:02d}:{m:02d}" for h in range(8, 23) for m in (0, 15, 30, 45) if not (h == 22 and m > 0)]
        cb_bas = ttk.Combobox(row_frame, values=saatler, width=5)
        cb_bas.set("14:00")
        cb_bas.pack(side=tk.LEFT, padx=2)

        cb_bit = ttk.Combobox(row_frame, values=saatler, width=5)
        cb_bit.set("16:00")
        cb_bit.pack(side=tk.LEFT, padx=2)

        lbl_durum = self._tema_bagla(
            tk.Label(outer_frame, text="", font=("Segoe UI", 8, "bold"), bg=t["surface_alt"], fg=t["text_muted"], anchor="w", justify="left", wraplength=380),
            bg="surface_alt"
        )
        self._durum_etiket_rolleri[lbl_durum] = "text_muted"
        lbl_durum.pack(fill=tk.X, pady=(2, 0))

        for w in (cb_kaynak, ent_tarih, cb_bas, cb_bit):
            w.bind("<<ComboboxSelected>>", lambda e: self._canli_json_guncelle())
            w.bind("<KeyRelease>", lambda e: self._canli_json_guncelle())

        self.paket_kalem_satirlari.append({
            "frame": outer_frame,
            "kaynak": cb_kaynak,
            "tarih": ent_tarih,
            "var_tarih": var_tarih,
            "bas": cb_bas,
            "bit": cb_bit,
            "durum_lbl": lbl_durum,
        })
        self._canli_json_guncelle()

    def _paket_kalem_cikar(self) -> None:
        if len(self.paket_kalem_satirlari) > 1:
            item = self.paket_kalem_satirlari.pop()
            self._durum_etiket_rolleri.pop(item["durum_lbl"], None)
            item["frame"].destroy()
            self._canli_json_guncelle()

    def _olustur_sekme_kullanici(self, parent: tk.Widget) -> None:
        t = self._tema()
        pan = self._tema_bagla(tk.Frame(parent, bg=t["panel"], padx=16, pady=14), bg="panel")
        pan.pack(fill=tk.BOTH, expand=True)

        self._tema_bagla(
            tk.Label(pan, text="Kullanıcı Paneli", font=("Segoe UI", 11, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).pack(anchor="w", pady=(0, 8))

        secim_box = self._tema_bagla(tk.Frame(pan, bg=t["panel"]), bg="panel")
        secim_box.pack(fill=tk.X, pady=(0, 10))
        self._tema_bagla(
            tk.Label(secim_box, text="Kullanıcı Seç:", font=("Segoe UI", 9, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).pack(side=tk.LEFT)
        self.cb_panel_kullanici = ttk.Combobox(secim_box, state="readonly", width=16)
        self.cb_panel_kullanici.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))
        self.cb_panel_kullanici.bind("<<ComboboxSelected>>", lambda e: self._kullanici_paneli_guncelle())

        self._tema_bagla(
            tk.Button(
                secim_box, text="Sorgu Komutu Gönder", font=("Segoe UI", 8, "bold"),
                bg=t["btn_accent_bg"], fg=t["btn_accent_fg"],
                activebackground=t["btn_accent_hover"], activeforeground=t["btn_accent_fg"],
                relief="flat", padx=10, pady=4, cursor="hand2",
                command=self._kullanici_sorgu_gonder
            ),
            bg="btn_accent_bg", fg="btn_accent_fg", activebackground="btn_accent_hover", activeforeground="btn_accent_fg"
        ).pack(side=tk.RIGHT)

        self.frm_kullanici_kart = self._tema_bagla(
            tk.Frame(
                pan, bg=t["surface_alt"], padx=12, pady=10,
                relief="flat", bd=0, highlightthickness=1, highlightbackground=t["panel_border"]
            ),
            bg="surface_alt", highlightbackground="panel_border"
        )
        self.frm_kullanici_kart.pack(fill=tk.X, pady=(0, 10))

        self.lbl_kart_bilgi = self._tema_bagla(
            tk.Label(
                self.frm_kullanici_kart, text="Kullanıcı bilgisi yükleniyor...",
                font=("Segoe UI", 9), bg=t["surface_alt"], fg=t["text_dark"], justify="left"
            ),
            bg="surface_alt", fg="text_dark"
        )
        self.lbl_kart_bilgi.pack(anchor="w")

        self._tema_bagla(
            tk.Label(
                pan, text="Kullanıcının Rezervasyonları (Seçip doğrudan işlem yapabilirsiniz):",
                font=("Segoe UI", 9, "bold"), bg=t["panel"], fg=t["text_dark"]
            ),
            bg="panel", fg="text_dark"
        ).pack(anchor="w", pady=(2, 4))

        self.tree_kull_rez = ttk.Treeview(
            pan, columns=("id", "kaynak", "baslangic", "bitis", "durum", "ucret"),
            show="headings", height=6
        )
        self.tree_kull_rez.heading("id", text="ID")
        self.tree_kull_rez.heading("kaynak", text="Kaynak")
        self.tree_kull_rez.heading("baslangic", text="Başlangıç")
        self.tree_kull_rez.heading("bitis", text="Bitiş")
        self.tree_kull_rez.heading("durum", text="Durum")
        self.tree_kull_rez.heading("ucret", text="Ücret")

        self.tree_kull_rez.column("id", width=60, anchor="center")
        self.tree_kull_rez.column("kaynak", width=90, anchor="center")
        self.tree_kull_rez.column("baslangic", width=130, anchor="center")
        self.tree_kull_rez.column("bitis", width=130, anchor="center")
        self.tree_kull_rez.column("durum", width=100, anchor="center")
        self.tree_kull_rez.column("ucret", width=70, anchor="e")

        self.tree_kull_rez.pack(fill=tk.BOTH, expand=True, pady=(0, 6))
        self.tree_kull_rez.bind("<<TreeviewSelect>>", self._tablodan_rezervasyon_secildi)

        panel_eylem_bar = self._tema_bagla(
            tk.Frame(
                pan, bg=t["surface_alt"], padx=8, pady=6,
                relief="flat", bd=0, highlightthickness=1, highlightbackground=t["panel_border"]
            ),
            bg="surface_alt", highlightbackground="panel_border"
        )
        panel_eylem_bar.pack(fill=tk.X, pady=(0, 4))
        self._tema_bagla(
            tk.Label(panel_eylem_bar, text="Seçili Rezervasyon Eylemi:", font=("Segoe UI", 8, "bold"), bg=t["surface_alt"], fg=t["text_dark"]),
            bg="surface_alt", fg="text_dark"
        ).pack(side=tk.LEFT)

        self.btn_panel_iptal = tk.Button(
            panel_eylem_bar, text="İptal Et", font=("Segoe UI", 8, "bold"),
            bg=t["btn_disabled_bg"], fg="#ffffff", disabledforeground=t["btn_disabled_fg"],
            activebackground=t["error_hover"], activeforeground="#ffffff",
            relief="flat", padx=10, pady=3, cursor="hand2", state="disabled",
            command=self._eylem_iptal
        )
        self.btn_panel_iptal.pack(side=tk.RIGHT, padx=3)
        self.btn_panel_cikis = tk.Button(
            panel_eylem_bar, text="Çıkış Yap", font=("Segoe UI", 8, "bold"),
            bg=t["btn_disabled_bg"], fg="#ffffff", disabledforeground=t["btn_disabled_fg"],
            activebackground=t["info_hover"], activeforeground="#ffffff",
            relief="flat", padx=10, pady=3, cursor="hand2", state="disabled",
            command=self._eylem_cikis
        )
        self.btn_panel_cikis.pack(side=tk.RIGHT, padx=3)
        self.btn_panel_giris = tk.Button(
            panel_eylem_bar, text="Giriş Yap", font=("Segoe UI", 8, "bold"),
            bg=t["btn_disabled_bg"], fg="#ffffff", disabledforeground=t["btn_disabled_fg"],
            activebackground=t["success_hover"], activeforeground="#ffffff",
            relief="flat", padx=10, pady=3, cursor="hand2", state="disabled",
            command=self._eylem_giris
        )
        self.btn_panel_giris.pack(side=tk.RIGHT, padx=3)

        self.lbl_panel_eylem_sonuc = self._tema_bagla(
            tk.Label(
                pan, text="", font=("Segoe UI", 8, "bold"), bg=t["panel"], fg=t["text_muted"],
                anchor="w", justify="left", wraplength=700
            ),
            bg="panel"
        )
        self._durum_etiket_rolleri[self.lbl_panel_eylem_sonuc] = "text_muted"
        self.lbl_panel_eylem_sonuc.pack(fill=tk.X, pady=(0, 6))

        self._tema_bagla(
            tk.Label(pan, text="Bekleme Listesi Kayıtları:", font=("Segoe UI", 9, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).pack(anchor="w", pady=(2, 4))
        self.tree_kull_bek = ttk.Treeview(
            pan, columns=("id", "kaynak", "baslangic", "bitis", "sira"),
            show="headings", height=5
        )
        self.tree_kull_bek.heading("id", text="Bekleme ID")
        self.tree_kull_bek.heading("kaynak", text="Kaynak")
        self.tree_kull_bek.heading("baslangic", text="Başlangıç")
        self.tree_kull_bek.heading("bitis", text="Bitiş")
        self.tree_kull_bek.heading("sira", text="Sıra")

        self.tree_kull_bek.column("id", width=80, anchor="center")
        self.tree_kull_bek.column("kaynak", width=90, anchor="center")
        self.tree_kull_bek.column("baslangic", width=130, anchor="center")
        self.tree_kull_bek.column("bitis", width=130, anchor="center")
        self.tree_kull_bek.column("sira", width=60, anchor="center")

        self.tree_kull_bek.pack(fill=tk.BOTH, expand=True)

    def _olustur_sekme_gunluk(self, parent: tk.Widget) -> None:
        t = self._tema()
        pan = self._tema_bagla(tk.Frame(parent, bg=t["panel"], padx=16, pady=14), bg="panel")
        pan.pack(fill=tk.BOTH, expand=True)

        self._tema_bagla(
            tk.Label(pan, text="Olay Günlüğü", font=("Segoe UI", 11, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).pack(anchor="w", pady=(0, 6))

        self._tema_bagla(
            tk.Label(
                pan, text="Oturum İşlem Geçmişi (Seçilen satırın JSON detayı aşağıda açılır):",
                font=("Segoe UI", 9, "bold"), bg=t["panel"], fg=t["text_muted"]
            ),
            bg="panel", fg="text_muted"
        ).pack(anchor="w", pady=(0, 6))

        self.tree_gunluk = ttk.Treeview(
            pan, columns=("no", "komut", "durum", "ozet"),
            show="headings", height=12
        )
        self.tree_gunluk.heading("no", text="No")
        self.tree_gunluk.heading("komut", text="Komut")
        self.tree_gunluk.heading("durum", text="Durum")
        self.tree_gunluk.heading("ozet", text="Özet Sonuç")

        self.tree_gunluk.column("no", width=50, anchor="center")
        self.tree_gunluk.column("komut", width=120, anchor="w")
        self.tree_gunluk.column("durum", width=80, anchor="center")
        self.tree_gunluk.column("ozet", width=480, anchor="w")

        self.tree_gunluk.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.tree_gunluk.bind("<<TreeviewSelect>>", self._gunluk_secildi)

        self._tema_bagla(
            tk.Label(pan, text="Komut ve Çıktı JSON Formatı (Bölüm 5):", font=("Segoe UI", 8, "bold"), bg=t["panel"], fg=t["text_muted"]),
            bg="panel", fg="text_muted"
        ).pack(anchor="w", pady=(0, 4))
        self.txt_json_detay = self._tema_bagla(
            tk.Text(
                pan, height=9, font=("Consolas", 9),
                bg=t["code_bg"], fg=t["code_fg"], insertbackground=t["code_fg"],
                relief="flat", padx=10, pady=8
            ),
            bg="code_bg", fg="code_fg", insertbackground="code_fg"
        )
        self.txt_json_detay.pack(fill=tk.BOTH, expand=True)

    def _olustur_sekme_ekle(self, parent: tk.Widget) -> None:
        t = self._tema()
        pan = self._tema_bagla(tk.Frame(parent, bg=t["bg"]), bg="bg")
        pan.pack(fill=tk.BOTH, expand=True)
        pan.columnconfigure(0, weight=1, uniform="ekle")
        pan.columnconfigure(1, weight=1, uniform="ekle")
        pan.rowconfigure(0, weight=1)

        frm_k = self._tema_bagla(
            tk.Frame(
                pan, bg=t["panel"], padx=18, pady=16,
                highlightthickness=1, highlightbackground=t["panel_border"]
            ),
            bg="panel", highlightbackground="panel_border"
        )
        frm_k.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self._tema_bagla(
            tk.Label(frm_k, text="Yeni Kullanıcı Ekle (kullanici_ekle)", font=("Segoe UI", 11, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        self._tema_bagla(tk.Label(frm_k, text="ID:", bg=t["panel"], fg=t["text_dark"]), bg="panel", fg="text_dark").grid(row=1, column=0, sticky="w", pady=6)
        self.ent_ekle_uid = ttk.Entry(frm_k, width=14)
        self.ent_ekle_uid.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        self._tema_bagla(tk.Label(frm_k, text="Ad Soyad:", bg=t["panel"], fg=t["text_dark"]), bg="panel", fg="text_dark").grid(row=1, column=2, sticky="w", padx=(12, 0), pady=6)
        self.ent_ekle_uad = ttk.Entry(frm_k, width=20)
        self.ent_ekle_uad.grid(row=1, column=3, sticky="w", padx=6, pady=6)

        self._tema_bagla(tk.Label(frm_k, text="Rol:", bg=t["panel"], fg=t["text_dark"]), bg="panel", fg="text_dark").grid(row=2, column=0, sticky="w", pady=6)
        self.cb_ekle_urol = ttk.Combobox(frm_k, width=16, state="readonly")
        self.cb_ekle_urol.grid(row=2, column=1, sticky="w", padx=6, pady=6)
        self.cb_ekle_urol.bind("<<ComboboxSelected>>", self._ekle_rol_secildi)

        self._tema_bagla(tk.Label(frm_k, text="Bakiye (KP):", bg=t["panel"], fg=t["text_dark"]), bg="panel", fg="text_dark").grid(row=2, column=2, sticky="w", padx=(12, 0), pady=6)
        self.ent_ekle_ubakiye = ttk.Combobox(frm_k, width=14, values=["120", "300", "600", "0"])
        self.ent_ekle_ubakiye.set("120")
        self.ent_ekle_ubakiye.grid(row=2, column=3, sticky="w", padx=6, pady=6)

        self._tema_bagla(tk.Label(frm_k, text="Güvenilirlik (0-100):", bg=t["panel"], fg=t["text_dark"]), bg="panel", fg="text_dark").grid(row=3, column=0, sticky="w", pady=6)
        self.ent_ekle_uguv = ttk.Combobox(frm_k, width=14, values=["100", "90", "80", "70", "60", "50", "40", "0"])
        self.ent_ekle_uguv.set("80")
        self.ent_ekle_uguv.grid(row=3, column=1, sticky="w", padx=6, pady=6)

        self._tema_bagla(tk.Label(frm_k, text="Sertifikalar:", bg=t["panel"], fg=t["text_dark"]), bg="panel", fg="text_dark").grid(row=4, column=0, sticky="w", pady=6)
        self.frm_ekle_sertifikalar = self._tema_bagla(tk.Frame(frm_k, bg=t["panel"]), bg="panel")
        self.frm_ekle_sertifikalar.grid(row=4, column=1, columnspan=3, sticky="w", padx=6, pady=6)

        self._tema_bagla(
            tk.Button(
                frm_k, text="+ Kullanıcı Ekle", font=("Segoe UI", 9, "bold"),
                bg=t["primary"], fg=t["primary_fg"],
                activebackground=t["primary_hover"], activeforeground=t["primary_fg"],
                relief="flat", padx=14, pady=5, cursor="hand2",
                command=self._kullanici_ekle_gonder
            ),
            bg="primary", fg="primary_fg", activebackground="primary_hover", activeforeground="primary_fg"
        ).grid(row=5, column=0, columnspan=4, pady=(12, 0), sticky="e")

        self.lbl_ekle_kullanici_sonuc = self._tema_bagla(
            tk.Label(
                frm_k, text="", font=("Segoe UI", 8, "bold"), bg=t["panel"], fg=t["text_muted"],
                anchor="w", justify="left", wraplength=460
            ),
            bg="panel"
        )
        self._durum_etiket_rolleri[self.lbl_ekle_kullanici_sonuc] = "text_muted"
        self.lbl_ekle_kullanici_sonuc.grid(row=6, column=0, columnspan=4, sticky="we", pady=(8, 0))

        frm_r = self._tema_bagla(
            tk.Frame(
                pan, bg=t["panel"], padx=18, pady=16,
                highlightthickness=1, highlightbackground=t["panel_border"]
            ),
            bg="panel", highlightbackground="panel_border"
        )
        frm_r.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._tema_bagla(
            tk.Label(frm_r, text="Yeni Kaynak Ekle (kaynak_ekle)", font=("Segoe UI", 11, "bold"), bg=t["panel"], fg=t["text_dark"]),
            bg="panel", fg="text_dark"
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        self._tema_bagla(tk.Label(frm_r, text="ID:", bg=t["panel"], fg=t["text_dark"]), bg="panel", fg="text_dark").grid(row=1, column=0, sticky="w", pady=6)
        self.ent_ekle_rid = ttk.Entry(frm_r, width=14)
        self.ent_ekle_rid.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        self._tema_bagla(tk.Label(frm_r, text="Ad:", bg=t["panel"], fg=t["text_dark"]), bg="panel", fg="text_dark").grid(row=1, column=2, sticky="w", padx=(12, 0), pady=6)
        self.ent_ekle_rad = ttk.Entry(frm_r, width=20)
        self.ent_ekle_rad.grid(row=1, column=3, sticky="w", padx=6, pady=6)

        self._tema_bagla(tk.Label(frm_r, text="Tür:", bg=t["panel"], fg=t["text_dark"]), bg="panel", fg="text_dark").grid(row=2, column=0, sticky="w", pady=6)
        self.cb_ekle_rtur = ttk.Combobox(frm_r, width=16, state="readonly")
        self.cb_ekle_rtur.grid(row=2, column=1, sticky="w", padx=6, pady=6)

        self._tema_bagla(tk.Label(frm_r, text="İzinli Roller:", bg=t["panel"], fg=t["text_dark"]), bg="panel", fg="text_dark").grid(row=3, column=0, sticky="w", pady=6)
        self.frm_ekle_roller = self._tema_bagla(tk.Frame(frm_r, bg=t["panel"]), bg="panel")
        self.frm_ekle_roller.grid(row=3, column=1, columnspan=3, sticky="w", padx=6, pady=6)

        self._tema_bagla(
            tk.Button(
                frm_r, text="+ Kaynak Ekle", font=("Segoe UI", 9, "bold"),
                bg=t["primary"], fg=t["primary_fg"],
                activebackground=t["primary_hover"], activeforeground=t["primary_fg"],
                relief="flat", padx=14, pady=5, cursor="hand2",
                command=self._kaynak_ekle_gonder
            ),
            bg="primary", fg="primary_fg", activebackground="primary_hover", activeforeground="primary_fg"
        ).grid(row=4, column=0, columnspan=4, pady=(12, 0), sticky="e")

        self.lbl_ekle_kaynak_sonuc = self._tema_bagla(
            tk.Label(
                frm_r, text="", font=("Segoe UI", 8, "bold"), bg=t["panel"], fg=t["text_muted"],
                anchor="w", justify="left", wraplength=460
            ),
            bg="panel"
        )
        self._durum_etiket_rolleri[self.lbl_ekle_kaynak_sonuc] = "text_muted"
        self.lbl_ekle_kaynak_sonuc.grid(row=5, column=0, columnspan=4, sticky="we", pady=(8, 0))

    def _ekle_rol_secildi(self, event=None) -> None:
        rol_ad = self.cb_ekle_urol.get()
        if rol_ad in self.motor.roller:
            kota = self.motor.roller[rol_ad].haftalik_kota
            self.ent_ekle_ubakiye.set(str(kota))

    def _otomatik_baslat(self) -> None:
        if os.path.exists("baslangic.json"):
            self._yukle_dosya("baslangic.json")
        else:
            self._dosya_sec()

    def _dosya_sec(self) -> None:
        yol = filedialog.askopenfilename(
            title="Başlangıç Dosyasını Seç (baslangic.json)",
            filetypes=[("JSON Dosyaları", "*.json"), ("Tüm Dosyalar", "*.*")]
        )
        if yol:
            self._yukle_dosya(yol, bilgi_ver=True)

    def _dosyayi_yeniden_yukle(self) -> None:
        if self.baslangic_dosyasi and os.path.exists(self.baslangic_dosyasi):
            self._yukle_dosya(self.baslangic_dosyasi, bilgi_ver=True)

    def _yukle_dosya(self, yol: str, bilgi_ver: bool = False) -> None:
        try:
            self.motor = RezervasyonMotoru()
            self.motor.yukle(yol)
            self.baslangic_dosyasi = yol
            self.olay_gunlugu.clear()
            self.secili_rezervasyon = None
            self.son_red_edilen_talep = None

            for item in self.tree_gunluk.get_children():
                self.tree_gunluk.delete(item)
            self.txt_json_detay.delete("1.0", tk.END)

            self.goruntulenen_gun = self.motor.saat.date()

            self.lbl_dosya_durumu.configure(text=f"Dosya: {os.path.basename(yol)}")
            if hasattr(self, "var_talep_tarih"):
                self.var_talep_tarih.set(self.goruntulenen_gun.strftime("%Y-%m-%d"))
            if hasattr(self, "paket_kalem_satirlari"):
                for k in self.paket_kalem_satirlari:
                    k["var_tarih"].set(self.goruntulenen_gun.strftime("%Y-%m-%d"))
                    self._etiket_durum_yaz(k["durum_lbl"], "", "text_muted")
            if hasattr(self, "lbl_sonuc_durum"):
                self._etiket_durum_yaz(self.lbl_sonuc_durum, "Henüz talep gönderilmedi.", "text_muted")
            if hasattr(self, "btn_hizli_bekleme"):
                self.btn_hizli_bekleme.pack_forget()
            if hasattr(self, "lbl_eylem_sonuc"):
                self._etiket_durum_yaz(self.lbl_eylem_sonuc, "", "text_muted")
            if hasattr(self, "lbl_panel_eylem_sonuc"):
                self._etiket_durum_yaz(self.lbl_panel_eylem_sonuc, "", "text_muted")
            if hasattr(self, "lbl_ekle_kullanici_sonuc"):
                self._etiket_durum_yaz(self.lbl_ekle_kullanici_sonuc, "", "text_muted")
            if hasattr(self, "lbl_ekle_kaynak_sonuc"):
                self._etiket_durum_yaz(self.lbl_ekle_kaynak_sonuc, "", "text_muted")
            if hasattr(self, "cb_hedef_saat"):
                self.cb_hedef_saat.set("")
            self.vars_ekle_sert.clear()
            self.vars_ekle_roller.clear()

            self._tum_arayuzu_guncelle()
            if bilgi_ver:
                self._etiket_durum_yaz(
                    self.lbl_saat_olay_bildirimi,
                    f"Başlangıç dosyası yüklendi ve tüm durum sıfırlandı: {os.path.basename(yol)}",
                    "success",
                )
        except Exception as e:
            self._etiket_durum_yaz(
                self.lbl_saat_olay_bildirimi,
                f"Başlangıç dosyası yüklenirken hata oluştu: {e}",
                "error",
            )

    def _komut_calistir(self, cmd: dict[str, Any]) -> dict[str, Any]:
        ham_sonuc = self.motor.komut_isle(dict(cmd))
        no = len(self.olay_gunlugu) + 1
        sonuc: dict[str, Any] = {"no": no, "komut": ham_sonuc.pop("komut")}
        sonuc.update(ham_sonuc)

        kayit = {
            "no": no,
            "komut": cmd,
            "sonuc": sonuc,
        }
        self.olay_gunlugu.append(kayit)

        ozet = self._sonuc_ozeti_olustur(cmd, sonuc)
        item_id = self.tree_gunluk.insert("", "end", values=(no, cmd.get("komut"), sonuc.get("durum"), ozet))
        self.tree_gunluk.selection_set(item_id)
        self.tree_gunluk.see(item_id)
        self._gunluk_secildi(None)

        self._tum_arayuzu_guncelle()

        return sonuc

    def _sonuc_ozeti_olustur(self, cmd: dict, res: dict) -> str:
        durum = res.get("durum")
        if durum == "RED":
            kod = res.get("kod")
            return f"RED: {kod}"
        komut = cmd.get("komut")
        if komut == "rezervasyon":
            return f"Rez: {res.get('rezervasyon_id')} ({res.get('ucret')}KP)"
        if komut == "paket":
            return f"Paket: {res.get('paket_id')} (Toplam: {res.get('toplam')}KP)"
        if komut == "iptal":
            return f"İade: {res.get('iade')}KP, Yeni Bakiye: {res.get('bakiye')}KP"
        if komut == "bekleme":
            return f"Bekleme: {res.get('bekleme_id')}, Sıra: {res.get('sira')}"
        if komut == "saat":
            olay_sayisi = len(res.get("olaylar", []))
            return f"Saat ilerletildi ({olay_sayisi} olay)"
        return "İşlem başarılı"

    def _tum_arayuzu_guncelle(self) -> None:
        gun_adlari = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        saat_str = self.motor.saat.strftime("%Y-%m-%d %H:%M")
        gun_adi = gun_adlari[self.motor.saat.weekday()]
        self.lbl_simule_saat.configure(text=f"{saat_str} ({gun_adi})")

        if hasattr(self, "cb_hedef_saat"):
            aday_saatler = [
                (self.motor.saat + timedelta(minutes=m)).strftime(TIME_FMT)
                for m in (15, 20, 30, 45, 60, 120, 180, 240, 1440)
            ]
            self.cb_hedef_saat["values"] = aday_saatler
            if not self.cb_hedef_saat.get() or self.cb_hedef_saat.get() < self.motor.saat.strftime(TIME_FMT):
                self.cb_hedef_saat.set(aday_saatler[0])

        g_adi = gun_adlari[self.goruntulenen_gun.weekday()]
        self.lbl_takvim_gun.configure(text=f"{self.goruntulenen_gun.strftime('%Y-%m-%d')} {g_adi}")

        secili_id = self.secili_rezervasyon.get("id") if self.secili_rezervasyon else None
        self.takvim.ciz(
            gun=self.goruntulenen_gun,
            simule_saat=self.motor.saat,
            kaynaklar=list(self.motor.kaynaklar.values()),
            rezervasyonlar=self.motor.rezervasyonlar,
            bakimlar=self.motor.bakim_pencereleri,
            kaynak_turleri=self.motor.kaynak_turleri,
            secili_rez_id=secili_id,
        )

        self._eylem_butonlarini_guncelle()

        kull_idler = list(self.motor.kullanicilar.keys())
        kayn_idler = list(self.motor.kaynaklar.keys())
        roller = list(self.motor.roller.keys())
        turler = list(self.motor.kaynak_turleri.keys())

        def _cb_guncelle(cb: ttk.Combobox, degerler: list[str]) -> bool:
            cb["values"] = degerler
            if not degerler:
                cb.set("")
                return False
            if cb.get() not in degerler:
                cb.current(0)
                return True
            return False

        _cb_guncelle(self.cb_talep_kullanici, kull_idler)
        _cb_guncelle(self.cb_talep_kaynak, kayn_idler)

        if hasattr(self, "var_talep_tarih") and not self.var_talep_tarih.get():
            self.var_talep_tarih.set(self.goruntulenen_gun.strftime("%Y-%m-%d"))

        if hasattr(self, "cb_takvim_kaynak"):
            _cb_guncelle(self.cb_takvim_kaynak, kayn_idler)

        for k in self.paket_kalem_satirlari:
            _cb_guncelle(k["kaynak"], kayn_idler)
            if not k["var_tarih"].get():
                k["var_tarih"].set(self.goruntulenen_gun.strftime("%Y-%m-%d"))

        _cb_guncelle(self.cb_panel_kullanici, kull_idler)

        if _cb_guncelle(self.cb_ekle_urol, roller):
            self._ekle_rol_secildi()

        _cb_guncelle(self.cb_ekle_rtur, turler)

        self._ekleme_seceneklerini_guncelle()
        self._kullanici_paneli_guncelle()
        self._canli_json_guncelle()

    def _ekleme_seceneklerini_guncelle(self) -> None:
        if not hasattr(self, "frm_ekle_sertifikalar") or not hasattr(self, "frm_ekle_roller"):
            return

        t = self._tema()
        mevcut_sertifikalar = set()
        for kt in self.motor.kaynak_turleri.values():
            if kt.sertifika:
                mevcut_sertifikalar.add(kt.sertifika)
        for k in self.motor.kullanicilar.values():
            for s in k.sertifikalar:
                mevcut_sertifikalar.add(s)
        sert_listesi = sorted(mevcut_sertifikalar)

        silinecek = set(self.frm_ekle_sertifikalar.winfo_children()) | set(self.frm_ekle_roller.winfo_children())
        if silinecek:
            self._tema_baglantilari = [(w, e) for w, e in self._tema_baglantilari if w not in silinecek]

        secili_sertler = {s for s, var in self.vars_ekle_sert.items() if var.get()}
        for child in self.frm_ekle_sertifikalar.winfo_children():
            child.destroy()
        self.vars_ekle_sert.clear()

        if sert_listesi:
            for s in sert_listesi:
                var = tk.BooleanVar(value=(s in secili_sertler))
                self.vars_ekle_sert[s] = var
                cb = self._tema_bagla(
                    tk.Checkbutton(
                        self.frm_ekle_sertifikalar, text=s, variable=var,
                        bg=t["panel"], fg=t["text_dark"], selectcolor=t["input_bg"],
                        activebackground=t["panel"], activeforeground=t["text_dark"],
                        font=("Segoe UI", 8)
                    ),
                    bg="panel", fg="text_dark", selectcolor="input_bg", activebackground="panel", activeforeground="text_dark"
                )
                cb.pack(side=tk.LEFT, padx=3)
        else:
            self._tema_bagla(
                tk.Label(self.frm_ekle_sertifikalar, text="(Tanımlı sertifika yok)", bg=t["panel"], fg=t["text_muted"], font=("Segoe UI", 8)),
                bg="panel", fg="text_muted"
            ).pack(side=tk.LEFT)

        roller_listesi = list(self.motor.roller.keys())
        secili_roller = {r for r, var in self.vars_ekle_roller.items() if var.get()}
        for child in self.frm_ekle_roller.winfo_children():
            child.destroy()
        self.vars_ekle_roller.clear()

        if roller_listesi:
            for r in roller_listesi:
                is_selected = (r in secili_roller) if secili_roller else True
                var = tk.BooleanVar(value=is_selected)
                self.vars_ekle_roller[r] = var
                cb = self._tema_bagla(
                    tk.Checkbutton(
                        self.frm_ekle_roller, text=r, variable=var,
                        bg=t["panel"], fg=t["text_dark"], selectcolor=t["input_bg"],
                        activebackground=t["panel"], activeforeground=t["text_dark"],
                        font=("Segoe UI", 8)
                    ),
                    bg="panel", fg="text_dark", selectcolor="input_bg", activebackground="panel", activeforeground="text_dark"
                )
                cb.pack(side=tk.LEFT, padx=3)
        else:
            self._tema_bagla(
                tk.Label(self.frm_ekle_roller, text="(Tanımlı rol yok)", bg=t["panel"], fg=t["text_muted"], font=("Segoe UI", 8)),
                bg="panel", fg="text_muted"
            ).pack(side=tk.LEFT)

    def _eylem_butonlarini_guncelle(self) -> None:
        t = self._tema()
        buton_renkler = [
            (self.btn_giris, t["success"], t["success_hover"]),
            (self.btn_cikis, t["info"], t["info_hover"]),
            (self.btn_iptal, t["error"], t["error_hover"]),
        ]
        if hasattr(self, "btn_panel_giris"):
            buton_renkler.extend([
                (self.btn_panel_giris, t["success"], t["success_hover"]),
                (self.btn_panel_cikis, t["info"], t["info_hover"]),
                (self.btn_panel_iptal, t["error"], t["error_hover"]),
            ])

        if not self.secili_rezervasyon:
            self._etiket_durum_yaz(
                self.lbl_secili_rez,
                "Seçili Rezervasyon: (Takvimden veya tablodan bir rezervasyona tıklayın)",
                "text_muted",
            )
            for b, _, _ in buton_renkler:
                b.configure(state="disabled", bg=t["btn_disabled_bg"], disabledforeground=t["btn_disabled_fg"])
            return

        r_id = self.secili_rezervasyon["id"]
        rez_obj = None
        for r in self.motor.rezervasyonlar:
            if r.id == r_id:
                rez_obj = r
                break

        if not rez_obj:
            self._etiket_durum_yaz(self.lbl_secili_rez, f"Rezervasyon {r_id} bulunamadı.", "error")
            for b, renk, hover in buton_renkler:
                b.configure(state="normal", bg=renk, fg="#ffffff", activebackground=hover, activeforeground="#ffffff")
            return

        durum = rez_obj.durum
        paket_str = f" | Paket: {rez_obj.paket}" if rez_obj.paket else ""
        self._etiket_durum_yaz(
            self.lbl_secili_rez,
            f"Seçili: {r_id} | Kul: {rez_obj.kullanici} | Kaynak: {rez_obj.kaynak} | {rez_obj.baslangic.strftime('%H:%M')}-{rez_obj.bitis.strftime('%H:%M')} | {durum} | {rez_obj.ucret} KP{paket_str}",
            "text_dark",
        )

        for b, renk, hover in buton_renkler:
            b.configure(state="normal", bg=renk, fg="#ffffff", activebackground=hover, activeforeground="#ffffff")

    def _kullanici_paneli_guncelle(self) -> None:
        for item in self.tree_kull_rez.get_children():
            self.tree_kull_rez.delete(item)
        for item in self.tree_kull_bek.get_children():
            self.tree_kull_bek.delete(item)

        uid = self.cb_panel_kullanici.get()
        if not uid or uid not in self.motor.kullanicilar:
            self.lbl_kart_bilgi.configure(text="Seçili kullanıcı bulunamadı.")
            return

        u = self.motor.kullanicilar[uid]
        rol_obj = self.motor.roller.get(u.rol)
        kota = rol_obj.haftalik_kota if rol_obj else 0

        sert_str = ", ".join(u.sertifikalar) if u.sertifikalar else "Yok"
        kart_metin = (
            f"ID: {u.id} - {u.ad}\n"
            f"Rol: {u.rol} | Haftalık Kota: {kota} KP\n"
            f"Bakiye: {u.bakiye} KP | Güvenilirlik Puanı: {u.guvenilirlik} / 100\n"
            f"Sertifikalar: {sert_str}"
        )
        self.lbl_kart_bilgi.configure(text=kart_metin)

        kull_rezler = [r for r in self.motor.rezervasyonlar if r.kullanici == uid]
        kull_rezler.sort(key=lambda r: (r.baslangic, _id_num(r.id)))
        for r in kull_rezler:
            self.tree_kull_rez.insert("", "end", values=(
                r.id, r.kaynak,
                r.baslangic.strftime("%m-%d %H:%M"),
                r.bitis.strftime("%m-%d %H:%M"),
                r.durum, f"{r.ucret} KP"
            ))

        kull_bekler = [b for b in self.motor.bekleme_kayitlari if b.kullanici == uid]
        for b in kull_bekler:
            sira = self.motor._bekleme_sira(b.kaynak, b.id)
            self.tree_kull_bek.insert("", "end", values=(
                b.id, b.kaynak,
                b.baslangic.strftime("%m-%d %H:%M"),
                b.bitis.strftime("%m-%d %H:%M"),
                sira
            ))

    def _gun_degistir(self, delta_gun: int) -> None:
        self.goruntulenen_gun += timedelta(days=delta_gun)
        if hasattr(self, "var_talep_tarih"):
            self.var_talep_tarih.set(self.goruntulenen_gun.strftime("%Y-%m-%d"))
        self._tum_arayuzu_guncelle()

    def _takvimi_simule_gune_getir(self) -> None:
        self.goruntulenen_gun = self.motor.saat.date()
        if hasattr(self, "var_talep_tarih"):
            self.var_talep_tarih.set(self.goruntulenen_gun.strftime("%Y-%m-%d"))
        self._tum_arayuzu_guncelle()

    def _rezervasyon_secildi(self, info: dict[str, Any]) -> None:
        self.secili_rezervasyon = info
        if hasattr(self, "cb_takvim_kaynak") and info.get("kaynak"):
            self.cb_takvim_kaynak.set(info["kaynak"])
        self._tum_arayuzu_guncelle()

    def _tablodan_rezervasyon_secildi(self, event) -> None:
        sel = self.tree_kull_rez.selection()
        if not sel:
            return
        vals = self.tree_kull_rez.item(sel[0], "values")
        if vals:
            r_id = vals[0]
            kaynak_id = vals[1] if len(vals) > 1 else None
            self.secili_rezervasyon = {"id": r_id, "kaynak": kaynak_id}
            if hasattr(self, "cb_takvim_kaynak") and kaynak_id:
                self.cb_takvim_kaynak.set(kaynak_id)
            self._eylem_butonlarini_guncelle()
            self.takvim.selected_item_id = r_id
            self.takvim.ciz(
                gun=self.goruntulenen_gun,
                simule_saat=self.motor.saat,
                kaynaklar=list(self.motor.kaynaklar.values()),
                rezervasyonlar=self.motor.rezervasyonlar,
                bakimlar=self.motor.bakim_pencereleri,
                kaynak_turleri=self.motor.kaynak_turleri,
                secili_rez_id=r_id,
            )

    def _gunluk_secildi(self, event) -> None:
        sel = self.tree_gunluk.selection()
        if not sel:
            return
        idx = int(self.tree_gunluk.item(sel[0], "values")[0]) - 1
        if 0 <= idx < len(self.olay_gunlugu):
            kayit = self.olay_gunlugu[idx]
            self.txt_json_detay.delete("1.0", tk.END)
            metin = (
                f"Komut (#{kayit['no']}):\n"
                f"{json.dumps(kayit['komut'], ensure_ascii=False)}\n\n"
                f"Sonuç (#{kayit['no']}):\n"
                f"{json.dumps(kayit['sonuc'], ensure_ascii=False)}"
            )
            self.txt_json_detay.insert("1.0", metin)

    def _eylem_geri_bildirim_yaz(self, metin: str, rol: str) -> None:
        self._etiket_durum_yaz(self.lbl_eylem_sonuc, metin, rol)
        if hasattr(self, "lbl_panel_eylem_sonuc"):
            self._etiket_durum_yaz(self.lbl_panel_eylem_sonuc, metin, rol)

    def _otomatik_atama_metni(self, olaylar: list[dict[str, Any]]) -> str:
        if not olaylar:
            return " | Otomatik Atama: Yok"
        detaylar = [
            f"{o.get('bekleme')}->{o.get('rezervasyon')} ({o.get('kullanici')}, Ücret:{o.get('ucret')}KP, Bakiye:{o.get('bakiye')}KP)"
            for o in olaylar
        ]
        return " | Otomatik Atama: " + ", ".join(detaylar)

    def _eylem_giris(self) -> None:
        if not self.secili_rezervasyon:
            return
        r_id = self.secili_rezervasyon["id"]
        res = self._komut_calistir({"komut": "giris", "rezervasyon": r_id})
        if res.get("durum") == "TAMAM":
            self._eylem_geri_bildirim_yaz(
                f"[TAMAM] Giriş yapıldı: Rezervasyon {r_id} yeni durumu {res.get('yeni_durum')}.",
                "success"
            )
        else:
            kod = res.get("kod")
            aciklama = HATA_ACIKLAMALARI.get(kod, "Bilinmeyen hata.")
            self._eylem_geri_bildirim_yaz(f"[RED: {kod}] {aciklama}", "error")

    def _eylem_cikis(self) -> None:
        if not self.secili_rezervasyon:
            return
        r_id = self.secili_rezervasyon["id"]
        res = self._komut_calistir({"komut": "cikis", "rezervasyon": r_id})
        if res.get("durum") == "TAMAM":
            atama_str = self._otomatik_atama_metni(res.get("olaylar", []))
            self._eylem_geri_bildirim_yaz(
                f"[TAMAM] Çıkış yapıldı: {r_id} durumu {res.get('yeni_durum')} | Güvenilirlik: {res.get('guvenilirlik')}{atama_str}",
                "success"
            )
        else:
            kod = res.get("kod")
            aciklama = HATA_ACIKLAMALARI.get(kod, "Bilinmeyen hata.")
            self._eylem_geri_bildirim_yaz(f"[RED: {kod}] {aciklama}", "error")

    def _eylem_iptal(self) -> None:
        if not self.secili_rezervasyon:
            return
        r_id = self.secili_rezervasyon["id"]
        res = self._komut_calistir({"komut": "iptal", "rezervasyon": r_id})
        if res.get("durum") == "TAMAM":
            atama_str = self._otomatik_atama_metni(res.get("olaylar", []))
            self._eylem_geri_bildirim_yaz(
                f"[TAMAM] İptal edildi: {r_id} | İade: {res.get('iade')} KP | Yeni Bakiye: {res.get('bakiye')} KP | Güvenilirlik: {res.get('guvenilirlik')}{atama_str}",
                "success"
            )
        else:
            kod = res.get("kod")
            aciklama = HATA_ACIKLAMALARI.get(kod, "Bilinmeyen hata.")
            self._eylem_geri_bildirim_yaz(f"[RED: {kod}] {aciklama}", "error")

    def _hizli_saat_ilerlet(self, delta_dk: int) -> None:
        yeni = self.motor.saat + timedelta(minutes=delta_dk)
        self._saat_ilerlet_uygula(format_zaman(yeni))

    def _ozel_saat_ilerlet_uygula(self) -> None:
        zaman_str = self.cb_hedef_saat.get().strip()
        if not zaman_str:
            return
        self._saat_ilerlet_uygula(zaman_str)

    def _saat_ilerlet_uygula(self, zaman_str: str) -> None:
        res = self._komut_calistir({"komut": "saat", "zaman": zaman_str})

        if res.get("durum") == "RED":
            kod = res.get("kod")
            aciklama = HATA_ACIKLAMALARI.get(kod, "Saat geriye alınamaz.")
            self._etiket_durum_yaz(self.lbl_saat_olay_bildirimi, f"[RED: {kod}] {aciklama}", "error")
            return

        olaylar = res.get("olaylar", [])
        if not olaylar:
            self._etiket_durum_yaz(
                self.lbl_saat_olay_bildirimi,
                f"[TAMAM] Simülasyon saati {zaman_str} anına ilerletildi (Bu aralıkta gerçekleşen olay yok).",
                "info",
            )
            return

        parcalar = []
        for ol in olaylar:
            tur = ol.get("tur")
            z = ol.get("zaman")
            if tur == "HAFTALIK_SIFIRLAMA":
                parcalar.append(f"[{z}] HAFTALIK_SIFIRLAMA")
            elif tur == "TAMAMLANDI":
                parcalar.append(f"[{z}] {ol.get('rezervasyon')} TAMAMLANDI (Kul:{ol.get('kullanici')}, Güv:{ol.get('guvenilirlik')})")
            elif tur == "GELMEDI":
                parcalar.append(f"[{z}] {ol.get('rezervasyon')} GELMEDI (Kul:{ol.get('kullanici')}, Güv:{ol.get('guvenilirlik')})")
            elif tur == "OTOMATIK_ATAMA":
                parcalar.append(f"[{z}] OTOMATIK_ATAMA: {ol.get('bekleme')}->{ol.get('rezervasyon')} (Kul:{ol.get('kullanici')}, Ücret:{ol.get('ucret')}KP, Bakiye:{ol.get('bakiye')}KP)")

        self._etiket_durum_yaz(
            self.lbl_saat_olay_bildirimi,
            f"[TAMAM] Saat {zaman_str} ({len(olaylar)} olay): " + " | ".join(parcalar),
            "success",
        )

    def _talep_red_goster(self, cmd: dict[str, Any], kod: Optional[str]) -> None:
        aciklama = HATA_ACIKLAMALARI.get(kod, "")
        self._etiket_durum_yaz(self.lbl_sonuc_durum, f"[RED: {kod}]\n{aciklama}", "error")
        if kod in ("KESISME", "HAZIRLIK_IHLALI"):
            self.son_red_edilen_talep = cmd
            self.btn_hizli_bekleme.pack(fill=tk.X, pady=(6, 0))
        else:
            self.son_red_edilen_talep = None
            self.btn_hizli_bekleme.pack_forget()

    def _fiyat_hesapla(self) -> None:
        kullanici = self.cb_talep_kullanici.get()
        kaynak = self.cb_talep_kaynak.get()
        tarih = self.ent_talep_tarih.get().strip()
        bas = self.cb_talep_bas.get().strip()
        bit = self.cb_talep_bit.get().strip()

        cmd = {
            "komut": "fiyat",
            "kullanici": kullanici,
            "kaynak": kaynak,
            "baslangic": f"{tarih}T{bas}",
            "bitis": f"{tarih}T{bit}",
        }
        res = self._komut_calistir(cmd)
        if res.get("durum") == "TAMAM":
            ucret = res.get("ucret")
            self._etiket_durum_yaz(
                self.lbl_sonuc_durum,
                f"[TAMAM] Hesaplanan Fiyat: {ucret} KP\n(Durum değişmedi, onaylamak için 'Rezervasyon Yap' butonuna basın)",
                "success",
            )
            self.btn_hizli_bekleme.pack_forget()
        else:
            self._talep_red_goster(cmd, res.get("kod"))

    def _rezervasyon_gonder(self) -> None:
        kullanici = self.cb_talep_kullanici.get()
        kaynak = self.cb_talep_kaynak.get()
        tarih = self.ent_talep_tarih.get().strip()
        bas = self.cb_talep_bas.get().strip()
        bit = self.cb_talep_bit.get().strip()

        cmd = {
            "komut": "rezervasyon",
            "kullanici": kullanici,
            "kaynak": kaynak,
            "baslangic": f"{tarih}T{bas}",
            "bitis": f"{tarih}T{bit}",
        }
        res = self._komut_calistir(cmd)

        if res.get("durum") == "TAMAM":
            self.son_red_edilen_talep = None
            self.btn_hizli_bekleme.pack_forget()
            r_id = res.get("rezervasyon_id")
            ucret = res.get("ucret")
            bakiye = res.get("bakiye")
            self._etiket_durum_yaz(
                self.lbl_sonuc_durum,
                f"[TAMAM] REZERVASYON ONAYLANDI: {r_id}\nÜcret: {ucret} KP | Yeni Bakiye: {bakiye} KP",
                "success",
            )
            self.secili_rezervasyon = {"id": r_id, "kaynak": kaynak}
            self._eylem_butonlarini_guncelle()
        else:
            self._talep_red_goster(cmd, res.get("kod"))

    def _bekleme_komutu_gonder(self, cmd: dict[str, Any]) -> None:
        res = self._komut_calistir(cmd)
        if res.get("durum") == "TAMAM":
            b_id = res.get("bekleme_id")
            sira = res.get("sira")
            self.btn_hizli_bekleme.pack_forget()
            self._etiket_durum_yaz(
                self.lbl_sonuc_durum,
                f"[TAMAM] BEKLEME KAYDI AÇILDI: {b_id}\nKaynaktaki Sıranız: {sira}",
                "primary",
            )
        else:
            kod = res.get("kod")
            aciklama = HATA_ACIKLAMALARI.get(kod, "")
            self._etiket_durum_yaz(self.lbl_sonuc_durum, f"[RED: {kod}]\n{aciklama}", "error")

    def _hizli_bekleme_ac(self) -> None:
        if not self.son_red_edilen_talep:
            return
        cmd = {
            "komut": "bekleme",
            "kullanici": self.son_red_edilen_talep["kullanici"],
            "kaynak": self.son_red_edilen_talep["kaynak"],
            "baslangic": self.son_red_edilen_talep["baslangic"],
            "bitis": self.son_red_edilen_talep["bitis"],
        }
        self._bekleme_komutu_gonder(cmd)

    def _talep_bekleme_gonder(self) -> None:
        kullanici = self.cb_talep_kullanici.get().strip()
        kaynak = self.cb_talep_kaynak.get().strip()
        tarih = self.ent_talep_tarih.get().strip()
        bas = self.cb_talep_bas.get().strip()
        bit = self.cb_talep_bit.get().strip()

        cmd = {
            "komut": "bekleme",
            "kullanici": kullanici,
            "kaynak": kaynak,
            "baslangic": f"{tarih}T{bas}",
            "bitis": f"{tarih}T{bit}",
        }
        self._bekleme_komutu_gonder(cmd)

    def _kullanici_sorgu_gonder(self) -> None:
        uid = self.cb_panel_kullanici.get().strip()
        if not uid and self.motor.kullanicilar:
            uid = list(self.motor.kullanicilar.keys())[0]
        if not uid:
            return

        cmd = {
            "komut": "sorgu",
            "tur": "kullanici",
            "id": uid,
        }
        res = self._komut_calistir(cmd)
        if res.get("durum") == "TAMAM":
            self._eylem_geri_bildirim_yaz(
                f"[TAMAM] Kullanıcı '{uid}' sorgulandı: Bakiye {res.get('bakiye')} KP, Güvenilirlik {res.get('guvenilirlik')}, {len(res.get('rezervasyonlar', []))} rezervasyon.",
                "info"
            )

    def _kaynak_sorgu_gonder(self) -> None:
        kid = ""
        if hasattr(self, "cb_takvim_kaynak"):
            kid = self.cb_takvim_kaynak.get().strip()
        if not kid and self.secili_rezervasyon:
            kid = self.secili_rezervasyon.get("kaynak", "")
        if not kid:
            kid = self.cb_talep_kaynak.get().strip()
        if not kid and self.motor.kaynaklar:
            kid = list(self.motor.kaynaklar.keys())[0]
        if not kid:
            return

        gun_str = self.goruntulenen_gun.strftime("%Y-%m-%d")
        cmd = {
            "komut": "sorgu",
            "tur": "kaynak",
            "id": kid,
            "gun": gun_str,
        }
        res = self._komut_calistir(cmd)
        if res.get("durum") == "TAMAM":
            doluluk = res.get("doluluk", [])
            self._eylem_geri_bildirim_yaz(
                f"[TAMAM] Kaynak '{kid}' ({gun_str}) sorgulandı: {len(doluluk)} doluluk/bakım kaydı bulundu.",
                "info"
            )

    def _paket_fiyat_hesapla(self) -> None:
        kullanici = self.cb_talep_kullanici.get()
        if not self.paket_kalem_satirlari:
            return

        toplam_ucret = 0
        kalem_rapor = []
        tum_gecerli = True

        for idx, k in enumerate(self.paket_kalem_satirlari):
            kaynak = k["kaynak"].get().strip()
            tarih = k["tarih"].get().strip()
            bas = k["bas"].get().strip()
            bit = k["bit"].get().strip()
            cmd = {
                "komut": "fiyat",
                "kullanici": kullanici,
                "kaynak": kaynak,
                "baslangic": f"{tarih}T{bas}",
                "bitis": f"{tarih}T{bit}",
            }
            res = self._komut_calistir(cmd)
            if res.get("durum") == "TAMAM":
                u = res.get("ucret", 0)
                toplam_ucret += u
                kalem_rapor.append(f"Kalem {idx+1} ({kaynak}): {u} KP")
                self._etiket_durum_yaz(k["durum_lbl"], f"TAMAM - Ücret: {u} KP", "success")
            else:
                tum_gecerli = False
                kod = res.get("kod")
                aciklama = HATA_ACIKLAMALARI.get(kod, "")
                kalem_rapor.append(f"Kalem {idx+1} ({kaynak}): RED ({kod})")
                self._etiket_durum_yaz(k["durum_lbl"], f"RED: {kod} - {aciklama}", "error")

        detay = " | ".join(kalem_rapor)
        if tum_gecerli:
            self._etiket_durum_yaz(
                self.lbl_sonuc_durum,
                f"[TAMAM] Paket Tahmini Toplam: {toplam_ucret} KP\n{detay}",
                "success",
            )
        else:
            self._etiket_durum_yaz(
                self.lbl_sonuc_durum,
                f"[RED] Bazı Kalemler Geçersiz:\n{detay}",
                "error",
            )
        self.btn_hizli_bekleme.pack_forget()

    def _paket_gonder(self) -> None:
        kullanici = self.cb_talep_kullanici.get()
        kalemler = []
        for k in self.paket_kalem_satirlari:
            kaynak = k["kaynak"].get().strip()
            tarih = k["tarih"].get().strip()
            bas = k["bas"].get().strip()
            bit = k["bit"].get().strip()
            self._etiket_durum_yaz(k["durum_lbl"], "", "text_muted")
            kalemler.append({
                "kaynak": kaynak,
                "baslangic": f"{tarih}T{bas}",
                "bitis": f"{tarih}T{bit}",
            })

        cmd = {
            "komut": "paket",
            "kullanici": kullanici,
            "kalemler": kalemler,
        }
        res = self._komut_calistir(cmd)

        if res.get("durum") == "TAMAM":
            p_id = res.get("paket_id")
            rez_list = res.get("rezervasyonlar", [])
            ucret_list = res.get("ucretler", [])
            rezler = ", ".join(rez_list)
            toplam = res.get("toplam")
            bakiye = res.get("bakiye")
            for idx, k in enumerate(self.paket_kalem_satirlari):
                if idx < len(rez_list):
                    self._etiket_durum_yaz(
                        k["durum_lbl"],
                        f"TAMAM -> {rez_list[idx]} ({ucret_list[idx]} KP)",
                        "success",
                    )
            self._etiket_durum_yaz(
                self.lbl_sonuc_durum,
                f"[TAMAM] PAKET ONAYLANDI: {p_id}\nRezervasyonlar: [{rezler}]\nToplam Ücret: {toplam} KP | Yeni Bakiye: {bakiye} KP",
                "success",
            )
        else:
            kod = res.get("kod")
            aciklama = HATA_ACIKLAMALARI.get(kod, "")
            detay = f"[RED: {kod}]\n{aciklama}\n"
            kalem_sonuclari = res.get("kalemler", [])
            if kalem_sonuclari:
                detay += "\nKalem Sonuçları:\n"
                for item in kalem_sonuclari:
                    s_idx = item.get("sira", 0)
                    s = s_idx + 1
                    d = item.get("durum")
                    k_hata = item.get("kod", "")
                    h_acik = f" - {HATA_ACIKLAMALARI.get(k_hata, '')}" if k_hata else ""
                    detay += f"  Kalem {s}: {d} {k_hata}{h_acik}\n"
                    if 0 <= s_idx < len(self.paket_kalem_satirlari):
                        if d == "TAMAM":
                            self._etiket_durum_yaz(
                                self.paket_kalem_satirlari[s_idx]["durum_lbl"],
                                "Kalem Doğrulaması: TAMAM",
                                "success",
                            )
                        else:
                            self._etiket_durum_yaz(
                                self.paket_kalem_satirlari[s_idx]["durum_lbl"],
                                f"RED: {k_hata}{h_acik}",
                                "error",
                            )

            self._etiket_durum_yaz(self.lbl_sonuc_durum, detay.strip(), "error")

    def _kullanici_ekle_gonder(self) -> None:
        uid = self.ent_ekle_uid.get().strip()
        ad = self.ent_ekle_uad.get().strip()
        rol = self.cb_ekle_urol.get().strip()
        bak_str = self.ent_ekle_ubakiye.get().strip()
        guv_str = self.ent_ekle_uguv.get().strip()
        sertifikalar = [s for s, var in self.vars_ekle_sert.items() if var.get()]

        try:
            bakiye: Any = int(bak_str)
        except ValueError:
            try:
                bakiye = float(bak_str)
            except ValueError:
                bakiye = bak_str

        try:
            guvenilirlik: Any = int(guv_str)
        except ValueError:
            try:
                guvenilirlik = float(guv_str)
            except ValueError:
                guvenilirlik = guv_str

        cmd = {
            "komut": "kullanici_ekle",
            "id": uid,
            "ad": ad,
            "rol": rol,
            "sertifikalar": sertifikalar,
            "bakiye": bakiye,
            "guvenilirlik": guvenilirlik,
        }
        res = self._komut_calistir(cmd)
        if res.get("durum") == "TAMAM":
            self._etiket_durum_yaz(
                self.lbl_ekle_kullanici_sonuc,
                f"[TAMAM] Kullanıcı '{uid}' ({ad}) başarıyla eklendi.",
                "success",
            )
            self.ent_ekle_uid.delete(0, tk.END)
            self.ent_ekle_uad.delete(0, tk.END)
            for var in self.vars_ekle_sert.values():
                var.set(False)
            self.cb_talep_kullanici.set(uid)
            self.cb_panel_kullanici.set(uid)
            self._kullanici_paneli_guncelle()
        else:
            kod = res.get("kod")
            aciklama = HATA_ACIKLAMALARI.get(kod, "")
            self._etiket_durum_yaz(
                self.lbl_ekle_kullanici_sonuc,
                f"[RED: {kod}] {aciklama}",
                "error",
            )

    def _kaynak_ekle_gonder(self) -> None:
        kid = self.ent_ekle_rid.get().strip()
        ad = self.ent_ekle_rad.get().strip()
        tur = self.cb_ekle_rtur.get().strip()
        izinli_roller = [r for r, var in self.vars_ekle_roller.items() if var.get()]

        cmd = {
            "komut": "kaynak_ekle",
            "id": kid,
            "ad": ad,
            "tur": tur,
            "izinli_roller": izinli_roller,
        }
        res = self._komut_calistir(cmd)
        if res.get("durum") == "TAMAM":
            self._etiket_durum_yaz(
                self.lbl_ekle_kaynak_sonuc,
                f"[TAMAM] Kaynak '{kid}' ({ad}) başarıyla eklendi ve takvime yansıtıldı.",
                "success",
            )
            self.ent_ekle_rid.delete(0, tk.END)
            self.ent_ekle_rad.delete(0, tk.END)
            self.cb_talep_kaynak.set(kid)
        else:
            kod = res.get("kod")
            aciklama = HATA_ACIKLAMALARI.get(kod, "")
            self._etiket_durum_yaz(
                self.lbl_ekle_kaynak_sonuc,
                f"[RED: {kod}] {aciklama}",
                "error",
            )


def main() -> None:
    app = MasaustuUygulamasi()
    app.mainloop()


if __name__ == "__main__":
    main()
