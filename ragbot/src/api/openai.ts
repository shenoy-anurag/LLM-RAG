"use server";
import { createOpenAI } from '@ai-sdk/openai';
import { streamText, generateText } from 'ai';

const openai = createOpenAI({
    // custom settings, e.g.
    apiKey: import.meta.env.VITE_OPENAI_API_KEY,
    compatibility: 'strict', // strict mode, enable when using the OpenAI API
});

const system_prompt: string = `You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know. Keep the answer short and concise. Try to use less than 5 sentences.`

// System Prompt we are using: 
const rag_prompt = (question: string, context: string) => `
${system_prompt}
Question: ${question} 
Context: ${context} 
Answer:
`

function buildPrompt(question: string, context: string): string {
    const prompt: string = rag_prompt(question, context);
    return prompt;
}

export async function invokeChat(question: string, context: string) {
    const prompt: string = buildPrompt(question, context);
    const response = await generateText({
        model: openai(import.meta.env.VITE_OPENAI_MODEL_NAME || "gpt-4o-mini-2024-07-18"),
        prompt: prompt,
    });
    return response.text;
}

export async function streamChat(question: string, context: string) {
    const prompt: string = buildPrompt(question, context);
    const { textStream } = streamText({
        model: openai(import.meta.env.VITE_OPENAI_MODEL_NAME || "gpt-4o-mini-2024-07-18"),
        prompt: prompt,
    });
    return textStream;
}