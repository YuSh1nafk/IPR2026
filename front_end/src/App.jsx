import React, { useState } from 'react';
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  // --- States quản lý UI & Dữ liệu ---
  const [responseLog, setResponseLog] = useState("Sẵn sàng...");
  const [file, setFile] = useState(null);
  const [colName, setColName] = useState("");
  
  const [collections, setCollections] = useState([]); // Bước 2
  const [selectedColStep2, setSelectedColStep2] = useState(null);
  
  const [lpCollections, setLpCollections] = useState([]); // Bước 3
  const [selectedColStep3, setSelectedColStep3] = useState(null);
  
  const [finalSlide, setFinalSlide] = useState(null); // Bước 4

  const logResponse = (data) => {
    setResponseLog(typeof data === 'object' ? JSON.stringify(data, null, 2) : data);
  };

  // --- BƯỚC 1: Xử lý Upload ---
  const handleConfirmCreate = async () => {
    if (!file || !colName) return alert("Vui lòng nhập tên và chọn file!");
    logResponse("Đang khởi tạo collection...");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("col_name", colName);

    try {
      await axios.post(`${BASE_URL}/api/upload-and-ingest`, formData);
      const newCol = { id: Date.now(), name: colName, fileName: file.name };
      setCollections([...collections, newCol]);
      handleCancelStep1();
      logResponse(`Đã tạo thành công collection: ${colName}`);
    } catch (e) { logResponse("Lỗi: " + e.message); }
  };

  const handleCancelStep1 = () => {
    setFile(null);
    setColName("");
  };

  // --- HÀM XOÁ (Bổ sung mới) ---
  const deleteCollection = (id, step) => {
    if (step === 2) {
      setCollections(collections.filter(c => c.id !== id));
      if (selectedColStep2?.id === id) setSelectedColStep2(null);
      logResponse("Đã xoá collection khỏi danh sách duyệt.");
    } else if (step === 3) {
      setLpCollections(lpCollections.filter(c => c.id !== id));
      if (selectedColStep3?.id === id) setSelectedColStep3(null);
      logResponse("Đã xoá Lesson Plan khỏi danh sách.");
    }
  };

  // --- BƯỚC 2: Tạo Lesson Plan ---
  const handleExportToLP = async () => {
    logResponse("Đang chạy CrewAI soạn giáo án...");
    try {
      const formData = new FormData();
      formData.append("col_name", selectedColStep2.name);
      formData.append("unit_title", "FULL LESSON PLAN");
      await axios.post(`${BASE_URL}/api/generate-lesson-plan`, formData);
      
      setLpCollections([...lpCollections, selectedColStep2]);
      setSelectedColStep2(null);
      logResponse("Đã tạo xong Lesson Plan!");
    } catch (e) { logResponse("Lỗi LP: " + e.message); }
  };

  // --- BƯỚC 3: Xuất Slide ---
  const handleExportToSlide = async () => {
    logResponse("Đang thiết kế Slide...");
    try {
      const formData = new FormData();
      formData.append("col_name", selectedColStep3.name);
      await axios.post(`${BASE_URL}/api/generate-slides`, formData);
      setFinalSlide({ name: `Slide_${selectedColStep3.name}.pptx`, url: `${BASE_URL}/static/outputs/presentation.pptx` });
      logResponse("Đã tạo xong Slide!");
    } catch (e) { logResponse("Lỗi Slide: " + e.message); }
  };

  return (
    <div style={containerStyle}>
      <h1 style={{ textAlign: 'center', color: '#333' }}>🎓 EdTech AI Master</h1>

      <div style={cardStyle}>
        <h2 style={h2Style}>💻 Terminal System Log</h2>
        <div style={logStyle}>{responseLog}</div>
      </div>

      {/* BƯỚC 1 */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Bước 1: Upload sách lên database</h2>
        <input type="text" placeholder="Đặt tên Collection..." value={colName} onChange={(e) => setColName(e.target.value)} style={inputStyle} />
        <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} style={inputStyle} />
        {file && <div style={fileBox} onDoubleClick={() => window.open(URL.createObjectURL(file), '_blank')}>📄 {file.name} (Click đúp để xem)</div>}
        <div style={{ marginTop: '10px' }}>
          <button onClick={handleConfirmCreate} style={btnGreen}>Xác nhận tạo</button>
          <button onClick={handleCancelStep1} style={btnCancel}>Huỷ</button>
        </div>
      </div>

      {/* BƯỚC 2 */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Bước 2: Tạo Lesson plan</h2>
        <div style={gridContainer}>
          {collections.map(c => (
            <div key={c.id} style={{ position: 'relative' }}>
              <div onClick={() => setSelectedColStep2(selectedColStep2?.id === c.id ? null : c)} style={selectedColStep2?.id === c.id ? itemActive : itemStyle}>
                📚 {c.name}
              </div>
              <button onClick={() => deleteCollection(c.id, 2)} style={deleteBadge}>X</button>
            </div>
          ))}
        </div>
        <button disabled={!selectedColStep2} onClick={handleExportToLP} style={selectedColStep2 ? btnGreen : btnGray}>Xuất ra Lesson Plan</button>
      </div>

      {/* BƯỚC 3 */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Bước 3: Tạo Slide</h2>
        <div style={gridContainer}>
          {lpCollections.map(c => (
            <div key={c.id} style={{ position: 'relative' }}>
              <div 
                onClick={() => setSelectedColStep3(c)}
                onDoubleClick={() => window.open(`${BASE_URL}/api/database-preview?col_name=${c.name}`, '_blank')}
                style={selectedColStep3?.id === c.id ? itemActive : itemStyle}
              >
                📝 LP: {c.name}<br/><small>(Double click xem HTML)</small>
              </div>
              <button onClick={() => deleteCollection(c.id, 3)} style={deleteBadge}>X</button>
            </div>
          ))}
        </div>
        <button disabled={!selectedColStep3} onClick={handleExportToSlide} style={selectedColStep3 ? btnGreen : btnGray}>Xuất ra Slide</button>
      </div>

      {/* BƯỚC 4 */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Bước 4: Slide của bạn</h2>
        {finalSlide && <div style={fileBox} onDoubleClick={() => window.location.href = finalSlide.url}>📊 {finalSlide.name} (Click đúp tải về)</div>}
        <div style={{ marginTop: '10px' }}>
          <button disabled={!finalSlide} onClick={() => window.location.href = finalSlide.url} style={finalSlide ? btnGreen : btnGray}>Tải xuống</button>
          <button onClick={() => setFinalSlide(null)} style={{ ...btnCancel, marginLeft: '10px' }}>Làm mới</button>
        </div>
      </div>
    </div>
  );
}

// --- CSS-IN-JS (Đã sửa lỗi tràn chữ & căn giữa) ---
const containerStyle = { fontFamily: 'Arial, sans-serif', padding: '20px', backgroundColor: '#f4f7f6', maxWidth: '900px', margin: 'auto' };
const cardStyle = { background: 'white', padding: '20px', marginBottom: '20px', borderRadius: '10px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' };
const h2Style = { marginTop: 0, paddingBottom: '10px', borderBottom: '2px solid #eee', fontSize: '18px', color: '#444' };
const inputStyle = { width: '100%', padding: '10px', margin: '8px 0', border: '1px solid #ddd', borderRadius: '5px', boxSizing: 'border-box' };
const logStyle = { background: '#2d2d2d', color: '#4af626', padding: '15px', borderRadius: '5px', fontFamily: 'monospace', whiteSpace: 'pre-wrap', maxHeight: '150px', overflowY: 'auto' };
const fileBox = { padding: '15px', background: '#eef', border: '1px dashed #77a', borderRadius: '5px', cursor: 'pointer', marginTop: '10px', textAlign: 'center' };

const gridContainer = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '15px', margin: '15px 0' };
const itemStyle = { 
  padding: '20px 10px', 
  border: '1px solid #ddd', 
  borderRadius: '8px', 
  cursor: 'pointer', 
  textAlign: 'center', 
  display: 'flex', 
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '80px',
  wordBreak: 'break-word', // Chống tràn chữ
  overflow: 'hidden',
  transition: '0.2s' 
};
const itemActive = { ...itemStyle, backgroundColor: '#d4edda', borderColor: '#28a745', fontWeight: 'bold' };

const btnGreen = { background: '#28a745', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold' };
const btnGray = { ...btnGreen, background: '#ccc', cursor: 'not-allowed' };
const btnCancel = { ...btnGreen, background: '#dc3545' };
const deleteBadge = { position: 'absolute', top: '-5px', right: '-5px', background: '#ff4d4d', color: 'white', border: 'none', borderRadius: '50%', width: '22px', height: '22px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold', zIndex: 10 };

export default App;