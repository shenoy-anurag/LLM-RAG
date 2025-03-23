import { ChatInput } from "@/components/custom/chatinput";
import { PreviewMessage, ThinkingMessage } from "../../components/custom/message";
import { useScrollToBottom } from '@/components/custom/use-scroll-to-bottom';
import { useState, useRef } from "react";
import { message } from "../../interfaces/interfaces"
import { Overview } from "@/components/custom/overview";
import { Header } from "@/components/custom/header";
import { v4 as uuidv4 } from 'uuid';
import { getCollections, retrieveContext } from "@/api/qdrant";
// import { streamChat } from "@/api/openai";
// import { streamChat } from "@/api/langchain";
// import {
//   AIMessage,
//   BaseMessage,
//   isAIMessage
// } from "@langchain/core/messages";

// const socket = new WebSocket("ws://localhost:8090"); //change to your websocket endpoint

export function Chat() {
  const [messagesContainerRef, messagesEndRef] = useScrollToBottom<HTMLDivElement>();
  const [messages, setMessages] = useState<message[]>([]);
  const [question, setQuestion] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // async function searchQuery(query: string) {
  //   try {
  //     if (query === "") return;
  //     if (query !== keyword) {
  //       setKeyword(query);
  //     }
  //     setStatus("loading");
  //     setData(undefined);
  //     const dynamicData = await streamChat(query);
  //     return dynamicData;
  //   } catch (error) {
  //     console.log(error);
  //     setStatus("failed");
  //   }
  // }

  // const prettyPrint = (message: BaseMessage) => {
  //     let txt = `[${message.getType()}]: ${message.content}`;
  //     if ((isAIMessage(message) && message.tool_calls?.length) || 0 > 0) {
  //         const tool_calls = (message as AIMessage)?.tool_calls
  //             ?.map((tc) => `- ${tc.name}(${JSON.stringify(tc.args)})`)
  //             .join("\n");
  //         txt += ` \nTools: \n${tool_calls}`;
  //     }
  //     console.log(txt);
  // };

  const messageHandlerRef = useRef<((event: MessageEvent) => void) | null>(null);

  const cleanupMessageHandler = () => {
    // if (messageHandlerRef.current && socket) {
    if (messageHandlerRef.current) {
      // socket.removeEventListener("message", messageHandlerRef.current);
      messageHandlerRef.current = null;
    }
  };

  async function handleSubmit(text?: string) {
    // if (!socket || socket.readyState !== WebSocket.OPEN || isLoading) return;

    const messageText = text || question;
    setIsLoading(true);
    cleanupMessageHandler();

    const traceId = uuidv4();
    setMessages(prev => [...prev, { content: messageText, role: "user", id: traceId }]);
    // socket.send(messageText);
    const collections = getCollections();
    console.log('List of collections:', collections);
    const context = await retrieveContext(messageText);
    console.log(context);
    // const resp = streamChat(messageText);
    setQuestion("");

    // for await (const step of await resp) {
    //   const lastMessage = step.messages[step.messages.length - 1];
    //   console.log(lastMessage);
    // }

    // try {
    //   const messageHandler = (event: MessageEvent) => {
    //     setIsLoading(false);
    //     if (event.data.includes("[END]")) {
    //       return;
    //     }

    //     setMessages(prev => {
    //       const lastMessage = prev[prev.length - 1];
    //       const newContent = lastMessage?.role === "assistant"
    //         ? lastMessage.content + event.data
    //         : event.data;

    //       const newMessage = { content: newContent, role: "assistant", id: traceId };
    //       return lastMessage?.role === "assistant"
    //         ? [...prev.slice(0, -1), newMessage]
    //         : [...prev, newMessage];
    //     });

    //     if (event.data.includes("[END]")) {
    //       cleanupMessageHandler();
    //     }
    //   };

    //   messageHandlerRef.current = messageHandler;
    //   socket.addEventListener("message", messageHandler);
    // } catch (error) {
    //   console.error("WebSocket error:", error);
    //   setIsLoading(false);
    // }
  }

  return (
    <div className="flex flex-col min-w-0 h-dvh bg-background">
      <Header />
      {/* <div className="mx-auto flex-col" >Should the Transformer model be used as the primary architecture for all natural language processing tasks?</div> */}
      <div className="flex flex-col min-w-0 gap-6 flex-1 overflow-y-scroll pt-4" ref={messagesContainerRef}>
        {messages.length == 0 && <Overview />}
        {messages.map((message, index) => (
          <PreviewMessage key={index} message={message} />
        ))}
        {isLoading && <ThinkingMessage />}
        <div ref={messagesEndRef} className="shrink-0 min-w-[24px] min-h-[24px]" />
      </div>
      <div className="flex mx-auto px-4 bg-background pb-4 md:pb-6 gap-2 w-full md:max-w-3xl">
        <ChatInput
          question={question}
          setQuestion={setQuestion}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};