import { useEffect } from 'react';

export default function Modal({ eyebrow, title, onClose, onSubmit, children }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <form
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(Object.fromEntries(new FormData(e.currentTarget)));
        }}
      >
        <div className="modal-head">
          <div>
            <p className="eyebrow">{eyebrow}</p>
            <h2 id="modal-title">{title}</h2>
          </div>
          <button type="button" className="close" onClick={onClose} aria-label="Close">×</button>
        </div>
        {children}
      </form>
    </div>
  );
}
