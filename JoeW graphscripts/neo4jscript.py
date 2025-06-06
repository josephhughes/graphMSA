from neo4j import GraphDatabase


class SequenceGraphBuilder:
    def __init__(self):
        self.queries = []

    def add_query(self, cypher, **params):
        self.queries.append((cypher.strip(), params))

    def run_all_queries(self, uri, user, password):
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            session.execute_write(self._run_queries_transactionally)
        driver.close()

    def _run_queries_transactionally(self, tx):
        for cypher, params in self.queries:
            tx.run(cypher, **params)

    def parse_fasta(self, text):
        sequences = {}
        current_id = None
        for line in text.strip().splitlines():
            line = line.strip()
            if line.startswith(">"):
                current_id = line[1:]
                sequences[current_id] = ""
            else:
                sequences[current_id] += line.upper()
        return sequences

    def parse_metadata(self, text):
        metadata = {}
        lines = text.strip().splitlines()
        if not lines:
            return metadata

        headers = lines[0].split('\t')

        for line in lines[1:]:
            parts = line.split('\t')
            if len(parts) != len(headers):
                continue
            record = dict(zip(headers, parts))
            seq_id = record.pop('id')
            metadata[seq_id] = record
        return metadata

    def create_labeled_base_node(self, pos, sym):
        self.add_query("MERGE (n:Mutation:Base {position: $pos, symbol: $sym})", pos=pos, sym=sym)

    def create_nodes_and_relationships(self, sequences, metadata=None):
        ref_id = "ref"
        ref_seq = sequences[ref_id]
        length = len(ref_seq)
        for k in sequences:
            sequences[k] = sequences[k].ljust(length, '-')

        self.add_query("MATCH (n) DETACH DELETE n")

        ref_nodes = []
        for i, symbol in enumerate(ref_seq):
            if symbol == '-':
                ref_nodes.append(None)
            else:
                labels = ":Base"
                if i == 0:
                    labels = ":Head:Base"
                elif i == length - 1:
                    labels = ":Tail:Base"
                self.add_query(f"CREATE ({labels} {{seq_id: $seq_id, position: $pos, symbol: $sym}})",
                               seq_id=ref_id, pos=i, sym=symbol)
                ref_nodes.append((ref_id, i))

        for i in range(length - 1):
            if ref_nodes[i] is None:
                continue
            j = i + 1
            while j < length and ref_nodes[j] is None:
                j += 1
            if j >= length:
                continue
            from_id, from_pos = ref_nodes[i]
            to_id, to_pos = ref_nodes[j]
            self.add_query("""
                MATCH (a:Base {seq_id: $from_id, position: $from_pos}),
                      (b:Base {seq_id: $to_id, position: $to_pos})
                CREATE (a)-[:NEXT_REF]->(b)
            """, from_id=from_id, from_pos=from_pos, to_id=to_id, to_pos=to_pos)

        all_node_ids = {}
        for seq_id, seq in sequences.items():
            if seq_id == ref_id:
                all_node_ids[ref_id] = ref_nodes
                continue
            node_ids = []

            for i in range(length):
                base = seq[i]
                if base == ref_seq[i]:
                    node_ids.append((ref_id, i))
                else:
                    if base == '-':
                        node_ids.append(None)
                    else:
                        self.create_labeled_base_node(i, base)
                        node_ids.append((None, i))
            all_node_ids[seq_id] = node_ids

            for i in range(length - 1):
                from_sym = seq[i]
                j = i + 1
                while j < length and seq[j] == '-':
                    j += 1
                if from_sym == '-' or j >= length:
                    continue

                from_node = node_ids[i]
                to_node = node_ids[j]

                if from_node is None or to_node is None:
                    continue
                if from_node == to_node:
                    continue
                if from_node[0] == ref_id and to_node[0] == ref_id:
                    continue

                from_pos = from_node[1]
                to_pos = to_node[1]

                self.add_query("""
                    MATCH (a:Base {position: $from_pos, symbol: $from_sym}),
                          (b:Base {position: $to_pos, symbol: $to_sym})
                    CREATE (a)-[:NEXT_SEQ {seq: $seq_id}]->(b)
                """, from_sym=seq[from_pos], from_pos=from_pos,
                      to_sym=seq[to_pos], to_pos=to_pos, seq_id=seq_id)

        for seq_id, seq in sequences.items():
            if metadata:
                metadata_for_seq = metadata.get(seq_id, {})
                params = {"seq_id": seq_id, **metadata_for_seq}
                props = ", ".join(f"{key}: ${key}" for key in params.keys())
                self.add_query(f"CREATE (:Pointer {{{props}}})", **params)
            else:
                self.add_query("CREATE (:Pointer {seq_id: $seq_id})", seq_id=seq_id)

            node_ids = all_node_ids[seq_id]
            for i, base in enumerate(seq):
                if base != '-':
                    actual_id, actual_pos = node_ids[i]
                    if actual_id == ref_id:
                        self.add_query("""
                            MATCH (p:Pointer {seq_id: $seq_id}),
                                  (b:Base {seq_id: $actual_id, position: $actual_pos})
                            CREATE (p)-[:STARTS_AT]->(b)
                        """, seq_id=seq_id, actual_id=actual_id, actual_pos=actual_pos)
                    else:
                        self.add_query("""
                            MATCH (p:Pointer {seq_id: $seq_id}),
                                  (b:Base {position: $actual_pos, symbol: $sym})
                            CREATE (p)-[:STARTS_AT]->(b)
                        """, seq_id=seq_id, actual_pos=actual_pos, sym=seq[actual_pos])
                    break

        if metadata:
            self.create_metadata_hierarchy(metadata)

    def create_metadata_hierarchy(self, metadata):
        for seq_id, record in metadata.items():
            continent = record.get("continent", "Unknown")
            country = record.get("country", "Unknown")
            region = record.get("region", "Unknown")
            if region.upper() in {"N/A", "", "NA"}:
                region = "Unknown"

            self.add_query("""
                MERGE (c:Continent {name: $continent})
                MERGE (co:Country {name: $country})
                MERGE (r:Region {name: $region})
                MERGE (p:Pointer {seq_id: $seq_id})
                MERGE (c)-[:HAS_COUNTRY]->(co)
                MERGE (co)-[:HAS_REGION]->(r)
                MERGE (r)-[:HAS_SEQUENCE]->(p)
            """, continent=continent, country=country, region=region, seq_id=seq_id)


if __name__ == "__main__":
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "readingroom"

    with open("Dummy/dummy_aln.fa", "r") as file:
        fasta_input = file.read()
    try:
        with open("Dummy/dummy_metadata.tsv", "r") as file:
            metadata_txt = file.read()
    except FileNotFoundError:
        metadata_txt = None
        metadata = None

    builder = SequenceGraphBuilder()
    sequences = builder.parse_fasta(fasta_input)
    if metadata_txt:
        metadata = builder.parse_metadata(metadata_txt)
    print("Parsed sequences:", list(sequences.keys()))
    builder.create_nodes_and_relationships(sequences, metadata)
    builder.run_all_queries(URI, USER, PASSWORD)
