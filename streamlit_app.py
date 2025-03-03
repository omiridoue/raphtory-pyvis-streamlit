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
smoking = (
    pd.DataFrame(glasgow_substances["tobacco"])
    .fillna(0)
    .astype(int)
    .rename_axis("id")
    .reset_index()
    .melt(id_vars=["id"], var_name="time", value_name="tobacco")
)
smoking["time"] = smoking["time"].str.extract("(\d+)").astype(int)

color_map = ["#5F9EA0", "#318CE7", "#0066b2", "#00308F"]
smoking["color"] = smoking["tobacco"].apply(lambda x: color_map[x])

# Create Raphtory Graph
graph = Graph.load_from_pandas(
    node_df=smoking, node_time="time", node_id="id", node_props=["tobacco", "color"],
    edge_df=df, edge_src="src_id", edge_dst="dst_id", edge_time="time"
)

# Export to Pyvis for Visualization
pyvis_graph = export.to_pyvis(
    graph=graph, height="800px", width="100%", bgcolor="#e5eaf9",
    font_color="white", directed=True, neighborhood_highlight=True
)
pyvis_graph.barnes_hut(gravity=-1000000, central_gravity=0.3)

# Make Graph Interactive & Responsive
pyvis_graph.show_buttons(filter_=["nodes", "edges", "physics"])
pyvis_graph.set_edge_smooth("straightCross")
pyvis_graph.repulsion(node_distance=420, central_gravity=0.33, spring_length=110, damping=0.95)

# Save Graph as HTML (Ensure it exists before reading)
graph_path = "/tmp/pyvis_graph.html"
pyvis_graph.save_graph(graph_path)

# Streamlit UI
st.title("Glasgow Teenage Friendship Network Visual")

# Sidebar Information
with st.sidebar:
    st.subheader("How to Use This Visualization")
    st.markdown("""
    - Nodes represent students.
    - Links show friendships (directional).
    - Darker colors indicate higher smoking frequency.
    - Use the dropdowns below to explore relationships!
    """)
    st.image("MRC_CSO_SPHSU_Glasgow_RGB_0.png")

# Fix CSS for Responsive Graph
st.markdown("""
<style>
    .vis-network {
        width: 100% !important;
        height: 80vh !important;
    }
</style>
""", unsafe_allow_html=True)

# Load Graph into Streamlit
if os.path.exists(graph_path):
    with open(graph_path, "r", encoding="utf-8") as HtmlFile:
        components.html(HtmlFile.read(), height=800)
else:
    st.error("Graph failed to generate. Please check data processing.")
  
