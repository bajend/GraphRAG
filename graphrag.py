# -*- coding: utf-8 -*-
"""GraphRAG.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1SsF-dza7YjeOlBHj4-P1jFi_sDpZBs_K
"""

sample_docs = [
    "Doc 1: The capital of France is Paris. Paris is known for its Eiffel Tower and delicious croissants.",
    "Doc 2: Mount Everest is the highest mountain in the world, located in the Himalayas. Scaling it is a huge challenge.",
    "Doc 3: The Amazon rainforest is the largest rainforest on Earth, home to incredible biodiversity, including jaguars and toucans.",
    "Doc 4: Water (H2O) is essential for all known forms of life. It covers about 71% of the Earth's surface.",
    "Doc 5: Machine learning is a field of artificial intelligence that enables systems to learn from data without explicit programming.",
    "Doc 6: The Golden Gate Bridge is an iconic suspension bridge spanning the Golden Gate strait in California, connecting San Francisco to Marin County.",
    "Doc 7: Renewable energy sources like solar and wind power are crucial for a sustainable future, reducing reliance on fossil fuels.",
    "Doc 8: Historical records indicate that ancient Egypt was a civilization of ancient Northeastern Africa, concentrated along the lower reaches of the Nile River.",
    "Doc 9: Dogs are domesticated mammals, known for their loyalty and diverse breeds like Golden Retrievers and German Shepherds.",
    "Doc 10: The human heart is a muscular organ that pumps blood through the circulatory system, supplying oxygen and nutrients to the body."
]

print (sample_docs)

!pip install -q transformers sentence-transformers faiss-cpu networkx
!pip install -q wikipedia-api # For potential future knowledge extraction but not directly used for doc generation here

import torch
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import re
from collections import defaultdict

# 1. Load Embedding Model
# We'll use a small, fast model for embeddings
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Dummy LLM Function (to simulate response generation)
def dummy_llm_generate(prompt, context=None):
    """
    A simple function to simulate an LLM's response.
    It tries to incorporate context if provided, otherwise responds generically.
    """
    if context:
        # Simple heuristic: try to extract keywords from context and weave them in
        keywords = set(word.lower() for word in re.findall(r'\b\w+\b', context) if len(word) > 3)
        common_keywords = " ".join(list(keywords)[:5]) # Take up to 5 keywords

        if "capital of france" in prompt.lower() and "paris" in context.lower():
            return f"Based on the information, the capital of France is Paris. It is known for its {common_keywords}."
        elif "highest mountain" in prompt.lower() and "everest" in context.lower():
            return f"According to the context, the highest mountain is Mount Everest, located in the Himalayas. It is {common_keywords}."
        elif "amazon rainforest" in prompt.lower() and "biodiversity" in context.lower():
            return f"The Amazon rainforest, as described, is the largest rainforest, known for its {common_keywords} and vast biodiversity."
        elif "water" in prompt.lower() and "h2o" in context.lower():
            return f"The context states that Water, or H2O, is crucial for life and covers much of Earth. It's {common_keywords}."
        elif "machine learning" in prompt.lower() and "ai" in context.lower():
            return f"Machine learning, a field of AI, enables systems to learn from data without explicit programming, as per the text. It involves {common_keywords}."
        elif "golden gate bridge" in prompt.lower() and "san francisco" in context.lower():
            return f"The Golden Gate Bridge is an iconic suspension bridge in California, connecting San Francisco, known for its {common_keywords}."
        elif "renewable energy" in prompt.lower() and "solar" in context.lower():
            return f"Renewable energy, like solar and wind, is vital for sustainability, as mentioned. It aims to reduce {common_keywords}."
        elif "ancient egypt" in prompt.lower() and "nile river" in context.lower():
            return f"Ancient Egypt was a civilization along the Nile River in Northeastern Africa, as the context indicates. It has a rich {common_keywords}."
        elif "dogs" in prompt.lower() and "loyalty" in context.lower():
            return f"Dogs are domesticated mammals recognized for their loyalty and diverse breeds, including {common_keywords}."
        elif "human heart" in prompt.lower() and "blood" in context.lower():
            return f"The human heart is a muscular organ that pumps blood through the circulatory system, supplying {common_keywords} to the body."
        else:
            return f"Based on the provided context: '{context}', I can tell you that: {prompt.replace('?', '')}. Key themes include {common_keywords}."
    else:
        return f"I don't have specific context for '{prompt.replace('?', '')}'. Can you provide more details?"

