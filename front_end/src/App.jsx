import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [responseLog, setResponseLog] = useState("Hệ thống đã sẵn sàng...");
  
  const [file, setFile] = useState(null);
  const [colName, setColName] = useState("");
  const [dbCollections, setDbCollections] = useState([]); 
  
  const [selectedColStep2, setSelectedColStep2] = useState(null);
  const [exportedDump, setExportedDump] = useState(null); 
  
  const [selectedColStep3, setSelectedColStep3] = useState(null);
  const [isGeneratingLP, setIsGeneratingLP] = useState(false); // Trạng thái chờ tạo LP
  const [activeLessonPlan, setActiveLessonPlan] = useState(null); 
  
  const [isGeneratingSlide, setIsGeneratingSlide] = useState(false); // Trạng thái chờ tạo Slide
  const [finalSlide, setFinalSlide] = useState(null);

  const logResponse = (msg) => {
    setResponseLog(typeof msg === 'object' ? JSON.stringify(msg, null, 2) : msg);
  };

  const fetchCollections = async () => {
    try {
      const res = await axios.get(`${BASE_URL}/api/list-collections`);
      if (res.data.collections) setDbCollections(res.data.collections);
    } catch (e) {
      logResponse("Lỗi tải danh sách Database. Hãy kiểm tra Backend.");
    }
  };

  useEffect(() => { fetchCollections(); }, []);

  // --- BƯỚC 1: UPLOAD ---
  const handleUpload = async () => {
    if (!file || !colName) return alert("Vui lòng nhập tên Collection và chọn file!");
    logResponse(`[BƯỚC 1] Đang nạp sách vào: ${colName}...`);
    const formData = new FormData();
    formData.append("file", file); formData.append("col_name", colName);
    try {
      await axios.post(`${BASE_URL}/api/upload-and-ingest`, formData);
      logResponse(`[BƯỚC 1] THÀNH CÔNG! Đã khởi tạo ${colName}.`);
      fetchCollections(); setFile(null); setColName("");
    } catch (e) {
      logResponse(`[BƯỚC 1] LỖI: ${e.response?.data?.detail || e.message}`);
    }
  };

  // --- BƯỚC 2: EXPORT DUMP ---
  const handleExportDump = () => {
    if (!selectedColStep2) return;
    logResponse(`[BƯỚC 2] Đã xuất Database Dump cho: ${selectedColStep2}`);
    setExportedDump({
      fileName: `database_dump_${selectedColStep2}.html`,
      url: `${BASE_URL}/api/database-preview?col_name=${selectedColStep2}`
    });
  };

  // --- BƯỚC 3: TẠO LESSON PLAN (CHẠY NGẦM) ---
  const handleGenerateLP = async () => {
    if (!selectedColStep3) return;
    setActiveLessonPlan(null); setFinalSlide(null);
    setIsGeneratingLP(true); 
    
    logResponse(`[BƯỚC 3] CrewAI BẮT ĐẦU soạn giáo án cho: ${selectedColStep3}. Quá trình sẽ diễn ra ngầm (3-5 phút)...`);
    const formData = new FormData();
    formData.append("col_name", selectedColStep3);
    formData.append("unit_title", "FULL LESSON PLAN");

    try {
      await axios.post(`${BASE_URL}/api/generate-lesson-plan`, formData);
      logResponse(`[BƯỚC 3] Lệnh đã gửi! Hãy đợi vài phút rồi ấn "Kiểm tra trạng thái file".`);
    } catch (e) {
      setIsGeneratingLP(false);
      logResponse(`[BƯỚC 3] LỖI: ${e.response?.data?.detail || e.message}`);
    }
  };

  // --- KIỂM TRA FILE LESSON PLAN XONG CHƯA ---
  const checkLessonPlanReady = async () => {
    const fileName = `${selectedColStep3}_LessonPlan.html`;
    try {
      const res = await axios.get(`${BASE_URL}/api/check-file?filename=${fileName}`);
      if (res.data.status === "ready") {
        setActiveLessonPlan({
          colName: selectedColStep3,
          fileName: fileName,
          url: `${BASE_URL}/static/${fileName}`
        });
        setIsGeneratingLP(false);
        logResponse("[BƯỚC 3] FILE GIÁO ÁN ĐÃ ĐƯỢC TẠO THÀNH CÔNG!");
      } else {
        logResponse("[BƯỚC 3] CrewAI vẫn đang viết giáo án. Vui lòng đợi thêm một lát nhé!");
      }
    } catch (e) {
      logResponse("Lỗi kiểm tra file.");
    }
  };

  // --- BƯỚC 4: TẠO SLIDE (CHẠY NGẦM) ---
  const handleExportSlide = async () => {
    if (!activeLessonPlan) return;
    setIsGeneratingSlide(true);
    logResponse(`[BƯỚC 4] Đang thiết kế Slide cho: ${activeLessonPlan.colName}...`);
    
    const formData = new FormData();
    formData.append("col_name", activeLessonPlan.colName);
    try {
      await axios.post(`${BASE_URL}/api/generate-slides`, formData);
      logResponse(`[BƯỚC 4] Lệnh tạo Slide đã gửi. Đang xử lý...`);
    } catch (e) {
      setIsGeneratingSlide(false);
      logResponse(`[BƯỚC 4] LỖI: ${e.response?.data?.detail || e.message}`);
    }
  };

  // --- KIỂM TRA FILE SLIDE XONG CHƯA ---
  const checkSlideReady = async () => {
    const fileName = `${activeLessonPlan.colName}_Presentation.pptx`;
    try {
      const res = await axios.get(`${BASE_URL}/api/check-file?filename=${fileName}`);
      if (res.data.status === "ready") {
        setFinalSlide({
          name: fileName,
          url: `${BASE_URL}/static/${fileName}`
        });
        setIsGeneratingSlide(false);
        logResponse("[BƯỚC 4] SLIDE ĐÃ HOÀN THIỆN!");
      } else {
        logResponse("[BƯỚC 4] Vẫn đang gen Slide. Chờ chút nữa bạn nhé!");
      }
    } catch (e) {
      logResponse("Lỗi kiểm tra Slide.");
    }
  };

  return (
    <div style={containerStyle}>
      <h1 style={{ textAlign: 'center', color: '#1a73e8' }}>🚀 EdTech AI Master System</h1>

      <div style={cardStyle}>
        <h2 style={h2Style}>💻 Terminal System Log</h2>
        <div style={logStyle}>{responseLog}</div>
      </div>

      {/* BƯỚC 1: UPLOAD */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Bước 1: Upload sách lên Database Zilliz</h2>
        <input type="text" placeholder="Nhập tên Collection mới (VD: Book_Level_1)" value={colName} onChange={e => setColName(e.target.value)} style={inputStyle} />
        <input type="file" accept=".pdf" onChange={e => setFile(e.target.files[0])} style={inputStyle} />
        <button onClick={handleUpload} style={btnPrimary}>📤 Xác nhận Upload</button>
      </div>

      {/* BƯỚC 2: EXPORT DATABASE */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Bước 2: Hiển thị Database Zilliz (Export Dump)</h2>
        <div style={gridContainer}>
          {dbCollections.map(col => (
            <div 
              key={`step2-${col}`} 
              onClick={() => { setSelectedColStep2(col === selectedColStep2 ? null : col); setExportedDump(null); }}
              style={selectedColStep2 === col ? itemActive : itemStyle}
            >
              🗄️ <strong>{col}</strong>
            </div>
          ))}
        </div>
        <button disabled={!selectedColStep2} onClick={handleExportDump} style={selectedColStep2 ? btnPrimary : btnDisabled}>
          Xác nhận Export Database Dump
        </button>

        {exportedDump && (
          <div style={resultArea}>
            <div style={fileBox} onDoubleClick={() => window.open(exportedDump.url, '_blank')}>
              📄 <strong>{exportedDump.fileName}</strong> <br/>
              <span style={{ fontSize: '12px', color: '#555' }}>(Double click để mở tab Preview)</span>
            </div>
          </div>
        )}
      </div>

      {/* BƯỚC 3: TẠO LESSON PLAN */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Bước 3: Tạo Lesson Plan từ Database</h2>
        <div style={gridContainer}>
          {dbCollections.map(col => (
            <div 
              key={`step3-${col}`} 
              onClick={() => setSelectedColStep3(col === selectedColStep3 ? null : col)}
              style={selectedColStep3 === col ? itemActive : itemStyle}
            >
              📚 <strong>{col}</strong>
            </div>
          ))}
        </div>
        
        <button disabled={!selectedColStep3 || isGeneratingLP} onClick={handleGenerateLP} style={selectedColStep3 && !isGeneratingLP ? btnPrimary : btnDisabled}>
          {isGeneratingLP ? "⏳ AI đang phân tích..." : "Tạo Lesson Plan"}
        </button>

        {/* UI Chờ tạo Lesson Plan */}
        {isGeneratingLP && (
          <div style={resultArea}>
            <h3 style={{ color: '#e67e22', marginTop: 0 }}>⏳ CrewAI đang cặm cụi viết giáo án...</h3>
            <p style={{fontSize: '13px', color: '#555'}}>Quá trình này cần <strong>3-5 phút</strong> để hoàn thành ở local. Thỉnh thoảng hãy ấn nút bên dưới để xem file đã lưu thành công chưa nhé.</p>
            <button onClick={checkLessonPlanReady} style={btnCheck}>🔄 Kiểm tra xem file đã tạo xong chưa?</button>
          </div>
        )}

        {/* UI Kết quả Lesson Plan */}
        {activeLessonPlan && !isGeneratingLP && (
          <div style={resultArea}>
            <h3 style={{ marginTop: '0', color: '#333' }}>📝 Kết quả: Giáo án điện tử</h3>
            <div style={fileBox} onClick={() => window.open(activeLessonPlan.url, '_blank')}>
              📄 <strong>{activeLessonPlan.fileName}</strong> <br/>
              <span style={{ fontSize: '12px', color: '#555' }}>(Click để xem bản Preview trên tab mới)</span>
            </div>
            <div style={{ marginTop: '15px', textAlign: 'center' }}>
              <button disabled={isGeneratingSlide} onClick={handleExportSlide} style={btnSuccess}>
                 📊 Export file Lesson Plan này sang Slide
              </button>
            </div>
          </div>
        )}
      </div>

      {/* BƯỚC 4: KẾT QUẢ SLIDE */}
      <div style={cardStyle}>
        <h2 style={h2Style}>Bước 4: Tải xuống Slide hoàn chỉnh</h2>
        
        {isGeneratingSlide && (
          <div style={resultArea}>
             <h3 style={{ color: '#e67e22', marginTop: 0 }}>⏳ Đang thiết kế Slide...</h3>
             <button onClick={checkSlideReady} style={btnCheck}>🔄 Kiểm tra xem Slide đã xuất xong chưa?</button>
          </div>
        )}

        {finalSlide && !isGeneratingSlide ? (
          <>
            <div style={fileBox} onClick={() => window.open(finalSlide.url, '_blank')} onDoubleClick={() => window.location.href = finalSlide.url}>
              📊 <strong>{finalSlide.name}</strong> <br/>
              <span style={{ fontSize: '12px', color: '#555' }}>(Click 1 lần để xem, Double click để tải về)</span>
            </div>
            <div style={{ textAlign: 'center', marginTop: '15px' }}>
              <button onClick={() => window.location.href = finalSlide.url} style={btnPrimary}>⬇️ Tải xuống (Download)</button>
            </div>
          </>
        ) : (
          !isGeneratingSlide && <p style={{ textAlign: 'center', color: '#999', padding: '20px 0' }}>Chưa có Slide nào được tạo.</p>
        )}
      </div>
    </div>
  );
}

// --- CSS STYLES ---
const containerStyle = { fontFamily: 'Segoe UI, sans-serif', padding: '20px', backgroundColor: '#f4f6f9', maxWidth: '900px', margin: 'auto' };
const cardStyle = { background: 'white', padding: '25px', marginBottom: '25px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.06)' };
const h2Style = { marginTop: 0, color: '#2c3e50', fontSize: '18px', borderBottom: '2px solid #eee', paddingBottom: '12px', marginBottom: '15px' };
const inputStyle = { width: '100%', padding: '12px', margin: '8px 0 15px', border: '1px solid #ced4da', borderRadius: '6px', boxSizing: 'border-box' };
const logStyle = { background: '#1e1e1e', color: '#4caf50', padding: '15px', borderRadius: '8px', fontFamily: 'Consolas, monospace', fontSize: '13px', whiteSpace: 'pre-wrap', maxHeight: '180px', overflowY: 'auto' };
const btnPrimary = { background: '#007bff', color: 'white', border: 'none', padding: '12px 20px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' };
const btnSuccess = { ...btnPrimary, background: '#28a745' };
const btnCheck = { ...btnPrimary, background: '#e67e22', display: 'block', margin: '10px auto' };
const btnDisabled = { ...btnPrimary, background: '#e9ecef', color: '#6c757d', cursor: 'not-allowed' };
const gridContainer = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '15px', marginBottom: '15px' };
const itemStyle = { padding: '20px 10px', border: '1px solid #dee2e6', borderRadius: '8px', textAlign: 'center', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8f9fa' };
const itemActive = { ...itemStyle, background: '#e7f1ff', borderColor: '#0d6efd', color: '#0d6efd', fontWeight: 'bold' };
const resultArea = { marginTop: '20px', padding: '20px', background: '#fff9e6', borderRadius: '8px', border: '1px solid #ffeeba' };
const fileBox = { padding: '20px', background: '#e0f7fa', border: '2px dashed #00bcd4', borderRadius: '8px', textAlign: 'center', cursor: 'pointer' };

export default App;