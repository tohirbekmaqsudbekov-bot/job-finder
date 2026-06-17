export interface Job {
  Kasb: string;
  "Ish haqi": string;
  Joylashuv: string;
  "Ish turi": string;
  "Bandlik turi": string;
  Telefon?: string;
  Link: string;
  moslik_foizi?: number;
}

export interface Message {
  type: "user" | "bot";
  content: string | null;
  jobs: Job[] | null;
}

export interface ConversationState {
  userSkills: string[];
  userExperience: string;
  userInterests: string[];
  recommendedJobs: Job[];
}

export const intentPatterns = {
  greeting: /salom|assalomu alaykum|hello|hi/i,
  goodbye: /xayr|bye|ko'rishguncha/i,
};

export const jobsDatabase: Job[] = [];