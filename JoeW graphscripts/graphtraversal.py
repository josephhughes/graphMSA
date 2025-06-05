from neo4j import GraphDatabase

class SequenceGraphTraverser:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def traverse_sequence(self, seq_id):
        with self.driver.session() as session:
            # Step 1: Find the starting Base node
            result = session.run(
                """
                MATCH (p:Pointer {seq_id: $seq_id})-[:STARTS_AT]->(start:Base)
                RETURN start.position AS position, start.symbol AS symbol
                """,
                seq_id=seq_id
            )
            record = result.single()
            if not record:
                print(f"No start node found for sequence: {seq_id}")
                return

            path = []
            current = {
                "position": record["position"],
                "symbol": record["symbol"]
            }
            path.append(current)

            # Step 2: Traverse via NEXT_SEQ or NEXT_REF
            while True:
                result = session.run(
                    """
                    MATCH (a:Base {position: $position, symbol: $symbol})
                    OPTIONAL MATCH (a)-[seqRel:NEXT_SEQ {seq: $seq_id}]->(b1)
                    OPTIONAL MATCH (a)-[refRel:NEXT_REF]->(b2)
                    RETURN 
                        b1.position AS seq_position, b1.symbol AS seq_symbol,
                        b2.position AS ref_position, b2.symbol AS ref_symbol
                    """,
                    position=current["position"],
                    symbol=current["symbol"],
                    seq_id=seq_id
                )
                record = result.single()

                if record["seq_position"] is not None:
                    current = {
                        "position": record["seq_position"],
                        "symbol": record["seq_symbol"]
                    }
                elif record["ref_position"] is not None:
                    current = {
                        "position": record["ref_position"],
                        "symbol": record["ref_symbol"]
                    }
                else:
                    break  # No more edges
                path.append(current)

        # Unaligned: just symbols in order
        unaligned_string = ''.join(step['symbol'] for step in path)

        # Aligned: fill in missing positions with '-'
        max_pos = max(base["position"] for base in path)
        aligned_list = ["-"] * (max_pos + 1)
        for base in path:
            aligned_list[base["position"]] = base["symbol"]
        aligned_string = ''.join(aligned_list)

        return aligned_string, unaligned_string


if __name__ == "__main__":
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "readingroom"

    traverser = SequenceGraphTraverser(URI, USER, PASSWORD)
    seq_id = input("Please enter the sequence u wish to traverse.\n")
    aligned, unaligned = traverser.traverse_sequence(seq_id)
    traverser.close()

    if aligned and unaligned:
        print(f"\nAligned sequence:\n{aligned}")
        print(f"\nUnaligned sequence:\n{unaligned}")
