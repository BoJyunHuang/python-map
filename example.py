import geopandas as gpd
import matplotlib.pyplot as plt

# 读取地图数据
map_data = gpd.read_file('Taiwan.json')

# 計算面積
map_data = map_data.set_index("NAME_2014")
map_data['area'] = map_data.area

# 绘制地图
map_data.plot("area", legend=True)
# map_data.explore("NAME_2010", legend=False)

# 显示地图
plt.show()
