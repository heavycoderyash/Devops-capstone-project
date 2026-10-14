import { useEffect } from 'react';

export default function Toast({ message, tone, onDone }) {
  useEffect(() => {
    const timer = setTimeout(onDone, 3500);
    return () => clearTimeout(timer);
  }, [onDone]);

  return (
    <div className={`toast ${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      {tone === 'error' ? '⚠ ' : '✓ '}
      {message}
    </div>
  );
}
