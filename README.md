🐰 Pomodoro - Çalışma Takip Uygulaması
Tkinter ile geliştirilmiş, sevimli tavşan temalı bir Pomodoro zaman yönetimi uygulaması. Kullanıcı girişi, kişisel istatistikler ve detaylı çalışma kayıtları içerir.
✨ Özellikler

🔐 Kullanıcı Sistemi: Kayıt ve giriş ekranı (SHA-256 ile hash'lenmiş şifreler)
⏱️ Pomodoro Sayacı: Klasik 25 dakika çalışma / 5 dakika mola döngüsü
📊 Kişisel İstatistikler: Toplam çalışma ve mola süreleri takibi
📝 Çalışma Kayıtları: Her oturum için not ekleme ve geçmiş görüntüleme
🐰 Animasyonlu Arayüz: Çalışma ve mola modları için ayrı tavşan GIF'leri
💾 SQLite Veritabanı: Tüm veriler yerel olarak saklanır

🛠️ Kullanılan Teknolojiler

Python 3
Tkinter - GUI
SQLite3 - Veritabanı
Pillow (PIL) - GIF animasyonları ve görsel işleme
hashlib - Şifre hashleme

📦 Kurulum

Repoyu klonla:

bash   git clone https://github.com/Ezgnur35/pomodoro-app.git
   cd pomodoro-app

Gerekli kütüphaneleri yükle:

bash   pip install -r requirements.txt

Uygulamayı çalıştır:

bash   python main.py
🎮 Kullanım

Uygulama açıldığında kayıt ol veya giriş yap
Pomodoro butonuna basarak çalışma seansını başlat
Süre dolduğunda otomatik mola moduna geçer
Geçmiş kayıtlardan önceki seanslarını görüntüleyebilirsin

📁 Proje Yapısı
pomodoro-app/
├── main.py                 # Ana uygulama dosyası
├── requirements.txt        # Python bağımlılıkları
├── mola_tavşanı.gif       # Mola animasyonu
├── study_tavşan.gif       # Çalışma animasyonu
└── README.md

Not: pomodoro.db dosyası uygulama ilk çalıştırıldığında otomatik olarak oluşturulur.


📄 Lisans
Bu proje eğitim amaçlı geliştirilmiştir.