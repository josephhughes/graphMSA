from neo4j import GraphDatabase

# Example run command: python3 retrieve_aligned_seq.py seq1


# Connection details
URI = "neo4j://localhost:7690"
AUTH = ("neo4j", "13102010@Gla")
DB_NAME = "neo4j"


def get_sequence_by_sample(driver, sample_name):
    with driver.session(database=DB_NAME) as session:
        return session.execute_read(_fetch_sequence_tx, sample_name)

def _fetch_sequence_tx(tx, sample_name):
    query = """
    MATCH (s:Sample {name: $sample_name})-[:STARTS_AT]->(start)
    MATCH path = (start)-[:NEXT*]->(n)
    WHERE ALL(r IN relationships(path) WHERE r.sample = $sample_name)
    WITH path
    ORDER BY length(path) DESC
    LIMIT 1
    RETURN [node IN nodes(path) | node.base] AS sequence
    """
    result = tx.run(query, sample_name=sample_name)
    record = result.single()
    if record:
        return "".join(record["sequence"])
    return None
    
    
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python extract_sequence_by_sample.py <sample_name>")
        sys.exit(1)

    sample_name = sys.argv[1]

    driver = GraphDatabase.driver(URI, auth=AUTH)
    sequence = get_sequence_by_sample(driver, sample_name)
    driver.close()

    if sequence:
        print(f">{sample_name}")
        print(sequence)
    else:
        print(f"Sample '{sample_name}' not found or sequence is empty.")
