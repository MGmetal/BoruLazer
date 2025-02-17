import streamlit as st
import numpy as np
import pyvista as pv
import pyiges
import os

os.environ["PYVISTA_OFF_SCREEN"] = "true"
os.environ["DISPLAY"] = ":99"
os.system("Xvfb :99 -screen 0 1024x768x24 &")

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
    axis_option = st.selectbox("Lütfen kesim eksenini seçin:", ["X", "Y", "Z"])
    axis_dict = {"X": 0, "Y": 1, "Z": 2}
    ekşen = axis_dict[axis_option]

    # VTK formatına çevirme
    lines = iges.to_vtk(surfaces=False, merge=False)

    # 3D Model Görselleştirme
    st.subheader("📷 3D Model Görüntüsü")
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(lines, color="b", line_width=2)
    plotter.show_axes()
    screenshot_path = "main_plot.png"
    plotter.screenshot(screenshot_path, scale=3.0)
    st.image(screenshot_path, caption="Ana 3D Model", use_container_width=True)

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
    perakende_tl_cm = st.number_input("Perakende fiyatı (TL/cm)", min_value=0.0, value=0.15, step=0.01)
    toptan_tl_cm = st.number_input("Toptan fiyatı (TL/cm)", min_value=0.0, value=0.10, step=0.01)
    
    # Lineer fiyat orantısı
    if adet >= 1000:
        birim_fiyat = toptan_tl_cm
    elif adet == 1:
        birim_fiyat = perakende_tl_cm
    else:
        birim_fiyat = perakende_tl_cm - ((perakende_tl_cm - toptan_tl_cm) * (adet / 1000))
    
    # Fiyat Hesaplama
    toplam_fiyat = total_length * birim_fiyat * adet

    # Sonuçları Göster
    st.subheader("📊 Hesaplama Sonuçları")
    st.write(f"**Parçanın Boyutları:**")
    st.write(f"- **X:** {x_length} mm")
    st.write(f"- **Y:** {y_length} mm")
    st.write(f"- **Z:** {z_length} mm")
    st.write(f"**Kesim Yapılan Uzunluk:** {total_length:.2f} mm")
    st.write(f"**Birim Fiyat:** {birim_fiyat:.4f} TL/cm")
    st.write(f"**Toplam Fiyat:** {toplam_fiyat:.2f} TL")

    st.success("✅ 3D model başarıyla yüklendi ve hesaplandı!")
