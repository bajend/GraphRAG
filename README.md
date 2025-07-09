# GraphRAG
Key Concepts1. Vector Database-Based RAGCore Idea: Uses vector embeddings (e.g., from models like BERT, Sentence-BERT, or OpenAI embeddings) to represent text chunks. Queries are matched to relevant chunks via similarity search (e.g., cosine similarity) in a vector database (e.g., Pinecone, Weaviate, FAISS).
Strengths:Fast and scalable for large datasets.
Effective for semantic similarity search.
Simple to implement with pre-trained embedding models.

Weaknesses:Lacks explicit representation of relationships between entities or concepts.
May struggle with complex queries requiring contextual or relational understanding.
Retrieval can be "flat," missing hierarchical or networked connections.

2. Graph-Based RAGCore Idea: Represents knowledge as a graph (nodes = entities/concepts, edges = relationships) using a knowledge graph (e.g., Neo4j, RDF, or custom graph structures). Retrieval leverages graph traversal or queries (e.g., Cypher) to fetch relevant nodes/edges, which are then used to augment generation.
Strengths:Captures explicit relationships (e.g., "Person A works at Company B") for better contextual retrieval.
Excels in queries requiring multi-hop reasoning (e.g., "Who are the colleagues of Person A at Company B?").
Can incorporate structured data and ontologies.

Weaknesses:More complex to set up and maintain (requires graph construction).
May be slower for large-scale similarity searches compared to vector DBs.
Less effective for unstructured, free-form text without clear relationships.

Some example graph db options: For general graph data structures, algorithms, and visualization of small to medium-sized graphs (hundreds of thousands of nodes/edges): NetworkX is your best bet. It's pure Python, requires no external server, and is incredibly versatile.

For performance-critical graph algorithms on larger in-memory graphs: Consider python-igraph.

For semantic web, RDF data, and SPARQL queries (knowledge graphs): RDFLib is the ideal choice.

For experimenting with a full-fledged graph database's features (like Cypher queries, persistence if you enable it, or specific graph database functionalities) but still wanting to keep it contained: You'd need a separate Memgraph (or Neo4j/other) instance and connect to it. While you can technically run Docker within Colab for some containers, it's generally not straightforward for persistent database services. Connecting to a free cloud tier of a graph database is often simpler for this purpose.

Metrics for RAG (Overview)
Beyond faithfulness and relevance, other important RAG metrics include:

Retrieval Metrics:

Precision@k: Out of the top 'k' retrieved documents, how many are truly relevant?

Recall@k: Out of all truly relevant documents, how many were retrieved in the top 'k'?

F1-Score: Harmonic mean of precision and recall.

Mean Reciprocal Rank (MRR): Measures the inverse of the rank of the first relevant document. Higher is better.

Normalized Discounted Cumulative Gain (NDCG): Accounts for the graded relevance of documents and their position in the ranking.

Generation Metrics (Beyond Faithfulness & Relevance):

Answer Correctness/Accuracy: Is the generated answer factually correct according to a ground truth?

Coherence/Fluency: Is the answer well-written, grammatically correct, and easy to understand?

Conciseness: Is the answer to the point, or does it include unnecessary verbosity?

Safety/Toxicity: Does the answer contain any harmful or biased content?

System Performance Metrics:

Latency: Time taken to generate a response.

Token Consumption/Cost: Number of tokens used for input and output, which relates to API costs.

How Faithfulness is Measured
Faithfulness (also known as Groundedness, Factuality, or Hallucination Rate) measures the extent to which the LLM's generated answer is supported by the provided context. A faithful answer does not introduce new, unsubstantiated claims or contradict the given information. It directly addresses the problem of LLM hallucination.

How it's Measured:

Claim Extraction: The first step is to break down the generated answer into individual, atomic claims or statements. This can be done manually or, more commonly in automated systems, by using another LLM or a specialized NLP model.

Example: If the answer is "Paris is the capital of France, and it's known for its delicious croissants and the Eiffel Tower.", the claims might be:

Claim 1: "Paris is the capital of France."

Claim 2: "Paris is known for its delicious croissants."

Claim 3: "Paris is known for its Eiffel Tower."

Context Entailment/Verification: For each extracted claim, it is then checked against the retrieved context to determine if the context explicitly supports, implies, or contradicts that claim. This is often done using:

LLM as a Judge: A powerful LLM (e.g., GPT-4) is prompted to act as an evaluator. For each claim from the generated answer, the LLM receives the claim and the retrieved context and is asked to determine if the claim is entailed by the context (supported), contradicted, or not found.

