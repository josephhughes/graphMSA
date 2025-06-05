from neo4j import GraphDatabase

class SequenceGraphTraverser:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def traverse_sequence(self, seq_id):
        with self.driver.session() as session:
            # Find the first base node using the Pointer node
            result = session.run(
                """
                MATCH (p:Pointer {seq_id: $seq_id})-[:STARTS_AT]->(start:Base)
                RETURN start.seq_id AS seq_id, start.position AS position, start.symbol AS symbol
                """,
                seq_id=seq_id
            )
            record = result.single()
            if not record:
                print(f"No start node found for sequence: {seq_id}")
                return

            path = []
            current = {
                "seq_id": record["seq_id"],
                "position": record["position"],
                "symbol": record["symbol"]
            }
            path.append(current)

            # Traverse through NEXT_SEQ (prefer) or NEXT_REF
            while True:
                result = session.run(
                    """
                    MATCH (a:Base {seq_id: $seq_id, position: $position})
                    OPTIONAL MATCH (a)-[seqRel:NEXT_SEQ {seq: $target_seq}]->(b1)
                    OPTIONAL MATCH (a)-[refRel:NEXT_REF]->(b2)
                    RETURN 
                        b1.seq_id AS seq_seq_id, b1.position AS seq_position, b1.symbol AS seq_symbol,
                        b2.seq_id AS ref_seq_id, b2.position AS ref_position, b2.symbol AS ref_symbol
                    """,
                    seq_id=current["seq_id"],
                    position=current["position"],
                    target_seq=seq_id
                )
                record = result.single()

                if record["seq_seq_id"] is not None:
                    current = {
                        "seq_id": record["seq_seq_id"],
                        "position": record["seq_position"],
                        "symbol": record["seq_symbol"]
                    }
                elif record["ref_seq_id"] is not None:
                    current = {
                        "seq_id": record["ref_seq_id"],
                        "position": record["ref_position"],
                        "symbol": record["ref_symbol"]
                    }
                else:
                    break  # No more edges
                path.append(current)
        sequence_string = ''.join(step['symbol'] for step in path)

        return path, sequence_string


if __name__ == "__main__":
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "readingroom"

    traverser = SequenceGraphTraverser(URI, USER, PASSWORD)
    seq_id = input("Please enter the sequence u wish to traverse. \n")
    path, sequence_string = traverser.traverse_sequence(seq_id)
    traverser.close()

    if path:
        print(f"Traversed path for {seq_id}:")
        for step in path:
            print(f"{step['symbol']} (pos {step['position']}, from {step['seq_id']})")
        print(sequence_string)