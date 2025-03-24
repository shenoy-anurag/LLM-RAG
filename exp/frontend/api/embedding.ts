"use server";
import { createOpenAI } from '@ai-sdk/openai';
import { embedMany, EmbedManyResult } from 'ai';


const openai = createOpenAI({
    // custom settings, e.g.
    apiKey: import.meta.env.VITE_OPENAI_API_KEY,
    compatibility: 'strict', // strict mode, enable when using the OpenAI API
});

const embeddingModel = openai.embedding(
    import.meta.env.VITE_OPENAI_EMBEDDINGS_NAME || "text-embedding-3-small"
);

const generateChunks = (input: string): string[] => {
    return input
        .trim()
        .split('.')
        .filter(i => i !== '');
};

// export const generateEmbeddings = async (
//     value: string,
// ): Promise<Array<{ embedding: number[]; content: string }>> => {
//     const chunks = generateChunks(value);
//     const { embeddings } = await embedMany({
//         model: embeddingModel,
//         values: chunks,
//     });
//     return embeddings.map((e, i) => ({ content: chunks[i], embedding: e }));
// };

// export const createEmbeddingVector = async (
//     embeddings: Array<{ embedding: number[]; content: string }>,
// ): Promise<Array<number>> => {
//     const queryVector: number[] = [];
//     for (let i = 0; i < embeddings.length; i++) {
//         const v = embeddings[i].embedding[0];
//         queryVector.push(v);
//     }
//     return queryVector;
// };

export const generateEmbeddings = async (
    value: string,
) => {
    const chunks = generateChunks(value);
    const embeddings = await embedMany({
        model: embeddingModel,
        values: chunks,
    });
    return embeddings;
};

export const createEmbeddingVector = async (
    embeddingsResult: EmbedManyResult<string>,
): Promise<Array<number>> => {
    const queryVector: number[] = embeddingsResult.embeddings.map(embedding => embedding[0]);
    return queryVector;
};