Natural Language Inference (NLI) Models: These are specialized models trained for tasks like entailment, contradiction, and neutrality. They can be used to programmatically check if a generated claim is entailed by a piece of context.

Keyword/Semantic Overlap (Simpler): As a simpler, less robust proxy (like in our Colab example), you might check for the presence of key phrases or high semantic similarity between the claim and sentences in the context.

Scoring:

Binary: A common approach is to assign a score of 1 if a claim is supported by the context and 0 if it's not (or contradicted). The overall faithfulness score is then the proportion of supported claims out of all claims.

Formula (Simple): Faithfulness = (Number of Supported Claims) / (Total Number of Claims)

Graded: More sophisticated methods might use a Likert scale (e.g., 1-5) or a continuous score for how strongly each claim is supported.

Example (using LLM as a Judge logic):

Query: "What is the capital of France and what is it known for?"

Retrieved Context: "Doc A: The capital of France is Paris. Doc B: Paris is known for its Eiffel Tower and delicious croissants."

Generated Answer: "The capital of France is Paris. It is famous for its Eiffel Tower, delicious croissants, and ancient Roman architecture."

Claims from Answer:

"The capital of France is Paris." (Supported by Doc A) -> Score 1

"It is famous for its Eiffel Tower." (Supported by Doc B) -> Score 1

"It is famous for its delicious croissants." (Supported by Doc B) -> Score 1

"It is famous for its ancient Roman architecture." (Not supported by Context) -> Score 0

Faithfulness Score: 3/4 = 0.75

Tools that help measure Faithfulness:

Ragas: A popular open-source framework specifically designed for RAG evaluation, including a faithfulness metric.

DeepEval: Another library offering various RAG evaluation metrics.

IBM Watsonx.governance: Enterprise solution with faithfulness evaluation.

How Relevance is Measured
Relevance in RAG can refer to two main aspects:

Context Relevance (Retrieval Relevance): How relevant are the retrieved documents/chunks to the original query? This assesses the quality of your retriever.

Answer Relevance (Generation Relevance): How relevant is the generated answer to the original query? This assesses if the LLM directly addresses the user's question.

Measuring Context Relevance:
Goal: Ensure the retriever provides useful information to the LLM.

Methods:

Human Annotation: Human evaluators manually label each retrieved document/chunk as relevant or irrelevant to the query. This is the gold standard but labor-intensive.

LLM as a Judge: An LLM is given the query, the retrieved chunk, and asked to rate its relevance (e.g., on a scale of 1-5, or binary relevant/irrelevant).

Embeddings Similarity: Compare the embedding of the retrieved chunk with the embedding of the query. While useful, it's an approximation of relevance; high semantic similarity doesn't always guarantee factual relevance to answer the specific query.

Keyword Overlap: A simple, less sophisticated method, checking for common keywords between the query and the retrieved text.

Metrics Derived: Precision@k, Recall@k, F1-Score, MRR, NDCG (as mentioned in Retrieval Metrics above).

Measuring Answer Relevance:
Goal: Ensure the LLM's response directly addresses the user's question without providing extraneous information or going off-topic.

Methods:

Human Evaluation: Human evaluators rate the generated answer's relevance to the query (e.g., on a Likert scale or binary).

LLM as a Judge: An LLM is given the query and the generated answer and asked to rate how relevant the answer is to the query. This is a common and effective automated approach.

Semantic Similarity (Answer vs. Query): Compute the cosine similarity between the embeddings of the generated answer and the original query. High similarity suggests high relevance.

Keyword Overlap (Simple): Check for key terms from the query in the generated answer.

Comparison to Ground Truth (if available): If you have a "gold standard" correct answer for a query, you can compare the generated answer to it using metrics like ROUGE (Recall-Oriented Understudy for Gisting Evaluation) or BLEU (Bilingual Evaluation Understudy), which measure overlap with a reference answer.

Example (using LLM as a Judge logic for Answer Relevance):

Query: "What is the capital of France?"

Generated Answer: "The capital of France is Paris. Did you know the Louvre Museum is also in Paris?"

LLM Judge's Role: Given the query and answer, the judge would assess if the answer primarily and directly addresses the query. In this case, "The capital of France is Paris" is highly relevant, but the "Louvre Museum" part might be considered slightly less relevant or verbose depending on strictness. The judge would assign a relevance score.

Tools that help measure Relevance:

Ragas: Offers answer_relevancy and context_relevancy metrics.

DeepEval: Provides AnswerRelevancyMetric and ContextualRelevancyMetric.

Many general LLM evaluation frameworks also include relevance assessment capabilities.
