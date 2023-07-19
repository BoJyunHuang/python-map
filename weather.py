import tkinter as tk
from tkinter import ttk
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import urllib.request
import json
from shapely.geometry import Point
import numpy as np

# 建立視窗
window = tk.Tk()
window.title('Data Visualization')
window.geometry('1920x1080')

# 讀取地圖向量數據(geojson)
map_data = gpd.read_file('鄉鎮市區行政區域界線.json')

# 讀取氣候數據(json)，編碼格式要記得是UTF-8
# with open('weather.json', 'r', encoding='utf-8') as f:
#     weather_data = json.load(f)
# 線上API
response = urllib.request.urlopen('https://opendata.cwb.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=CWB-620CE123-D3D7-4A29-9DD3-C4AD6A0E982F')
weather_data = json.load(response)

# 將地圖轉換為世界座標的標準
map_data = map_data.to_crs('EPSG:4326')

# 將轉換後的數據存到data中
data = []
for record in weather_data['records']['location']:
    data.append({
        'lat': float(record['lat']),
        'lon': float(record['lon']),
        'locationName': record['locationName'],
        'stationId': record['stationId'],
        'obsTime': pd.to_datetime(record['time']['obsTime']),
        'meanTemp': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'TEMP'), None),
        'maxTemp': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'D_TX'), None),
        'minTemp': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'D_TN'), None),
        'rain': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'H_24R'), None),
        'humi': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'HUMD'), None),
        'wdir': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'WDIR'), None),
        'wdsd': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'WDSD'), None)
    })

# 建立Pandas DataFrame
df = pd.DataFrame(data)
geometry = [Point(lon, lat) for lat, lon in zip(df['lat'], df['lon'])]
crs = 'EPSG:4326'
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs)

# 將資料點與行政區域進行空間判斷
merged_data = gpd.sjoin(map_data, gdf, predicate='contains', how='left')
# 將測站資料進行統計，同一行政區會有平均值
grouped_data = merged_data.groupby('T_Name')
# 建立空的DataFrame用來存平均值
averaged_data = pd.DataFrame(columns=merged_data.columns)
# 需要排除的非數值陣列
exclude_columns = ['T_UID', 'Town_ID', 'T_Name', 'Add_Date', 'Add_Accept', 'Remark', 'County_ID', 'C_Name']
# 對各行政區的測站進行平均處理
for name, group in grouped_data:
    # 排除非數值的列
    numeric_group = group.drop(columns=exclude_columns + ['geometry'])
    # 替換非數值陣列的值為Nan
    numeric_group = numeric_group.apply(pd.to_numeric, errors='coerce')
    # 計算平均
    average_values = numeric_group.mean(skipna=True)
    # 建立新的行政區數據
    new_row = gpd.GeoDataFrame(average_values).transpose()
    # 設置幾何
    new_row['geometry'] = map_data[map_data['T_Name'] == name]['geometry'].values[0]
    # 添加到平均值数据集
    averaged_data = pd.concat([averaged_data, new_row])
# 將平均值數據轉為GeoDataFrame
averaged_data = gpd.GeoDataFrame(averaged_data, geometry='geometry')

# 設定溫度範圍及顏色
vmin_temp = 0
vmax_temp = 40
cmap_temp = plt.colormaps.get_cmap('coolwarm')
# 設定雨量範圍及顏色
vmin_rain = 0
vmax_rain = 30
cmap_rain = plt.colormaps.get_cmap('BuPu')
# 設定濕度範圍及顏色
vmin_humi = 0
vmax_humi = 1
cmap_humi = plt.colormaps.get_cmap('Blues')

# 建立視窗選項
notebook = ttk.Notebook(window)
notebook.pack(fill="both", expand=True)

# 建立子畫面和標籤的陣列
tabs = [("Mean Temperature", "meanTemp"), ("Max Temperature", "maxTemp"), ("Min Temperature", "minTemp"), ("Rainfall", "rain"), ("Humidity", "humi"), ("Wind", "wind")]
# 設定顯示時間
latest_obs_time = gdf['obsTime'].max().strftime('%Y-%m-%d %H:%M')

# 建立子畫面與圖
for tab_name, column_name in tabs:
    # 宣告
    tab = ttk.Frame(notebook)
    notebook.add(tab, text=tab_name)

    # 在子畫面繪製圖
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_title(f"{tab_name} Map")
    map_data.plot(ax=ax, color='lightgray', edgecolor='gray')

    if 'Wind' in tab_name:
        # 繪製風向，建立箭頭
        angles = df['wdir']
        speeds = df['wdsd']
        x = df['lon']
        y = df['lat']
        u = np.cos(np.radians(angles))
        v = np.sin(np.radians(angles))
        colors = speeds
        ax.quiver(x, y, u, v, colors, angles='xy', scale_units='xy', scale=5, width=0.001, headlength=5, headwidth=4, headaxislength=4, linewidth=0.5, cmap='cool', norm=plt.Normalize(vmin=0, vmax=10))

        # 在圖中顯示風向箭頭和顏色
        cbar = fig.colorbar(plt.cm.ScalarMappable(cmap='cool', norm=plt.Normalize(vmin=0, vmax=10)), ax=ax, orientation='vertical')
        cbar.set_label('Speed (m/s)')
    else:
        # 繪製其他地圖
        if 'Temp' in column_name:
            merged_data.plot(ax=ax, column=column_name, cmap=cmap_temp, linewidth=0.8, edgecolor='0.8', legend=False, vmin=vmin_temp, vmax=vmax_temp)
            merged_data[merged_data[column_name] < 0].plot(ax=ax, color='gray', linewidth=0.8, edgecolor='0.8')
            sm = plt.cm.ScalarMappable(cmap=cmap_temp, norm=plt.Normalize(vmin=vmin_temp, vmax=vmax_temp))
        elif 'humi' in column_name:
            averaged_data.plot(ax=ax, column=column_name, cmap=cmap_humi, linewidth=0.8, edgecolor='0.8', legend=False, vmin=vmin_humi, vmax=vmax_humi)
            sm = plt.cm.ScalarMappable(cmap=cmap_humi, norm=plt.Normalize(vmin=vmin_humi, vmax=vmax_humi))
        else:
            averaged_data.plot(ax=ax, column=column_name, cmap=cmap_rain, linewidth=0.8, edgecolor='0.8', legend=False, vmin=vmin_rain, vmax=vmax_rain)
            sm = plt.cm.ScalarMappable(cmap=cmap_rain, norm=plt.Normalize(vmin=vmin_rain, vmax=vmax_rain))
        # 建立顏色條
        cbar = fig.colorbar(sm, ax=ax, orientation='vertical')
        if 'Temp' in column_name:
            cbar.set_label('Temperature (°C)')
        elif 'humi' in column_name:
            cbar.set_label('Humidity')
        else:
            cbar.set_label('Rainfall (mm)')
        sm.set_array([])
    # 附上時間
    plt.text(0.99, 0.97, f'Latest Observation Time: {latest_obs_time}', transform=ax.transAxes, ha='right')

    # 在子畫面中顯示圖表
    canvas = FigureCanvasTkAgg(fig, master=tab)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

# 顯示GUI介面
window.mainloop()
