interface LoadingStateProps {
  message?: string;
  subMessage?: string;
}

export function LoadingState({
  message = 'Analyzing clinical trials...',
  subMessage = 'This may take a moment'
}: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className="flex space-x-2">
        <div className="w-3 h-3 bg-primary-blue rounded-full animate-pulse" />
        <div className="w-3 h-3 bg-primary-blue rounded-full animate-pulse" style={{ animationDelay: '0.1s' }} />
        <div className="w-3 h-3 bg-primary-blue rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
      </div>
      <p className="mt-4 text-gray-600">{message}</p>
      {subMessage && <p className="text-sm text-gray-400 mt-1">{subMessage}</p>}
    </div>
  );
}
