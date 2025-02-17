import streamlit as st
import numpy as np
import pyvista as pv
import pyiges
import os
import subprocess

os.environ["PYVISTA_OFF_SCREEN"] = "true"

# X11 ve Xvfb kilit dosyasını kontrol et ve ilgili süreci öldür
lock_file = "/tmp/.X99-lock"
x11_dir = "/tmp/.X11-unix"

# X11 dizini yoksa oluştur ve izinleri ayarla
if not os.path.exists(x11_dir):
    os.makedirs(x11_dir, mode=0o1777, exist_ok=True)

# Eğer Xvfb kilit dosyası varsa, içindeki PID'yi öldür
if os.path.exists(lock_file):
    try:
        with open(lock_file, "r") as f:
            pid = f.read().strip()
        if pid.isdigit():
            subprocess.run(["kill", "-9", pid], check=False)
        os.remove(lock_file)
    except Exception as e:
        print(f"Hata oluştu: {e}")

# Xvfb zaten çalışıyorsa yeniden başlatma
try:
    xvfb_check = subprocess.run(["pgrep", "Xvfb"], capture_output=True, text=True)
    if not xvfb_check.stdout.strip():
        os.environ["DISPLAY"] = ":99"
        os.system("Xvfb :99 -ac -screen 0 1024x768x24 +extension GLX +render -noreset &")
except Exception as e:
    print(f"Xvfb başlatılamadı: {e}")



# Başlık
st.title("MG Metal \n Boru Lazer CNC Fiyat Tahmin Uygulaması")
st.text("Uygulama henüz deneme aşamasındadır. Aldığınız herhangi bir hata için lütfen geri dönüş yapınız")

# Kullanıcıdan IGES dosyası yüklemesini iste
uploaded_file = st.file_uploader("Bir IGES dosyası yükleyin", type=["iges"])

if uploaded_file is not None:
    with open("temp.iges", "wb") as f:
        f.write(uploaded_file.getbuffer())

    iges = pyiges.read("temp.iges")

    # Eksen seçimi
    axis_option = st.selectbox("Parçanın uzandığı ekseni seçin:", ["X", "Y", "Z"])
    axis_dict = {"X": 0, "Y": 1, "Z": 2}
    ekşen = axis_dict[axis_option]

    # VTK formatına çevirme
    lines = iges.to_vtk(surfaces=False, merge=False)

    # 3D Model Görselleştirme - Ortogonal ve İzometrik Görünümler
    axes = [i for i in range(3) if i != ekşen]
    views = [
        (f"{['X', 'Y', 'Z'][axes[0]]} Ekseninden Görünüm", [1 if i == axes[0] else 0 for i in range(3)], "view_1.png"),
        (f"-{['X', 'Y', 'Z'][axes[0]]} Ekseninden Görünüm", [-1 if i == axes[0] else 0 for i in range(3)], "view_2.png"),
        (f"{['X', 'Y', 'Z'][axes[1]]} Ekseninden Görünüm", [1 if i == axes[1] else 0 for i in range(3)], "view_3.png"),
        (f"-{['X', 'Y', 'Z'][axes[1]]} Ekseninden Görünüm", [-1 if i == axes[1] else 0 for i in range(3)], "view_4.png"),
        ("İzometrik Görünüm", [1, 1, 1], "view_iso.png"),
    ]

    for title, position, file in views:
        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(lines, color="b", line_width=2)
        plotter.view_vector(position, (0, 0, 1))
        plotter.camera.parallel_projection = True
        plotter.show_axes()
        plotter.screenshot(file, scale=3.0)
        st.subheader(f"📷 {title}")
        st.image(file, caption=title, use_container_width=True)

    # Boyutları Hesapla
    bounds = lines.bounds
    x_length = round(bounds[1] - bounds[0], 1)
    y_length = round(bounds[3] - bounds[2], 1)
    z_length = round(bounds[5] - bounds[4], 1)
    lengths = np.array([x_length, y_length, z_length])
    uzun_kenar = lengths[ekşen]

    # Kesim Uzunluğu Hesaplama
    total_length = 0
    for line in lines:
        points = np.array(line.points)
        if len(points) > 1:
            for j in range(len(points) - 1):
                total_length += np.linalg.norm(points[j + 1] - points[j])

    hesap_icin_lengths = lengths.copy()
    hesap_icin_lengths[ekşen] = 0
    total_length = total_length - uzun_kenar * 16 - hesap_icin_lengths.sum() * 8
    total_length = total_length / 2

    # Kullanıcıdan fiyat girdileri ve adet bilgisi
    adet = st.number_input("Kaç adet üretilecek?", min_value=1, value=1, step=1)
    perakende_tl_cm = st.number_input("Kesim Perakende fiyatı - 1 adet için (TL/cm)", min_value=0.0, value=1.5, step=0.01)
    toptan_tl_cm = st.number_input("Kesim Toptan fiyatı - 1000 adet için (TL/cm)", min_value=0.0, value=1.0, step=0.01)
    hammadde_fiyati_6m = st.number_input("6 metre profil fiyatı (TL)", min_value=0.0, value=100.0, step=1.0)
    
    # Lineer fiyat orantısı
    if adet >= 1000:
        birim_fiyat = toptan_tl_cm
    elif adet == 1:
        birim_fiyat = perakende_tl_cm
    else:
        birim_fiyat = perakende_tl_cm - ((perakende_tl_cm - toptan_tl_cm) * (adet / 1000))
    
    # Fiyat Hesaplama
    parcabasikesimcm = total_length / 10
    birim_parca_fiyat = total_length * birim_fiyat / 10
    toplam_fiyat = birim_parca_fiyat * adet
    hammadde_birim_fiyat = (uzun_kenar / 6000) * hammadde_fiyati_6m
    hammadde_fiyat = hammadde_birim_fiyat * adet
    parca_toplam_fiyat = hammadde_birim_fiyat + birim_parca_fiyat
    toplam_maliyet = toplam_fiyat + hammadde_fiyat
    
    # Sonuçları Göster
    st.subheader("📊 Hesaplama Sonuçları")
    st.write(f"**Parça Boyutları:** X: {x_length} mm, Y: {y_length} mm, Z: {z_length} mm")
    st.write(f"**Kesim Birim Uzunluk Fiyatı:** {birim_fiyat:.4f} TL/cm")
    st.write(f"**Parça Başına Kesim Uzunluğu:** {parcabasikesimcm:.2f} cm")
    st.write(f"**Kesim Parça Fiyatı:** {birim_parca_fiyat:.2f} TL")
    st.write(f"**Hammadde Parça Maliyeti:** {hammadde_birim_fiyat:.2f} TL")
    st.write(f"**Parça Fiyatı:** {parca_toplam_fiyat:.2f} TL")
    st.write(f"**Toplam Fiyat:** {toplam_maliyet:.2f} TL")

    st.success("✅ 3D model başarıyla yüklendi ve hesaplandı!")
