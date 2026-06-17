import { getJobsFromBackend } from './utils/api';
import { getAIJobResponse } from './utils/ai';
import { useState, useEffect, useRef, type MouseEvent, type KeyboardEvent } from 'react';

import Login from './components/login';
import "./app.css";
import type { Job, Message, ConversationState } from './data';
import { intentPatterns } from './data';

// Chat ob'ekti uchun TypeScript interfeysi
interface Chat {
  id: string;
  title: string;
  messages: Message[];
}

const theme = {
  background: '#1E223D',
  surface: '#242a4b',
  surfaceAlt: '#2c304f',
  border: '#2b3155',
  accent: '#F54F1B',
  accentHover: '#d24416',
  danger: '#EF5F3D',
  text: '#F5F7FF',
  muted: '#95A0C1',
  icon: '#8C98BB',
  overlay: 'rgba(30, 34, 61, 0.9)',
  overlayStrong: 'rgba(30, 34, 61, 0.98)',
  panel: '#101427'
};


// ================= JOB CARD COMPONENT =================
function JobCard({ job, onView, onApply, onSave, isSaved }: {
  job: Job;
  onView: (job: Job) => void;
  onApply: (job: Job) => void;
  onSave: (job: Job) => void;
  isSaved: boolean;
}) {
  return (
    <div style={{
      backgroundColor: theme.overlay,
      backdropFilter: 'blur(8px)',
      border: `1px solid ${theme.border}`,
      borderRadius: '12px',
      padding: '16px',
      transition: 'all 0.2s',
      cursor: 'default'
    }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = theme.accent;
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = theme.border;
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: '12px',
        marginBottom: '12px'
      }}>
        <div style={{ flex: 1 }}>
          <h3 style={{
            margin: '0 0 6px 0',
            color: '#fff',
            fontSize: '16px',
            fontWeight: 600,
            lineHeight: '1.4'
          }}>
            {job.Kasb}
          </h3>
          <p style={{
            margin: 0,
            color: theme.accent,
            fontSize: '13px',
            fontWeight: 500
          }}>
            {job["Bandlik turi"]}
          </p>
        </div>
        <span style={{
          backgroundColor: 'rgba(245, 79, 27, 0.14)',
          color: theme.accent,
          padding: '4px 10px',
          borderRadius: '12px',
          fontSize: '11px',
          fontWeight: 600,
          whiteSpace: 'nowrap'
        }}>
          OLX E'loni
        </span>
      </div>

      {/* Meta info */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px',
        marginBottom: '14px',
        fontSize: '13px',
        color: theme.muted
      }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <i className="fas fa-map-marker-alt" style={{ color: theme.icon }}></i>
          {job.Joylashuv}
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <i className="fas fa-money-bill" style={{ color: theme.icon }}></i>
          {job["Ish haqi"]}
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <i className="fas fa-briefcase" style={{ color: theme.icon }}></i>
          {job["Ish turi"]}
        </span>
      </div>

      {/* Actions */}
      <div style={{
        display: 'flex',
        gap: '8px'
      }}>
        <button
          onClick={() => onView(job)}
          style={{
            flex: 1,
            padding: '10px',
            backgroundColor: theme.surface,
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = theme.border}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = theme.surface}
        >
          <i className="fas fa-eye"></i> Batafsil
        </button>

        <button
          onClick={() => onApply(job)}
          style={{
            flex: 1,
            padding: '10px',
            backgroundColor: theme.accent,
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = theme.accentHover}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = theme.accent}
        >
          <i className="fas fa-paper-plane"></i> Ariza
        </button>

        <button
          onClick={(e: MouseEvent<HTMLButtonElement>) => {
            e.stopPropagation();
            onSave(job);
          }}
          style={{
            width: '40px',
            padding: '10px',
            backgroundColor: isSaved ? theme.accent : theme.surface,
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 0.2s'
          }}
          title={isSaved ? "Saqlangan" : "Saqlash"}
        >
          <i className="fas fa-bookmark"></i>
        </button>
      </div>
    </div>
  );
}

