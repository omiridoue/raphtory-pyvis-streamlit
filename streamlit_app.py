!pip install matplotlib 

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import pyreadr

from pprint import pprint

import os
import glob

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

import inspect
from pprint import pprint

path = './Glasgow_data/'

for filename in glob.glob(os.path.join(path, '*.RData')): #only process .Rdata files in folder.
    with open(filename, encoding='utf-8', mode='r') as currentFile:
      file_index = (os.path.split(filename)[1]).replace('.RData', '')
      file_index = file_index.replace('-','_').lower()
      print(file_index) # use adjusted file names to name data objects

      globals()[file_index] = pyreadr.read_r(filename) # also works for Rds

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
                              cdn_resources='in_line',
                              width='100%',
                              bgcolor='#e5eaf9',
                              font_color='white',
                              directed=True,
                              neighborhood_highlight=True,
                              select_menu=False,
                              filter_menu=True # change to true if you want to display pyvis filtering options
                              )

pyvis_graph.barnes_hut()

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

count_per_combination = expanded_df.groupby(['src', 'periods']).size().reset_index(name='count')

# Iterate through each row in the original DataFrame
replicated_entry = []
for index, d in enumerate(pyvis_graph.edges):
    # Check if 'periods' is greater than 1
    #print(index)
    if mask_edge.loc[index, 'periods'] > 1:
        # Replicate the ith edge for each unit period above 1
        for _ in range(mask_edge.loc[index, 'periods'] - 1):
            d_temp = d.copy()
            d_temp.update((k, f"{mask_edge.loc[index,'periods']}") for k, v in d.items() if k == 'title')
            replicated_entry.append(d_temp)
            #pyvis_graph.add_edge(replicated_entry['from'], replicated_entry['to'])

mask_edge.rename(columns={'src': 'src_id', 'dst': 'dst_id', 'periods': 'time'}, inplace=True)
count_per_combination.rename(columns={'src': 'src_id', 'periods': 'time'}, inplace=True)

expanded_df.rename(columns={'src': 'src_id', 'dst': 'dst_id', 'periods': 'time'}, inplace=True)

for index, d in enumerate(pyvis_graph.edges):
    d.update((k, f"{mask_edge.loc[index,'time']}") for k, v in d.items() if k == 'title')

df_1 = node_temp[['id', 'time', 'color']]
df_1 = df_1.rename(columns={"id": "src_id"})
colored_edges = pd.merge(expanded_df, df_1, on=['src_id', 'time'], how='left')

family_smoking = pd.DataFrame(glasgow_various['familysmoking'])
family_smoking['parent.smoking'] = family_smoking['parent.smoking'].fillna(99)

family_smoking = family_smoking.rename(columns={"parent.smoking": "parent"})
family_smoking['parent'] = family_smoking['parent'].replace(1, 0)
family_smoking['parent'] = family_smoking['parent'].replace(2,1)

family_smoking['parent'] = family_smoking['parent'].astype('int64')

color_parent = ["#757AD8","#483D8B"] # Manually selected, same as visualse in R code

node_parent = [color_parent[value] if value is not None else '#808080' for value in family_smoking.parent]
node_list_parent= node_parent * 3

df_1['parent_smoking'] = node_list_parent

df_1 = pd.merge(df_1, count_per_combination, on=['src_id', 'time'], how='left')

df_1 = df_1.fillna(0)
df_1['count'] = df_1['count'].astype('Int64')
df_1['count'] = df_1['count'].apply(lambda x: np.ceil(20+25*np.log(x+1))).astype('Int64')

df_1 = df_1.replace(0, 10)

subset = colored_edges[colored_edges['count']>1]

subset =  subset.drop(subset[(subset['count']==2) & (subset['time']==1)].index)
subset =  subset.drop(subset[(subset['count']==3) & (subset['time']==1)].index)
subset =  subset.drop(subset[(subset['count']==2) & (subset['time']==2) & (subset['first_inst']==2)].index)

subset_new = subset.reset_index(drop = True, inplace = False)

color_df = pd.DataFrame(colored_edges)

