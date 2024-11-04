from sentence_transformers import SentenceTransformer
import json
import sys

PAPERS_JSON = sys.argv[1]
PAPER_EMBEDDINGS_JSON = sys.argv[2]

# Initialize the model
model = SentenceTransformer('all-MiniLM-L6-v2')
batch_size = 32

if __name__ == '__main__':
    # Load papers
    with open(PAPERS_JSON, "r") as f:
        papers = json.load(f)

    paper_embeddings = {}
    for i in range(0, len(papers), batch_size): 
        batch_papers = papers[i:i + batch_size]
        texts = [
            (paper.get("title") or "") + " " + (
                paper.get("abstract") or "") for paper in batch_papers]
        batch_embeddings = model.encode(texts)
        
        for j, embedding in enumerate(batch_embeddings):
            paper_id = batch_papers[j]["paper_id"]
            paper_embeddings[paper_id] = embedding.tolist()

    # Save embeddings to a JSON file
    with open(PAPER_EMBEDDINGS_JSON, "w") as f:
        json.dump(paper_embeddings, f)

    print("Embeddings saved to 'paper_embeddings.json'")