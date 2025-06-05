from neo4j import GraphDatabase

URI = "neo4j://localhost:7690"
AUTH = ("neo4j", "13102010@Gla")
DB_NAME = "neo4j"

def get_aligned_sequence_with_gaps(driver, sample_name):
    with driver.session(database=DB_NAME) as session:
        return session.execute_read(_fetch_aligned_sequence_tx, sample_name)

def _fetch_aligned_sequence_tx(tx, sample_name):
    query = """
    MATCH (s:Sample {name: $sample_name})-[:STARTS_AT]->(start)
    MATCH path = (start)-[:NEXT*]->(n)
    WHERE ALL(r IN relationships(path) WHERE r.sample = $sample_name)
    WITH path
    ORDER BY length(path) DESC
    LIMIT 1
    RETURN [node IN nodes(path) | {pos: node.pos, base: node.base}] AS nodes
    """
    result = tx.run(query, sample_name=sample_name)
    record = result.single()
    if record:
        return record["nodes"]
    return None

def reconstruct_sequence_with_gaps(nodes):
    if not nodes:
        return None
    
    sequence = []
    prev_pos = None

    for node in nodes:
        pos = node['pos']
        base = node['base']

        if prev_pos is not None:
            gap_size = pos - prev_pos - 1
            if gap_size > 0:
                sequence.extend(['-'] * gap_size)
        sequence.append(base)
        prev_pos = pos

    return "".join(sequence)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python extract_aligned_sequence.py <sample_name>")
        sys.exit(1)

    sample_name = sys.argv[1]

    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            nodes = get_aligned_sequence_with_gaps(driver, sample_name)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    sequence = reconstruct_sequence_with_gaps(nodes)

    if sequence:
        print(f">{sample_name}")
        print(sequence)
    else:
        print(f"Sample '{sample_name}' not found or sequence is empty.")
