# fasta_to_graph_skip_gaps.py
# working script where a multi fast can be provided and gaps are ignored
# the position is the alignment position


from neo4j import GraphDatabase
from Bio import SeqIO
import sys

# Neo4j configuration
URI = "neo4j://localhost:7690"
AUTH = ("neo4j", "13102010@Gla")  # Replace with your actual password
DB_NAME = "neo4j"

queries = []


def run_all_queries():
    queries.insert(0, ("MATCH (n) DETACH DELETE n", {}))
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_write(run_queries_transactionally)
    driver.close()


def run_queries_transactionally(tx):
    for cypher, params in queries:
        tx.run(cypher, **params)


def add_query(cypher, **params):
    queries.append((cypher.strip(), params))


def create_deduplicated_sequence(driver, sample_name, sequence):
    with driver.session(database=DB_NAME) as session:
        session.execute_write(_deduplicated_sequence_tx, sample_name, str(sequence))


def _deduplicated_sequence_tx(tx, sample_name, sequence):
    # Ensure Sample node exists
    add_query("MERGE (:Sample {name: $sample_name})", sample_name=sample_name)

    prev_pos, prev_base = None, None
    first_node_linked = False  # To track first non-gap base

    for i, base in enumerate(sequence, start=1):  # alignment position
        if base == "-":
            continue  # skip gaps entirely

        # Merge Nucleotide node at alignment position (pos) and base
        add_query(
            "MERGE (:Nucleotide {pos: $pos, base: $base})",
            pos=i, base=base
        )

        # STARTS_AT relationship only from first non-gap base
        if not first_node_linked:
            add_query(
                """
                MATCH (s:Sample {name: $sample_name}), (n:Nucleotide {pos: $pos, base: $base})
                MERGE (s)-[:STARTS_AT]->(n)
                """,
                sample_name=sample_name, pos=i, base=base
            )
            first_node_linked = True

        # NEXT relationship between consecutive non-gap Nucleotide nodes
        if prev_pos is not None:
            add_query(
                """
                MATCH (a:Nucleotide {pos: $prev_pos, base: $prev_base}),
                      (b:Nucleotide {pos: $pos, base: $base})
                MERGE (a)-[:NEXT {sample: $sample_name}]->(b)
                """,
                prev_pos=prev_pos, prev_base=prev_base,
                pos=i, base=base,
                sample_name=sample_name
            )

        prev_pos, prev_base = i, base


def load_fasta_and_add_to_graph(fasta_path):
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        for record in SeqIO.parse(fasta_path, "fasta"):
            print(f"Adding sequence: {record.id}")
            create_deduplicated_sequence(driver, record.id, record.seq)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fasta_to_graph_skip_gaps.py input.fasta")
        sys.exit(1)

    fasta_file = sys.argv[1]
    load_fasta_and_add_to_graph(fasta_file)
    run_all_queries()