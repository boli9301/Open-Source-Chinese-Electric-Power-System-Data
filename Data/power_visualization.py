def osm_data_import_os(place, network, filter, save_path, plot_state):
    '''
    Import the osm data of the country designated by parameter "place"
    Save cache into the folder "cache"
    Save the constructed model as "graph.graphml"
    
    Parameters
    ----------
    place: designate the geographic region of interest
    network: specify the network type
    filter: add filter parameter to save the interest information only
    save_path: specify the path to save the network graphml model
    plot_state: determine whether to plot the figure, 1 for plot
    '''
    
    import osmnx as ox
    from shapely.errors import GEOSException
    # map data source http://download.geofabrik.de/asia.html
    
    # Construct the graphml object
    ox.config(use_cache=True, log_console=True)
    try:
        G = ox.graph_from_place(place, network_type= network, custom_filter= filter, retain_all = False, simplify=True)
    except GEOSException:
        pass
    
    # Save graph as graphml
    ox.save_graphml(G, save_path + "/GuangXiGraph.graphml")
    
    # Calculate basic street network metrics and display average circuitry
    stats = ox.basic_stats(G)
    print(stats)
    
    # Visualization
    if plot_state == 1:
        fig, ax = ox.plot_graph(G)
    return G, stats

def df_to_gdf(df, lon_name, lat_name):
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
    gdf = gpd.GeoDataFrame(df, 
                          crs = crs, 
                          geometry = geometry)
    
    return gdf

def infra_data_import(infra_data, shapefile):
    '''
    Import the infrastructure data and visualize together with the power grid saved in graphml
    
    Parameters
    ----------
    infra_data: xlsx data containing the power infrastructure
    shapefile: the shapefile of interested place
    '''
    import pandas as pd
    import geopandas as gpd
    import numpy as np
    
    atomic_data = "nuclear power plant"
    solar_data = "solar power plant"
    thermal_data = "coal power plant"
    wind_data = "wind power plant"
    gas_data = "gas power plant"
    water_data = "hydro power plant"
    
    # Import the shapefile of interested place
    gdf_provincial = gpd.read_file(shapefile)
    
    # Import the data
    atomic = pd.read_excel(infra_data, index_col=None, sheet_name=atomic_data)
    atomic.rename(columns = {'capacity_mw':'MW'}, inplace = True)
    atomic = atomic[atomic["country"] == "CHN"]
    
    gas_0 = atomic[atomic["primary_fuel"] == "Gas"]
    thermal_0 = atomic[atomic["primary_fuel"] == "Coal"]
    water_0 = atomic[atomic["primary_fuel"] == "Hydro"]
    solar_0 = atomic[atomic["primary_fuel"] == "Solar"]
    wind_0 = atomic[atomic["primary_fuel"] == "Wind"]
    
    atomic = atomic[atomic["primary_fuel"] == "Nuclear"]
    atomic = atomic.reset_index()
    atomic = atomic[["MW","longitude", "latitude"]]
    atomic = df_to_gdf(atomic, "longitude", "latitude")
    atomic = gpd.sjoin(atomic, gdf_provincial, how='inner', op='within')

    gas = pd.read_excel(infra_data, index_col=None, sheet_name=gas_data)
    gas.rename(columns = {'capacity_mw':'MW'}, inplace = True)
    gas = gas[gas["province.1"] == "Guangxi"]
    gas = gas[["MW","longitude", "latitude"]]
    gas = gas._append(gas_0, ignore_index = True)
    gas = gas.reset_index()
    gas = df_to_gdf(gas, "longitude", "latitude")
    gas = gpd.sjoin(gas, gdf_provincial, how='inner', op='within')
    
    thermal = pd.read_excel(infra_data, index_col=None, sheet_name=thermal_data)
    thermal.rename(columns = {'Capacity_MW':'MW', "Longitude":"longitude", "Latitude":"latitude"}, inplace = True)
    thermal = thermal[thermal["province"] == "Guangxi"]
    thermal = thermal[["MW","longitude", "latitude"]]
    thermal = thermal._append(thermal_0, ignore_index = True)
    thermal = thermal.reset_index()
    thermal = df_to_gdf(thermal, "longitude", "latitude")
    thermal = gpd.sjoin(thermal, gdf_provincial, how='inner', op='within')
    
    water = pd.read_excel(infra_data, sheet_name=water_data, index_col=None)
    water.rename(columns = {'Install_Nom':'MW', "Lon_P_X":"longitude", "Lat_P_Y":"latitude"}, inplace = True)
    water = water[water["Province"] == "Guangxi"]
    water = water[["MW","longitude", "latitude"]]
    water = water._append(water_0, ignore_index = True)
    water = water.reset_index()
    water = df_to_gdf(water, "longitude", "latitude")
    water = gpd.sjoin(water, gdf_provincial, how='inner', op='within')
    
    #########################################################
    # No coordinates
    solar = pd.read_excel(infra_data, sheet_name=solar_data, index_col=None)
    solar['MW'] = solar['装机容量(MW)'].replace('', np.nan)
    solar = solar.dropna(subset=['MW'])
    solar['编号'] = solar['编号'].replace('编号', np.nan)
    solar = solar.dropna(subset=['编号'])
    solar = solar[["MW","longitude", "latitude"]]
    solar = solar._append(solar_0, ignore_index = True)
    solar = solar.reset_index()
    solar = df_to_gdf(solar, "longitude", "latitude")
    solar = gpd.sjoin(solar, gdf_provincial, how='inner', op='within')
    
    wind = pd.read_excel(infra_data, sheet_name=wind_data, index_col=None)
    wind['MW'] = wind['装机容量(MW)'].replace('', np.nan)
    wind = wind.dropna(subset=['MW'])
    wind['编号'] = wind['编号'].replace('编号', np.nan)
    wind = wind.dropna(subset=['编号'])
    wind = wind[["MW","longitude", "latitude"]]
    wind = wind._append(wind_0, ignore_index = True)
    wind = wind.reset_index()
    wind = df_to_gdf(wind, "longitude", "latitude")
    wind = gpd.sjoin(wind, gdf_provincial, how='inner', op='within')
    
    return atomic, solar, thermal, wind, gas, water