# 3. Evaluation Metrics (Simplified)
def evaluate_rag(query, expected_answer_keywords, generated_answer):
    """
    Evaluates a RAG system's response based on keyword presence and a very basic similarity.
    """
    generated_answer_lower = generated_answer.lower()
    query_lower = query.lower()

    # Faithfulness/Precision (do expected keywords appear?)
    faithfulness_score = sum(1 for kw in expected_answer_keywords if kw.lower() in generated_answer_lower) / len(expected_answer_keywords) if expected_answer_keywords else 0

    # Relevance (does the answer contain query terms?)
    query_terms = set(word for word in query_lower.split() if len(word) > 2)
    relevance_score = sum(1 for term in query_terms if term in generated_answer_lower) / len(query_terms) if query_terms else 0

    return {
        "faithfulness": faithfulness_score,
        "relevance": relevance_score,
        "generated_answer": generated_answer
    }

print("Setup complete.")

print("\n--- 1. In-Memory Vector-Based RAG ---")

# 1. Indexing: Create embeddings for documents and store them in FAISS
document_embeddings = embedding_model.encode(sample_docs)
d = document_embeddings.shape[1] # Dimension of embeddings
index = faiss.IndexFlatL2(d) # L2 distance for similarity
index.add(document_embeddings)

# 2. RAG Function
def vector_rag(query, top_k=2):
    # Embed the query
    query_embedding = embedding_model.encode([query])

    # Search the FAISS index
    distances, indices = index.search(query_embedding, top_k)

    # Retrieve relevant documents
    retrieved_docs = [sample_docs[i] for i in indices[0]]
    context = "\n".join(retrieved_docs)

    # Generate response using dummy LLM
    response = dummy_llm_generate(query, context)
    return response, retrieved_docs

# Test Queries and Evaluation
queries_vector = [
    {"query": "What is the capital of France?", "expected_keywords": ["paris", "eiffel tower"]},
    {"query": "Tell me about the highest mountain.", "expected_keywords": ["mount everest", "himalayas"]},
    {"query": "Which creatures live in the Amazon rainforest?", "expected_keywords": ["jaguars", "toucans", "biodiversity"]},
    {"query": "What is the importance of H2O?", "expected_keywords": ["water", "life", "earth's surface"]},
    {"query": "Describe machine learning.", "expected_keywords": ["artificial intelligence", "learn from data"]}
]

vector_rag_results = {}
for i, q_data in enumerate(queries_vector):
    print(f"\nQuery {i+1}: {q_data['query']}")
    response, retrieved_docs = vector_rag(q_data['query'])
    vector_rag_results[q_data['query']] = evaluate_rag(q_data['query'], q_data['expected_keywords'], response)
    print(f"Retrieved Docs: {retrieved_docs}")
    print(f"Generated Answer: {response}")
    print(f"Evaluation: {vector_rag_results[q_data['query']]}")

# Calculate average scores
avg_faithfulness = np.mean([res['faithfulness'] for res in vector_rag_results.values()])
avg_relevance = np.mean([res['relevance'] for res in vector_rag_results.values()])
print(f"\nVector RAG Average Faithfulness: {avg_faithfulness:.2f}")
print(f"Vector RAG Average Relevance: {avg_relevance:.2f}")

print("\n--- 2. Graph RAG using NetworkX ---")

# 1. Indexing: Build a knowledge graph from documents
G = nx.Graph()

