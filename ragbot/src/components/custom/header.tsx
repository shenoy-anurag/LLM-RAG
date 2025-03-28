import { InfoIcon } from "lucide-react";
import { ThemeToggle } from "./theme-toggle";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const technologies = [
  {
    technology: "LLM",
    tool: "OpenAI's GPT",
    version: "4o-mini",
  },
  {
    technology: "Vector DB",
    tool: "Qdrant",
    version: "v1.13.4",
  },
  {
    technology: "LLM Framework",
    tool: "LangChain",
    version: "latest",
  },
  {
    technology: "Frontend Framework",
    tool: "React",
    version: "latest",
  },
]

function TableTechStack() {
  return (
    <Table>
      <TableCaption>Tech Stack</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Technology</TableHead>
          <TableHead>Tool</TableHead>
          <TableHead className="text-right">Model / Version</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {technologies.map((technology) => (
          <TableRow key={technology.technology}>
            <TableCell className="font-medium">{technology.technology}</TableCell>
            <TableCell>{technology.tool}</TableCell>
            <TableCell className="text-right">{technology.version}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}


export const Header = () => {
  return (
    <>
      <header className="flex items-center justify-between px-2 sm:px-4 py-2 bg-background text-black dark:text-white w-full">
        <div className="flex items-center space-x-1 sm:space-x-2">
          Medical FAQ Bot
        </div>
        <div className="flex items-center space-x-1 sm:space-x-2">

          <Dialog>
            <DialogTrigger>
              <Button
                variant="outline"
                className="bg-background border border-gray text-gray-600 hover:white dark:text-gray-200 h-10"
                onClick={() => { }}
              >
                <InfoIcon />
                <span className="sr-only">Information / Help</span>
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader className="flex flex-col gap-4">
                <DialogTitle>About</DialogTitle>
                <DialogDescription className="flex flex-col gap-4">
                  <p>
                    A Chatbot utilizing the <strong>MedQuAD</strong> Dataset to provide accurate medical information using awesome technologies such as Retrieval Augmented Generation (RAG) and Large Language Models (LLMs).
                  </p>
                  <p>
                    <strong>Note: </strong>The Generated text does not stream due to restrictions of AWS Lambda, and the way it is setup right now.
                    <br />
                    <br />
                    I'm working to switch to Websockets for the communication instead of streaming REST APIs,
                    so that I can use AWS API Gateway's Websocket API to stream the outputs.
                  </p>
                  <p>For now, you'll have to be a bit patient, and give it a couple of seconds to search, retrieve and generate the answer.</p>
                  <p>Thanks for understanding.</p>
                  <p>Hope you enjoy using this chatbot!</p>
                  <TableTechStack />
                </DialogDescription>
              </DialogHeader>
            </DialogContent>
          </Dialog>

          <ThemeToggle />
        </div>
      </header>
    </>
  );
};