def gx_grid_mapping(graph, figure_path, shapefile_path, plot_state):
    '''
    Carry out the visualization and save figure
    
    Parameters
    ----------
    graph: the power graph constructed from graphml obtained earlier
    figure_path: the path to save figure
    shapefile_path: the path of the shapefile of place of interest
    plot_state: determine whether to plot the figure, 1 for plot
    '''
    import osmnx as ox
    import matplotlib.pyplot as plt
    import geopandas as gpd
    
    # Add the provincial border line
    # https://data.humdata.org/dataset/cod-ab-chn
    gdf_provincial = gpd.read_file()

    # Plot the figure
    if plot_state == 1:
        fig, ax = ox.plot_graph(graph,
                                bgcolor="#FFFFFF",
                                node_color="#457b9d",
                                node_size=0,
                                edge_color="#000000",
                                save=False,
                                close=False,
                                show=False)

        # Add the place shape to this matplotlib axis
        gdf_provincial.plot(ax=ax, ec="#d9d9d9", lw=1, facecolor="none")
        
        #####################################################################
        # Add data
        atomic, solar, thermal, wind, gas, water = infra_data_import(infra_data="./Data/SourceData/Power plant database of Guangxi.xlsx",
                                                                     shapefile=shapefile_path)
        water.plot(ax=ax, color="#0077b6", markersize=water["MW"], alpha = 0.5, label="Hydro", legend=True)
        thermal.plot(ax=ax, color="#001427", markersize=thermal["MW"], alpha = 0.5, label="Thermal")
        solar.plot(ax=ax, color="#fca311", markersize=solar["MW"], alpha = 0.5, label="Solar")
        gas.plot(ax=ax, color="#9d4edd", markersize=gas["MW"], alpha = 0.5, label="Gas")
        atomic.plot(ax=ax, color="#d62828", markersize=atomic["MW"], alpha = 0.5, label="Nuclear")
        wind.plot(ax=ax, color="#70e000", markersize=wind["MW"], alpha = 0.5, label="Wind")
        
        # Set the label
        #####################################################################
        
        #size_values = [1, 10]  # Choose the specific size values you want to include in the legend
        #legend_labels = [str(size) for size in size_values]

        # Create custom legend handles with the chosen size values
        #handles = [plt.Line2D([], [], marker='o', linestyle='None', markersize=size, label=label, alpha = 0.5) for size, label in zip(size_values, legend_labels)]
        #ax.legend(labels=legend_labels, handles=handles, bbox_to_anchor=(1.05, 1))

        #####################################################################

        # Optionally set up the axes extents
        margin = 0.02
        west, south, east, north = gdf_provincial.unary_union.bounds
        margin_ns = (north - south) * margin
        margin_ew = (east - west) * margin
        ax.set_ylim((south - margin_ns, north + margin_ns))
        ax.set_xlim((west - margin_ew, east + margin_ew))
        
        # Save and show figure
        plt.savefig(figure_path + "/GuangXiDistribution.png", dpi=900)
        plt.show()

    return graph

if __name__ == "__main__":
    import osmnx as ox
    
    # Import the osm power data
    #osm_data, osm_stats = osm_data_import_os('Guangxi, China', 'all', '["power"~"line"]', "./Data/Intermediate", 0)
    
    # Import the collected power grid system of Guangxi Province
    gx_graph = ox.load_graphml("./Data/Intermediate/GuangXiPower.graphml")
    
    # Plot the distribution of power plants in Guangxi Province
    gx_grid_mapping(graph=gx_graph, 
                    figure_path="./Result/Figure",
                    shapefile_path="./Data/ShapeData/GuangXi/guangxi.shp", 
                    plot_state=1)
    

    