# Simple entity/relationship extraction (can be improved with LLM for real use)
def extract_entities_and_relationships(doc_id, text):
    entities = []
    relationships = []

    # Simple keyword-based entity extraction
    if "France" in text: entities.append(("France", {"type": "Country", "doc_id": doc_id}))
    if "Paris" in text: entities.append(("Paris", {"type": "City", "doc_id": doc_id}))
    if "Eiffel Tower" in text: entities.append(("Eiffel Tower", {"type": "Landmark", "doc_id": doc_id}))
    if "Mount Everest" in text: entities.append(("Mount Everest", {"type": "Mountain", "doc_id": doc_id}))
    if "Himalayas" in text: entities.append(("Himalayas", {"type": "Mountain Range", "doc_id": doc_id}))
    if "Amazon rainforest" in text: entities.append(("Amazon rainforest", {"type": "Forest", "doc_id": doc_id}))
    if "biodiversity" in text: entities.append(("biodiversity", {"type": "Concept", "doc_id": doc_id}))
    if "jaguars" in text: entities.append(("jaguars", {"type": "Animal", "doc_id": doc_id}))
    if "toucans" in text: entities.append(("toucans", {"type": "Animal", "doc_id": doc_id}))
    if "Water" in text or "H2O" in text: entities.append(("Water (H2O)", {"type": "Compound", "doc_id": doc_id}))
    if "Machine learning" in text: entities.append(("Machine learning", {"type": "Field", "doc_id": doc_id}))
    if "artificial intelligence" in text: entities.append(("Artificial Intelligence", {"type": "Field", "doc_id": doc_id}))
    if "Golden Gate Bridge" in text: entities.append(("Golden Gate Bridge", {"type": "Bridge", "doc_id": doc_id}))
    if "San Francisco" in text: entities.append(("San Francisco", {"type": "City", "doc_id": doc_id}))
    if "California" in text: entities.append(("California", {"type": "State", "doc_id": doc_id}))
    if "Renewable energy" in text: entities.append(("Renewable energy", {"type": "Concept", "doc_id": doc_id}))
    if "solar" in text: entities.append(("solar power", {"type": "Energy Source", "doc_id": doc_id}))
    if "wind power" in text: entities.append(("wind power", {"type": "Energy Source", "doc_id": doc_id}))
    if "ancient Egypt" in text: entities.append(("ancient Egypt", {"type": "Civilization", "doc_id": doc_id}))
    if "Nile River" in text: entities.append(("Nile River", {"type": "River", "doc_id": doc_id}))
    if "Dogs" in text: entities.append(("Dogs", {"type": "Animal", "doc_id": doc_id}))
    if "human heart" in text: entities.append(("human heart", {"type": "Organ", "doc_id": doc_id}))
    if "blood" in text: entities.append(("blood", {"type": "Body Fluid", "doc_id": doc_id}))


    # Add nodes
    for entity, attrs in entities:
        if not G.has_node(entity):
            G.add_node(entity, **attrs, original_text=text)
        else: # Update existing node's original_text if it's from a new document
            if 'original_text' in G.nodes[entity]:
                if isinstance(G.nodes[entity]['original_text'], list):
                    G.nodes[entity]['original_text'].append(text)
                else:
                    G.nodes[entity]['original_text'] = [G.nodes[entity]['original_text'], text]
            else:
                 G.nodes[entity]['original_text'] = text

    # Simple relationship extraction (co-occurrence)
    if "Paris" in text and "France" in text: relationships.append(("Paris", "France", "is_capital_of"))
    if "Eiffel Tower" in text and "Paris" in text: relationships.append(("Eiffel Tower", "Paris", "located_in"))
    if "Mount Everest" in text and "Himalayas" in text: relationships.append(("Mount Everest", "Himalayas", "located_in"))
    if "Amazon rainforest" in text and ("jaguars" in text or "toucans" in text): relationships.append(("Amazon rainforest", "biodiversity", "known_for"))
    if "Machine learning" in text and "artificial intelligence" in text: relationships.append(("Machine learning", "Artificial Intelligence", "part_of"))
    if "Golden Gate Bridge" in text and "San Francisco" in text: relationships.append(("Golden Gate Bridge", "San Francisco", "connects"))
    if "Golden Gate Bridge" in text and "California" in text: relationships.append(("Golden Gate Bridge", "California", "located_in_state"))
    if "Renewable energy" in text and ("solar power" in text or "wind power" in text): relationships.append(("Renewable energy", "sustainable future", "leads_to"))
    if "ancient Egypt" in text and "Nile River" in text: relationships.append(("ancient Egypt", "Nile River", "located_along"))
    if "Dogs" in text and "mammals" in text: relationships.append(("Dogs", "mammals", "is_a_type_of"))
    if "human heart" in text and "blood" in text: relationships.append(("human heart", "blood", "pumps"))


    # Add edges
    for source, target, rel_type in relationships:
        if G.has_node(source) and G.has_node(target):
            G.add_edge(source, target, relationship=rel_type, doc_id=doc_id)

