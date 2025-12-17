const TypingIndicator = () => {
  return (
    <div className="flex w-full justify-start px-4 py-2">
      <div className="flex items-center gap-1 rounded-2xl border border-border bg-card px-4 py-3">
        <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
        <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
        <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground" />
      </div>
    </div>
  );
};

export default TypingIndicator;
