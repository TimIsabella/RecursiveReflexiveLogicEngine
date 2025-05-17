
import networkx as nx
import random
from collections import defaultdict
import pandas as pd

# Initialize graph
G = nx.DiGraph()

# Base inputs
G.add_node("I1", type="input", value=random.randint(0, 1))
G.add_node("I2", type="input", value=random.randint(0, 1))

def evaluate_consistency(val1, val2):
    return val1 == val2

# Meta-layer
G.add_node("M1", type="meta", value=evaluate_consistency(G.nodes["I1"]["value"], G.nodes["I2"]["value"]))
G.add_edge("I1", "M1")
G.add_edge("I2", "M1")

# Initialize structures
memory = []
trust_weights = defaultdict(lambda: 1.0)
contradiction_buffer = []
reward_history = []
goal_state = True

def weighted_consistency(val1, val2, memory, key, trust_weights):
    bias = trust_weights[key]
    normal_consistency = val1 == val2
    result = normal_consistency if bias >= 0.5 else not normal_consistency
    expected = normal_consistency
    if result != expected:
        contradiction_buffer.append({'pair': key, 'expected': expected, 'evaluated': result})
    return result

def evolve_with_weights(G, memory, trust_weights, contradiction_buffer, steps=5):
    current_index = max(int(n[1:]) for n in G.nodes if n.startswith("I")) + 1
    for i in range(current_index, current_index + steps):
        prev_input = f"I{i-1}"
        new_input = f"I{i}"
        G.add_node(new_input, type="input", value=random.randint(0, 1))
        key = (G.nodes[prev_input]["value"], G.nodes[new_input]["value"])
        consistent = weighted_consistency(G.nodes[prev_input]["value"], G.nodes[new_input]["value"], memory, key, trust_weights)
        memory.append({'i1': prev_input, 'i2': new_input, 'key': key, 'evaluated_consistent': consistent})
        trust_weights[key] += 0.05 if consistent else -0.05
        trust_weights[key] = max(0.0, min(1.0, trust_weights[key]))
        meta_node = f"M{i-2}"
        G.add_node(meta_node, type="meta", value=consistent)
        G.add_edge(prev_input, meta_node, weight=trust_weights[key])
        G.add_edge(new_input, meta_node, weight=trust_weights[key])
    return G

def create_meta_meta_nodes(G, cluster_size=3):
    meta_nodes = sorted([n for n in G.nodes if G.nodes[n]['type'] == 'meta'], key=lambda x: int(x[1:]))
    clusters = [meta_nodes[i:i+cluster_size] for i in range(0, len(meta_nodes), cluster_size)]
    for idx, cluster in enumerate(clusters):
        if len(cluster) < cluster_size:
            continue
        meta_meta_node = f"MM{idx}"
        values = [G.nodes[n]['value'] for n in cluster]
        consistent = values.count(True) >= 2
        G.add_node(meta_meta_node, type="meta-meta", value=consistent)
        for n in cluster:
            G.add_edge(n, meta_meta_node, weight=1.0)
    return G

def apply_goal_influence(G, goal_state, reward_history):
    for node in G:
        if G.nodes[node]['type'] == 'meta-meta':
            evaluation = G.nodes[node]['value']
            reward = 1 if evaluation == goal_state else -1
            reward_history.append({'node': node, 'reward': reward})
            for pred in G.predecessors(node):
                for sub_pred in G.predecessors(pred):
                    if G.has_edge(sub_pred, pred):
                        # Ensure weight exists before updating
                        if 'weight' not in G[sub_pred][pred]:
                            G[sub_pred][pred]['weight'] = 1.0
                        G[sub_pred][pred]['weight'] += 0.1 * reward
                        G[sub_pred][pred]['weight'] = max(0.1, min(2.0, G[sub_pred][pred]['weight']))
    return G

def restructure_from_contradictions(G, contradiction_buffer):
    for entry in contradiction_buffer:
        u_val, v_val = entry['pair']
        for u in G.nodes:
            if G.nodes[u].get('value') == u_val:
                for v in G.nodes:
                    if G.nodes[v].get('value') == v_val and G.has_edge(u, v):
                        G[u][v]['weight'] *= 0.8
                        if G[u][v]['weight'] < 0.2:
                            G.remove_edge(u, v)
    contradiction_buffer.clear()
    return G

def simulate_cycles(G, memory, trust_weights, contradiction_buffer, reward_history, cycles=5, cluster_size=3):
    for _ in range(cycles):
        G = evolve_with_weights(G, memory, trust_weights, contradiction_buffer, steps=3)
        G = create_meta_meta_nodes(G, cluster_size=cluster_size)
        G = apply_goal_influence(G, goal_state, reward_history)
        G = restructure_from_contradictions(G, contradiction_buffer)
    return G

# Run simulation
G = simulate_cycles(G, memory, trust_weights, contradiction_buffer, reward_history, cycles=111)

# Export to CSV
nodes_export = pd.DataFrame([
    {"id": n, **G.nodes[n]} for n in G.nodes
])
edges_export = pd.DataFrame([
    {"source": u, "target": v, **G[u][v]} for u, v in G.edges
])

nodes_export.to_csv("nodes.csv", index=False)
edges_export.to_csv("edges.csv", index=False)
