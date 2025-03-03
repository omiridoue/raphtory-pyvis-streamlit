import pandas as pd
import numpy as np
import pyreadr
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from raphtory import Graph, export
import os

# Load Data
glasgow_friendship = pyreadr.read_r("./data/Glasgow-friendship.RData")
glasgow_substances = pyreadr.read_r("./data/Glasgow-substances.RData")

# Convert Adjacency Matrices into Edges
def process_adjacency_matrix(adj_matrix, time_step):
    adj_matrix = adj_matrix.fillna(0).replace({10.0: 0.0, 2.0: 1.0})
    return (
        adj_matrix.rename_axis("Source")
        .reset_index()
        .melt("Source", value_name="Weight", var_name="Target")
        .query("Source != Target and Weight != 0")
        .assign(Time=time_step)
    )

df_list = [process_adjacency_matrix(glasgow_friendship[f'friendship.{i}'], i) for i in range(1, 4)]
df = pd.concat(df_list, ignore_index=True)
df.rename(columns={"Source": "src_id", "Target": "dst_id", "Time": "time"}, inplace=True)

# Process Node Attributes (Smoking Behavior)
smoking = pd.DataFrame(glasgow_substances["tobacco"]).fillna(0)
smoking = smoking.rename_axis('id').reset_index()
node_temp = pd.melt(smoking, var_name='time', value_name='tobacco', id_vars=['id'])
node_temp['time'] = node_temp['time'].str.extract('(\d+)', expand=False).astype(int)

color_list = ["#5F9EA0", "#318CE7", "#0066b2", "#00308F"]
node_temp['color'] = node_temp['tobacco'].apply(lambda x: color_list[x])

# Create Raphtory Graph
graph = Graph.load_from_pandas(
    node_df=node_temp, node_time="time", node_id="id", node_props=["tobacco", "color"],
    edge_df=df, edge_src="src_id", edge_dst="dst_id", edge_time="time"
)

# Export to Pyvis for Visualization
pyvis_graph = export.to_pyvis(
    graph=graph, height="800px", width="100%", bgcolor="#e5eaf9",
    font_color="white", directed=True, neighborhood_highlight=True
)
pyvis_graph.barnes_hut(gravity=-1000000, central_gravity=0.3)

# Graph Settings
pyvis_graph.show_buttons(filter_=["nodes", "edges", "physics"])
pyvis_graph.set_edge_smooth("straightCross")
pyvis_graph.repulsion(node_distance=420, central_gravity=0.33, spring_length=110, damping=0.95)

# ✅ Save Graph as HTML (Ensure it exists before reading)
graph_path = "/tmp/pyvis_graph.html"
pyvis_graph.save_graph(graph_path)

# Streamlit UI
st.title("Glasgow Teenage Friendship Network Visual")

with st.sidebar:
    st.subheader("Explore Smoking Behaviours through Different Elements of the Visual:")
    st.markdown("""
    - The edges connecting students in the school year show which way a friendship was initiated. 
    - The edges are colored dark blue for students reporting frequent smoking and light blue for those mentioning occasionally or never smoking.
    - A dark purple color for a node indicates whether a student mentioned a parent smoking at home.
    - Clicking on a node highlights those they have mentioned as friends.
    """)
    st.image("MRC_CSO_SPHSU_Glasgow_RGB_0.png")

# ✅ Fix for Mobile & Desktop Responsiveness
st.markdown("""
<style>
    .vis-network {
        width: 100% !important;
        height: 80vh !important;
        display: flex;
        justify-content: center;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# ✅ Ensure the Graph File Exists Before Loading
if os.path.exists(graph_path):
    with open(graph_path, "r", encoding="utf-8") as HtmlFile:
        components.html(HtmlFile.read(), height=800, width=1000)  # ✅ Properly loads the visualization
else:
    st.error("⚠️ Graph failed to generate. Please check data processing.")
