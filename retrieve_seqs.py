import retrieve_unaligned_seq as unaligned_seq
import retrieve_aligned_seq as aligned_seq

GraphDatabase = unaligned_seq.GraphDatabase
URI = unaligned_seq.URI
AUTH = unaligned_seq.AUTH
DB_NAME = unaligned_seq.DB_NAME

def get_all_sample_names(tx):
    query = """
        MATCH (s:Sample)
        RETURN s.name AS sample_name
        """
    result = tx.run(query)
    return [record["sample_name"] for record in result]

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python retrieve_seqs.py [<sample_name> | all | <file_name>.txt] [--aligned | --unaligned]")
        sys.exit(1)

    sequences = []
    # check if arg is a txt file
    if sys.argv[1][-4:]== ".txt":
        with open(sys.argv[1], 'r') as file:
            sequences = [line.strip() for line in file]
    elif sys.argv[1] != "all":
        sample_name = sys.argv[1]
        sequences.append(sample_name)
    else:
        print("Retrieving all sequences...")
        sequences = get_all_sample_names(GraphDatabase.driver(URI, auth=AUTH).session(database=DB_NAME))

    mode = sys.argv[2]

    for sample_name in sequences:
        try:
            if mode =="--aligned":
                with GraphDatabase.driver(URI, auth=AUTH) as driver:
                    nodes = aligned_seq.get_aligned_sequence_with_gaps(driver, sample_name)
                sequence = aligned_seq.reconstruct_sequence_with_gaps(nodes)

            elif mode == "--unaligned":
                with GraphDatabase.driver(URI, auth=AUTH) as driver:
                    nodes = unaligned_seq.get_sequence_by_sample(driver, sample_name)
                sequence = unaligned_seq.get_sequence_by_sample(driver, sample_name)
                
            else:
                print("Invalid mode. Use --aligned or --unaligned.")
                sys.exit(1)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

        if sequence:
            print(f">{sample_name}")
            print(sequence)
        else:
            print(f"Sample '{sample_name}' not found or sequence is empty.")