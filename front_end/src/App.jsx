import React, { useState } from 'react';
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [responseLog, setResponseLog] = useState("Sẵn sàng...");
  const [file, setFile] = useState(null);
  const [colName, setColName] = useState("");
  
  const [collections, setCollections] = useState([]); 
  const [lpCollections, setLpCollections] = useState([]); 
  const [selectedColStep2, setSelectedColStep2] = useState(null);
  const [selectedColStep3, setSelectedColStep3] = useState(null);
  const [finalSlide, setFinalSlide] = useState(null);

  const logResponse = (data) => {
    setResponseLog(typeof data === 'object' ? JSON.stringify(data, null, 2) : data);
  };

  // --- BƯỚC 1: UPLOAD ---
  const handleConfirmCreate = async () => {
    if (!file || !colName) return alert("Vui lòng nhập tên và chọn file PDF!");
    
    logResponse("Đang khởi tạo dữ liệu...");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("col_name", colName);

    try {
      const res = await axios.post(`${BASE_URL}/api/upload-and-ingest`, formData);
      logResponse(res.data);
      // Lưu thông tin file vào collection để hiển thị
      setCollections([...collections, { id: Date.now(), name: colName, fileName: file.name }]);
      handleCancelStep1();
    } catch (e) {
      logResponse("Lỗi: " + (e.response?.data?.detail || e.message));
    }
  };

  const handleCancelStep1 = () => {
    setFile(null);
    setColName("");
  };

  // --- LOGIC XOÁ FILE TRONG COLLECTION (CẬP NHẬT MỚI) ---
  const handleClearFileFromCollection = (id) => {
    setCollections(prev => prev.map(c => {
      if (c.id === id) {
        // Chỉ xóa tên file gắn với collection đó, giữ lại tên collection
        return { ...c, fileName: null }; 
      }
      return c;
    }));
    // Nếu đang chọn collection này thì bỏ chọn để nút Xuất ẩn đi
    if (selectedColStep2?.id === id) setSelectedColStep2(null);
    logResponse("Đã xóa file khỏi collection. Bạn có thể upload file mới vào collection này ở Bước 1.");
  };

  // Xoá hoàn toàn ở Bước 3 (Giữ nguyên vì đây là xoá kết quả đầu ra)
  const removeLP = (id) => {
    setLpCollections(lpCollections.filter(c => c.id !== id));
    if (selectedColStep3?.id === id) setSelectedColStep3(null);
  };

  // --- BƯỚC 2: SOẠN GIÁO ÁN ---
  const handleExportToLP = async () => {
    if (!selectedColStep2) return;
    logResponse(`Đang soạn giáo án cho: ${selectedColStep2.name}...`);
    
    const formData = new FormData();
    formData.append("col_name", selectedColStep2.name);
    formData.append("unit_title", "FULL LESSON PLAN");

    try {
      const res = await axios.post(`${BASE_URL}/api/generate-lesson-plan`, formData);
      logResponse(res.data);
      setLpCollections([...lpCollections, selectedColStep2]);
      setSelectedColStep2(null);
    } catch (e) {
      logResponse("Lỗi: " + (e.response?.data?.detail || e.message));
    }
  };

  // --- BƯỚC 3: XUẤT SLIDE ---
  const handleExportToSlide = async () => {
    if (!selectedColStep3) return;
    logResponse(`Đang tạo slide cho: ${selectedColStep3.name}...`);
    const formData = new FormData();
    formData.append("col_name", selectedColStep3.name);

    try {
      const res = await axios.post(`${BASE_URL}/api/generate-slides`, formData);
      logResponse(res.data);
      setFinalSlide({
        name: `Slide_${selectedColStep3.name}.pptx`,
        url: `${BASE_URL}/static/${res.data.download_link}`
      });
    } catch (e) {
      logResponse("Lỗi: " + (e.response?.data?.detail || e.message));
    }
  };

  return (
    <div style={containerStyle}>
      <h1 style={{ textAlign: 'center', color: '#1a73e8' }}>🚀 EdTech AI Master System</h1>

      <div style={cardStyle}>
        <h2 style={h2Style}>💻 Terminal / Hệ thống Log</h2>
        <div style={logStyle}>{responseLog}</div>
      </div>

      {/* BƯỚC 1 */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Bước 1: Upload sách lên database</h2>
        <input type="text" placeholder="Đặt tên Collection..." value={colName} onChange={e => setColName(e.target.value)} style={inputStyle} />
        <input type="file" accept=".pdf" onChange={e => setFile(e.target.files[0])} style={inputStyle} />
        <div style={{ marginTop: '10px' }}>
          <button onClick={handleConfirmCreate} style={btnGreen}>Xác nhận tạo</button>
          <button onClick={handleCancelStep1} style={btnCancel}>Huỷ</button>
        </div>
      </div>

      {/* BƯỚC 2: Duyệt Collection & Xoá file */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Bước 2: Tạo Lesson plan</h2>
        <div style={gridContainer}>
          {collections.map(c => (
            <div key={c.id} style={{ position: 'relative' }}>
              <div 
                onClick={() => c.fileName && setSelectedColStep2(selectedColStep2?.id === c.id ? null : c)} 
                style={selectedColStep2?.id === c.id ? itemActive : (c.fileName ? itemStyle : itemEmpty)}
              >
                📚 <strong>{c.name}</strong>
                {c.fileName ? <small style={{marginTop: '5px', color: '#666'}}>{c.fileName}</small> : <small style={{color: 'red'}}>Chưa có file</small>}
              </div>
              {/* Nút X lúc này chỉ xoá file bên trong */}
              {c.fileName && <button onClick={() => handleClearFileFromCollection(c.id)} style={deleteBadge} title="Xoá file trong collection">X</button>}
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
                onClick={() => setSelectedColStep3(selectedColStep3?.id === c.id ? null : c)}
                onDoubleClick={() => window.open(`${BASE_URL}/api/database-preview?col_name=${c.name}`, '_blank')}
                style={selectedColStep3?.id === c.id ? itemActive : itemStyle}
              >
                📝 LP: {c.name} <br/> <small>(Click đúp xem HTML)</small>
              </div>
              <button onClick={() => removeLP(c.id)} style={deleteBadge}>X</button>
            </div>
          ))}
        </div>
        <button disabled={!selectedColStep3} onClick={handleExportToSlide} style={selectedColStep3 ? btnGreen : btnGray}>Xuất ra Slide</button>
      </div>

      {/* BƯỚC 4 */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Bước 4: Slide của bạn</h2>
        {finalSlide ? (
          <div style={fileBox} onDoubleClick={() => window.location.href = finalSlide.url}>
            📊 {finalSlide.name} <br/> <small>(Click đúp để tải file)</small>
          </div>
        ) : <p style={{ textAlign: 'center', color: '#999' }}>Chưa có Slide hoàn chỉnh</p>}
        <div style={{ marginTop: '10px', textAlign: 'center' }}>
          <button disabled={!finalSlide} onClick={() => window.location.href = finalSlide.url} style={finalSlide ? btnGreen : btnGray}>Tải xuống</button>
          <button onClick={() => setFinalSlide(null)} style={{ ...btnCancel, marginLeft: '10px' }}>Làm mới</button>
        </div>
      </div>
    </div>
  );
}

// --- CSS STYLES (Giữ nguyên sự tối ưu)[cite: 5] ---
const containerStyle = { fontFamily: 'Segoe UI, sans-serif', padding: '20px', backgroundColor: '#f0f4f8', maxWidth: '900px', margin: 'auto' };
const cardStyle = { background: 'white', padding: '20px', marginBottom: '20px', borderRadius: '12px', boxShadow: '0 4px 10px rgba(0,0,0,0.05)' };
const h2Style = { marginTop: 0, color: '#333', fontSize: '18px', borderBottom: '2px solid #f0f0f0', paddingBottom: '10px' };
const inputStyle = { width: '100%', padding: '10px', margin: '10px 0', border: '1px solid #ddd', borderRadius: '6px', boxSizing: 'border-box' };
const logStyle = { background: '#1e1e1e', color: '#00ff00', padding: '15px', borderRadius: '8px', fontFamily: 'Consolas, monospace', fontSize: '13px', whiteSpace: 'pre-wrap', maxHeight: '180px', overflowY: 'auto' };
const btnGreen = { background: '#28a745', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' };
const btnGray = { ...btnGreen, background: '#ccc', cursor: 'not-allowed' };
const btnCancel = { ...btnGreen, background: '#dc3545' };
const gridContainer = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '15px', margin: '15px 0' };
const itemStyle = { padding: '20px 10px', border: '1px solid #ddd', borderRadius: '10px', textAlign: 'center', cursor: 'pointer', minHeight: '100px', display: 'flex', flexDirection: 'column', justifyContent: 'center', wordBreak: 'break-word', overflow: 'hidden' };
const itemEmpty = { ...itemStyle, background: '#f9f9f9', border: '1px dashed #ccc', cursor: 'default' };
const itemActive = { ...itemStyle, backgroundColor: '#e6ffed', borderColor: '#28a745', fontWeight: 'bold', color: '#28a745' };
const deleteBadge = { position: 'absolute', top: '-5px', right: '-5px', background: '#ff4d4d', color: 'white', border: 'none', borderRadius: '50%', width: '24px', height: '24px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' };
const fileBox = { padding: '15px', background: '#e7f3ff', border: '1px solid #007bff', borderRadius: '8px', textAlign: 'center', cursor: 'pointer', fontWeight: 'bold', marginBottom: '10px' };

export default App;