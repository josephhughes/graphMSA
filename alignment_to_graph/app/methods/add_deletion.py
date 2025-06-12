def add_deletion(read, current_position, cigar_tuple):
    read_name = read.query_name
    next_node = current_position + cigar_tuple[1]

    deletion = (
        (
            f"""
        MATCH (s:Nucleotide {{pos: $pos}})
        MATCH (e:Nucleotide {{pos: $next_pos}})
        MERGE (s)-[:`{read_name}`]->(e)
        """
        ).strip(),
        {"pos": current_position, "next_pos": next_node, "read_name": read_name},
    )

    return deletion