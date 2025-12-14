const TypingIndicator = () => {
  return (
    <div className="flex items-center gap-3 p-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary">
        <span className="text-sm font-semibold text-primary-foreground">AI</span>
      </div>
      <div className="flex items-center gap-1 rounded-2xl bg-card px-4 py-3 shadow-sm">
        <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
        <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
        <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground" />
      </div>
    </div>
  );
};

export default TypingIndicator;
