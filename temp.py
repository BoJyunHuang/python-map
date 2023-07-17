import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import json
from shapely.geometry import Point
import mplleaflet

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
    lat = float(record['lat'])
    lon = float(record['lon'])
    location_name = record['locationName']
    station_id = record['stationId']
    obs_time = pd.to_datetime(record['time']['obsTime'])

    temperature = None

    for element in record['weatherElement']:
        if element['elementName'] == 'TEMP':
            temperature = float(element['elementValue'])

    if temperature is not None:
        data.append({
            'lat': lat,
            'lon': lon,
            'locationName': location_name,
            'stationId': station_id,
            'obsTime': obs_time,
            'temperature': temperature
        })

# 建立Pandas DataFrame
df = pd.DataFrame(data)
geometry = [Point(lon, lat) for lat, lon in zip(df['lat'], df['lon'])]
crs = 'EPSG:4326'
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs)

# 將資料點與行政區域進行空間判斷
merged_data = gpd.sjoin(map_data, gdf, predicate='contains', how='left')

# 設定溫度範圍及顏色
vmin = 0
vmax = 40
cmap = plt.colormaps.get_cmap('coolwarm')

fig, ax = plt.subplots(figsize=(10, 10))
# 繪製行政區域面
map_data.plot(ax=ax, color='lightgray', edgecolor='gray')
# 繪製溫度數據
merged_data.plot(ax=ax, column='temperature', cmap=cmap, linewidth=0.8,
                 edgecolor='0.8', legend=False, vmin=vmin, vmax=vmax)

# 將溫度低於-10度的區域顏色設為灰色
merged_data[merged_data['temperature'] < -10].plot(ax=ax, color='gray', linewidth=0.8,
                                                   edgecolor='0.8')

# 创建 ScalarMappable 对象
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
sm.set_array([])  # 设置虚拟数组

# 顯示溫度色條並設定單位
cbar = fig.colorbar(sm, ax=ax, orientation='vertical')
cbar.set_label('Temperature (°C)')

# 設定顯示時間
latest_obs_time = gdf['obsTime'].max().strftime('%Y-%m-%d %H:%M')
plt.text(0.99, 0.97,
         f'Latest Observation Time: {latest_obs_time}', transform=ax.transAxes, ha='right')

# 顯示地圖
plt.title('Taiwan Temperature Map')

# mplleaflet.save_html(fig, 'temp.html')
plt.show()
