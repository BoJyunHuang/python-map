import tkinter as tk
from tkinter import ttk
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
from shapely.geometry import Point

# 创建主窗口
window = tk.Tk()
window.title('Data Visualization')
window.geometry('800x600')

# 讀取地圖向量數據(geojson)
map_data = gpd.read_file('鄉鎮市區行政區域界線.json')

# 讀取氣候數據(json)，編碼格式要記得是UTF-8
with open('weather.json', 'r', encoding='utf-8') as f:
    weather_data = json.load(f)

# 將地圖轉換為世界座標的標準
map_data = map_data.to_crs('EPSG:4326')

# 進行氣候數據的解析與轉換
records = weather_data['records']['location']
# 將轉換後的數據存到data中
data = []
for record in records:
    data.append({
        'lat': float(record['lat']),
        'lon': float(record['lon']),
        'locationName': record['locationName'],
        'stationId': record['stationId'],
        'obsTime': pd.to_datetime(record['time']['obsTime']),
        'meanTemp': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'TEMP'), -99),
        'maxTemp': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'D_TX'), -99),
        'minTemp': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'D_TN'), -99),
        'rain': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'H_24R'), -99),
        'huni': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'HUMD'), -99),
        'wdir': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'WDIR'), -99),
        'wdsd': next((float(e['elementValue']) for e in record['weatherElement'] if e['elementName'] == 'WDSD'), -99)
    })

# 建立Pandas DataFrame
df = pd.DataFrame(data)
geometry = [Point(lon, lat) for lat, lon in zip(df['lat'], df['lon'])]
crs = 'EPSG:4326'
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs)

# 將資料點與行政區域進行空間判斷
merged_data = gpd.sjoin(map_data, gdf, predicate='contains', how='left')

# 設定溫度範圍及顏色
vmin_temp = 0
vmax_temp = 40
cmap_temp = plt.colormaps.get_cmap('coolwarm')

# 設定雨量範圍及顏色
vmin_rain = 0
vmax_rain = 1000
cmap_rain = plt.colormaps.get_cmap('Blues')

# 設定濕度範圍及顏色
vmin_humi = 0
vmax_humi = 1
cmap_humi = plt.colormaps.get_cmap('Blues')

# 创建选项卡
notebook = ttk.Notebook(window)
notebook.pack(fill="both", expand=True)

# 创建子窗口1（温度图）
temperature_tab = ttk.Frame(notebook)
notebook.add(temperature_tab, text="Temperature")

# 创建子窗口2（雨量图）
rainfall_tab = ttk.Frame(notebook)
notebook.add(rainfall_tab, text="Rainfall")

# 在子窗口1中绘制温度图
fig1, ax1 = plt.subplots(figsize=(8, 6))
ax1.set_title("Temperature Map")
# 绘制温度图的代码...
# 繪製行政區域面
map_data.plot(ax=ax1, color='lightgray', edgecolor='gray')
# 繪製溫度數據
merged_data.plot(ax=ax1, column='meanTemp', cmap=cmap_temp, linewidth=0.8,
                 edgecolor='0.8', legend=False, vmin=vmin_temp, vmax=vmax_temp)
# 將溫度低於-10度的區域顏色設為灰色
merged_data[merged_data['meanTemp'] < -10].plot(ax=ax1, color='gray', linewidth=0.8,
                                                edgecolor='0.8')
# 创建 ScalarMappable 对象
sm_mean = plt.cm.ScalarMappable(
    cmap=cmap_temp, norm=plt.Normalize(vmin=vmin_temp, vmax=vmax_temp))
sm_mean.set_array([])  # 设置虚拟数组
# 顯示溫度色條並設定單位
cbar = fig1.colorbar(sm_mean, ax=ax1, orientation='vertical')
cbar.set_label('Temperature (°C)')

 # 設定顯示時間
latest_obs_time = gdf['obsTime'].max().strftime('%Y-%m-%d %H:%M')
plt.text(0.99, 0.97,
         f'Latest Observation Time: {latest_obs_time}', transform=ax1.transAxes, ha='right')

# 在子窗口2中绘制雨量图
fig2, ax2 = plt.subplots(figsize=(8, 6))
ax2.set_title("Rainfall Map")
# 绘制雨量图的代码...
# 繪製行政區域面
map_data.plot(ax=ax2, color='lightgray', edgecolor='gray')
# 繪製雨量數據
merged_data.plot(ax=ax2, column='rain', cmap=cmap_rain, linewidth=0.8,
                 edgecolor='0.8', legend=False, vmin=vmin_rain, vmax=vmax_rain)
# 创建 ScalarMappable 对象
sm_rain = plt.cm.ScalarMappable(
    cmap=cmap_rain, norm=plt.Normalize(vmin=vmin_rain, vmax=vmax_rain))
sm_rain.set_array([])  # 设置虚拟数组
# 顯示雨量色條並設定單位
cbar_rain = fig2.colorbar(sm_rain, ax=ax2, orientation='vertical')
cbar_rain.set_label('Rainfall (mm)')
plt.text(0.99, 0.97,
         f'Latest Observation Time: {latest_obs_time}', transform=ax2.transAxes, ha='right')


# 在子窗口1中显示温度图
canvas1 = FigureCanvasTkAgg(fig1, master=temperature_tab)
canvas1.draw()
canvas1.get_tk_widget().pack(fill="both", expand=True)

# 在子窗口2中显示雨量图
canvas2 = FigureCanvasTkAgg(fig2, master=rainfall_tab)
canvas2.draw()
canvas2.get_tk_widget().pack(fill="both", expand=True)

# 显示GUI窗口
window.mainloop()

