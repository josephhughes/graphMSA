# graphMSA
Graph representation of multiple sequence alignment and BAM files


This project provides a set of python scripts and cypher queries to transform multiple sequence alignment data into a Neo4j graph database. By representing sequences and their relationships as a graph, this approach enables a powerful visual exploration of genetic variations, shared regions and individual sequence paths.

This project explores different graph data models, evolving from simpler representations to more optimised variation graphs. Each model offers different advantages for querying and visualisation. 

# Getting Started

## Prerequisites:

1. Python 3
2. Neo4j Desktop or Server (a running neo4j instance is required, all scripts in this repository are configured to connect to neo4j://localhost:7690 or neo4j://localhost:7687)
3. Neo4j Python Driver (install it using pip: pip install neo4j)
4. Biopython (Install it using pip: pip install biopython)


## Installation:

1.	Clone this repository to your local machine
```
git clone <your-repo-url>
cd <your-repo-name>
```
3.	(recommended) Set up a Python Virtual Environment
```
python3 -m venv venv
source venv/bin/activate
```
Install dependencies within the virtual environment
```
pip install neo4j biopython
```
5.	Configure your neo4j connection and ensure your database is running and accessible
6.	IMPORTANT Update the AUTH tuple in all python scripts to match your actual neo4j username and password



## Database Management
Managing your neo4j database correctly is crucial, especially when switching between graph models or re-importing data.

### Clearing the Database
1.	Open neo4j browser
2.	Run the following cypher query
```
MATCH (n) DETACH DELETE n;
```

### Creating Constraints

For optimal performance, ensure the following constraints are created by running them in the Neo4j Browser before running the script in python:
```
CREATE CONSTRAINT IF NOT EXISTS FOR (s:Sample) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Nucleotide) REQUIRE (n.pos, n.base) IS UNIQUE;
```


# Scripts Overview

### check_differences.cypher
CYPHER code to quickly identify where individual sequences differ from a designated reference sequence. This query allows you to pinpoint the exact positions and base changes where a sample sequence deviates from the reference.

### fasta_to_graph.py
(Version 1) Building a Graph

This script processes FASTA-formatted sequence data and converts it into a graph database structure within Neo4j where each sequence is represented as a linear chain of nucleotide nodes for visualisation of individual sequence paths.

This version implements a “Separate Chains” graph model where each input sequence creates its own distinct set of nucleotide nodes.

Usage:
```
python3 fasta_to_graph.py <path_to_your_fasta_file>
```
Nodes: 

Sample – representing individual biological sequences

Nucleotide – representing a single nucleotide base within a sequence

Relationships:

:STARTS_AT – connects a sample node to its first nucleotide

:NEXT – links consecutive nucleotide nodes within the same sequence chain

### fasta_to_graphv2.py
(Version 2) Deduplicated Nucleotides

This script processes FASTA-formatted sequence data and converts it into a graph database structure within Neo4j. This script builds on v1 by deduplicating identical nucleotide bases at the same position across different sequences, making the graph more efficient for visualising shared genetic regions.

This optimised graph model merges nucleotide nodes that are representing the same base at the same position, rather than creating separate nodes for each sequence. This means common regions are represented by a single, shared path of nucleotide nodes.

Usage:
```
python3 fasta_to_graphv2.py <path_to_your_fasta_file>
```
Nodes: 

Sample – representing individual biological sequences

Nucleotide – representing a single nucleotide base within a sequence

Relationships:

:STARTS_AT – connects a sample node to its first nucleotide

:NEXT – links consecutive nucleotide nodes within the same sequence chain

### fasta_to_graphv4.py
(Version 4) Deduplicated Nucleotides and Gaps Skipped

Building on v1 and v2, this script represents multiple sequence alignments as a variation graph where common nucleotide stretches are shared and gap characters (-) are skipped. This results in a cleaner, more biologically focused visualisation of genetic variations. 

This script creates an optimised variation graph by preventing gap characters from being added as nucleotide nodes. Instead, relationships :NEXT will skip over these gaps, directly connecting the last non-gap nucleotide to the next non-gap nucleotide in a sequence. 

Usage:
```
python3 fasta_to_graphv4.py <path_to_your_fasta_file>
```
Nodes: 

Sample – representing individual biological sequences

Nucleotide – representing a single nucleotide base within a sequence

Relationships:

:STARTS_AT – connects a sample node to its first nucleotide

:NEXT – links consecutive nucleotide nodes within the same sequence chain

### retrieve_aligned_seq.py

This script reconstructs the full, aligned sequence for a. specified sample from a Neo4j graph database. This is useful for extracting individual sequences in their aligned form after they’ve been processed and stored in the graph by fasta_to_graphv4.py. 

This script performs two main operations, Graph Traversal, executed using a cypher query and Sequence Reconstruction, a python function that takes the output of the Graph Traversal and iteratively compares position values to infer the original alignment length.

Usage:
To reconstruct and print a specific sample’s aligned sequence.
```
python3 retrieve_aligned_seq.py <path_to_your_fasta_file>
```
N.B. This script relies on the graph structure created by fasta_to_graphv4.py.

### retrieve_unaligned_seq.py

This scripts extracts the raw, ungapped sequence for a specific sample directly from the Neo4j database. Unlike retrieve_aligned_seq.py, this script focuses solely on retrieving the sequence content as it would appear before alignment-induced gaps by concatenating the base properties of the Nucleotides nodes in a sample’s path.

Usage:
```
python retrieve_unaligned_seq.py <sample_name>
```
N.B. This script expects the graph database to be in a compatible structure, such as the one created by fasta_to_graphv4.py.

### retrieve_seqs.py

This script allows retrieval of aligned or unaligned sequences for individual samples, a list of samples from a file, or all samples in your database.

Dependencies:

retrieve_aligned_seq.py

retrieve_unaligned_seq.py

Please ensure these scripts are in the same directory.

Usage:
```
python retrieve_seqs.py <samples_input> <mode>
```
Options:

<sample_input> : <sample_name>,all,<file_name>.txt

<mode> : --aligned, --unaligned

Example:
```
python3 retrieve_seqs.py sequence1 --unaligned
```
### compressed_edge_graphMSA/neo4jscript.py

This script provides a highly flexible framework for building a comprehensive graph database, explicitly distinguishing between reference bases and mutations, handling gaps and integrating a hierarchical metadata structure for contextual analysis and visualisation.

Usage:

python3 sequence_graph_builder.py

N.B. Input file paths are hardcoded into this script.

Nodes: 

Pointer – representing individual biological sequences

Base – representing a single nucleotide base within a sequence

Continent, Country, Region – hierarchical nodes representing geographical metadata

Relationships:

:NEXT_REF – links consecutive base nodes that form the reference sequence path

:STARTS_AT – connects a pointer node to the first non-gap base node of its respective sequence

:HAS_COUNTRY – establishes the hierarchy between continent and country nodes

:HAS_REGION – establishes hierarchy between country and region nodes

:HAS_SEQUENCE – links a region node to the pointer nodes originating from that region

### compressed_edge_graphMSA/graphtraversal.py

This script provides an interactive command-line interface for querying the neo4j graph database, enabling retrieval of individual sequence paths and exploration of sequences based on their geographical location.

Dependencies:

This script requires the advanced model created by neo4jscript.py.

Usage:
```
python3 graph_traversal.py
```
