from neo4j import GraphDatabase
from Bio import SeqIO

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "13102010@Gla")
DB_NAME = "neo4j"


def create_deduplicated_sequence(driver, sample_name, sequence):
    with driver.session(database=DB_NAME) as session:
        session.execute_write(_deduplicated_sequence_tx, sample_name, str(sequence))


def _deduplicated_sequence_tx(tx, sample_name, sequence):
    # Ensure Sample node exists
    tx.run("MERGE (:Sample {name: $sample_name})", sample_name=sample_name)

    prev_pos, prev_base = None, None
    for i, base in enumerate(sequence, start=1):
        # Merge Nucleotide node (deduplicated by pos + base)
        tx.run(
            "MERGE (:Nucleotide {pos: $pos, base: $base})",
            pos=i, base=base
        )

        # STARTS_AT relationship from Sample to first Nucleotide
        if i == 1:
            tx.run(
                """
                MATCH (s:Sample {name: $sample_name}), (n:Nucleotide {pos: $pos, base: $base})
                MERGE (s)-[:STARTS_AT]->(n)
                """,
                sample_name=sample_name, pos=i, base=base
            )

        # NEXT relationship between consecutive Nucleotide nodes
        if prev_pos is not None:
            tx.run(
                """
                MATCH (a:Nucleotide {pos: $prev_pos, base: $prev_base}),
                      (b:Nucleotide {pos: $pos, base: $base})
                MERGE (a)-[r:NEXT {sample: $sample_name}]->(b)
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
    import sys
    if len(sys.argv) != 2:
        print("Usage: python fasta_to_graph.py input.fasta")
        sys.exit(1)

    fasta_file = sys.argv[1]
    load_fasta_and_add_to_graph(fasta_file)