# Populate the graph
for i, doc_text in enumerate(sample_docs):
    extract_entities_and_relationships(f"doc_{i+1}", doc_text)

print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

# 2. RAG Function for Graph
def graph_rag(query, max_hops=1):
    # Simple entity extraction from query (can be improved with LLM entity linking)
    query_entities = [
        "France" if "france" in query.lower() else None,
        "Mount Everest" if "everest" in query.lower() else None,
        "Amazon rainforest" if "amazon" in query.lower() else None,
        "Water (H2O)" if "h2o" in query.lower() or "water" in query.lower() else None,
        "Machine learning" if "machine learning" in query.lower() else None,
        "Golden Gate Bridge" if "golden gate" in query.lower() else None,
        "Renewable energy" if "renewable energy" in query.lower() else None,
        "ancient Egypt" if "ancient egypt" in query.lower() else None,
        "Dogs" if "dogs" in query.lower() else None,
        "human heart" if "heart" in query.lower() else None,
    ]
    query_entities = [e for e in query_entities if e is not None and e in G]

    context_nodes = set()
    retrieved_info_snippets = []

    for entity in query_entities:
        context_nodes.add(entity)
        if 'original_text' in G.nodes[entity]:
            if isinstance(G.nodes[entity]['original_text'], list):
                retrieved_info_snippets.extend(G.nodes[entity]['original_text'])
            else:
                retrieved_info_snippets.append(G.nodes[entity]['original_text'])

        # Traverse neighbors
        for neighbor in nx.neighbors(G, entity):
            context_nodes.add(neighbor)
            if 'original_text' in G.nodes[neighbor]:
                if isinstance(G.nodes[neighbor]['original_text'], list):
                    retrieved_info_snippets.extend(G.nodes[neighbor]['original_text'])
                else:
                    retrieved_info_snippets.append(G.nodes[neighbor]['original_text'])
            edge_data = G.get_edge_data(entity, neighbor)
            if 'relationship' in edge_data:
                retrieved_info_snippets.append(f"{entity} --({edge_data['relationship']})--> {neighbor}")

    context = "\n".join(list(set(retrieved_info_snippets))) # Use set to deduplicate
    response = dummy_llm_generate(query, context)
    return response, list(set(retrieved_info_snippets))

# Test Queries and Evaluation
queries_graph = [
    {"query": "What city is the Eiffel Tower in and what country is it the capital of?", "expected_keywords": ["paris", "france", "eiffel tower"]},
    {"query": "Tell me about the biggest mountain and its range.", "expected_keywords": ["mount everest", "himalayas"]},
    {"query": "What animals are found in the large forest?", "expected_keywords": ["jaguars", "toucans", "amazon rainforest"]},
    {"query": "Can you explain the connection between machine learning and AI?", "expected_keywords": ["machine learning", "artificial intelligence", "part of"]},
    {"query": "Which bridge connects San Francisco to Marin County and where is it located?", "expected_keywords": ["golden gate bridge", "san francisco", "california"]}
]

graph_rag_results = {}
for i, q_data in enumerate(queries_graph):
    print(f"\nQuery {i+1}: {q_data['query']}")
    response, retrieved_info = graph_rag(q_data['query'])
    graph_rag_results[q_data['query']] = evaluate_rag(q_data['query'], q_data['expected_keywords'], response)
    print(f"Retrieved Info: {retrieved_info}")
    print(f"Generated Answer: {response}")
    print(f"Evaluation: {graph_rag_results[q_data['query']]}")

# Calculate average scores
avg_faithfulness = np.mean([res['faithfulness'] for res in graph_rag_results.values()])
avg_relevance = np.mean([res['relevance'] for res in graph_rag_results.values()])
print(f"\nGraph RAG Average Faithfulness: {avg_faithfulness:.2f}")
print(f"Graph RAG Average Relevance: {avg_relevance:.2f}")

