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
    # Dosyayı geçici olarak kaydet ve oku
    with open("temp.iges", "wb") as f:
        f.write(uploaded_file.getbuffer())

    iges = pyiges.read("temp.iges")
    ekşen = 2  # Orijinal koddaki eksen

    # VTK formatına çevirme
    lines = iges.to_vtk(surfaces=False, merge=False)

    # 🎯 **Ana 3D Modeli PNG Olarak Göster**
    st.subheader("📷 3D Model Görüntüsü")
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(lines, color="b", line_width=2)
    plotter.show_axes()
    
    # PNG olarak kaydet
    screenshot_path = "main_plot.png"
    plotter.screenshot(screenshot_path)

    # Streamlit içinde göster
    st.image(screenshot_path, caption="Ana 3D Model", use_container_width=True)

    # 🎯 **X, Y, Z Eksenlerinden Görünümler**
    st.subheader("📷 Farklı Açılardan 3D Görünümler")

    views = [
        {"name": "X Ekseninden Bakış", "position": (1, 0, 0), "file": "view_x.png"},
        {"name": "-X Ekseninden Bakış", "position": (-1, 0, 0), "file": "view_x_neg.png"},
        {"name": "Y Ekseninden Bakış", "position": (0, 1, 0), "file": "view_y.png"},
        {"name": "-Y Ekseninden Bakış", "position": (0, -1, 0), "file": "view_y_neg.png"},
    ]

    for view in views:
        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(lines, color="b", line_width=2)
        plotter.view_vector(view["position"], (0, 0, 1))
        plotter.camera.parallel_projection = True
        plotter.show_axes()
        plotter.screenshot(view["file"])
        st.image(view["file"], caption=view["name"], use_container_width=True)

    # 🎯 **Kesim Uzunluğu Hesaplama**
    total_length = 0
    for line in lines:
        points = np.array(line.points)
        if len(points) > 1:
            for j in range(len(points) - 1):
                total_length += np.linalg.norm(points[j + 1] - points[j])

    # 🎯 **Boyutları Hesapla**
    bounds = lines.bounds
    x_length = round(bounds[1] - bounds[0], 1)
    y_length = round(bounds[3] - bounds[2], 1)
    z_length = round(bounds[5] - bounds[4], 1)
    lengths = np.array([x_length, y_length, z_length])
    uzun_kenar = lengths[ekşen]

    # 🎯 **Kesim Uzunluğu ve Fiyat Hesabı**
    hesap_icin_lengths = lengths.copy()
    hesap_icin_lengths[ekşen] = 0
    total_length = total_length - uzun_kenar * 16 - hesap_icin_lengths.sum() * 8
    total_length = total_length / 2
    fiyat = total_length * 1.5

    # 🎯 **Sonuçları Göster**
    st.subheader("📊 Hesaplama Sonuçları")
    st.write(f"**Parçanın Boyutları:**")
    st.write(f"- **X:** {x_length} mm")
    st.write(f"- **Y:** {y_length} mm")
    st.write(f"- **Z:** {z_length} mm")
    st.write(f"**Kesim Yapılan Uzunluk:** {total_length:.2f} mm")
    st.write(f"**Tahmini Fiyat:** {fiyat:.2f} TL")

    st.success("✅ 3D model başarıyla yüklendi ve hesaplandı!")

