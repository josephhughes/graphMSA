def add_insertion(read, current_position, cigar_tuple):
    queries = []
    read_name = read.query_name
    start_pos = current_position
    insertion_length = cigar_tuple[1]

    # Get the sequence of inserted bases from the read
    read_offset = current_position - read.reference_start
    inserted_bases = read.query_sequence[read_offset : read_offset + insertion_length]

    prev_pos = None
    for i, base in enumerate(inserted_bases):
        insert_pos = start_pos + (i + 1) * 0.01

        if i == 0:
            # Link first insertion to reference position
            queries.append(
                (
                    f"""
                CREATE (n:Insertion {{pos: $insert_pos, base: $base}})
                WITH n
                MATCH (l:Nucleotide {{pos: $ref_pos}})
                MERGE (l)-[:`{read_name}`]->(n)
                """.strip(),
                    {
                        "insert_pos": insert_pos,
                        "ref_pos": start_pos,
                        "base": base,
                    },
                )
            )
        else:
            # Link insertion to previous insertion
            queries.append(
                (
                    f"""
                CREATE (n:Insertion {{pos: $insert_pos, base: $base}})
                WITH n
                MATCH (l:Insertion {{pos: $prev_pos}})
                MERGE (l)-[:`{read_name}`]->(n)
                """.strip(),
                    {
                        "insert_pos": insert_pos,
                        "prev_pos": prev_pos,
                        "base": base,
                    },
                )
            )

        prev_pos = insert_pos

    # Link last insertion to the next reference nucleotide
    if prev_pos is not None:
        queries.append(
            (
                f"""
            MATCH (s:Insertion {{pos: $insert_pos}})
            MATCH (e:Nucleotide {{pos: $next_ref_pos}})
            MERGE (s)-[:`{read_name}`]->(e)
            """.strip(),
                {
                    "insert_pos": prev_pos,
                    "next_ref_pos": start_pos + 1,
                },
            )
        )

    return queries
