import React from 'react';
import './sidebar.css';

interface SidebarProps {
  chats: any[];
  activeChatId: string | null;
  setActiveChatId: (id: string | null) => void;
  setChats: React.Dispatch<React.SetStateAction<any[]>>;
}

export default function Sidebar({ chats, activeChatId, setActiveChatId, setChats }: SidebarProps) {
  
  // Chatni o'chirish funksiyasi
  const handleDeleteChat = (id: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Chat ochilib ketmasligi uchun
    setChats(prev => prev.filter(chat => chat.id !== id));
    if (activeChatId === id) {
      setActiveChatId(null);
    }
  };

  return (
    <div className="sidebar-container">
      <button className="new-chat-btn" onClick={() => setActiveChatId(null)}>
        + Yangi suhbat
      </button>

      <div className="old-searches">
        <p className="sidebar-title">Oldingi qidiruvlar</p>
        
        {chats.length === 0 ? (
          <p style={{ color: '#888', fontSize: '14px', paddingLeft: '10px' }}>
            Hozircha qidiruvlar yo'q
          </p>
        ) : (
          chats.map((chat) => (
            <div 
              key={chat.id} 
              className={`sidebar-item ${chat.id === activeChatId ? 'active' : ''}`}
              onClick={() => setActiveChatId(chat.id)} // Faqat chatni tanlaydi, qayta qidirmaydi!
            >
              <div className="chat-title-wrapper">
                <span className="chat-icon">💬</span>
                <span className="chat-text">{chat.title}</span>
              </div>
              <span 
                className="delete-chat-btn" 
                onClick={(e) => handleDeleteChat(chat.id, e)}
              >
                ×
              </span>
            </div>
          ))
        )}
      </div>

      {/* Sizning profilingiz qismi (Tohir Maxsudbekov) pastda turaveradi */}
      <div className="sidebar-footer">
        {/* Profil ma'lumotlari kodi shu yerda bo'ladi */}
      </div>
    </div>
  );
}