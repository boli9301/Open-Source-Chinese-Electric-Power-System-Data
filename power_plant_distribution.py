# coding: utf-8
import pandas as pd
import numpy as np
import geopandas as gpd
import os
import time
import matplotlib.pyplot as plt
from shapely.wkt import loads
from matplotlib.font_manager import FontProperties
import seaborn as sns
from matplotlib.patches import Patch, Circle

sns.set_style({'font.family':'serif', 'font.serif':'Times New Roman'})
sns.set_theme(style="whitegrid")

def df_to_gdf(df, lon_name="Longitude", lat_name="Latitude"):
    '''
    Convert dataframe to geodataframe
    
    Parameters
    ----------
    df: the input dataframe
    lon_name: the column name for longitude
    lat_name: the column name for latitude
    '''
    
    import geopandas as gpd
    from shapely.geometry import Point
    
    # Designate the coordinate system
    crs = {'init':'EPSG:4326'}
    # Construct the geometry for geodataframe
    geometry = [Point(xy) for xy in zip(df[lon_name], df[lat_name])]
    gdf = gpd.GeoDataFrame(df, crs = crs, geometry = geometry)
    
    return gdf

def data_filter(df, year):
    df = df[["Country", "Capacity (MW)", "Start year", "Retired year", "Latitude", "Longitude", ]]
    df = df.dropna(subset=['Longitude', 'Latitude', "Start year", "Country"])
    # By country
    df = df[df["Country"] == "China"]
    df["Retired year"] = df["Retired year"].fillna("2024")
    df.astype({"Capacity (MW)":float, "Start year":int, "Retired year":int, "Latitude":float, "Longitude":float})
    df = df[df["Start year"] <= year]

    # Merge those with the same "Plant name"
    df = df.groupby(['Latitude', 'Longitude'], as_index=False)['Capacity (MW)'].sum()
    df = df.reset_index(drop=True)
    
    gdf = df_to_gdf(df=df)
    
    return gdf

def visualization(gdf_list, provincial_gdf, year):
    save_path = "./Result/distribution_" + str(year) + ".png"
    color_list = ["#001427", "#0077b6", "#d62828", "#fca311","#70e000"]
    
    plt.figure(figsize=(20, 15))
    provincial_gdf.boundary.plot(linewidth=0.5, color="#adb5bd", zorder=1)
    bounds = provincial_gdf.total_bounds
    ax = plt.gca()
    
    # Set the aspect of the plot to be equal
    ax.set_aspect('equal')
    extend = 0
    ax.set_xlim(bounds[0]-extend, bounds[2]+extend)
    ax.set_ylim(bounds[1]-extend, bounds[3]+extend)
    ax.axis('off')
    
    ratio = 1
    
    for iter in range(len(gdf_list)):
        temp_gdf = gdf_list[iter]
        temp_color = color_list[iter]
        for index, row in temp_gdf.iterrows():
            ax.scatter(row.geometry.x, row.geometry.y, s=ratio*row["Capacity (MW)"], color=temp_color, linewidths=0, edgecolor=None, alpha=0.5)

    # Define legend for circle sizes
    circle_sizes = [1, 0.5, 0.1]  # Define circle sizes for legend
    legend_circle_labels = ['1 MW', '0.5 MW', '0.1 MW']  # Corresponding labels
    
    former_rad = 0
    for iter in range(len(circle_sizes)):
        rad = circle_sizes[iter]
        text = legend_circle_labels[iter]
        if iter == 0:
            bound = bounds[1] + 0.11
        else:
            bound = bound + former_rad + rad + 0.1
        circle = Circle((bounds[0]-0.1, bound), radius=rad*ratio, color="#8d99ae", alpha=0.5, clip_on=False)
        ax.add_artist(circle)
        ax.text(bounds[0] + rad, bound, text, verticalalignment='center', fontfamily='Times New Roman')
        former_rad = rad
        



    # Define custom legend handles and labels
    legend_handles = [
        Patch(color='#001427', label='Coal'),
        Patch(color="#0077b6", label='Wind'),
        Patch(color="#d62828", label='Atomic'),
        Patch(color="#fca311", label='Solar'),
        Patch(color="#70e000", label='Wind'),
    ]
    
    # Add legend to the plot
    legend = plt.legend(handles=legend_handles, loc='upper left', frameon=False,
                        bbox_to_anchor=(0, 0.98, 1, 0.2), mode="expand", borderaxespad=0, ncol=5)
    
    for text in legend.get_texts():
        text.set_fontfamily('Times New Roman')

    #plt.tight_layout()
    plt.savefig(save_path, dpi=900)
    plt.close()
    
    
    return None

if __name__ == "__main__":
    # Data import
    data_base_path = "./Data/SourceData/2023/"
    coal_df = pd.read_excel(data_base_path + "Global-Coal-Plant-Tracker-July-2023" + ".xlsx", sheet_name="Units")
    hydro_df = pd.read_excel(data_base_path + "Global-Hydropower-Tracker-May-2023" + ".xlsx", sheet_name="Data")
    hydro_df.rename({"Start Year":"Start year", "Retired Year": "Retired year", "Country 1":"Country"}, axis=1, inplace=True)
    nuclear_df = pd.read_excel(data_base_path + "Global-Nuclear-Power-Tracker-October-2023" + ".xlsx", sheet_name="Data")
    nuclear_df.rename({"Retirement Year": "Retired year", "Start Year":"Start year"}, axis=1, inplace=True)
    solar_df = pd.read_excel(data_base_path + "Global-Solar-Power-Tracker-May-2023" + ".xlsx", sheet_name="Data")
    wind_df = pd.read_excel(data_base_path + "Global-Wind-Power-Tracker-May-2023" + ".xlsx", sheet_name="Data")
    df_list = [coal_df, hydro_df, nuclear_df, solar_df, wind_df]
    
    gdf_provincial = gpd.read_file("./Data/ShapeData/GuangXi/guangxi.shp")
    
    year_list = [2000, 2010, 2022]
    
    for year in year_list:
        print(year)
        # Data filtering
        gdf_list = []
        for df in df_list:
            temp_gdf = data_filter(df, year)
            gdf = gpd.sjoin(temp_gdf, gdf_provincial, how='inner', op='within')
            gdf_list.append(gdf)
            
        # Data visualization
        visualization(gdf_list, gdf_provincial, year)