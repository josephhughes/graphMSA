from neo4j import GraphDatabase
import sys

# Connection details
URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "12345678")
DB_NAME = "neo4j"

def get_all_sample_names(tx):
    query = """
        CALL db.labels() YIELD label
        WHERE label STARTS WITH "Position_"
        RETURN replace(label, "Position_", "") AS sample_name
    """
    result = tx.run(query)
    return [record["sample_name"] for record in result]

def get_aligned_sequence_from_position_nodes(driver, sample_name):
    with driver.session() as session:
        result = session.run(f"""
            MATCH (p:Position_{sample_name})
            RETURN p.id AS id, p.nucleotide AS nt
            ORDER BY id
        """)
        return "".join([record["nt"] for record in result])

def get_unaligned_sequence_from_position_nodes(driver, sample_name):
    with driver.session() as session:
        result = session.run(f"""
            MATCH (p:Position_{sample_name})
            WHERE p.hasNucleotide = true
            RETURN p.id AS id, p.nucleotide AS nt
            ORDER BY id
        """)
        return "".join([record["nt"] for record in result])

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python retrieve_seqs_position_model.py [<sample_name> | all | <file_name>.txt] [--aligned | --unaligned]")
        sys.exit(1)

    arg = sys.argv[1]
    mode = sys.argv[2]
    sequences = []

    # Handle input: list from file, single name, or all
    if arg.endswith(".txt"):
        with open(arg, 'r') as file:
            sequences = [line.strip() for line in file]
    elif arg != "all":
        sequences = [arg]
    else:
        # Get all samples from graph
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session(database=DB_NAME) as session:
                sequences = session.execute_read(get_all_sample_names)

    # Retrieve and print sequences
    for sample_name in sequences:
        try:
            with GraphDatabase.driver(URI, auth=AUTH) as driver:
                if mode == "--aligned":
                    sequence = get_aligned_sequence_from_position_nodes(driver, sample_name)
                elif mode == "--unaligned":
                    sequence = get_unaligned_sequence_from_position_nodes(driver, sample_name)
                else:
                    print("Invalid mode. Use --aligned or --unaligned.")
                    sys.exit(1)

        except Exception as e:
            print(f"Error retrieving sequence for '{sample_name}': {e}")
            continue

        if sequence:
            print(f">{sample_name}")
            print(sequence)
        else:
            print(f"Sample '{sample_name}' not found or sequence is empty.")