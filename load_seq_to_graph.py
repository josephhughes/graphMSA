import neo4j
import dotenv
import os
dotenv.load_dotenv()

# 1. Read the sequence from the .fa file
def read_fasta_sequence(fasta_path)->dict[str, str]:
    """
    Reads a fasta file and returns a dictionary of headers and sequences.
    """
    with open(fasta_path, 'r') as f:
        headers = []
        seqs = []
        lines = f.readlines()
        for line in lines:
            if line.startswith('>'):
                headers.append(line.strip('>').strip())
            else:
                seqs.append(line.strip())       

    fasta_dict = dict(zip(headers, seqs)) 
    return fasta_dict


def load_seq_to_graph(seq)->None:
    for key, value in seq.items():
        create_node_template = f"""
            WITH "{value}" AS seq
            WITH seq, size(seq) AS len
            UNWIND range(0, len - 1) AS i
            WITH i + 1 AS position, substring(seq, i, 1) AS nt
            MERGE (p:Position_{key} {{id: position}})
            SET p.nucleotide = nt, 
                p.hasNucleotide = nt <> '-'
        """
        create_relationship_template = f"""
            MATCH (p1:Position_{key}), (p2:Position_{key})
            WHERE p2.id = p1.id + 1 AND p1.id >= 1
            MERGE (p1)-[:IS_NEXT]->(p2)
        """
        create_mismatch_template = ""
        if key != "Ref":
            create_mismatch_template += f"""
                MATCH (p1:Position_Ref), (p2:Position_{key})
                WHERE p1.id = p2.id
                AND p1.nucleotide <> p2.nucleotide
                MERGE (p1)-[:hasMismatch]->(p2)
            """

        try:
            driver = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.getenv("PASSWORD")))
            session = driver.session()
            session.run(create_node_template)
            session.run(create_relationship_template)
            session.run(create_mismatch_template)
            session.close()
        except Exception as e:
            print(e)
        finally:
            driver.close()

if __name__ == "__main__":
    seq = read_fasta_sequence("sample.fa")
    load_seq_to_graph(seq)
