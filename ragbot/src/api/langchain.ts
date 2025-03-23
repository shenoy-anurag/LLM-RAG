// import { z } from "zod";
// import {
//     AIMessage,
//     HumanMessage,
//     SystemMessage,
//     ToolMessage,
// } from "@langchain/core/messages";
// import { ChatOpenAI } from "@langchain/openai";
// import { OpenAIEmbeddings } from "@langchain/openai";
// import { QdrantVectorStore } from "@langchain/qdrant";
// import { MessagesAnnotation, StateGraph } from "@langchain/langgraph";
// import { tool } from "@langchain/core/tools";
// import { ToolNode, toolsCondition } from "@langchain/langgraph/prebuilt";
// // import { BaseMessage, isAIMessage } from "@langchain/core/messages";
// // import { ChatPromptTemplate } from "@langchain/core/prompts";


// const llm = new ChatOpenAI({
//     model: process.env.VITE_OPENAI_MODEL_NAME || "gpt-4o-mini-2024-07-18",
//     temperature: 0,
//     apiKey: process.env.VITE_OPENAI_API_KEY,
// });

// const embeddings = new OpenAIEmbeddings({
//     model: process.env.VITE_OPENAI_EMBEDDINGS_NAME || "text-embedding-3-small",
//     apiKey: process.env.VITE_OPENAI_API_KEY,
// });


// // function getVectorStore(collectionName: string) {
// //     const vectorStore = await QdrantVectorStore.fromExistingCollection(embeddings, {
// //         url: process.env.VITE_QDRANT_URL,
// //         collectionName: collectionName,
// //         apiKey: process.env.VITE_QDRANT_API_KEY,
// //     });
// //     return vectorStore;
// // }

// const vectorStore = await QdrantVectorStore.fromExistingCollection(embeddings, {
//     url: process.env.VITE_QDRANT_URL,
//     collectionName: process.env.VITE_QDRANT_COLLECTION,
//     apiKey: process.env.VITE_QDRANT_API_KEY,
// });


// const retrieveSchema = z.object({ query: z.string() });

// const system_prompt: string = `You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. 
// If you don't know the answer, just say that you don't know. Keep the answer short and concise. Try to use less than 5 sentences.`

// const retrieve = tool(
//     async ({ query }) => {
//         const retrievedDocs = await vectorStore.similaritySearch(query, 4);
//         const serialized = retrievedDocs
//             .map(
//                 (doc) => `Source: ${doc.metadata.source}\nContent: ${doc.pageContent}`
//             )
//             .join("\n");
//         return [serialized, retrievedDocs];
//     },
//     {
//         name: "retrieve",
//         description: "Retrieve information related to a query.",
//         schema: retrieveSchema,
//         responseFormat: "content_and_artifact",
//     }
// );


// // Step 1: Generate an AIMessage that may include a tool-call to be sent.
// async function queryOrRespond(state: typeof MessagesAnnotation.State) {
//     const llmWithTools = llm.bindTools([retrieve]);
//     const response = await llmWithTools.invoke(state.messages);
//     // MessagesState appends messages to state instead of overwriting
//     return { messages: [response] };
// }

// // Step 2: Execute the retrieval.
// const tools = new ToolNode([retrieve]);

// // Step 3: Generate a response using the retrieved content.
// async function generate(state: typeof MessagesAnnotation.State) {
//     // Get generated ToolMessages
//     let recentToolMessages = [];
//     for (let i = state["messages"].length - 1; i >= 0; i--) {
//         let message = state["messages"][i];
//         if (message instanceof ToolMessage) {
//             recentToolMessages.push(message);
//         } else {
//             break;
//         }
//     }
//     let toolMessages = recentToolMessages.reverse();

//     // Format into prompt
//     const docsContent = toolMessages.map((doc) => doc.content).join("\n");
//     const systemMessageContent =
//         system_prompt +
//         "\n\n" +
//         `${docsContent}`;

//     const conversationMessages = state.messages.filter(
//         (message) =>
//             message instanceof HumanMessage ||
//             message instanceof SystemMessage ||
//             (message instanceof AIMessage && message.tool_calls.length == 0)
//     );
//     const prompt = [
//         new SystemMessage(systemMessageContent),
//         ...conversationMessages,
//     ];

//     // Run
//     const response = await llm.invoke(prompt);
//     return { messages: [response] };
// }

// const graphBuilder = new StateGraph(MessagesAnnotation)
//     .addNode("queryOrRespond", queryOrRespond)
//     .addNode("tools", tools)
//     .addNode("generate", generate)
//     .addEdge("__start__", "queryOrRespond")
//     .addConditionalEdges("queryOrRespond", toolsCondition, {
//         __end__: "__end__",
//         tools: "tools",
//     })
//     .addEdge("tools", "generate")
//     .addEdge("generate", "__end__");

// const graph = graphBuilder.compile();

// export async function streamChat(user_prompt: string) {
//     const inputs1 = { messages: [{ role: "user", content: user_prompt }] };

//     // for await (const step of await graph.stream(inputs1, {
//     //     streamMode: "values",
//     // })) {
//     //     const lastMessage = step.messages[step.messages.length - 1];
//     //     prettyPrint(lastMessage);
//     //     // console.log("-----\n");
//     // }
//     const resp = await graph.stream(inputs1, {
//         streamMode: "values",
//     });
//     return resp;
// }
