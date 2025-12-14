import { useEffect, useRef } from 'react';
import { Message } from '@/hooks/useChat';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageCircle } from 'lucide-react';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
}

const ChatWindow = ({ messages, isLoading }: ChatWindowProps) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
          <MessageCircle className="h-10 w-10 text-primary" />
        </div>
        <div className="text-center">
          <h3 className="text-xl font-semibold text-foreground">Welcome to LoanBuddy!</h3>
          <p className="mt-2 max-w-md text-muted-foreground">
            I'm your personal loan assistant. Ask me about loan offers, eligibility, or upload your salary slip to get started.
          </p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1">
      <div className="flex flex-col">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
};

export default ChatWindow;
