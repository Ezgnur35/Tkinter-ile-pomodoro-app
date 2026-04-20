"""
Tkinter Pomodoro & Odak Zamanlayıcı

 Giriş/kayıt ekranı, menü, timer kısmı ,çalışmayı kaydetme kısmı

"""

from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import hashlib
import sys
import os
from datetime import datetime
from PIL import Image, ImageTk, ImageSequence, ImageDraw


UYGULAMA_BASLIK = "Pomodoro & Odak Zamanlayıcı"
VERITABANI_ADI = "pomodoro.db"


ANA_RENK = "#FFF8F0"
IKINCI_RENK = "#FFE4D6"
VURGU_RENK = "#FFB088"
YAZI_RENK = "#8B4513"
BUTON_RENK = "#FFD4B8"


def init_db():

    conn = sqlite3.connect(VERITABANI_ADI)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            work_minutes INTEGER NOT NULL DEFAULT 0,
            break_minutes INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )


    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='work_sessions'")
    tablo_var = cur.fetchone()

    if not tablo_var:

        cur.execute(
            """
            CREATE TABLE work_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                duration_minutes INTEGER NOT NULL DEFAULT 0,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                note TEXT,
                created_date TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
    else:

        cur.execute("PRAGMA table_info(work_sessions)")
        sutunlar = [sutun[1] for sutun in cur.fetchall()]

        if 'duration_seconds' not in sutunlar:
            try:
                cur.execute("ALTER TABLE work_sessions ADD COLUMN duration_seconds INTEGER NOT NULL DEFAULT 0")
                print(" duration_seconds sütunu eklendi!")
            except Exception as hata:
                print(f"Sütun ekleme hatası: {hata}")

    conn.commit()
    conn.close()


def sifre_hash(sifre: str) -> str:

    return hashlib.sha256(sifre.encode("utf-8")).hexdigest()


def kullanici_kaydet(kullanici_adi: str, sifre: str):

    if not kullanici_adi or not sifre:
        messagebox.showwarning("Uyarı", "Kullanıcı adı ve şifre boş olamaz.")
        return False

    if len(kullanici_adi) < 3:
        messagebox.showwarning("Uyarı", "Kullanıcı adı en az 3 karakter olmalıdır.")
        return False

    if len(sifre) < 4:
        messagebox.showwarning("Uyarı", "Şifre en az 4 karakter olmalıdır.")
        return False

    conn = sqlite3.connect(VERITABANI_ADI)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (kullanici_adi, sifre_hash(sifre)),
        )
        conn.commit()
        messagebox.showinfo("Başarılı", "Kayıt tamamlandı! Giriş yapabilirsiniz. ")
        return True
    except sqlite3.IntegrityError:
        messagebox.showerror("Hata", "Bu kullanıcı adı zaten kayıtlı.")
        return False
    except Exception as hata:
        messagebox.showerror("Hata", f"Bir hata oluştu: {hata}")
        return False
    finally:
        conn.close()


def giris_kontrol(kullanici_adi: str, sifre: str):

    if not kullanici_adi or not sifre:
        return None

    conn = sqlite3.connect(VERITABANI_ADI)
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, password_hash FROM users WHERE username = ?", (kullanici_adi,))
        satir = cur.fetchone()

        if not satir:
            return None

        kullanici_id, sifre_ozet = satir
        if sifre_ozet == sifre_hash(sifre):
            return {"id": kullanici_id, "isim": kullanici_adi}
        return None
    except Exception as hata:
        print(f"Giriş hatası: {hata}")
        return None
    finally:
        conn.close()


class PomodoroUygulama:


    def __init__(self, pencere: Tk):

        self.pencere = pencere
        self.pencere.title(UYGULAMA_BASLIK)


        pencere_genislik = 650
        pencere_yukseklik = 850
        ekran_genislik = self.pencere.winfo_screenwidth()
        ekran_yukseklik = self.pencere.winfo_screenheight()
        x = (ekran_genislik - pencere_genislik) // 2
        y = (ekran_yukseklik - pencere_yukseklik) // 2

        self.pencere.geometry(f"{pencere_genislik}x{pencere_yukseklik}+{x}+{y}")
        self.pencere.resizable(False, False)
        self.pencere.configure(bg=ANA_RENK)


        self.giris_yapan_kullanici = None


        self.kalan_saniye = 0
        self.toplam_saniye = 0
        self.baslangic_saniye = 0
        self.zamanlayici_calisiyor = False
        self.zamanlayici_id = None
        self.calisma_modu = True


        self.mola_kareleri = []
        self.study_kareleri = []
        self.mevcut_kareler = []
        self.mevcut_kare_index = 0
        self.animasyon_id = None
        self.gif_yuklendi = False


        self.gif_yukle()


        self.menu_ekrani_goster()

    def gif_yukle(self):

        try:
            if getattr(sys, 'frozen', False):
                program_klasoru = os.path.dirname(sys.executable)
            else:
                program_klasoru = os.path.dirname(os.path.abspath(__file__))

            mola_gif_yolu = os.path.join(program_klasoru, "assets", "mola_tavşanı.gif")
            study_gif_yolu = os.path.join(program_klasoru, "assets", "study_tavşan.gif")


            if os.path.exists(mola_gif_yolu):
                mola_gif = Image.open(mola_gif_yolu)
                for kare in ImageSequence.Iterator(mola_gif):
                    kare_kopyasi = kare.copy().convert('RGBA')
                    kare_kopyasi = kare_kopyasi.resize((120, 120), Image.Resampling.LANCZOS)

                    kare_kopyasi = self.yuvarlak_yap(kare_kopyasi, 120)
                    self.mola_kareleri.append(ImageTk.PhotoImage(kare_kopyasi))


            if os.path.exists(study_gif_yolu):
                study_gif = Image.open(study_gif_yolu)
                for kare in ImageSequence.Iterator(study_gif):
                    kare_kopyasi = kare.copy().convert('RGBA')
                    kare_kopyasi = kare_kopyasi.resize((120, 120), Image.Resampling.LANCZOS)

                    self.study_kareleri.append(ImageTk.PhotoImage(kare_kopyasi))

            if self.mola_kareleri and self.study_kareleri:
                self.gif_yuklendi = True
                print(":) GIF dosyaları yüklendi!")
            else:
                print("!!!! GIF bulunamadı, emoji kullanılacak.")

        except Exception as hata:
            print(f"!!! GIF yükleme hatası: {hata}")
            self.gif_yuklendi = False

    def yuvarlak_yap(self, resim, boyut):

        from PIL import ImageDraw


        maske = Image.new('L', (boyut, boyut), 0)
        ciz = ImageDraw.Draw(maske)
        ciz.ellipse((0, 0, boyut, boyut), fill=255)


        yuvarlak_resim = Image.new('RGBA', (boyut, boyut), (0, 0, 0, 0))
        yuvarlak_resim.paste(resim, (0, 0))
        yuvarlak_resim.putalpha(maske)

        return yuvarlak_resim

    def mola_tavsancigi_goster(self):

        if self.animasyon_id:
            self.pencere.after_cancel(self.animasyon_id)
            self.animasyon_id = None

        if self.gif_yuklendi and self.mola_kareleri:
            self.mevcut_kareler = self.mola_kareleri
            self.mevcut_kare_index = 0
            self.gif_animasyon_goster()
        else:
            self.tavsancik.config(image="", text="😴", font=("Arial", 50))

    def study_tavsancigini_goster(self):

        if self.animasyon_id:
            self.pencere.after_cancel(self.animasyon_id)
            self.animasyon_id = None

        if self.gif_yuklendi and self.study_kareleri:
            self.mevcut_kareler = self.study_kareleri
            self.mevcut_kare_index = 0
            self.gif_animasyon_goster()
        else:
            self.tavsancik.config(image="", text="💪", font=("Arial", 50))

    def gif_animasyon_goster(self):

        if not self.mevcut_kareler:
            return

        kare = self.mevcut_kareler[self.mevcut_kare_index]
        self.tavsancik.config(image=kare, text="")

        self.mevcut_kare_index = (self.mevcut_kare_index + 1) % len(self.mevcut_kareler)
        self.animasyon_id = self.pencere.after(100, self.gif_animasyon_goster)

    def animasyon_durdur(self):

        if self.animasyon_id:
            self.pencere.after_cancel(self.animasyon_id)
            self.animasyon_id = None

    def menu_ekrani_goster(self):

        for widget in self.pencere.winfo_children():
            widget.destroy()

        self.animasyon_durdur()


        canvas_wrapper = Canvas(self.pencere, bg=ANA_RENK, highlightthickness=0)
        canvas_wrapper.pack(fill="both", expand=True)


        ana_cerceve = Frame(canvas_wrapper, bg=ANA_RENK)


        self.pencere.update_idletasks()
        canvas_wrapper.create_window(
            self.pencere.winfo_width() // 2,
            self.pencere.winfo_height() // 2,
            window=ana_cerceve,
            anchor="center"
        )

        Label(
            ana_cerceve,
            text="🐰 Pomodoro & Odak Zmanlayıcı 🐰",
            font=("Arial", 22, "bold"),
            bg=ANA_RENK,
            fg=YAZI_RENK,
        ).pack(pady=20)

        Label(
            ana_cerceve,
            text="🐰",
            font=("Arial", 80),
            bg=ANA_RENK,
        ).pack(pady=10)


        aciklama_cerceve = Frame(ana_cerceve, bg=IKINCI_RENK, padx=30, pady=20)
        aciklama_cerceve.pack(pady=20, padx=40)

        Label(
            aciklama_cerceve,
            text=" -Proje Hakkında-",
            font=("Arial", 14, "bold"),
            bg=IKINCI_RENK,
            fg=YAZI_RENK,
        ).pack(pady=(0, 10))

        aciklama_text = """
Pomodoro Tekniği ile Çalışma & Odak Zamanlayıcı Uygulaması

✨ Özellikler:
• Kullanıcı kayıt ve giriş sistemi
• Zamanlayıcı ile odaklanmış çalışma
• Çalışma kayıtlarını saklama
• Geçmiş çalışmaları görüntüleme ve silebilme
• Animasyonlu tatlı arayüz

🎯 Amacımız:
Pomodoro tekniği ile verimli çalışmanızı
desteklemek ve çalışma sürenizi kayıt altına almak.

        """

        Label(
            aciklama_cerceve,
            text=aciklama_text,
            font=("Arial", 10),
            bg=IKINCI_RENK,
            fg=YAZI_RENK,
            justify="left",
        ).pack()


        Button(
            ana_cerceve,
            text="🚀 Başla",
            font=("Arial", 14, "bold"),
            bg=VURGU_RENK,
            fg="white",
            width=20,
            cursor="hand2",
            command=self.giris_ekrani_goster,
        ).pack(pady=20)


        Label(
            ana_cerceve,
            text="Ezginur Ünver\nTüm hakları saklıdır © 2025",
            font=("Arial", 9),
            bg=ANA_RENK,
            fg=YAZI_RENK,
        ).pack(pady=10)

    def giris_ekrani_goster(self):

        for widget in self.pencere.winfo_children():
            widget.destroy()

        self.animasyon_durdur()


        canvas_wrapper = Canvas(self.pencere, bg=ANA_RENK, highlightthickness=0)
        canvas_wrapper.pack(fill="both", expand=True)


        ana_cerceve = Frame(canvas_wrapper, bg=ANA_RENK)


        self.pencere.update_idletasks()
        canvas_wrapper.create_window(
            self.pencere.winfo_width() // 2,
            self.pencere.winfo_height() // 2,
            window=ana_cerceve,
            anchor="center"
        )

        Label(
            ana_cerceve,
            text="🐰 Pomodoro & Odak Zamanlayıcı 🐰",
            font=("Arial", 20, "bold"),
            bg=ANA_RENK,
            fg=YAZI_RENK,
        ).pack(pady=20)

        Label(
            ana_cerceve,
            text="🐰",
            font=("Arial", 80),
            bg=ANA_RENK,
        ).pack(pady=10)

        giris_cerceve = Frame(ana_cerceve, bg=IKINCI_RENK, padx=30, pady=20)
        giris_cerceve.pack(pady=20, padx=40)

        Label(
            giris_cerceve,
            text="Kullanıcı Adı:",
            font=("Arial", 11),
            bg=IKINCI_RENK,
            fg=YAZI_RENK,
        ).grid(row=0, column=0, sticky="w", pady=5)

        self.giris_kullanici_adi = Entry(
            giris_cerceve,
            font=("Arial", 11),
            width=25,
            bg="white",
        )
        self.giris_kullanici_adi.grid(row=0, column=1, padx=10, pady=5)

        Label(
            giris_cerceve,
            text="Şifre:",
            font=("Arial", 11),
            bg=IKINCI_RENK,
            fg=YAZI_RENK,
        ).grid(row=1, column=0, sticky="w", pady=5)

        self.giris_sifre = Entry(
            giris_cerceve,
            font=("Arial", 11),
            width=25,
            show="●",
            bg="white",
        )
        self.giris_sifre.grid(row=1, column=1, padx=10, pady=5)

        buton_cerceve = Frame(giris_cerceve, bg=IKINCI_RENK)
        buton_cerceve.grid(row=2, column=0, columnspan=2, pady=15)

        Button(
            buton_cerceve,
            text="Giriş Yap",
            font=("Arial", 11, "bold"),
            bg=VURGU_RENK,
            fg="white",
            width=12,
            cursor="hand2",
            command=self.giris_yap_islem,
        ).pack(side="left", padx=5)

        Button(
            buton_cerceve,
            text="Kayıt Ol",
            font=("Arial", 11),
            bg=BUTON_RENK,
            fg=YAZI_RENK,
            width=12,
            cursor="hand2",
            command=self.kayit_ekrani_goster,
        ).pack(side="left", padx=5)

        Label(
            ana_cerceve,
            text="Ezginur Ünver\nTüm hakları saklıdır © 2025",
            font=("Arial", 9),
            bg=ANA_RENK,
            fg=YAZI_RENK,
        ).pack(pady=20)

    def kayit_ekrani_goster(self):

        for widget in self.pencere.winfo_children():
            widget.destroy()

        self.animasyon_durdur()


        canvas_wrapper = Canvas(self.pencere, bg=ANA_RENK, highlightthickness=0)
        canvas_wrapper.pack(fill="both", expand=True)


        ana_cerceve = Frame(canvas_wrapper, bg=ANA_RENK)


        self.pencere.update_idletasks()
        canvas_wrapper.create_window(
            self.pencere.winfo_width() // 2,
            self.pencere.winfo_height() // 2,
            window=ana_cerceve,
            anchor="center"
        )

        Label(
            ana_cerceve,
            text="🐰 Yeni Hesap Oluştur 🐰",
            font=("Arial", 20, "bold"),
            bg=ANA_RENK,
            fg=YAZI_RENK,
        ).pack(pady=20)

        Label(
            ana_cerceve,
            text="🐰",
            font=("Arial", 80),
            bg=ANA_RENK,
        ).pack(pady=10)

        kayit_cerceve = Frame(ana_cerceve, bg=IKINCI_RENK, padx=30, pady=20)
        kayit_cerceve.pack(pady=20, padx=40)

        Label(
            kayit_cerceve,
            text="Kullanıcı Adı (en az 3 karakter)",
            font=("Arial", 10),
            bg=IKINCI_RENK,
            fg=YAZI_RENK,
        ).grid(row=0, column=0, sticky="w", pady=5)

        self.kayit_kullanici_adi = Entry(
            kayit_cerceve,
            font=("Arial", 11),
            width=25,
            bg="white",
        )
        self.kayit_kullanici_adi.grid(row=0, column=1, padx=10, pady=5)

        Label(
            kayit_cerceve,
            text="Şifre (en az 4 karakter)",
            font=("Arial", 10),
            bg=IKINCI_RENK,
            fg=YAZI_RENK,
        ).grid(row=1, column=0, sticky="w", pady=5)

        self.kayit_sifre = Entry(
            kayit_cerceve,
            font=("Arial", 11),
            width=25,
            show="●",
            bg="white",
        )
        self.kayit_sifre.grid(row=1, column=1, padx=10, pady=5)

        buton_cerceve = Frame(kayit_cerceve, bg=IKINCI_RENK)
        buton_cerceve.grid(row=2, column=0, columnspan=2, pady=15)

        Button(
            buton_cerceve,
            text="Kayıt Ol",
            font=("Arial", 11, "bold"),
            bg=VURGU_RENK,
            fg="white",
            width=12,
            cursor="hand2",
            command=self.kayit_ol_islem,
        ).pack(side="left", padx=5)

        Button(
            buton_cerceve,
            text="Geri Dön",
            font=("Arial", 11),
            bg=BUTON_RENK,
            fg=YAZI_RENK,
            width=12,
            cursor="hand2",
            command=self.giris_ekrani_goster,
        ).pack(side="left", padx=5)

        Label(
            ana_cerceve,
            text="Ezginur Ünver\nTüm hakları saklıdır © 2025",
            font=("Arial", 9),
            bg=ANA_RENK,
            fg=YAZI_RENK,
        ).pack(pady=10)

    def giris_yap_islem(self):

        kullanici = self.giris_kullanici_adi.get().strip()
        sifre = self.giris_sifre.get()

        if not kullanici or not sifre:
            messagebox.showwarning("Uyarı", "Lütfen tüm alanları doldurun.")
            return

        dogrulama = giris_kontrol(kullanici, sifre)

        if dogrulama:
            self.giris_yapan_kullanici = dogrulama
            messagebox.showinfo("Hoş geldiniz", f"Merhaba {dogrulama['isim']}! 🐰")
            self.ana_ekrani_goster()
        else:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre hatalı.")

    def kayit_ol_islem(self):

        kullanici = self.kayit_kullanici_adi.get().strip()
        sifre = self.kayit_sifre.get()

        if kullanici_kaydet(kullanici, sifre):
            self.giris_ekrani_goster()

    def ana_ekrani_goster(self):

        for widget in self.pencere.winfo_children():
            widget.destroy()


        canvas_wrapper = Canvas(self.pencere, bg=ANA_RENK, highlightthickness=0)
        canvas_wrapper.pack(fill="both", expand=True)


        ana_cerceve = Frame(canvas_wrapper, bg=ANA_RENK)


        self.pencere.update_idletasks()
        canvas_wrapper.create_window(
            self.pencere.winfo_width() // 2,
            self.pencere.winfo_height() // 2,
            window=ana_cerceve,
            anchor="center"
        )

        Label(
            ana_cerceve,
            text=f"Hoş Geldin, {self.giris_yapan_kullanici['isim']}! 🐰",
            font=("Arial", 18, "bold"),
            bg=ANA_RENK,
            fg=YAZI_RENK,
        ).pack(pady=10)


        self.canvas_cerceve = Frame(ana_cerceve, bg=ANA_RENK)
        self.canvas_cerceve.pack(pady=15)

        self.canvas = Canvas(
            self.canvas_cerceve,
            width=300,
            height=300,
            bg=ANA_RENK,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.daire_ciz(1.0)

        self.tavsancik = Label(
            self.canvas_cerceve,
            bg=ANA_RENK,
        )
        self.tavsancik.place(in_=self.canvas, relx=0.5, rely=0.5, anchor="center")
        self.mola_tavsancigi_goster()


        sure_cerceve = Frame(ana_cerceve, bg=IKINCI_RENK, padx=20, pady=15)
        sure_cerceve.pack(pady=10)

        Label(
            sure_cerceve,
            text="Çalışma Süresi (dakika):",
            font=("Arial", 11),
            bg=IKINCI_RENK,
            fg=YAZI_RENK,
        ).pack(side="left", padx=5)

        self.sure_giris = Entry(
            sure_cerceve,
            font=("Arial", 11),
            width=10,
            bg="white",
        )
        self.sure_giris.insert(0, "25")
        self.sure_giris.pack(side="left", padx=5)


        self.zaman_etiketi = Label(
            ana_cerceve,
            text="25:00",
            font=("Arial", 36, "bold"),
            bg=ANA_RENK,
            fg=YAZI_RENK,
        )
        self.zaman_etiketi.pack(pady=10)


        self.durum_etiketi = Label(
            ana_cerceve,
            text="Başlamak için butona bas! 🚀",
            font=("Arial", 11),
            bg=ANA_RENK,
            fg=YAZI_RENK,
        )
        self.durum_etiketi.pack(pady=5)


        buton_cerceve = Frame(ana_cerceve, bg=ANA_RENK)
        buton_cerceve.pack(pady=10)

        Button(
            buton_cerceve,
            text="▶ Başlat",
            font=("Arial", 10, "bold"),
            bg=VURGU_RENK,
            fg="white",
            width=9,
            cursor="hand2",
            command=self.baslat,
        ).grid(row=0, column=0, padx=3)

        Button(
            buton_cerceve,
            text="⏸ Durdur",
            font=("Arial", 10),
            bg=BUTON_RENK,
            fg=YAZI_RENK,
            width=9,
            cursor="hand2",
            command=self.durdur,
        ).grid(row=0, column=1, padx=3)

        Button(
            buton_cerceve,
            text="▶▶ Devam",
            font=("Arial", 10),
            bg=BUTON_RENK,
            fg=YAZI_RENK,
            width=9,
            cursor="hand2",
            command=self.devam_et,
        ).grid(row=0, column=2, padx=3)

        Button(
            buton_cerceve,
            text="↺ Sıfırla",
            font=("Arial", 10),
            bg="#FFE4E4",
            fg=YAZI_RENK,
            width=9,
            cursor="hand2",
            command=self.sifirla,
        ).grid(row=0, column=3, padx=3)


        Button(
            ana_cerceve,
            text="💾 Çalışmayı Kaydet",
            font=("Arial", 11, "bold"),
            bg="#90EE90",
            fg=YAZI_RENK,
            cursor="hand2",
            command=self.kayit_penceresi_ac,
        ).pack(pady=10)


        kayit_cerceve = Frame(ana_cerceve, bg=IKINCI_RENK, padx=15, pady=10)
        kayit_cerceve.pack(pady=5, fill="x")

        Label(
            kayit_cerceve,
            text="📚 Geçmiş Kayıtlarım:",
            font=("Arial", 10, "bold"),
            bg=IKINCI_RENK,
            fg=YAZI_RENK,
        ).pack(anchor="w", pady=(0, 5))

        self.kayitlar_combobox = ttk.Combobox(
            kayit_cerceve,
            font=("Arial", 9),
            state="readonly",
            width=50
        )
        self.kayitlar_combobox.pack(fill="x", pady=(0, 10))

        self.kayitlari_yukle()


        Button(
            kayit_cerceve,
            text="🗑️ Seçili Kaydı Sil",
            font=("Arial", 10, "bold"),
            bg="#FF6B6B",
            fg="white",
            cursor="hand2",
            command=self.kayit_sil,
        ).pack(fill="x")


        Button(
            ana_cerceve,
            text="Çıkış Yap",
            font=("Arial", 10),
            bg="#FFF",
            fg=YAZI_RENK,
            cursor="hand2",
            command=self.cikis_yap,
        ).pack(pady=15)

    def kayitlari_yukle(self):

        if not self.giris_yapan_kullanici:
            return

        try:
            conn = sqlite3.connect(VERITABANI_ADI)
            cur = conn.cursor()

            cur.execute(
                """
                SELECT duration_minutes, duration_seconds, note, created_date 
                FROM work_sessions 
                WHERE user_id = ? 
                ORDER BY created_date DESC 
                LIMIT 20
                """,
                (self.giris_yapan_kullanici["id"],)
            )

            kayitlar = cur.fetchall()
            conn.close()

            kayit_listesi = []
            for dakika, saniye, note, tarih in kayitlar:
                try:
                    tarih_obj = datetime.strptime(tarih, "%Y-%m-%d %H:%M:%S")
                    tarih_str = tarih_obj.strftime("%d.%m.%Y")
                    saat_str = tarih_obj.strftime("%H:%M")
                    saat_str = "Saat yok"
                except:
                    tarih_str = "Tarih yok"
                    saat_str = ""

                not_text = note if note else "Not yok"
                sure_text = f"{dakika:02d}:{saniye:02d}"
                kayit_text = f"{sure_text} - {not_text} - {tarih_str} {saat_str}"
                kayit_listesi.append(kayit_text)

            self.kayitlar_combobox['values'] = kayit_listesi if kayit_listesi else ["Henüz kayıt yok"]
            if kayit_listesi:
                self.kayitlar_combobox.current(0)

        except Exception as hata:
            print(f"Kayıt yükleme hatası: {hata}")

    def kayit_penceresi_ac(self):

        gecen_saniye = self.baslangic_saniye - self.kalan_saniye
        gecen_dakika = gecen_saniye // 60
        gecen_saniye_kalan = gecen_saniye % 60

        kayit_pencere = Toplevel(self.pencere)
        kayit_pencere.title("Çalışma Kaydı Ekle")
        kayit_pencere.geometry("450x380")
        kayit_pencere.configure(bg=ANA_RENK)
        kayit_pencere.resizable(False, False)


        kayit_pencere.transient(self.pencere)
        kayit_pencere.grab_set()


        kayit_pencere.update_idletasks()
        x = (kayit_pencere.winfo_screenwidth() // 2) - (450 // 2)
        y = (kayit_pencere.winfo_screenheight() // 2) - (380 // 2)
        kayit_pencere.geometry(f"450x380+{x}+{y}")


        baslik_label = Label(
            kayit_pencere,
            text="📝 Yeni Çalışma Kaydı",
            font=("Arial", 16, "bold"),
            bg=ANA_RENK,
            fg=YAZI_RENK,
        )
        baslik_label.pack(pady=20)


        form_cerceve = Frame(kayit_pencere, bg=IKINCI_RENK, padx=30, pady=20)
        form_cerceve.pack(pady=5, padx=30, fill="x")


        sure_label = Label(
            form_cerceve,
            text=f"⏱️ Geçen Süre: {gecen_dakika:02d}:{gecen_saniye_kalan:02d}",
            font=("Arial", 14, "bold"),
            bg=IKINCI_RENK,
            fg=VURGU_RENK,
        )
        sure_label.pack(pady=15)


        not_baslik = Label(
            form_cerceve,
            text="Not (isteğe bağlı):",
            font=("Arial", 11),
            bg=IKINCI_RENK,
            fg=YAZI_RENK,
        )
        not_baslik.pack(anchor="w", pady=(10, 5))

        not_text = Text(
            form_cerceve,
            font=("Arial", 10),
            width=40,
            height=5,
            bg="white",
            wrap="word",
        )
        not_text.pack(pady=(0, 10))

        def kayit_ekle():

            try:
                not_metni = not_text.get("1.0", "end-1c").strip()

                conn = sqlite3.connect(VERITABANI_ADI)
                cur = conn.cursor()

                simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cur.execute(
                    """
                    INSERT INTO work_sessions (user_id, duration_minutes, duration_seconds, note, created_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (self.giris_yapan_kullanici["id"], gecen_dakika, gecen_saniye_kalan, not_metni, simdi)
                )


                cur.execute(
                    "INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)",
                    (self.giris_yapan_kullanici["id"],)
                )
                cur.execute(
                    "UPDATE user_stats SET work_minutes = work_minutes + ? WHERE user_id = ?",
                    (gecen_dakika, self.giris_yapan_kullanici["id"])
                )

                conn.commit()
                conn.close()

                messagebox.showinfo("Başarılı", f"✅ {gecen_dakika:02d}:{gecen_saniye_kalan:02d} çalışma kaydedildi!")
                kayit_pencere.destroy()

                self.kayitlari_yukle()

            except Exception as hata:
                messagebox.showerror("Hata", f"Kayıt eklenirken hata: {hata}")


        buton_cerceve = Frame(kayit_pencere, bg=ANA_RENK)
        buton_cerceve.pack(pady=20)

        kaydet_buton = Button(
            buton_cerceve,
            text="💾 Kaydet",
            font=("Arial", 11, "bold"),
            bg=VURGU_RENK,
            fg="white",
            width=12,
            cursor="hand2",
            command=kayit_ekle,
        )
        kaydet_buton.pack(side="left", padx=5)

        iptal_buton = Button(
            buton_cerceve,
            text="❌ İptal",
            font=("Arial", 11),
            bg=BUTON_RENK,
            fg=YAZI_RENK,
            width=12,
            cursor="hand2",
            command=kayit_pencere.destroy,
        )
        iptal_buton.pack(side="left", padx=5)

    def kayit_sil(self):

        secili = self.kayitlar_combobox.get()

        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen silinecek kaydı seçin!")
            return


        onay = messagebox.askyesno(
            "Kayıt Sil",
            f"Bu kaydı silmek istediğinize emin misiniz ? \n\n{secili}",
            icon='warning'
        )

        if not onay:
            return

        try:

            parcalar = secili.split("  - ")
            if len(parcalar) < 3:
                messagebox.showerror("Hata", "Kayıt formatı hatalı!")
                return

            sure_str = parcalar[0]
            not_str = parcalar[1]
            tarih_saat = parcalar[2]


            sure_parcalar = sure_str.split(":")
            dakika = int(sure_parcalar[0])
            saniye = int(sure_parcalar[1])


            tarih_saat_parcalar = tarih_saat.strip().split()
            tarih_str = tarih_saat_parcalar[0]  # "21.12.2024"


            tarih_obj = datetime.strptime(tarih_str, "%d.%m.%Y")
            tarih_db = tarih_obj.strftime("%Y-%m-%d")

            conn = sqlite3.connect(VERITABANI_ADI)
            cur = conn.cursor()


            cur.execute(
                """
                DELETE FROM work_sessions 
                WHERE user_id = ? 
                AND duration_minutes = ? 
                AND duration_seconds = ?
                AND date(created_date) = ?
                """,
                (self.giris_yapan_kullanici["id"], dakika, saniye, tarih_db)
            )

            silinen_satir = cur.rowcount

            if silinen_satir > 0:

                cur.execute(
                    "UPDATE user_stats SET work_minutes = CASE WHEN work_minutes >= ? THEN work_minutes - ? ELSE 0 END WHERE user_id = ?",
                    (dakika, dakika, self.giris_yapan_kullanici["id"])
                )

                conn.commit()
                messagebox.showinfo("Başarılı", "✅ Kayıt silindi!")


                self.kayitlari_yukle()
            else:
                messagebox.showerror("Hata", "Kayıt bulunamadı!")

            conn.close()

        except Exception as hata:
            messagebox.showerror("Hata", f"Kayıt silinirken hata oluştu: {hata}")

    def daire_ciz(self, oran):

        self.canvas.delete("daire")
        merkez_x, merkez_y = 150, 150
        yaricap = 120


        self.canvas.create_oval(
            merkez_x - yaricap,
            merkez_y - yaricap,
            merkez_x + yaricap,
            merkez_y + yaricap,
            outline=IKINCI_RENK,
            width=10,
            tags="daire",
        )


        if oran > 0:
            derece = 360 * oran
            self.canvas.create_arc(
                merkez_x - yaricap,
                merkez_y - yaricap,
                merkez_x + yaricap,
                merkez_y + yaricap,
                start=90,
                extent=-derece,
                outline=VURGU_RENK,
                width=10,
                style="arc",
                tags="daire",
            )

    def baslat(self):

        try:
            dakika = int(self.sure_giris.get())
            if dakika <= 0:
                messagebox.showwarning("Uyarı", "Lütfen 0'dan büyük bir süre girin.")
                return
        except ValueError:
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir sayı girin.")
            return

        if self.zamanlayici_id:
            self.pencere.after_cancel(self.zamanlayici_id)

        self.toplam_saniye = dakika * 60
        self.kalan_saniye = self.toplam_saniye
        self.baslangic_saniye = self.toplam_saniye
        self.zamanlayici_calisiyor = True
        self.calisma_modu = True

        self.study_tavsancigini_goster()
        self.durum_etiketi.config(text="Çalışıyorsun! Devam et! 🔥")

        self.zamanlayici_isle()

    def zamanlayici_isle(self):

        if not self.zamanlayici_calisiyor:
            return

        self.zaman_etiketi.config(text=self.saniye_formatla(self.kalan_saniye))

        if self.toplam_saniye > 0:
            oran = self.kalan_saniye / self.toplam_saniye
            self.daire_ciz(oran)

        if self.kalan_saniye <= 0:
            self.zamanlayici_calisiyor = False
            self.animasyon_durdur()
            self.tavsancik.config(image="", text="🎉", font=("Arial", 50))
            self.durum_etiketi.config(text="Harika! Süre doldu! 🎊")
            messagebox.showinfo("Tebrikler", "Çalışma süren bitti! 🎉")
            self.dakika_ekle(self.toplam_saniye // 60)
            self.mola_tavsancigi_goster()
            return

        self.kalan_saniye -= 1
        self.zamanlayici_id = self.pencere.after(1000, self.zamanlayici_isle)

    def durdur(self):

        if self.zamanlayici_id:
            self.pencere.after_cancel(self.zamanlayici_id)
            self.zamanlayici_id = None
        self.zamanlayici_calisiyor = False
        self.mola_tavsancigi_goster()
        self.durum_etiketi.config(text="Duraklatıldı. Biraz nefes al! 🌸")

    def devam_et(self):

        if self.kalan_saniye > 0 and not self.zamanlayici_calisiyor:
            self.zamanlayici_calisiyor = True
            self.study_tavsancigini_goster()
            self.durum_etiketi.config(text="Devam ediyorsun! 🚀")
            self.zamanlayici_isle()

    def sifirla(self):

        if self.zamanlayici_id:
            self.pencere.after_cancel(self.zamanlayici_id)
            self.zamanlayici_id = None

        self.zamanlayici_calisiyor = False

        try:
            dakika = int(self.sure_giris.get())
            self.toplam_saniye = dakika * 60
            self.kalan_saniye = self.toplam_saniye
            self.baslangic_saniye = self.toplam_saniye
        except:
            self.kalan_saniye = 25 * 60
            self.toplam_saniye = 25 * 60
            self.baslangic_saniye = 25 * 60

        self.zaman_etiketi.config(text=self.saniye_formatla(self.kalan_saniye))
        self.mola_tavsancigi_goster()
        self.durum_etiketi.config(text="Sıfırlandı. Hazır mısın? 🐰")
        self.daire_ciz(1.0)

    def dakika_ekle(self, dakika: int):

        if not self.giris_yapan_kullanici:
            return
        try:
            conn = sqlite3.connect(VERITABANI_ADI)
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)",
                (self.giris_yapan_kullanici["id"],)
            )
            cur.execute(
                "UPDATE user_stats SET work_minutes = work_minutes + ? WHERE user_id = ?",
                (dakika, self.giris_yapan_kullanici["id"])
            )
            conn.commit()
            conn.close()
        except Exception as hata:
            print(f"İstatistik güncelleme hatası: {hata}")

    def cikis_yap(self):

        self.giris_yapan_kullanici = None
        if self.zamanlayici_id:
            self.pencere.after_cancel(self.zamanlayici_id)
        self.animasyon_durdur()
        self.giris_ekrani_goster()

    @staticmethod
    def saniye_formatla(toplam_saniye: int) -> str:

        dakika = toplam_saniye // 60
        saniye = toplam_saniye % 60
        return f"{dakika:02d}:{saniye:02d}"


def main():

    init_db()
    pencere = Tk()
    uygulama = PomodoroUygulama(pencere)
    pencere.mainloop()


if __name__ == "__main__":
    main()