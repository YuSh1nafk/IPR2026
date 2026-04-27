import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL;

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // 1. Xử lý Upload & Ingest
  const handleUpload = async () => {
    if (!file) return alert("Vui lòng chọn file PDF!");
    
    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/api/upload-and-ingest`, formData);
      setMessage(res.data.message);
    } catch (err) {
      setMessage("Lỗi upload: " + err.response?.data?.detail || err.message);
    }
    setLoading(false);
  };

  // 2. Xử lý Chạy Lesson Plan / Slide
  const runTask = async (endpoint) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}${endpoint}`);
      setMessage(res.data.message);
    } catch (err) {
      setMessage("Lỗi thực thi: " + err.message);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '40px', fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: 'auto' }}>
      <h1>EdTech AI Master - Dashboard</h1>
      <hr />

      {/* Section 1: Upload */}
      <section style={{ marginBottom: '30px' }}>
        <h3>1. Tải lên sách giáo khoa (PDF)</h3>
        <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files[0])} />
        <button onClick={handleUpload} disabled={loading} style={btnStyle}>
          Tải lên & Phân tích (Ingest)
        </button>
      </section>

      {/* Section 2: View Database */}
      <section style={{ marginBottom: '30px' }}>
        <h3>2. Kiểm tra dữ liệu</h3>
        <a href={`${API_BASE_URL}/api/database-preview`} target="_blank" rel="noreferrer">
          <button style={btnStyleSecondary}>Xem Database Preview (HTML)</button>
        </a>
      </section>

      {/* Section 3: AI Task */}
      <section style={{ marginBottom: '30px' }}>
        <h3>3. Công cụ AI</h3>
        <button onClick={() => runTask('/api/generate-lesson-plan')} disabled={loading} style={btnStyleAction}>
          Soạn Giáo Án (CrewAI)
        </button>
        <button onClick={() => runTask('/api/generate-slides')} disabled={loading} style={btnStyleAction}>
          Tạo Slide PowerPoint
        </button>
      </section>

      {/* Thông báo */}
      {loading && <p style={{ color: 'blue' }}>Đang xử lý, vui lòng đợi...</p>}
      {message && (
        <div style={{ background: '#f0f0f0', padding: '15px', borderRadius: '5px', borderLeft: '5px solid #4CAF50' }}>
          <strong>Thông báo:</strong> {message}
        </div>
      )}
    </div>
  );
}

// CSS cơ bản
const btnStyle = { padding: '10px 20px', backgroundColor: '#4CAF50', color: 'white', border: 'none', cursor: 'pointer', marginRight: '10px' };
const btnStyleSecondary = { padding: '10px 20px', backgroundColor: '#2196F3', color: 'white', border: 'none', cursor: 'pointer' };
const btnStyleAction = { padding: '10px 20px', backgroundColor: '#ff9800', color: 'white', border: 'none', cursor: 'pointer', marginRight: '10px' };

export default App;