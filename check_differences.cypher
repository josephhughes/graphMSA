MATCH (s:Nucleotide)-[d:DIFFERS_FROM]->(r:Nucleotide)
RETURN d.sample AS sample, s.pos, s.base AS sample_base, r.base AS ref_base
ORDER BY sample, s.pos