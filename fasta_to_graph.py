from neo4j import GraphDatabase, RoutingControl
from Bio import SeqIO

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "13102010@Gla")
DB_NAME = "neo4j"


def create_sequence(driver, sample_name, sequence):
    with driver.session(database=DB_NAME) as session:
        session.execute_write(_create_sequence_tx, sample_name, str(sequence))


def _create_sequence_tx(tx, sample_name, sequence):
    # Create the Sample node
    tx.run("MERGE (:Sample {name: $sample_name})", sample_name=sample_name)

    prev_node_var = None
    for i, base in enumerate(sequence, start=1):
        node_var = f"{sample_name}_n{i}"

        # Create the nucleotide node
        tx.run(
            "CREATE (n:Nucleotide {pos: $pos, base: $base})",
            pos=i, base=base
        )

        # Create the STARTS_AT relationship
        if i == 1:
            tx.run(
                """
                MATCH (s:Sample {name: $sample_name}), (n:Nucleotide {pos: $pos, base: $base})
                MERGE (s)-[:STARTS_AT]->(n)
                """,
                sample_name=sample_name, pos=i, base=base
            )
        else:
            # Create NEXT relationship with sample label
            tx.run(
                """
                MATCH (a:Nucleotide {pos: $prev_pos, base: $prev_base}),
                      (b:Nucleotide {pos: $pos, base: $base})
                MERGE (a)-[:NEXT {sample: $sample_name}]->(b)
                """,
                prev_pos=i-1, prev_base=sequence[i-2],
                pos=i, base=base,
                sample_name=sample_name
            )


def load_fasta_and_create_graph(fasta_path):
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        for record in SeqIO.parse(fasta_path, "fasta"):
            print(f"Processing {record.id}")
            create_sequence(driver, record.id, record.seq)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python fasta_to_graph.py input.fasta")
        sys.exit(1)

    fasta_file = sys.argv[1]
    load_fasta_and_create_graph(fasta_file)
