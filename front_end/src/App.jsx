import React, { useState } from 'react';
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  // State quản lý log và dữ liệu nhập
  const [responseLog, setResponseLog] = useState("Chưa có dữ liệu...");
  const [colName, setColName] = useState("");
  const [unitTitle, setUnitTitle] = useState("FULL LESSON PLAN");
  const [file, setFile] = useState(null);

  // Hàm ghi log giống logResponse trong file test
  const logResponse = (data) => {
    setResponseLog(typeof data === 'object' ? JSON.stringify(data, null, 2) : data);
  };

  // 1. API Upload & Ingest
  const uploadAndIngest = async () => {
    if (!file || !colName) {
      alert("Vui lòng chọn file PDF và nhập tên Collection!");
      return;
    }

    logResponse("Đang gửi file lên server...");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("col_name", colName);

    try {
      const response = await axios.post(`${BASE_URL}/api/upload-and-ingest`, formData);
      logResponse(response.data);
    } catch (error) {
      logResponse("Lỗi kết nối: " + error.message);
    }
  };

  // 2. API Database Preview
  const previewDatabase = () => {
    if (!colName) {
      alert("Vui lòng nhập tên Collection!");
      return;
    }
    const url = `${BASE_URL}/api/database-preview?col_name=${colName}`;
    window.open(url, '_blank');
  };

  // 3. API Generate Lesson Plan[cite: 4]
  const generateLessonPlan = async () => {
    if (!colName) {
      alert("Vui lòng nhập tên Collection!");
      return;
    }

    logResponse("Đang ra lệnh cho CrewAI soạn giáo án ngầm...");
    const formData = new FormData();
    formData.append("col_name", colName);
    formData.append("unit_title", unitTitle);

    try {
      const response = await axios.post(`${BASE_URL}/api/generate-lesson-plan`, formData);
      logResponse(response.data);
    } catch (error) {
      logResponse("Lỗi kết nối: " + error.message);
    }
  };

  // 4. API Generate Slides[cite: 4]
  const generateSlides = async () => {
    if (!colName) {
      alert("Vui lòng nhập tên Collection!");
      return;
    }

    logResponse("Đang ra lệnh thiết kế Slide ngầm...");
    const formData = new FormData();
    formData.append("col_name", colName);

    try {
      const response = await axios.post(`${BASE_URL}/api/generate-slides`, formData);
      logResponse(response.data);
    } catch (error) {
      logResponse("Lỗi kết nối: " + error.message);
    }
  };

  return (
    <div style={containerStyle}>
      <h1 style={{ textAlign: 'center' }}>🚀 Giao diện EdTech AI Master</h1>

      {/* Terminal / Kết quả trả về[cite: 4] */}
      <div style={cardStyle}>
        <h2 style={h2Style}>💻 Terminal / Kết quả trả về</h2>
        <div style={logStyle}>{responseLog}</div>
      </div>

      {/* 1. Upload Section[cite: 4] */}
      <div style={cardStyle}>
        <h2 style={h2Style}>1. Upload PDF & Đẩy lên Zilliz (/api/upload-and-ingest)</h2>
        <input 
          type="file" 
          accept=".pdf" 
          onChange={(e) => setFile(e.target.files[0])} 
          style={inputStyle} 
        />
        <input 
          type="text" 
          placeholder="Nhập tên Collection (VD: Global_Success_Book_1)" 
          value={colName}
          onChange={(e) => setColName(e.target.value)}
          style={inputStyle} 
        />
        <button onClick={uploadAndIngest} style={btnPrimary}>📤 Upload & Ingest</button>
      </div>

      {/* 2. Database Preview[cite: 4] */}
      <div style={cardStyle}>
        <h2 style={h2Style}>2. Xem dữ liệu Zilliz Database (/api/database-preview)</h2>
        <button onClick={previewDatabase} style={btnGet}>👁️ Mở tab xem Database</button>
      </div>

      {/* 3. Lesson Plan Section[cite: 4] */}
      <div style={cardStyle}>
        <h2 style={h2Style}>3. Soạn Giáo Án CrewAI (/api/generate-lesson-plan)</h2>
        <input 
          type="text" 
          placeholder="Tên Unit (VD: UNIT 1: LEISURE TIME)" 
          value={unitTitle}
          onChange={(e) => setUnitTitle(e.target.value)}
          style={inputStyle} 
        />
        <button onClick={generateLessonPlan} style={btnPrimary}>📝 Bắt đầu soạn giáo án</button>
      </div>

      {/* 4. Generate Slides Section[cite: 4] */}
      <div style={cardStyle}>
        <h2 style={h2Style}>4. Tạo Slide PowerPoint (/api/generate-slides)</h2>
        <button onClick={generateSlides} style={btnPrimary}>📊 Tạo file PPTX</button>
      </div>
    </div>
  );
}

// --- CSS-in-JS bám sát style cũ ---
const containerStyle = { fontFamily: 'Arial, sans-serif', padding: '20px', backgroundColor: '#f4f7f6', maxWidth: '800px', margin: 'auto' };
const cardStyle = { background: 'white', padding: '20px', marginBottom: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' };
const h2Style = { marginTop: 0, color: '#333', fontSize: '18px', borderBottom: '2px solid #eee', paddingBottom: '10px' };
const inputStyle = { width: '100%', padding: '8px', margin: '10px 0', border: '1px solid #ccc', borderRadius: '4px', boxSizing: 'border-box' };
const btnPrimary = { background: '#007bff', color: 'white', border: 'none', padding: '10px 15px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' };
const btnGet = { ...btnPrimary, background: '#28a745' };

// DÒNG ĐÃ SỬA LỖI whiteSpace Ở ĐÂY:
const logStyle = { 
    background: '#333', 
    color: '#0f0', 
    padding: '15px', 
    borderRadius: '4px', 
    fontFamily: 'monospace', 
    whiteSpace: 'pre-wrap', 
    minHeight: '100px', 
    maxHeight: '300px', 
    overflowY: 'auto' 
};
export default App;