from sentence_transformers import SentenceTransformer
import json

# Initialize the model
model = SentenceTransformer('all-MiniLM-L6-v2')
batch_size = 32

API_

# Load your papers
with open("../data/api/papers.json", "r") as f:
    papers = json.load(f)

paper_embeddings = {}
for i in range(0, len(papers), batch_size): 
    batch_papers = papers[i:i + batch_size]
    texts = [(paper.get("title") or "") + " " + (paper.get("abstract") or "") for paper in batch_papers]
    batch_embeddings = model.encode(texts)
    
    for j, embedding in enumerate(batch_embeddings):
        paper_id = batch_papers[j]["paper_id"]
        paper_embeddings[paper_id] = embedding.tolist()  # Store each embedding as a list

# Save embeddings to a JSON file
with open("../data/api/paper_embeddings.json", "w") as f:
    json.dump(paper_embeddings, f)

print("Embeddings saved to 'paper_embeddings.json'")