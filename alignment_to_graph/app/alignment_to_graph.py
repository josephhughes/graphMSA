import os
import sys
from neo4j import GraphDatabase
import pysam
from env_variables import URI, USER_NAME, PASSWORD
from methods.add_match import add_match
from methods.add_insertion import add_insertion
from methods.add_deletion import add_deletion
from methods.add_softclip import add_softclip

AUTH = (USER_NAME, PASSWORD)
DB_NAME = "neo4j"

queries = []


def alignment_to_graph(alignment_file_path):
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session(database=DB_NAME) as session:
        alignment_file = pysam.AlignmentFile(alignment_file_path, "rb")
        reads = alignment_file.fetch()
        for read in reads:
            print("processing", read.query_name)
            current_position = (
                read.reference_start + 1
            )  # add 1 because reference_start property is 0-based

            """
            The first element of a cigar_tuple is a single integer from 0-9, that matches the different cigar operations.
            0: Match; 1: Insertion; 2: Deletion; 3: Skipped Region; 4: Softclip 5: Hardclip; 6: Padding; 7: Sequence Match; 8: Sequence Mismatch

            The second element of a cigar_tuple is an integer, equal to the number of bases in the read that the cigar_operation applies to.
            e.g (0, 50) => 50 matching bases; (1, 10) => 10 inserted bases;

            Still need to add methods for 3, 5, 6, 7, 8...
            """

            for cigar_tuple in read.cigar:
                match cigar_tuple[0]:
                    case 0:
                        queries.extend(add_match(read, current_position, cigar_tuple))
                        current_position += cigar_tuple[1] - 1
                    case 1:
                        queries.extend(
                            add_insertion(read, current_position, cigar_tuple)
                        )
                        current_position += 1
                    case 2:
                        queries.append(
                            add_deletion(read, current_position, cigar_tuple)
                        )
                        current_position += cigar_tuple[1]
                    case 3:
                        pass
                    case 4:
                        queries.extend(
                            add_softclip(read, current_position, cigar_tuple)
                        )
                        current_position += cigar_tuple[1]
                    case 5:
                        pass
                    case 6:
                        pass
                    case 7:
                        pass
                    case 8:
                        pass
        alignment_file.close()
        session.execute_write(run_queries_transactionally)


def run_queries_transactionally(tx):
    for cypher, params in queries:
        tx.run(cypher, **params)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python bam_to_graph.py input.bam")
        sys.exit(1)
    while os.path.splitext(sys.argv[1])[1] not in [".bam", ".sam"]:
        print("format error: Input file must be .bam or .sam format")
        sys.exit(1)
    alignment_to_graph(sys.argv[1])
