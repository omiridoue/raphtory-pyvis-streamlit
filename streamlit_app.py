import pandas as pd
import numpy as np
import pyreadr
from raphtory import Graph
from raphtory import export
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.cm as cm
import matplotlib.colors as mcolors

# Load data
glasgow_friendship = pyreadr.read_r("./data/Glasgow-friendship.RData")
glasgow_substances = pyreadr.read_r("./data/Glasgow-substances.RData")
glasgow_various = pyreadr.read_r("./data/Glasgow-various.RData")

# Process friendship data
def process_adjacency(adj_df):
    adj_df = adj_df.fillna(0).replace({10.0: 0.0, 2.0: 1.0})
    return adj_df.rename_axis('Source').reset_index().melt('Source', value_name='Weight', var_name='Target').query('Source != Target and (Weight != 0)').reset_index(drop=True)

adj_t1 = process_adjacency(pd.DataFrame(glasgow_friendship['friendship.1']))
adj_t2 = process_adjacency(pd.DataFrame(glasgow_friendship['friendship.2']))
adj_t3 = process_adjacency(pd.DataFrame(glasgow_friendship['friendship.3']))

# Process smoking data
smoking = pd.DataFrame(glasgow_substances['tobacco']).fillna(0)
smoking.loc[:, ['t1', 't2', 't3']] = smoking[['t1', 't2', 't3']].astype(int)
smoking = smoking.rename_axis('id').reset_index()
node_temp = pd.melt(smoking, var_name='time', value_name='tobacco', id_vars=['id'])
node_temp['time'] = node_temp['time'].str.extract('(\d+)', expand=False).astype(int)
node_temp['tobacco'] = node_temp['tobacco'].astype(int)

# Color mapping for smoking
color_list = ["#5F9EA0", "#318CE7", "#0066b2", "#00308F"]
node_colors = [color_list[value] if value is not None else '#808080' for value in node_temp.tobacco]
node_temp['color'] = node_colors

# Combine adjacency dataframes
dfs = [process_adjacency(globals()[f'adj_t{i}']).assign(Time=f'{i}') for i in range(1, 4)]
df = pd.concat(dfs, ignore_index=True).rename(columns={'Source': 'src_id', 'Target': 'dst_id', 'Time': 'time'})
df['time'] = df['time'].astype(int)
df['Weight'] = df['Weight'].astype(int)

# Create Raphtory Graph
node_cols = ["tobacco", "color"]
graph = Graph.load_from_pandas(node_df=node_temp, node_time="time", node_id="id", node_props=node_cols, edge_df=df, edge_src="src_id", edge_dst="dst_id", edge_time="time")

# Export to Pyvis
pyvis_graph = export.to_pyvis(graph=graph, notebook=True, height='900px', width='100%', bgcolor='#e5eaf9', font_color='white', directed=True, neighborhood_highlight=True, select_menu=False, cdn_resources='in_line', filter_menu=True)
pyvis_graph.barnes_hut(gravity=-1000000, central_gravity=0.3)

# Process edge data
mask_edge = export.to_edge_df(graph)
mask_edge['periods'] = mask_edge['update_history'].apply(len)
mask_edge['from'] = [str(i['from']) for i in pyvis_graph.edges]
mask_edge['to'] = [str(i['to']) for i in pyvis_graph.edges]

expanded_df = pd.concat([pd.DataFrame([row.copy() for _ in range(row['periods'])], index=range(row['periods'])) if row['periods'] > 1 else pd.DataFrame([row]) for _, row in mask_edge.iterrows()], ignore_index=True)
expanded_df['periods'] = expanded_df.groupby(['src', 'dst']).cumcount() + 1
period_len_vec = expanded_df.groupby(['src', 'dst']).size().reset_index(name='count')
expanded_df = pd.merge(expanded_df, period_len_vec, on=['src', 'dst'], how='left')
expanded_df['periods'] = expanded_df.apply(lambda x: x['update_history'][0] if x['count'] == 1 else (x['update_history'][1] if (x['count'] == 2 and x['periods'] == 2) else (x['update_history'][0] if (x['count'] == 2 and x['periods'] == 1) else x['periods'])), axis=1)
expanded_df['first_inst'] = expanded_df['update_history'].apply(lambda x: x[0])
count_per_combination = expanded_df.groupby(['src', 'periods']).size().reset_index(name='count')

# Replicate edges
replicated_entry = [d.copy().update((k, f"{mask_edge.loc[index,'periods']}") for k, v in d.items() if k == 'title') or d for index, d in enumerate(pyvis_graph.edges) for _ in range(mask_edge.loc[index, 'periods'] - 1) if mask_edge.loc[index, 'periods'] > 1]

# Rename columns
mask_edge.rename(columns={'src': 'src_id', 'dst': 'dst_id', 'periods': 'time'}, inplace=True)
count_per_combination.rename(columns={'src': 'src_id', 'periods': 'time'}, inplace=True)
expanded_df.rename(columns={'src': 'src_id', 'dst': 'dst_id', 'periods': 'time'}, inplace=True)

# Update edge titles and colors
for index, d in enumerate(pyvis_graph.edges):
    d.update((k, f"{mask_edge.loc[index,'time']}") for k, v in d.items() if k == 'title')

df_1 = node_temp[['id', 'time', 'color']].rename(columns={"id": "src_id"})
colored_edges = pd.merge(expanded_df, df_1, on=['src_id', 'time'], how='left')

# Process family smoking data
family_smoking = pd.DataFrame(glasgow_various['familysmoking']).rename(columns={"parent.smoking": "parent"})
family_smoking['parent'] = family_smoking['parent'].fillna(99).replace({1: 0, 2: 1}).astype(int)
color_parent = ["#757AD8", "#483D8B"]
node_list_parent = [color_parent[value] if value is not None else '#808080' for value in family_smoking.parent] * 3
df_1['parent_smoking'] = node_list_parent
df_1 = pd.merge(df_1, count_per_combination, on=['src_id', 'time'], how='left').fillna(0)
df_1['count'] = df_1['count'].astype('Int64').apply(lambda x: np.ceil(20 + 25 * np.log(x + 1))).astype('Int64').replace(0, 10)

# Subset and merge
subset = colored_edges[(colored_edges['count'] > 1) & ~((colored_edges['count'] == 2) & (colored_edges['time'] == 1)) & ~((colored_edges['count'] == 3) & (colored_edges['time'] == 1)) & ~((colored_edges['count'] == 2) & (colored_edges['time'] == 2) & (colored_edges['first_inst'] == 2))].reset_index(drop=True)
outer_merge = colored_edges.drop(subset.index).reset_index(drop=True)

# Update edge attributes
for index, d in enumerate(pyvis_graph.edges):
    d.update((k, f"{outer_merge.loc[index,'time']}") for k, v in d.items() if k == 'title')
    d.update((k, f"{outer_merge.loc[index,'color']}") for k, v in d.items
