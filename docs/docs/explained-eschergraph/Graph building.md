---
sidebar_position: 2
---

# Graph Building Pipeline
### Eschergraph Pipeline

Some aspects of this graph building pipeline have been inspired by [GraphRAG](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/), a Microsoft Research project. Their great work and insights on communities in a graph have been especially inspiring. 

The steps for the EscherGraph building are: 

1) Parse document into chunks of about 500 tokens
2) Extract nodes & edges for each chunk using an LLM
3) Extract properties for each node using an LLM
4) Match similar nodes, and merging their edges and properties (more on this [below](#node-matcher))
5) Persist the graph to a database
6) Build communities with the [LeidenAlg](https://github.com/vtraag/leidenalg)
7) Sync all nodes, edges and properties to a vector database, by default [ChromaDB](https://www.trychroma.com/)


![EscherGraph building steps](img/Eschergraph_background.png.png)

### Node Matcher
The node matcher is used to match and merge nodes that refer to the same entity.
It involves two steps.

1. Identify potentially matching nodes using the Levenshtein distance. Indeed, nodes with exactly the same name are matched straight away.
   - For example:
     - matching 'p100' to 'p100 gpu'
     - 'Sam' and 'Sam Altman'

2) Decide on potential matches using LLM reasoning and contextual clues. This is done to make the right decision, even for edge cases: when dealing with different entities that are referenced by the same name across different chunks. For example, 'Sam', 'Sam Altman', and 'Sam Bankman-Fried'.
Therefore, the node matcher utilizes additional context to differentiate between them. This process involves:
     - LLM identifies node name ambiguities: given a list of potentially matching entity names, the LLM returns a list of edge cases.

     - Re-ranking potential matches: a re-ranker evaluates the similarity of the nodes based on context, metadata, or additional attributes to accurately determine which specific entity a node is referring to.

     - Contextual clues: the re-ranker leverages additional contextual information from the surrounding data or relationships to classify which node is the correct match. This might include looking at node connections, associated attributes, or other identifiers to make a more informed decision.