print("\n--- 3. Hybrid RAG (Vector + Graph) ---")

# Re-using the vector index and graph G from previous sections

# 1. Hybrid RAG Function
def hybrid_rag(query, top_k_vector=2, max_hops_graph=1):
    # Step 1: Initial Vector Search to find relevant documents/chunks
    query_embedding = embedding_model.encode([query])
    distances, indices = index.search(query_embedding, top_k_vector)
    initial_retrieved_docs = [sample_docs[i] for i in indices[0]]

    # Step 2: Extract entities from the query AND initial retrieved docs for graph traversal
    combined_text_for_graph_extraction = query + " ".join(initial_retrieved_docs)

    # Simplified entity extraction from combined text for graph query
    # This is a very basic example; in real systems, you'd use NER/Entity Linking
    query_entities = [
        node for node in G.nodes() if node.lower() in combined_text_for_graph_extraction.lower()
    ]
    # Filter for entities that actually exist in our graph
    query_entities = [e for e in query_entities if e in G]

    graph_context_snippets = set()

    for entity in query_entities:
        # Add the entity's own original text
        if 'original_text' in G.nodes[entity]:
            if isinstance(G.nodes[entity]['original_text'], list):
                for text_snippet in G.nodes[entity]['original_text']:
                    graph_context_snippets.add(text_snippet)
            else:
                graph_context_snippets.add(G.nodes[entity]['original_text'])

        # Traverse neighbors for related information
        for neighbor in nx.neighbors(G, entity):
            if 'original_text' in G.nodes[neighbor]:
                if isinstance(G.nodes[neighbor]['original_text'], list):
                    for text_snippet in G.nodes[neighbor]['original_text']:
                        graph_context_snippets.add(text_snippet)
                else:
                    graph_context_snippets.add(G.nodes[neighbor]['original_text'])
            edge_data = G.get_edge_data(entity, neighbor)
            if 'relationship' in edge_data:
                graph_context_snippets.add(f"{entity} --({edge_data['relationship']})--> {neighbor}")


    # Combine context from initial vector search and graph traversal
    # Prioritize graph context if available, otherwise fall back to vector context
    if graph_context_snippets:
        final_context = "\n".join(list(graph_context_snippets))
    else:
        final_context = "\n".join(initial_retrieved_docs)

    # Generate response
    response = dummy_llm_generate(query, final_context)
    return response, list(initial_retrieved_docs), list(graph_context_snippets)

# Test Queries and Evaluation (using a mix of query types)
queries_hybrid = [
    {"query": "What is the capital of France and what famous landmark is there?", "expected_keywords": ["paris", "eiffel tower", "france"]},
    {"query": "Which mountain is the highest and in what range is it located?", "expected_keywords": ["mount everest", "himalayas"]},
    {"query": "Tell me about the animals in the largest rainforest.", "expected_keywords": ["jaguars", "toucans", "amazon rainforest"]},
    {"query": "What is AI and how does machine learning relate to it?", "expected_keywords": ["machine learning", "artificial intelligence", "part of"]},
    {"query": "What is a characteristic of dogs, and what's a common breed?", "expected_keywords": ["loyalty", "golden retrievers", "german shepherds"]}
]

hybrid_rag_results = {}
for i, q_data in enumerate(queries_hybrid):
    print(f"\nQuery {i+1}: {q_data['query']}")
    response, vec_retrieved, graph_retrieved = hybrid_rag(q_data['query'])
    hybrid_rag_results[q_data['query']] = evaluate_rag(q_data['query'], q_data['expected_keywords'], response)
    print(f"Vector Retrieved Docs: {vec_retrieved}")
    print(f"Graph Retrieved Info: {graph_retrieved}")
    print(f"Generated Answer: {response}")
    print(f"Evaluation: {hybrid_rag_results[q_data['query']]}")

# Calculate average scores
avg_faithfulness = np.mean([res['faithfulness'] for res in hybrid_rag_results.values()])
avg_relevance = np.mean([res['relevance'] for res in hybrid_rag_results.values()])
print(f"\nHybrid RAG Average Faithfulness: {avg_faithfulness:.2f}")
print(f"Hybrid RAG Average Relevance: {avg_relevance:.2f}")