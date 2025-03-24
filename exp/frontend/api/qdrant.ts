import { QdrantClient } from '@qdrant/js-client-rest';
import { createEmbeddingVector, generateEmbeddings } from './embedding';

// Qdrant Cloud client
const qdrant = new QdrantClient({
    url: import.meta.env.VITE_QDRANT_URL,
    apiKey: import.meta.env.VITE_QDRANT_API_KEY,
});

const collectionName: string = import.meta.env.VITE_QDRANT_COLLECTION || "medquad";
const K: number = 4;


export async function getCollections() {
    const result = await qdrant.getCollections();
    return result.collections;
}

export async function retrieveContext(user_prompt: string) {
    console.log(user_prompt);
    // Convert user_prompt to query vector
    const queryEmbeddings = await generateEmbeddings(user_prompt);
    const queryVector = await createEmbeddingVector(queryEmbeddings);
    
    const res = await qdrant.search(collectionName, {
        vector: queryVector,
        limit: K,
    });
    return res
}