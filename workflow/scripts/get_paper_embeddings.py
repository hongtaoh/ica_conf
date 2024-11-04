from sentence_transformers import SentenceTransformer
import json
import sys
from sklearn.decomposition import PCA
import pickle
from sklearn.preprocessing import normalize

PAPERS_JSON = sys.argv[1]
PAPER_EMBEDDINGS_JSON = sys.argv[2]
PCA_MODEL = sys.argv[3]

# Initialize the model
model = SentenceTransformer('all-MiniLM-L6-v2')
batch_size = 32
target_dim = 80

if __name__ == '__main__':
    # Load papers
    with open(PAPERS_JSON, "r") as f:
        papers = json.load(f)

    all_embeddings = []

    # Collect all embeddings first
    for i in range(0, len(papers), batch_size): 
        batch_papers = papers[i:i + batch_size]
        texts = [
            (paper.get("title") or "") + " " + (
                paper.get("abstract") or "") for paper in batch_papers]
        batch_embeddings = model.encode(texts)
        all_embeddings.extend(batch_embeddings)

    # Perform PCA to reduce dimensionality
    pca = PCA(n_components=target_dim)
    reduced_embeddings = pca.fit_transform(all_embeddings)
    reduced_embeddings = normalize(reduced_embeddings, norm='l2')
    with open(PCA_MODEL, "wb") as f:
        pickle.dump(pca, f)
    print("pre-trained PCA saved to 'pca_model.pkl'")

    # Create an array of objects for the embeddings
    paper_embeddings = [
        {"paper_id": paper["paper_id"], "embedding": reduced_embeddings[i].tolist()}
        for i, paper in enumerate(papers)
    ]

    with open(PAPER_EMBEDDINGS_JSON, "w") as f:
        json.dump(paper_embeddings, f, indent=2)

    print("Reduced embeddings saved to 'paper_embeddings.json'")