outer_merge = color_df.drop(subset.index)
outer_merge.reset_index(drop = True, inplace = True)

for index, d in enumerate(pyvis_graph.edges):
    d.update((k, f"{outer_merge.loc[index,'time']}") for k, v in d.items() if k == 'title')
    d.update((k, f"{outer_merge.loc[index,'color']}") for k, v in d.items() if k == 'color')

# Iterate through each row in the original DataFrame
for index, d in enumerate(replicated_entry):
    pyvis_graph.add_edge(source = replicated_entry[index]['from'],
                         to = replicated_entry[index]['to'],
                         title = f"{subset_new['time'][index]}",
                         arrowStrikethrough = replicated_entry[index]['arrowStrikethrough'],
                         value = replicated_entry[index]['value'],
                         color = f"{subset_new['color'][index]}",
                         arrows = replicated_entry[index]['arrows']
                         )

for index, d in enumerate(pyvis_graph.edges):
    d['value'] = d.get('title', '')  # Adds a new key 'title' with the value of 'label'
    d['hidden'] = True  # Adds a new key 'title' with the value of 'label'
    if d['title'] in ["1"]:
       d.update((k, False) for k, v in d.items() if k == 'hidden')

for index, d in enumerate(pyvis_graph.edges):
    #d['value'] = d.get('title', '')  # Adds a new key 'title' with the value of 'label'
    d['hidden'] = True  # Adds a new key 'title' with the value of 'label'
    if d['title'] in ["1"]:
       d.update((k, False) for k, v in d.items() if k == 'hidden')


for index, d in enumerate(pyvis_graph.nodes):
    d.update((k, f"diamond") for k, v in d.items() if k == 'shape')
    d['title'] = d.get('label', '')  # Adds a new key 'title' with the value of 'label'
    #d['size'] = 150

    # Update nested 'color' under 'font' to 'black'
    if 'font' in d:
        d['font'].update((k, '#13345e') for k, v in d['font'].items() if k == 'color')

 #pyvis_graph.nodes

st.title('Glasgow Teenage Friendship Network')

slider = st.slider(
    min_value = 1,
    max_value = 3,
    value=1,
    label='Filter by Wave:'
)
st.write("Wave:", slider)

for index, d in enumerate(pyvis_graph.edges):
    d['value'] = 2  # Adds a new key 'title' with the value of 'label'
    d['hidden'] = True  # Adds a new key 'title' with the value of 'label'

    if d['title'] in [f'{slider}']:
       d.update((k, False) for k, v in d.items() if k == 'hidden')

df_parent_col = pd.DataFrame()
df_parent_col = df_1.loc[df_1['time'] == slider][:]
df_parent_col.parent_smoking = df_parent_col.parent_smoking.astype('string')

df_parent_col.reset_index(inplace=True, drop=True)

for index, d in enumerate(pyvis_graph.nodes):
    d.update((k, np.int(df_parent_col.loc[index,'count'])) for k, v in d.items() if k == 'size')
    d.update((k, f"{df_parent_col.loc[index,'parent_smoking']}") for k, v in d.items() if k == 'color')

pyvis_graph.repulsion(
                    node_distance=420,
                    central_gravity=0.33,
                    spring_length=110,
                    spring_strength=0.10,
                    damping=0.95
                    )

pyvis_graph.show_buttons(filter_=['nodes'])
#'manipulation', 'interaction', 'edges'

options = {
    "interaction": {
        "hover": True,
        "selectConnectedEdges": True

    }
}

# Step 5: Define the options
pyvis_graph.set_options = options

#pyvis_graph.set_template('/content/')
#pyvis_graph.generate_html(name='template.html', local=True, notebook=False)

# Save and read graph as HTML file (on Streamlit Sharing)
try:
    path = '/tmp'
    pyvis_graph.save_graph(f'{path}/pyvis_graph.html')
    HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

# Save and read graph as HTML file (locally)
except:
    path = '/html_files'
    pyvis_graph.save_graph(f'{path}/pyvis_graph.html')
    HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

# Load HTML file in HTML component for display on Streamlit page
components.html(HtmlFile.read(), height=1500, width=900)
