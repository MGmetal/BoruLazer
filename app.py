import streamlit as st
import numpy as np
import pyvista as pv
import pyiges
import os
import subprocess
import pyvista

def find_bounds(line_list):
    if not line_list:
        return None  # Boş liste olursa None döndür

    all_points = np.concatenate([np.array(line.points) for line in line_list])  # Tüm noktaları birleştir
    min_bounds = np.min(all_points, axis=0)  # Her eksende en küçük değerleri al
    max_bounds = np.max(all_points, axis=0)  # Her eksende en büyük değerleri al

    return min_bounds, max_bounds  # (min, max) olarak döndür

def filter_lines_by_own_bound(lines, bound_axis):
    if not lines:
        return []  

    min_bounds, max_bounds = find_bounds(lines)
    min_bound, max_bound = min_bounds[bound_axis], max_bounds[bound_axis]

    # Filtreleme işlemi
    filtered_lines = [
        line for line in lines if np.any(
            (np.array(line.points)[:, bound_axis] >= min_bound + 0.01) & 
            (np.array(line.points)[:, bound_axis] <= max_bound - 0.01)
        )
    ]

    return filtered_lines
def calculate_total_length(lines):
    total_length = 0.0
    for line in lines:
        total_length += line.length 
    
    return total_length


pyvista.start_xvfb()

os.environ["PYVISTA_OFF_SCREEN"] = "true"
os.environ["DISPLAY"] = ":99"



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
    eksen = axis_dict[axis_option]

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
    uzun_kenar = lengths[eksen]

    y_plus_list = []
    y_minus_list = []
    z_plus_list = []
    z_minus_list = []
    x_plus_list = []
    x_minus_list = []
    
    for line in lines:
        points = np.array(line.points)
    
        if eksen == 0:
            if np.all(points[:, 1] >= bounds[3] - 0.1): y_plus_list.append(line)
            if np.all(points[:, 1] <= bounds[2] + 0.1): y_minus_list.append(line)
            if np.all(points[:, 2] >= bounds[5] - 0.1): z_plus_list.append(line)
            if np.all(points[:, 2] <= bounds[4] + 0.1): z_minus_list.append(line)
            filtered_y_plus = filter_lines_by_own_bound(y_plus_list, bound_axis=2)
            filtered_y_minus = filter_lines_by_own_bound(y_minus_list, bound_axis=2)
            filtered_z_plus = filter_lines_by_own_bound(z_plus_list, bound_axis=1)
            filtered_z_minus = filter_lines_by_own_bound(z_minus_list, bound_axis=1)
            total_lines = filtered_y_plus + filtered_y_minus + filtered_z_plus + filtered_z_minus
            total_filtered_length = calculate_total_length(total_lines)
    
        elif eksen == 1:
            if np.all(points[:, 0] >= bounds[1] - 0.1): x_plus_list.append(line)
            if np.all(points[:, 0] <= bounds[0] + 0.1): x_minus_list.append(line)
            if np.all(points[:, 2] >= bounds[5] - 0.1): z_plus_list.append(line)
            if np.all(points[:, 2] <= bounds[4] + 0.1): z_minus_list.append(line)
            filtered_x_plus = filter_lines_by_own_bound(x_plus_list, bound_axis=2)
            filtered_x_minus = filter_lines_by_own_bound(x_minus_list, bound_axis=2)
            filtered_z_plus = filter_lines_by_own_bound(z_plus_list, bound_axis=0)
            filtered_z_minus = filter_lines_by_own_bound(z_minus_list, bound_axis=0)
            total_lines = filtered_x_plus + filtered_x_minus + filtered_z_plus + filtered_z_minus
            total_filtered_length = calculate_total_length(total_lines)
    
        elif eksen == 2:
            if np.all(points[:, 0] >= bounds[1] - 0.1): x_plus_list.append(line)
            if np.all(points[:, 0] <= bounds[0] + 0.1): x_minus_list.append(line)
            if np.all(points[:, 1] >= bounds[3] - 0.1): y_plus_list.append(line)
            if np.all(points[:, 1] <= bounds[2] + 0.1): y_minus_list.append(line)
            filtered_x_plus = filter_lines_by_own_bound(x_plus_list, bound_axis=1)
            filtered_x_minus = filter_lines_by_own_bound(x_minus_list, bound_axis=1)
            filtered_y_plus = filter_lines_by_own_bound(y_plus_list, bound_axis=0)
            filtered_y_minus = filter_lines_by_own_bound(y_minus_list, bound_axis=0)
            total_lines = filtered_x_plus + filtered_x_minus + filtered_y_plus + filtered_y_minus
            total_filtered_length = calculate_total_length(total_lines)
    st.subheader("✂️ Kesilecek Yerler")

    filtered_lines = filtered_y_plus + filtered_y_minus + filtered_z_plus + filtered_z_minus
    
    if filtered_lines:
        filtered_plot = pv.MultiBlock(filtered_lines)
        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(filtered_plot, color='r', line_width=3)
        plotter.show_axes()
        
        screenshot_path = "filtered_plot.png"
        plotter.screenshot(screenshot_path, scale=3.0)
        
        st.image(screenshot_path, caption="Kesilecek Yerler", use_container_width=True)
    else:
        st.warning("Kesilecek çizgiler bulunamadı.")
    total_length = total_filtered_length
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
