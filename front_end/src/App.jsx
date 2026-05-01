import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  // State quản lý dữ liệu nhập vào
  const [file, setFile] = useState(null);
  const [collectionName, setCollectionName] = useState('');
  const [unitTitle, setUnitTitle] = useState('FULL LESSON PLAN');
  
  // State quản lý trạng thái giao diện
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // 1. API: Upload & Ingest (Cần file và col_name)
  const handleUploadAndIngest = async () => {
    if (!file || !collectionName) {
      return alert("Vui lòng chọn file PDF và nhập tên Collection!");
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('col_name', collectionName);

    setLoading(true);
    setMessage('Đang gửi yêu cầu...');
    try {
      const res = await axios.post(`${API_BASE_URL}/api/upload-and-ingest`, formData);
      setMessage(res.data.message);
    } catch (err) {
      setMessage("Lỗi: " + (err.response?.data?.detail || err.message));
    }
    setLoading(false);
  };

  // 2. API: Soạn giáo án (Cần col_name và unit_title)
  const handleGenerateLessonPlan = async () => {
    if (!collectionName) return alert("Vui lòng nhập tên Collection!");

    const formData = new FormData();
    formData.append('col_name', collectionName);
    formData.append('unit_title', unitTitle);

    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/api/generate-lesson-plan`, formData);
      setMessage(res.data.message);
    } catch (err) {
      setMessage("Lỗi: " + (err.response?.data?.detail || err.message));
    }
    setLoading(false);
  };

  // 3. API: Tạo Slide (Cần col_name)
  const handleGenerateSlides = async () => {
    if (!collectionName) return alert("Vui lòng nhập tên Collection!");

    const formData = new FormData();
    formData.append('col_name', collectionName);

    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/api/generate-slides`, formData);
      setMessage(res.data.message);
    } catch (err) {
      setMessage("Lỗi: " + (err.response?.data?.detail || err.message));
    }
    setLoading(false);
  };

  return (
    <div className="container" style={containerStyle}>
      <h1 style={{ color: '#2c3e50' }}>EdTech AI Master Dashboard</h1>
      <p style={{ color: '#7f8c8d' }}>Hệ thống hỗ trợ soạn bài và thiết kế bài giảng AI</p>
      <hr />

      {/* Bước 1: Cấu hình Collection */}
      <section style={sectionStyle}>
        <h3>Bước 1: Cấu hình Tài liệu</h3>
        <div style={inputGroup}>
          <label>Tên Collection (Ví dụ: Toan_Lop_10):</label>
          <input 
            type="text" 
            value={collectionName} 
            onChange={(e) => setCollectionName(e.target.value)} 
            placeholder="Nhập tên không dấu, không khoảng cách..."
            style={inputStyle}
          />
        </div>
      </section>

      {/* Bước 2: Upload File */}
      <section style={sectionStyle}>
        <h3>Bước 2: Tải lên & Ingest</h3>
        <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} style={{marginBottom: '10px'}} />
        <br />
        <button onClick={handleUploadAndIngest} disabled={loading} style={btnGreen}>
          Bắt đầu Phân tích (Ingest)
        </button>
      </section>

      {/* Bước 3: Công cụ AI */}
      <section style={sectionStyle}>
        <h3>Bước 3: Công cụ AI Master</h3>
        <div style={inputGroup}>
          <label>Tiêu đề bài học (Unit Title):</label>
          <input 
            type="text" 
            value={unitTitle} 
            onChange={(e) => setUnitTitle(e.target.value)} 
            style={inputStyle}
          />
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={handleGenerateLessonPlan} disabled={loading} style={btnOrange}>Soạn Giáo Án (CrewAI)</button>
          <button onClick={handleGenerateSlides} disabled={loading} style={btnPurple}>Thiết kế Slide PPTX</button>
          <button 
            onClick={() => window.open(`${API_BASE_URL}/api/database-preview?col_name=${collectionName}`, '_blank')}
            style={btnBlue}
          >
            Xem Database Preview
          </button>
        </div>
      </section>

      {/* Hiển thị thông báo */}
      {loading && <div style={{ color: '#2980b9', fontWeight: 'bold' }}>Hệ thống đang xử lý...</div>}
      {message && (
        <div style={messageBox}>
          <strong>Kết quả:</strong> {message}
        </div>
      )}
    </div>
  );
}

// --- Styles (Inline CSS để bạn chạy được ngay) ---
const containerStyle = { maxWidth: '900px', margin: '40px auto', padding: '20px', backgroundColor: '#f9f9f9', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' };
const sectionStyle = { backgroundColor: '#fff', padding: '20px', borderRadius: '8px', marginBottom: '20px', border: '1px solid #eee' };
const inputGroup = { marginBottom: '15px', display: 'flex', flexDirection: 'column', gap: '5px' };
const inputStyle = { padding: '10px', borderRadius: '5px', border: '1px solid #ccc', fontSize: '16px' };
const messageBox = { marginTop: '20px', padding: '15px', backgroundColor: '#e8f6ef', borderLeft: '5px solid #2ecc71', borderRadius: '4px' };

// Buttons
const baseBtn = { padding: '12px 20px', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' };
const btnGreen = { ...baseBtn, backgroundColor: '#27ae60' };
const btnBlue = { ...baseBtn, backgroundColor: '#2980b9' };
const btnOrange = { ...baseBtn, backgroundColor: '#e67e22' };
const btnPurple = { ...baseBtn, backgroundColor: '#8e44ad' };

export default App;