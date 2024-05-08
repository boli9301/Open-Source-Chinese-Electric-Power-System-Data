import pandas as pd
import numpy as np
import geopandas as gpd
import os
import time
import matplotlib.pyplot as plt
from shapely.wkt import loads
from matplotlib.font_manager import FontProperties
import seaborn as sns

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
    print(df)
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
            print(gdf)
            gdf_list.append(gdf)
            
        # Data visualization
        visualization(gdf_list, gdf_provincial, year)