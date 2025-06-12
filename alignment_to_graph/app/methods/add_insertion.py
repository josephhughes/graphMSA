def add_insertion(read, current_position, cigar_tuple):
    queries = []
    read_name = read.query_name
    start = current_position
    i = 0.01  # appending a decimal place to each insertion node, so they can be accounted for in numerical order before joining the final insertion base to the next reference sequence node

    # create first insertion node
    insertion_base = read.query_sequence[current_position - read.reference_start]
    queries.append(
        (
            (
                f"""
            CREATE (n:Insertion {{pos: $insert_position, base: $base}})
            WITH n
            MATCH (n:Insertion {{pos: $insert_position}})
            MATCH (l:Nucleotide {{pos: $pos}})
            MERGE (l)-[:`{read_name}`]->(n)
            """
            ).strip(),
            {
                "pos": start,
                "insert_position": current_position + i,
                "base": insertion_base,
            },
        )
    )

    if cigar_tuple[1] > 1:
        i += 0.01
        j = (
            cigar_tuple[1] - 1 #decrement j by 1, before executing the while-loop, because we've added the first insertion node already
        )
        while j > 0:
            queries.append(
                (
                    (
                        f"""
                        CREATE (n:Insertion {{pos: $insert_position, base: $base}})
                        WITH n
                        MATCH (n:Insertion {{pos: $insert_position}})
                        MATCH (l:Insertion {{pos: $last_position}})
                        MERGE (l)-[:`{read_name}`]->(n)
                        """
                    ).strip(),
                    {
                        "insert_position": current_position + i,
                        "last_position": current_position + (i - 0.01),
                        "base": insertion_base,
                    },
                )
            )

            j -= 1
            i += 0.01

        # merge final insertion node to the next reference sequence node
        queries.append(
            (
                (
                    f"""
                MATCH (s:Insertion {{pos: $insert_position}})
                MATCH (e:Nucleotide {{pos: $ref_position}})
                MERGE (s)-[:`{read_name}`]->(e)
                """
                ).strip(),
                {
                    "insert_position": current_position + (i - 0.01),
                    "ref_position": current_position + 1,
                },
            )
        )

    else:
        # when there is only 1 insertion node created, its merged with the next reference sequence node here
        queries.append(
            (
                (
                    f"""
                MATCH (s:Insertion {{pos: $insert_position}})
                MATCH (e:Nucleotide {{pos: $ref_position}})
                MERGE (s)-[:`{read_name}`]->(e)
                """
                ).strip(),
                {
                    "insert_position": current_position + i,
                    "ref_position": current_position + 1,
                },
            )
        )

    return queries
