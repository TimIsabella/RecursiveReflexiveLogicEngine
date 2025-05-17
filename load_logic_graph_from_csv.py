
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

def load_graph_from_csv(nodes_path, edges_path):
    # Load CSV files
    nodes_df = pd.read_csv(nodes_path)
    edges_df = pd.read_csv(edges_path)

    # Initialize directed graph
    G = nx.DiGraph()

    # Add nodes with attributes
    for _, row in nodes_df.iterrows():
        G.add_node(row['id'], type=row['type'], value=row['value'])

    # Add edges with weights
    for _, row in edges_df.iterrows():
        G.add_edge(row['source'], row['target'], weight=row['weight'])

    return G

def visualize_logic_graph(G):
    # Color map by node type
    color_map = []
    for node in G.nodes:
        node_type = G.nodes[node].get('type', 'input')
        if node_type == 'input':
            color_map.append('skyblue')
        elif node_type == 'meta':
            color_map.append('lightcoral')
        else:
            color_map.append('gold')

    # Edge weights
    edge_weights = [G[u][v].get('weight', 1.0) * 2 for u, v in G.edges()]

    # Layout and draw
    pos = nx.spring_layout(G)
    plt.figure(figsize=(14, 10))
    nx.draw(G, pos, with_labels=True, node_color=color_map, node_size=1600,
            font_size=10, width=edge_weights, arrows=True)
    plt.title("Logic Graph from CSV")
    plt.show()

# Example usage
if __name__ == "__main__":
    G = load_graph_from_csv("nodes.csv", "edges.csv")
    visualize_logic_graph(G)
