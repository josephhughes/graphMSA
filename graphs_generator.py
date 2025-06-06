import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

data = pd.read_csv('sequence_identity_benchmark_data.csv')

def extract_data(data,identity_column,metric_columns):
    sequence_identities = data[identity_column].unique()
    grouped = data.set_index(identity_column).sort_index()
    metric_data = [
        grouped[col].values for col in metric_columns
    ]
    return sequence_identities, list(zip(*metric_data))  # Transpose

def plot_grouped_bars(sequence_identities, categories, metric_matrix, title, ylabel):
    import matplotlib.pyplot as plt

    bar_width = 0.8 / len(sequence_identities)
    x = list(range(len(categories)))

    plt.figure(figsize=(12, 6))
    
    for i, (identity, row) in enumerate(zip(sequence_identities, metric_matrix)):
        x_shifted = [xi + (i - len(sequence_identities) / 2) * bar_width + bar_width / 2 for xi in x]
        bars = plt.bar(x_shifted, row, width=bar_width, label=f'Seq ID: {identity}')

        # 🔢 Add value labels on top of each bar
        for xi, yi in zip(x_shifted, row):
            plt.text(xi, yi, f'{yi}', ha='center', va='bottom', fontsize=8)

    plt.xticks(x, categories)
    plt.xlabel('File Type')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend(title='Sequence Identity')
    plt.tight_layout()
    plt.show()


# names
names =  ['Compressed Edges', 'Many Edges', 'Many Nodes'] # joe, joseph, ifedayo

# File size
metric_cols = ['fasta_file_size', 'joe_file_size', 'joseph_file_size', 'ifed_file_size']
sequence_ids, matrix = extract_data(data, 'sequence_identity', metric_cols)
plot_grouped_bars(sequence_ids,['Fasta', 'Compressed Edges', 'Many Edges', 'Many Nodes'], matrix, 'File Size Comparison', 'File Size (bytes)')

# File time
metric_cols = ['joe_file_time', 'joseph_file_time', 'ifed_file_time']
sequence_ids, matrix = extract_data(data, 'sequence_identity', metric_cols)
plot_grouped_bars(sequence_ids, names, matrix, 'File Time Comparison', 'File Time (s)')

# Number of nodes
metric_cols = ['joe_node_number', 'joseph_node_number', 'ifed_node_number']
sequence_ids, matrix = extract_data(data, 'sequence_identity', metric_cols)
plot_grouped_bars(sequence_ids, names, matrix, 'Number of Nodes Comparison', 'Number of Nodes')

# Number of edges 
metric_cols = ['joe_relationship_number', 'joseph_relationship_number', 'ifed_relationship_number']
sequence_ids, matrix = extract_data(data, 'sequence_identity', metric_cols)
plot_grouped_bars(sequence_ids, names, matrix, 'Number of  Edges Comparison', 'Number of Edges')



