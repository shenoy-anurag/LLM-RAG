import { motion } from 'framer-motion';
import { MessageCircle, BotIcon } from 'lucide-react';

export const Overview = () => {
  return (
    <>
    <motion.div
      key="overview"
      className="max-w-3xl mx-auto md:mt-20"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ delay: 0.75 }}
    >
      <div className="rounded-xl p-6 flex flex-col gap-8 leading-relaxed text-center max-w-xl">
        <p className="flex flex-row justify-center gap-4 items-center">
          <BotIcon size={44}/>
          <span>+</span>
          <MessageCircle size={44}/>
        </p>
        <p>
          Welcome to my RAG chatbot!<br/>
          Ask any health and medical related questions, <br/> 
          and it'll answer them for you.
        </p>
        <p>
          Made possible by the magic of Vector Databases (<strong>Qdrant</strong>),<br/>
          LLMs like OpenAI's <strong>4o-mini</strong>, <br/>
          and <strong>LangChain</strong> to perform/manage the retrieval,  <br/>
          augmentation (Prompt Engineering) and generation.
        </p>
      </div>
    </motion.div>
    </>
  );
};