// ================= WELCOME COMPONENT =================
function Welcome() {
  return (
    <div className="welcome-message" style={{ position: 'relative', zIndex: 3 }}>
      <div className="welcome-icon">
        <i className="fas fa-robot"></i>
      </div>
      <h2>Xush kelibsiz!</h2>
      <p>Men Job Finder - sizning AI yordamchingizman. OLX bazasidan sizga eng mos keladigan ishlarni topishga yordam beraman.</p>
      <div className="suggestions">
        <p>Qidirish uchun qanday ish kerakligini va joylashuvni yozing:</p>
      </div>
    </div>
  );
}

// ================= MESSAGE COMPONENT =================
function MessageComponent({ type, content, jobs, onView, onApply, onSave, savedJobs }: {
  type: 'user' | 'bot';
  content: string | null;
  jobs: Job[] | null;
  onView: (job: Job) => void;
  onApply: (job: Job) => void;
  onSave: (job: Job) => void;
  savedJobs: Job[];
}) {
  const isUser = type === 'user';

  return (
    <div style={{
      display: 'flex',
      gap: '16px',
      marginBottom: '40px',
      flexDirection: isUser ? 'row-reverse' : 'row',
      alignItems: 'flex-start',
      width: '100%',
      animation: 'fadeIn 0.3s ease',
      position: 'relative',
      zIndex: 3
    }}>
      {/* Avatar */}
      <div style={{
        width: '40px',
        height: '40px',
        borderRadius: '50%',
        backgroundColor: isUser ? theme.accent : theme.accent,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        fontSize: '16px',
        flexShrink: 0,
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
      }}>
        <i className={`fas fa-${isUser ? 'user' : 'robot'}`}></i>
      </div>

      {/* Message content */}
      <div style={{
        maxWidth: jobs && jobs.length > 0 ? '85%' : '75%',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        alignItems: isUser ? 'flex-end' : 'flex-start'
      }}>
        {/* Text bubble */}
        {content && (
          <div style={{
            backgroundColor: isUser ? theme.accent : theme.surfaceAlt,
            backdropFilter: 'blur(8px)',
            color: '#fff',
            padding: '14px 20px',
            borderRadius: isUser ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
            fontSize: '15px',
            lineHeight: '1.6',
            wordWrap: 'break-word',
            whiteSpace: 'pre-wrap',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
          }}>
            {content}
          </div>
        )}

        {/* Job cards */}
        {jobs && jobs.length > 0 && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            width: '100%'
          }}>
            {jobs.map((job: Job, idx: number) => (
              <JobCard
                key={job.Link || idx}
                job={job}
                onView={onView}
                onApply={onApply}
                onSave={onSave}
                isSaved={savedJobs.some((sj: Job) => sj.Link === job.Link)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ================= JOB MODAL COMPONENT =================
function JobModal({ job, isOpen, onClose, onApply, onSave, isSaved, onTriggerAlert }: {
  job: Job | null;
  isOpen: boolean;
  onClose: () => void;
  onApply: (job: Job) => void;
  onSave: (job: Job) => void;
  isSaved: boolean;
  onTriggerAlert: (title: string, msg: string) => void;
}) {
  if (!isOpen || !job) return null;

  return (
    <div className="modal active" style={{ zIndex: 999 }}>
      <div className="modal-overlay" onClick={onClose}></div>
      <div className="modal-content">
        <button className="modal-close" onClick={onClose}>
          <i className="fas fa-times"></i>
        </button>
        <div className="modal-header">
          <h2>{job.Kasb}</h2>
          <p>{job["Bandlik turi"]}</p>
        </div>
        <div className="modal-body">
          <div className="job-meta">
            <span><i className="fas fa-map-marker-alt"></i> <span>{job.Joylashuv}</span></span>
            <span><i className="fas fa-money-bill"></i> <span>{job["Ish haqi"]}</span></span>
            <span><i className="fas fa-briefcase"></i> <span>{job["Ish turi"]}</span></span>
            {job.Telefon && job.Telefon !== "Ko'rsatilmadi" && (
              <span><i className="fas fa-phone"></i> <span>{job.Telefon}</span></span>
            )}
            {job.Link && (
              <span><i className="fas fa-link"></i> <a href={job.Link} target="_blank" rel="noreferrer" className="job-link">E'longa o'tish</a></span>
            )}
          </div>
          <div className="job-section">
            <h3><i className="fas fa-info-circle"></i> Qo'shimcha ma'lumot</h3>
            <p>Bu e'lon OLX bazasidan olindi. To'liq ma'lumot va ish beruvchi bilan bog'lanish uchun quyidagi havola orqali asl e'longa o'ting.</p>
          </div>
        </div>
        <div className="modal-footer">
          <button
            className="btn btn-primary"
            onClick={() => {
              if (job.Link) {
                window.open(job.Link, '_blank', 'noopener');
              } else {
                onApply(job);
              }
            }}
          >
            <i className="fas fa-external-link-alt"></i> OLX da ko'rish
          </button>
          <button className="btn btn-secondary" onClick={() => onSave(job)}>
            <i className="fas fa-bookmark"></i>
            {isSaved ? 'Saqlangan' : 'Saqlash'}
          </button>
          <button className="btn btn-secondary" onClick={() => {
            const shareText = `📢 Ish topdim!\n\n💼 ${job.Kasb}\n📍 ${job.Joylashuv}\n💰 ${job["Ish haqi"]}\n🔗 ${job.Link}`;
            navigator.clipboard.writeText(shareText);
            onTriggerAlert('Muvaffaqiyatli', 'E\'lon matnidan nusxa olindi!');
          }}>
            <i className="fas fa-share"></i> Ulashish
          </button>
        </div>
      </div>
    </div>
  );
}

// ================= TYPING INDICATOR =================
function TypingIndicator() {
  return (
    <div className="message bot" style={{ position: 'relative', zIndex: 3 }}>
      <div className="message-avatar"><i className="fas fa-robot"></i></div>
      <div className="message-content">
        <div className="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );
}

// ================= SAVED SIDEBAR =================
function SavedSidebar({ isOpen, onClose, savedJobs, onView, onRemove }: {
  isOpen: boolean;
  onClose: () => void;
  savedJobs: Job[];
  onView: (job: Job) => void;
  onRemove: (link: string) => void;
}) {
  return (
    <div className={`sidebar ${isOpen ? 'active' : ''}`} style={{ zIndex: 990 }}>
      <div className="sidebar-header">
        <h3><i className="fas fa-bookmark"></i> Saqlangan ishlar</h3>
        <button className="sidebar-close" onClick={onClose}>
          <i className="fas fa-times"></i>
        </button>
      </div>
      <div className="sidebar-content">
        {savedJobs.length === 0 ? (
          <div className="empty-sidebar">
            <i className="fas fa-bookmark"></i>
            <p>Hali saqlangan ishlar yo'q</p>
          </div>
        ) : (
          savedJobs.map((job: Job, idx: number) => (
            <div key={job.Link || idx} className="saved-job-item" onClick={() => onView(job)}>
              <h4>{job.Kasb}</h4>
              <p>{job["Bandlik turi"]}</p>
              <div className="job-card-meta">
                <span><i className="fas fa-map-marker-alt"></i> {job.Joylashuv}</span>
                <span><i className="fas fa-money-bill"></i> {job["Ish haqi"]}</span>
              </div>
              <button className="btn-save-card saved" onClick={(e: MouseEvent<HTMLButtonElement>) => {
                e.stopPropagation();
                onRemove(job.Link);
              }}>
                <i className="fas fa-trash"></i> O'chirish
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ================= CUSTOM POPUP MODAL =================
function CustomAlertModal({ isOpen, title, message, type, onConfirm, onClose }: {
  isOpen: boolean;
  title: string;
  message: string;
  type: 'confirm' | 'alert';
  onConfirm: (() => void) | null;
  onClose: () => void;
}) {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'transparent',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      animation: 'fadeIn 0.2s ease'
    }}>
      <div style={{
        backgroundColor: theme.surface,
        border: `1px solid ${theme.border}`,
        borderRadius: '16px',
        padding: '24px',
        width: '90%',
        maxWidth: '400px',
        boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
        textAlign: 'center',
        color: '#fff',
        animation: 'scaleIn 0.2s ease'
      }}>
        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: type === 'confirm' ? 'rgba(248, 113, 113, 0.15)' : 'rgba(245, 79, 27, 0.14)',
          color: type === 'confirm' ? theme.danger : theme.accent,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '24px',
          margin: '0 auto 16px auto'
        }}>
          <i className={type === 'confirm' ? "fas fa-sign-out-alt" : "fas fa-check-circle"}></i>
        </div>

        <h3 style={{ margin: '0 0 8px 0', fontSize: '18px', fontWeight: 600 }}>{title}</h3>
        <p style={{ margin: '0 0 24px 0', fontSize: '14px', color: theme.muted, lineHeight: '1.5' }}>{message}</p>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          {type === 'confirm' ? (
            <>
              <button
                onClick={onClose}
                style={{
                  flex: 1,
                  padding: '12px',
                  backgroundColor: theme.surface,
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 500,
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = theme.border}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = theme.surface}
              >
                Yo'q, qolish
              </button>
              <button
                onClick={() => {
                  if (onConfirm) onConfirm();
                  onClose();
                }}
                style={{
                  flex: 1,
                  padding: '12px',
                  backgroundColor: theme.danger,
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 500,
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = theme.danger}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = theme.danger}
              >
                Ha, chiqish
              </button>
            </>
          ) : (
            <button
              onClick={onClose}
              style={{
                padding: '10px 24px',
                backgroundColor: theme.accent,
                border: 'none',
                borderRadius: '8px',
                color: '#fff',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'background 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = theme.accentHover}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = theme.accent}
            >
              Tushunarli
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ================= MAIN APP COMPONENT =================
export default function App() {

  // ============ 1. ASOSIY FOYDALANUVCHI STATE-I ============
  const [user, setUser] = useState<{ name: string; email: string } | null>(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });

  // ============ 2. FOYDALANUVCHIGA BOG'LIQ STATE-LAR (USER-SPECIFIC) ============
  const [chats, setChats] = useState<Chat[]>(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      const savedChats = localStorage.getItem(`job_finder_chats_${parsedUser.email}`);
      return savedChats ? JSON.parse(savedChats) : [];
    }
    return [];
  });

  const [savedJobs, setSavedJobs] = useState<Job[]>(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      const saved = localStorage.getItem(`savedJobs_${parsedUser.email}`);
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });

  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [userInput, setUserInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [customAlert, setCustomAlert] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    type: 'confirm' | 'alert';
    onConfirm: (() => void) | null;
  }>({
    isOpen: false,
    title: '',
    message: '',
    type: 'alert',
    onConfirm: null
  });

  const [_conversationState, setConversationState] = useState<ConversationState>({
    userSkills: [],
    userExperience: '',
    userInterests: [],
    recommendedJobs: []
  });

  const chatContainerRef = useRef<HTMLDivElement>(null);

  const activeChat = chats.find(c => c.id === activeChatId);
  const messages = activeChat ? activeChat.messages : [];

  // Scroll to bottom effect
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isTyping]);


  // ============ 3. MANTIQIY FUNKSIYALAR VA AUTHENTIFICATION ============

  const handleLogin = (userData: { name: string; email: string }) => {
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);

    const savedChats = localStorage.getItem(`job_finder_chats_${userData.email}`);
    setChats(savedChats ? JSON.parse(savedChats) : []);
    setActiveChatId(null);

    const saved = localStorage.getItem(`savedJobs_${userData.email}`);
    setSavedJobs(saved ? JSON.parse(saved) : []);
  };

  const handleLogout = () => {
    setCustomAlert({
      isOpen: true,
      title: 'Tizimdan chiqish',
      message: 'Haqiqatan ham tizimdan chiqishni xohlaysizmi?',
      type: 'confirm',
      onConfirm: () => {
        localStorage.removeItem('user');
        setUser(null);
        setChats([]);
        setActiveChatId(null);
        setSavedJobs([]);
      }
    });
  };

  const triggerCustomAlert = (title: string, message: string) => {
    setCustomAlert({
      isOpen: true,
      title: title,
      message: message,
      type: 'alert',
      onConfirm: null
    });
  };

  const detectIntent = (text: string): string => {
    if (intentPatterns?.greeting?.test(text)) return 'greeting';
    if (intentPatterns?.goodbye?.test(text)) return 'goodbye';
    return 'search';
  };

  const generateResponse = (intent: string): { content: string | null; jobs: Job[] | null } => {
    switch (intent) {
      case 'greeting':
        return {
          content: `Assalomu alaykum! 👋 Men Job Finder AI yordamchisiman. Qanday ish qidiryapsiz va qaysi hududdan?`,
          jobs: null
        };
      case 'goodbye':
        return {
          content: `Xayr! 👋 Omad yor bo'lsin.`,
          jobs: null
        };
      default:
        return { content: null, jobs: null };
    }
  };

  const handleMessage = async (text: string) => {
    const currentUser = user;
    if (!text.trim() || !currentUser) return;

    let currentChatId = activeChatId;
    let updatedChats = [...chats];

    // Yangi chat yaratish
    if (!currentChatId) {
      currentChatId = 'chat_' + Date.now();
      const newChat: Chat = {
        id: currentChatId,
        title: text.length > 25 ? text.substring(0, 25) + '...' : text,
        messages: []
      };

      updatedChats = [newChat, ...updatedChats];
      setChats(updatedChats);
      localStorage.setItem(`job_finder_chats_${currentUser.email}`, JSON.stringify(updatedChats));
      setActiveChatId(currentChatId);
    }

    // Foydalanuvchi xabari
    const userMsg: Message = { type: 'user', content: text, jobs: null };

    updatedChats = updatedChats.map(chat =>
      chat.id === currentChatId
        ? { ...chat, messages: [...chat.messages, userMsg] }
        : chat
    );

    setChats(updatedChats);
    localStorage.setItem(`job_finder_chats_${currentUser.email}`, JSON.stringify(updatedChats));
    setUserInput('');
    setIsTyping(true);

    try {
      const intent = detectIntent(text);

      // Salom / xayrlashish
      if (intent === 'greeting' || intent === 'goodbye') {
        const localResponse = generateResponse(intent);

        const botMsg: Message = {
          type: 'bot',
          content: localResponse.content,
          jobs: null
        };

        setChats((prevChats: Chat[]) => {
          const next = prevChats.map(chat =>
            chat.id === currentChatId
              ? { ...chat, messages: [...chat.messages, botMsg] }
              : chat
          );
          localStorage.setItem(`job_finder_chats_${currentUser.email}`, JSON.stringify(next));
          return next;
        });

        return;
      }

      // Backenddan ish tavsiyasi olish
      const backendData = await getJobsFromBackend(text, '', '', 50, 10);
      const backendJobs = (backendData.recommendations || []) as Job[];

      const aiResponse = backendJobs.length > 0
        ? await getAIJobResponse(text, backendJobs)
        : `Kechirasiz, "${text}" bo'yicha mos ish topilmadi.`;

      setConversationState((prev: ConversationState) => ({
        ...prev,
        recommendedJobs: backendJobs
      }));

      const botMsg: Message = {
        type: 'bot',
        content: aiResponse,
        jobs: backendJobs.length > 0 ? backendJobs : null
      };

      setChats((prevChats: Chat[]) => {
        const next = prevChats.map(chat =>
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, botMsg] }
            : chat
        );
        localStorage.setItem(`job_finder_chats_${currentUser.email}`, JSON.stringify(next));
        return next;
      });

    } catch (error) {
      console.error("Xatolik:", error);

      const errorMsg: Message = {
        type: 'bot',
        content: "Kechirasiz, server bilan ulanishda xatolik yuz berdi.",
        jobs: null
      };

      setChats((prevChats: Chat[]) => {
        const next = prevChats.map(chat =>
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, errorMsg] }
            : chat
        );
        localStorage.setItem(`job_finder_chats_${currentUser.email}`, JSON.stringify(next));
        return next;
      });

    } finally {
      setIsTyping(false);
    }
  };

  const handleSend = () => handleMessage(userInput);

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  

  const handleNewChat = () => {
    setActiveChatId(null);
  };

  const handleSaveJob = (job: Job) => {
    if (!user) return;

    setSavedJobs((prev: Job[]) => {
      const exists = prev.some(j => j.Link === job.Link);
      const next = exists ? prev.filter(j => j.Link !== job.Link) : [...prev, job];
      localStorage.setItem(`savedJobs_${user.email}`, JSON.stringify(next));
      return next;
    });
  };

  const handleApply = (job: Job) => {
    if (job.Link) {
      window.open(job.Link, '_blank', 'noopener');
    } else {
      triggerCustomAlert('Xatolik', 'Bu e\'lonning havolasi topilmadi.');
    }
  };

  const handleRemoveSaved = (link: string) => {
    if (!user) return;

    setSavedJobs((prev: Job[]) => {
      const next = prev.filter(j => j.Link !== link);
      localStorage.setItem(`savedJobs_${user.email}`, JSON.stringify(next));
      return next;
    });
  };


  const handleDeleteChat = (id: string) => {
    if (!user) return;
    setChats(prev => {
      const next = prev.filter(chat => chat.id !== id);
      localStorage.setItem(`job_finder_chats_${user.email}`, JSON.stringify(next));
      return next;
    });
    if (activeChatId === id) {
      setActiveChatId(null);
    }
  };

  // ============ 4. LOGINDAN O'TGANLIGINI TEKSHIRISH ============
  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', backgroundColor: theme.background }}>

      {/* =======================================================================
          CHAT SOHASI UCHUN MAYIN NEON JAVOHIR ANIMATSIYALARI (CSS STYLES)
          ======================================================================= */}
      <style>{`
        @keyframes scaleIn {
          from { transform: scale(0.95); opacity: 0; }
          to { transform: scale(1); opacity: 1; }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes chat-float-1 {
          0% { transform: translate(0px, 0px) scale(1); }
          50% { transform: translate(30px, -40px) scale(1.1); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        @keyframes chat-float-2 {
          0% { transform: translate(0px, 0px) scale(1); }
          50% { transform: translate(-30px, 30px) scale(1.15); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .chat-glow-orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(160px);
          opacity: 0.30; /* Juda mayin, ko'zni charchatmaydigan yorug'lik */
          pointer-events: none;
          z-index: 1;
        }
      `}</style>

      {/* ================= CHAP SIDEBAR (MENU) ================= */}
      <div
        style={{
          width: sidebarOpen ? '260px' : '0px',
          backgroundColor: theme.surface,
          color: theme.text,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: sidebarOpen ? '12px' : '0px',
          borderRight: sidebarOpen ? `1px solid ${theme.border}` : 'none',
          boxSizing: 'border-box',
          zIndex: 10,
          transition: 'width 0.3s ease, padding 0.3s ease',
          overflow: 'hidden'
        }}
      >
        {sidebarOpen && (
          <>
            <div style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', flex: 1 }}>
              {/* Yuqori panel: Yopish + Yangi chat */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                <button
                  onClick={() => setSidebarOpen(false)}
                  title="Sidebar'ni yopish"
                  style={{
                    width: '40px',
                    height: '40px',
                    backgroundColor: 'transparent',
                    border: `1px solid ${theme.border}`,
                    borderRadius: '8px',
                    color: '#fff',
                    cursor: 'pointer',
                    fontSize: '14px',
                    flexShrink: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = theme.surfaceAlt}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <i className="fas fa-bars"></i>
                </button>

                <button
                  onClick={handleNewChat}
                  style={{
                    flex: 1,
                    padding: '10px 14px',
                    backgroundColor: 'transparent',
                    border: `1px solid ${theme.border}`,
                    borderRadius: '8px',
                    color: '#fff',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    fontSize: '14px',
                    fontWeight: 500,
                    transition: 'background 0.2s',
                    whiteSpace: 'nowrap'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = theme.surfaceAlt}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <i className="fas fa-plus"></i>
                  <span>Yangi suhbat</span>
                </button>
              </div>

              {/* Chat Tarixi */}
              <div style={{ marginTop: '12px', overflowY: 'auto', flex: 1 }}>
                <p style={{ fontSize: '12px', color: theme.icon, marginBottom: '10px', fontWeight: 600, paddingLeft: '4px' }}>
                  Oldingi qidiruvlar
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {chats.length === 0 ? (
                    <p style={{ color: theme.icon, fontSize: '13px', paddingLeft: '8px', fontStyle: 'italic' }}>
                      Hozircha qidiruvlar yo'q
                    </p>
                  ) : (
                    chats.map((chat) => (
                      <div
                        key={chat.id}
                        onClick={() => setActiveChatId(chat.id)}
                        style={{
                          padding: '10px 12px',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '13px',
                          color: theme.text,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          transition: 'background 0.2s',
                          backgroundColor: chat.id === activeChatId ? theme.surfaceAlt : 'transparent',
                          borderLeft: chat.id === activeChatId ? `4px solid ${theme.accent}` : '4px solid transparent'
                        }}
                        onMouseEnter={(e) => {
                          if (chat.id !== activeChatId) {
                            e.currentTarget.style.backgroundColor = theme.border;
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (chat.id !== activeChatId) {
                            e.currentTarget.style.backgroundColor = 'transparent';
                          }
                        }}
                      >
                        <span style={{
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          flex: 1,
                          pointerEvents: 'none'
                        }}>
                          <i className="far fa-comment-alt" style={{ marginRight: '10px', color: theme.icon, pointerEvents: 'none' }}></i>
                          {chat.title}
                        </span>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteChat(chat.id);
                          }}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: theme.icon,
                            cursor: 'pointer',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            zIndex: 2
                          }}
                        >
                          <i className="fas fa-times"></i>
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </>
        )}

        {/* Sidebar Footer */}
        <div style={{ borderTop: `1px solid ${theme.border}`, paddingTop: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              backgroundColor: theme.accent,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              color: '#fff',
              fontSize: '14px',
              flexShrink: 0
            }}>
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div style={{ overflow: 'hidden', flex: 1 }}>
              <p style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: '#fff' }}>
                {user.name}
              </p>
              <p style={{
                margin: 0,
                fontSize: '11px',
                color: theme.icon,
                whiteSpace: 'nowrap',
                textOverflow: 'ellipsis',
                overflow: 'hidden'
              }}>
                {user.email}
              </p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            style={{
              width: '100%',
              padding: '8px 12px',
              backgroundColor: 'transparent',
              border: `1px solid ${theme.border}`,
              borderRadius: '8px',
              color: theme.danger,
              cursor: 'pointer',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = theme.surfaceAlt}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <i className="fas fa-sign-out-alt"></i>
            Chiqish
          </button>
        </div>
      </div>

      {/* ================= O'NG TOMON (CHAT OYNASI) ================= */}
      <div style={{
        flex: 1,
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: theme.panel, /* Orqa fonni biroz chuqurroq quyuq qildik */
      }}>

        <div className="chat-glow-orb" style={{
          width: '400px',
          height: '400px',
          backgroundColor: theme.accent, // Yashil neon
          top: '15%',
          left: '20%',
          animation: 'chat-float-1 25s infinite alternate ease-in-out'
        }} />
        <div className="chat-glow-orb" style={{
          width: '450px',
          height: '450px',
          backgroundColor: theme.accent, // Ko'k neon
          bottom: '15%',
          right: '15%',
          animation: 'chat-float-2 28s infinite alternate ease-in-out'
        }} />

        {/* Header */}
        <header style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px 20px',
          borderBottom: `1px solid ${theme.border}`,
          backgroundColor: 'rgba(12, 12, 15, 0.7)',
          backdropFilter: 'blur(10px)',
          flexShrink: 0,
          position: 'relative',
          zIndex: 5
        }}>
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              title="Sidebar'ni ochish"
              style={{
                width: '40px',
                height: '40px',
                backgroundColor: 'transparent',
                border: `1px solid ${theme.border}`,
                borderRadius: '8px',
                color: '#fff',
                cursor: 'pointer',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = theme.surfaceAlt}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <i className="fas fa-bars"></i>
            </button>
          )}

          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            backgroundColor: theme.accent,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: '16px'
          }}>
            <i className="fas fa-robot"></i>
          </div>
          <h1 style={{ margin: 0, fontSize: '18px', color: '#fff', fontWeight: 600 }}>Job Finder (OLX)</h1>
        </header>

        {/* Chat Asosiy Maydoni */}
        <main
          ref={chatContainerRef}
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '20px',
            paddingBottom: '140px',
            position: 'relative',
            zIndex: 3
          }}
        >
          <div style={{ maxWidth: '1050px', margin: '0 auto', width: '100%' }}>

            {messages.length === 0 ? (
              <Welcome />
            ) : (
              messages.map((msg, idx) => (
                <MessageComponent
                  key={idx}
                  type={msg.type}
                  content={msg.content}
                  jobs={msg.jobs}
                  onView={(job: Job) => { setSelectedJob(job); setShowModal(true); }}
                  onApply={handleApply}
                  onSave={handleSaveJob}
                  savedJobs={savedJobs}
                />
              ))
            )}

            {isTyping && <TypingIndicator />}
          </div>
        </main>

        {/* Input qismi */}
        <footer style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          padding: '16px 20px',
          backgroundColor: 'rgba(12, 12, 15, 0.7)',
          backdropFilter: 'blur(10px)',
          borderTop: `1px solid ${theme.border}`,
          zIndex: 5
        }}>
          <div style={{
            maxWidth: '1050px',
            margin: '0 auto',
            display: 'flex',
            gap: '8px',
            alignItems: 'flex-end',
            backgroundColor: 'rgba(40, 40, 45, 0.8)',
            borderRadius: '24px',
            padding: '8px 8px 8px 16px',
            border: `1px solid ${theme.border}`
          }}>
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Qanday ish kerak? (Kasb va shahar nomini yozing)..."
              rows={1}
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: '#fff',
                fontSize: '15px',
                resize: 'none',
                fontFamily: 'inherit',
                padding: '8px 0',
                maxHeight: '120px'
              }}
            />
            <button
              onClick={handleSend}
              disabled={!userInput.trim()}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                backgroundColor: userInput.trim() ? theme.accent : theme.border,
                color: '#fff',
                border: 'none',
                cursor: userInput.trim() ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '14px',
                transition: 'background 0.2s',
                flexShrink: 0
              }}
            >
              <i className="fas fa-paper-plane"></i>
            </button>
          </div>
          <p style={{
            textAlign: 'center',
            color: theme.icon,
            fontSize: '12px',
            margin: '8px 0 0',
          }}>
            Ma'lumotni kiritish uchun Enter bosing
          </p>
        </footer>

        {/* MODAL OYNALAR */}
        <JobModal
          job={selectedJob}
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          onApply={handleApply}
          onSave={handleSaveJob}
          isSaved={selectedJob ? savedJobs.some(j => j.Link === selectedJob.Link) : false}
          onTriggerAlert={triggerCustomAlert}
        />

        <SavedSidebar
          isOpen={showSidebar}
          onClose={() => setShowSidebar(false)}
          savedJobs={savedJobs}
          onView={(job: Job) => { setSelectedJob(job); setShowModal(true); setShowSidebar(false); }}
          onRemove={handleRemoveSaved}
        />

        {/* CUSTOM POPUP OGOHLANTIRISH MODALI */}
        <CustomAlertModal
          isOpen={customAlert.isOpen}
          title={customAlert.title}
          message={customAlert.message}
          type={customAlert.type}
          onConfirm={customAlert.onConfirm}
          onClose={() => setCustomAlert(prev => ({ ...prev, isOpen: false }))}
        />

        {savedJobs.length > 0 && (
          <button
            onClick={() => setShowSidebar(true)}
            style={{
              position: 'fixed',
              bottom: '120px',
              right: '20px',
              width: '50px',
              height: '50px',
              borderRadius: '50%',
              backgroundColor: theme.accent,
              color: '#fff',
              border: 'none',
              cursor: 'pointer',
              fontSize: '18px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              zIndex: 5
            }}
          >
            <i className="fas fa-bookmark"></i>
            <span style={{
              position: 'absolute',
              top: '-4px',
              right: '-4px',
              background: theme.danger,
              color: '#fff',
              borderRadius: '50%',
              width: '20px',
              height: '20px',
              fontSize: '11px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {savedJobs.length}
            </span>
          </button>
        )}
      </div>
    </div>
  );
}