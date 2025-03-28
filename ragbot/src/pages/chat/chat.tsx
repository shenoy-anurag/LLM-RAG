import { useState } from "react";
import { v4 as uuidv4 } from 'uuid';
import { PreviewMessage, ThinkingMessage } from "@/components/custom/message";
import { useScrollToBottom } from '@/components/custom/use-scroll-to-bottom';
import { ChatInput } from "@/components/custom/chatinput";
import { Overview } from "@/components/custom/overview";
import { Header } from "@/components/custom/header";
import { Separator } from "@/components/ui/separator";
import { message } from "@/interfaces/interfaces"

// const socket = new WebSocket("ws://localhost:8000/api/v1/chat/ws"); //change to your websocket endpoint

export function Chat() {
  const [messagesContainerRef, messagesEndRef] = useScrollToBottom<HTMLDivElement>();
  const [messages, setMessages] = useState<message[]>([]);
  const [question, setQuestion] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // const messageHandlerRef = useRef<((event: MessageEvent) => void) | null>(null);

  // const cleanupMessageHandler = () => {
  //   if (messageHandlerRef.current && socket) {
  //     socket.removeEventListener("message", messageHandlerRef.current);
  //     messageHandlerRef.current = null;
  //   }
  // };

  // async function handleSubmit(text?: string) {
  //   if (!socket || socket.readyState !== WebSocket.OPEN || isLoading) return;

  //   const messageText = text || question;
  //   setIsLoading(true);
  //   cleanupMessageHandler();

  //   const traceId = uuidv4();
  //   setMessages(prev => [...prev, { content: messageText, role: "user", id: traceId }]);
  //   socket.send(messageText);
  //   setQuestion("");

  //   try {
  //     const messageHandler = (event: MessageEvent) => {
  //       setIsLoading(false);
  //       if (event.data.includes("[END]")) {
  //         console.log("return");
  //         return;
  //       }

  //       setMessages(prev => {
  //         const lastMessage = prev[prev.length - 1];
  //         const newContent = lastMessage?.role === "assistant"
  //           ? lastMessage.content + event.data
  //           : event.data;
  //         console.log(event.data);
  //         const newMessage = { content: newContent, role: "assistant", id: traceId };
  //         return lastMessage?.role === "assistant"
  //           ? [...prev.slice(0, -1), newMessage]
  //           : [...prev, newMessage];
  //       });

  //       if (event.data.includes("[END]")) {
  //         console.log("cleaning up");
  //         cleanupMessageHandler();
  //       }
  //     };

  //     messageHandlerRef.current = messageHandler;
  //     socket.addEventListener("message", messageHandler);
  //   } catch (error) {
  //     console.error("WebSocket error:", error);
  //     setIsLoading(false);
  //   }
  // }

  async function searchQuery(text: string) {
    const API_URL_CHAT_RAG = import.meta.env.VITE_PUBLIC_API_URL + "/api/v1/chat/rag";
    // const params = new URLSearchParams();
    // params.append("user_prompt", text);
    // const queryString: string = `?${params}`;
    const response = fetch(API_URL_CHAT_RAG, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt: text
      }),
    })
    return response;
  }

  async function handleSubmit(text?: string) {
    const messageText = text || question;
    setIsLoading(true);

    const traceId = uuidv4();
    setMessages(prev => [...prev, { content: messageText, role: "user", id: traceId }]);
    const response = await searchQuery(messageText);
    setQuestion("");

    if (response && response.body) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      setIsLoading(false);

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        const textPart = decoder.decode(value, { stream: true });

        if (done) break;

        // if (textPart.includes("[END]") || done === true) {
        //   done = true;
        //   continue;
        // }
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          const newContent = lastMessage?.role === "assistant"
            ? lastMessage.content + textPart
            : textPart;

          const newMessage = { content: newContent, role: "assistant", id: traceId };
          return lastMessage?.role === "assistant"
            ? [...prev.slice(0, -1), newMessage]
            : [...prev, newMessage];
        });
      }
    } else {
      console.log("Ran into some error. Response body is undefined!");
    }
  }

  return (
    <div className="flex flex-col min-w-0 h-dvh bg-background">
      <Header />
      <Separator orientation="horizontal"/>
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