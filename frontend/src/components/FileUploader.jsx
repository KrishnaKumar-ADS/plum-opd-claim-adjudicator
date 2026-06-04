import { useRef, useState } from 'react';

export default function FileUploader({ onFilesChange }) {
  const [files, setFiles] = useState([]);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const handleFiles = (newFiles) => {
    const fileList = [...files, ...Array.from(newFiles)];
    setFiles(fileList);
    onFilesChange?.(fileList);
  };

  const removeFile = (index) => {
    const updated = files.filter((_, i) => i !== index);
    setFiles(updated);
    onFilesChange?.(updated);
  };

  return (
    <div>
      <div
        className={`file-upload-zone ${dragging ? 'dragging' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
      >
        <div className="file-upload-icon">📄</div>
        <div className="file-upload-text">Drop files here or click to browse</div>
        <div className="file-upload-hint">Supports PDF, JPG, PNG • Max 10MB per file</div>
        <input
          ref={inputRef} type="file" multiple hidden
          accept=".pdf,.jpg,.jpeg,.png,.webp"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <div className="file-list">
          {files.map((f, i) => (
            <div key={i} className="file-item">
              <span>📎 {f.name} ({(f.size / 1024).toFixed(1)} KB)</span>
              <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={() => removeFile(i)}>✕</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
