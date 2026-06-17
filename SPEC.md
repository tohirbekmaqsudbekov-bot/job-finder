# Job Finder - AI Powered Job Recommendation System

## Concept & Vision

Job Finder — bu foydalanuvchining bilimlari, ko'nikmalari va qiziqishlariga qarab aqlli ishlarni tavsiya qiladigan chat-based tizim. ChatGPT ga o'xshash interfeys orqali foydalanuvchi tabiiy tilda o'z ma'lumotlarini kiritadi va AI asosida unga mos keladigan ishlar tavsiya qilinadi. Interface zamonaviy, sodda va foydalanishga qulay bo'ladi.

## Design Language

### Aesthetic Direction
- ChatGPT dan ilhomlangan - minimal, sof, professionallik hissi
- Kechki rejim asosiy (dark mode)

### Color Palette
- Background Primary: #212121 (qora)
- Background Secondary: #1E1E1E (quyuq kulrang)
- Background Tertiary: #2D2D2D (yengil quyuq)
- Accent Primary: #10A37F (yashil - ChatGPT dan ilhomlangan)
- Accent Secondary: #19A36B (qorong'i yashil)
- Text Primary: #ECECF1 (oq)
- Text Secondary: #8B8B8B (kulrang)
- User message bg: #2D7D46 (yashil)
- Bot message bg: #2D2D2D (quyuq)
- Border: #404040

### Typography
- Font: Inter (Google Fonts)
- Headings: 600 weight
- Body: 400 weight
- Chat messages: 16px
- Buttons: 14px

### Spatial System
- Container max-width: 800px
- Message padding: 16px
- Gap between messages: 16px
- Border radius: 12px

### Motion Philosophy
- Smooth fade-in for new messages (300ms ease)
- Typing indicator animation
- Button hover transitions (200ms)
- Slide-up entrance for job cards

## Layout & Structure

### Main Layout
1. **Header** - Logo, title, "New Chat" button
2. **Chat Area** - Scrollable message history
3. **Input Area** - Fixed at bottom, text input + send button

### Message Types
- Welcome message (bot)
- User messages (right-aligned, green bg)
- Bot messages (left-aligned, dark bg)
- Job cards (special bot messages with job details)

## Features & Interactions

### Core Features
1. **Welcome Flow**
   - Bot greets and asks for basic info (skills, experience, interests)

2. **Interactive Chat**
   - User can type freely about their skills/experience
   - Bot analyzes and asks clarifying questions if needed

3. **Job Recommendations**
   - After gathering enough info, bot shows matching jobs
   - Each job as a card with: title, company, location, salary, match %

4. **Job Actions**
   - "Apply" button (opens modal with job details)
   - "Save" button (bookmark jobs)
   - "Share" button

5. **Filter & Refine**
   - User can ask for more/different recommendations
   - Filter by location, salary, job type

### Interaction Details
- Enter to send, Shift+Enter for new line
- Typing indicator while "AI thinks"
- Auto-scroll to newest message
- Hover effects on interactive elements

### Edge Cases
- Empty input: show hint
- Very short response: ask for more details
- No matching jobs: suggest related fields

## Component Inventory

### Header
- Logo (bot icon)
- App name
- New Chat button (top right)

### Chat Container
- Full height minus header and input
- Flex column, messages at bottom

### Message Bubble (User)
- Right aligned, green bg (#2D7D46), white text, rounded corners

### Message Bubble (Bot)
- Left aligned, dark bg (#2D2D2D), white text, rounded corners
- Contains text + optional job cards

### Job Card
- Title, Company, Location, Salary range
- Match percentage badge
- Tags (Remote, Full-time, etc.)
- Action buttons (View, Apply)

### Input Area
- Text input with placeholder
- Send button (disabled when empty)
- Suggestions chips below

### Typing Indicator
- Three animated dots

## Technical Approach

### Architecture
- Pure HTML/CSS/JS (no framework)
- LocalStorage for chat history and saved jobs
- Pre-defined job dataset (50+ jobs)
- Keyword-based matching algorithm for AI responses

### Data Model
```javascript
Job {
  id, title, company, location, salary, type,
  skills[], description, experience, remote
}

UserProfile {
  skills[], interests[], experience, preferredLocation
}

Conversation {
  messages[], currentStep, userProfile
}
```

### Matching Algorithm
- Extract keywords from user message
- Match against job skills and titles
- Calculate match percentage based on:
  - Skill overlap (60%)
  - Experience match (20%)
  - Location preference (20%)