import pandas as pd
import numpy as np

import pyreadr

from raphtory import Graph
from raphtory import algorithms as algo
#from raphtory import graphqlserver

from raphtory import export
from IPython.display import display, HTML

import ipywidgets as ipy
from ipywidgets import interact

import streamlit as st
import streamlit.components.v1 as components
import seaborn as sns

import pandas as pd

import matplotlib.cm as cm
import matplotlib.colors as mcolors

glasgow_friendship = pyreadr.read_r("./data/Glasgow-friendship.RData")
glasgow_substances = pyreadr.read_r("./data/Glasgow-substances.RData")
glasgow_various = pyreadr.read_r("./data/Glasgow-various.RData")

adj_t1 = pd.DataFrame(glasgow_friendship['friendship.1'])
adj_t2 = pd.DataFrame(glasgow_friendship['friendship.2'])
adj_t3 = pd.DataFrame(glasgow_friendship['friendship.3'])

# I have made all values binary and recoded struct. zeroes to zeroes

adj_t1 = adj_t1.fillna(0)
adj_t1 = adj_t1.replace(10.0, 0.0)
adj_t1 = adj_t1.replace(2.0, 1.0)

# I have made all values binary and recoded struct. zeroes to zeroes

adj_t2 = adj_t2.fillna(0)
adj_t2 = adj_t2.replace(10.0, 0.0)
adj_t2 = adj_t2.replace(2.0, 1.0)

# I have made all values binary and recoded struct. zeroes to zeroes

adj_t3 = adj_t3.fillna(0)
adj_t3 = adj_t3.replace(10.0, 0.0)
adj_t3 = adj_t3.replace(2.0, 1.0)

adj_t1.rename_axis('Source')\
  .reset_index()\
  .melt('Source', value_name='Weight', var_name='Target')\
  .query('Source != Target and (Weight != 0)')\
  .reset_index(drop=True)

smoking = pd.DataFrame(glasgow_substances['tobacco']).fillna(0)

smoking.loc[:, ['t1','t2','t3']] = smoking[['t1','t2','t3']].astype(int)

# Melt the DataFrame to reshape it
smoking = smoking.rename_axis('id')\
                  .reset_index()

node_temp = pd.melt(smoking, var_name='time', value_name='tobacco', id_vars=['id'])
node_temp['time'] = node_temp['time'].str.extract('(\d+)', expand=False)

colormap = cm.winter_r
# Normalize 'smoking_t2' values to the range [0, 1]
norm = mcolors.Normalize(vmin=min(node_temp.tobacco), vmax=max(node_temp.tobacco))
color_list = ["#5F9EA0", "#318CE7", "#0066b2", "#00308F"] # Manually selected, same as visualse in R code

# Map 'smoking_t2' values to colors using the colormap
#node_colors = [cm.colors.to_hex(colormap(norm(value))) if value is not None else '#808080' for value in node_temp.tobacco]
node_colors = [color_list[value] if value is not None else '#808080' for value in node_temp.tobacco]

node_temp['color'] = node_colors
node_temp = pd.DataFrame(node_temp)

# Assuming adj_t1, adj_t2, adj_t3 are your dataframes
# Adjust the range accordingly based on your actual data

dfs = []  # To store individual dataframes

for i in range(1, 4):  # Assuming adj_t1 through adj_t3
    placeholder = globals()[f'adj_t{i}']  # Fetch the dataframe dynamically
    result_df = placeholder.rename_axis('Source')\
                  .reset_index()\
                  .melt('Source', value_name='Weight', var_name='Target')\
                  .query('(Source != Target) and (Weight != 0)')\
                  .reset_index(drop=True)

    result_df['Time'] = f'{i}'  # Add a new column indicating the time

    dfs.append(result_df)

# Concatenate the dataframes in the list
df = pd.concat(dfs, ignore_index=True)

# Display the final dataframe
df.rename(columns={'Source': 'src_id', 'Target': 'dst_id', 'Time': 'time'}, inplace=True)

df['time'] = df['time'].astype('int64')
df['Weight'] = df['Weight'].astype(int)

node_temp['time'] = node_temp['time'].astype('int64')
node_temp['tobacco'] = node_temp['tobacco'].astype(int)

node_cols = ["tobacco", "color"]
"""

"""
#node_temp

graph = Graph.load_from_pandas(node_df= node_temp,
                               node_time = "time",
                               node_id= "id",
                               node_props= node_cols,
                               edge_df=df,
                               edge_src="src_id",
                               edge_dst="dst_id",
                               edge_time="time"
                               )

pyvis_graph = export.to_pyvis(graph=graph,
                              notebook=True,
                              #heading="Glasgow Teenage Friendship Network",
                              height='900px',
                              width='100%',
                              bgcolor='#e5eaf9',
                              font_color='white',
                              directed=True,
                              neighborhood_highlight=True,
                              select_menu=False,
                              cdn_resources = 'in_line',
                              filter_menu=True # change to true if you want to display pyvis filtering options
                              )

pyvis_graph.barnes_hut(gravity=-1000000, central_gravity=0.3)

mask_edge = export.to_edge_df(graph)

mask_edge['periods'] = mask_edge['update_history'].apply(len)

#print(mask_edge[['src', 'dst', 'update_history', 'periods']])

counting_src_orig = [str(i['from']) for i in pyvis_graph.edges]

counting_to_orig = [str(i['to']) for i in pyvis_graph.edges]

mask_edge['from'] = counting_src_orig
mask_edge['to'] = counting_to_orig

expanded_df = pd.DataFrame()

for _, row in mask_edge.iterrows():
    # Check if 'periods' is greater than 1
    if row['periods'] > 1:
        # Duplicate the row for each period, set 'periods' to 1, 2, 3, and append to the new DataFrame
        expanded_rows = pd.DataFrame([row.copy() for _ in range(row['periods'])])
        expanded_rows['periods'] = range(1, row['periods'] + 1)
        expanded_df = pd.concat([expanded_df, expanded_rows], ignore_index=True)
    else:
        # If 'periods' is 1, simply append the row to the new DataFrame
        expanded_df = pd.concat([expanded_df, pd.DataFrame([row])], ignore_index=True)

period_len_vec = expanded_df.groupby(['src', 'dst']).size().reset_index(name='count')

expanded_df = pd.merge(expanded_df, period_len_vec, on=['src', 'dst'], how='left')

expanded_df['periods']=expanded_df.apply(lambda x: x['update_history'][0] if x['count']==1 else x['periods'], axis=1)

expanded_df['periods']=expanded_df.apply(lambda x: x['update_history'][1] if (x['count']==2 and x['periods']==2) else x['periods'], axis=1)

expanded_df['periods']=expanded_df.apply(lambda x: x['update_history'][0] if (x['count']==2 and x['periods']==1) else x['periods'], axis=1)

expanded_df['first_inst']=expanded_df.apply(lambda x: x['update_history'][0], axis=1)

count_per_combination = expanded_df.groupby(['src', 'periods'])
