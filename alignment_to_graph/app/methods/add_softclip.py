def add_softclip(read, current_position, cigar_tuple):
    queries = []
    read_name = read.query_name
    start = current_position
    sequence = read.query_sequence

    # add first softclip base and link it to last reference base
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
                "pos": start,
                "last_pos": start - 1,
                "base": sequence[0],
                "read_name": read_name,
            },
        )
    )

    if cigar_tuple[1] > 1:
        start += 1  # increment start base by 1 as we've already added the first base
        positions = list(range(start, (start + cigar_tuple[1]) - 1))

        for pos in positions:
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
                        "pos": pos,
                        "last_pos": pos - 1,
                        "base": sequence[pos - current_position],
                        "read_name": read_name,
                    },
                )
            )

        # final join
        queries.append(
            (
                (
                    f"""
            MATCH (n:Softclip {{pos: $pos}})
            MATCH (l:Nucleotide {{pos: $next_ref_pos}})
            MERGE (n)-[:`{read_name}`]->(l)
            """
                ).strip(),
                {
                    "pos": positions[-1],
                    "next_ref_pos": positions[-1] + 1,
                    "read_name": read_name,
                },
            )
        )

    else:

        queries.append(
            (
                (
                    f"""
            MATCH (l:Softclip {{pos: $pos}})
            MATCH (n:Nucleotide {{pos: $next_ref_pos}})
            MERGE (n)-[:`{read_name}`]->(l)
            """
                ).strip(),
                {
                    "pos": positions[-1],
                    "next_ref_pos": positions[-1] + 1,
                    "read_name": read_name,
                },
            )
        )

    return queries
