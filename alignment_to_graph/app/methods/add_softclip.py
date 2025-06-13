def add_softclip(read, current_position, cigar_tuple):
    queries = []
    read_name = read.query_name
    start_pos = current_position
    softclip_length = cigar_tuple[1]

    # Get the sequence of inserted bases from the read
    read_offset = current_position - read.reference_start
    softclip_bases = read.query_sequence[read_offset : read_offset + softclip_length]

    prev_pos = None
    for i, base in enumerate(softclip_bases):
        insert_pos = start_pos + (i + 1)

        if i == 0:
            # Link first Softclip to reference position
            queries.append(
                (
                    (
                        f"""
            CREATE (n:Softclip {{pos: $pos, base: $base}})
            WITH n
            MATCH (n:Softclip {{pos: $pos}})
            MATCH (l:Nucleotide {{pos: $last_pos}})
            MERGE (l)-[:`{read_name}`]->(n)
            """
                    ).strip(),
                    {
                        "pos": insert_pos,
                        "last_pos": start_pos,
                        "base": base,
                        "read_name": read_name,
                    },
                )
            )
        else:
            # Link Softclip to previous Softclip
            queries.append(
                (
                    (
                        f"""
            CREATE (n:Softclip {{pos: $pos, base: $base}})
            WITH n
            MATCH (n:Softclip {{pos: $pos}})
            MATCH (l:Softclip {{pos: $last_pos}})
            MERGE (l)-[:`{read_name}`]->(n)
            """
                    ).strip(),
                    {
                        "pos": insert_pos,
                        "last_pos": prev_pos,
                        "base": base,
                        "read_name": read_name,
                    },
                )
            )

        prev_pos = insert_pos

    # Link last Softclip to the next reference nucleotide
    if prev_pos is not None:
        queries.append(
            (
                f"""
            MATCH (s:Softclip {{pos: $insert_pos}})
            MATCH (e:Nucleotide {{pos: $next_ref_pos}})
            MERGE (s)-[:`{read_name}`]->(e)
            """.strip(),
                {
                    "insert_pos": prev_pos,
                    "next_ref_pos": insert_pos + 1,
                },
            )
        )

    return queries
