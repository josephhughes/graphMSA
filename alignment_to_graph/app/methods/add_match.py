def add_match(read, current_position, cigar_tuple):
    queries = []
    read_name = read.query_name
    start = current_position
    positions = list(range(start, (start + cigar_tuple[1]) - 1))
    for pos in positions:
        queries.append(
            (
                (
                    f"""
                MATCH (s:Nucleotide {{pos: $pos}})
                MATCH (e:Nucleotide {{pos: $next_pos}})
                MERGE (s)-[:`{read_name}`]->(e)
                """
                ).strip(),
                {"pos": pos, "next_pos": pos + 1},
            )
        )

    return queries
