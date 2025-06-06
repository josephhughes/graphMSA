from neo4j import GraphDatabase


class SequenceGraphTraverser:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def traverse_sequence(self, seq_id):
        with self.driver.session() as session:
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
                return None, None

            path = []
            current = {
                "position": record["position"],
                "symbol": record["symbol"]
            }
            path.append(current)

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
                    break
                path.append(current)

        unaligned_string = ''.join(step['symbol'] for step in path)
        max_pos = max(base["position"] for base in path)
        aligned_list = ["-"] * (max_pos + 1)
        for base in path:
            aligned_list[base["position"]] = base["symbol"]
        aligned_string = ''.join(aligned_list)

        return aligned_string, unaligned_string

    def get_all_continents(self):
        with self.driver.session() as session:
            result = session.run("MATCH (c:Continent) RETURN c.name AS name ORDER BY name")
            return [record["name"] for record in result]

    def get_countries_in_continent(self, continent):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (:Continent {name: $continent})-[:HAS_COUNTRY]->(co:Country)
                RETURN co.name AS name ORDER BY name
                """, continent=continent
            )
            return [record["name"] for record in result]

    def get_regions_in_country(self, country):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (:Country {name: $country})-[:HAS_REGION]->(r:Region)
                RETURN r.name AS name ORDER BY name
                """, country=country
            )
            return [record["name"] for record in result]

    def get_sequences_for_area(self, level, name):
        with self.driver.session() as session:
            if level == "continent":
                query = """
                MATCH (:Continent {name: $name})-[:HAS_COUNTRY]->(:Country)-[:HAS_REGION]->(:Region)-[:HAS_SEQUENCE]->(p:Pointer)
                RETURN p.seq_id AS id
                """
            elif level == "country":
                query = """
                MATCH (:Country {name: $name})-[:HAS_REGION]->(:Region)-[:HAS_SEQUENCE]->(p:Pointer)
                RETURN p.seq_id AS id
                """
            elif level == "region":
                query = """
                MATCH (:Region {name: $name})-[:HAS_SEQUENCE]->(p:Pointer)
                RETURN p.seq_id AS id
                """
            else:
                return []

            result = session.run(query, name=name)
            return [record["id"] for record in result]


if __name__ == "__main__":
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "readingroom"

    traverser = SequenceGraphTraverser(URI, USER, PASSWORD)

    choice = input("Do you want to retrieve a specific sequence (1) or sequences by continent/country/region (2)? ")

    if choice.strip() == "1":
        seq_id = input("Enter sequence ID: ")
        aligned, unaligned = traverser.traverse_sequence(seq_id)
        if aligned and unaligned:
            print(f"\nAligned sequence:\n{aligned}")
            print(f"\nUnaligned sequence:\n{unaligned}")

    elif choice.strip() == "2":
        continents = traverser.get_all_continents()
        print("\nAvailable continents:")
        for i, c in enumerate(continents):
            print(f"{i + 1}. {c}")
        c_index = int(input("Select a continent by number: ")) - 1
        continent = continents[c_index]

        next_step = input("Get all sequences for this continent (c) or pick a country (o)? ").lower()

        if next_step == "c":
            seq_ids = traverser.get_sequences_for_area("continent", continent)

        elif next_step == "o":
            countries = traverser.get_countries_in_continent(continent)
            print("\nAvailable countries:")
            for i, c in enumerate(countries):
                print(f"{i + 1}. {c}")
            country = countries[int(input("Select a country by number: ")) - 1]

            level2 = input("Get all sequences for this country (o) or pick a region (r)? ").lower()

            if level2 == "o":
                seq_ids = traverser.get_sequences_for_area("country", country)

            elif level2 == "r":
                regions = traverser.get_regions_in_country(country)
                if not regions:
                    print("No regions found for this country.")
                    seq_ids = []
                else:
                    print("\nAvailable regions:")
                    for i, r in enumerate(regions):
                        print(f"{i + 1}. {r}")
                    region = regions[int(input("Select a region by number: ")) - 1]
                    seq_ids = traverser.get_sequences_for_area("region", region)
            else:
                print("Invalid option.")
                seq_ids = []
        else:
            print("Invalid option.")
            seq_ids = []

        print("\nRetrieved sequences:")
        for sid in seq_ids:
            print(f"\n--- Sequence ID: {sid} ---")
            aligned, unaligned = traverser.traverse_sequence(sid)
            if aligned and unaligned:
                print(f"Aligned: {aligned}\nUnaligned: {unaligned}")

    else:
        print("Invalid choice.")

    traverser.close()