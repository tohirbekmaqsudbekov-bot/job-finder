const API_URL = import.meta.env.VITE_API_URL || "";

async function fetchWithRetry(input: RequestInfo, init: RequestInit, retries = 2) {
  let lastError: unknown;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      const response = await fetch(input, init);
      if (!response.ok) {
        throw new Error(`AI server xato: ${response.status}`);
      }
      return response;
    } catch (error) {
      lastError = error;
      if (attempt === retries) {
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, 500 * (attempt + 1)));
    }
  }
  throw lastError;
}

export const getAIJobResponse = async (message: string, topilganIshlar: any[]) => {
  if (!API_URL) {
    throw new Error("VITE_API_URL is not configured. Set VITE_API_URL in your environment.");
  }

  try {
    const response = await fetchWithRetry(`${API_URL}/ai-response`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, jobs: topilganIshlar }),
    });

    if (!response.ok) {
      throw new Error(`AI server xato: ${response.status}`);
    }

    const data = await response.json();
    if (data?.status === 'success' && typeof data.response === 'string') {
      return data.response;
    }

    throw new Error('AI serverdan noto‘g‘ri javob olindi');
  } catch (error) {
    console.error('AI javob berishda xatolik:', error);

    if (!topilganIshlar || topilganIshlar.length === 0) {
      return `Kechirasiz, "${message}" bo'yicha hozircha mos vakansiya topilmadi.`;
    }

    const top3 = topilganIshlar.slice(0, 3);
    const summary = top3
      .map((job, index) => {
        const title = job.Kasb || "Noma'lum ish";
        const location = job.Joylashuv || "Noma'lum joy";
        const salary = job["Ish haqi"] || "Ma'lumot yo'q";
        return `${index + 1}. ${title} — ${location}, ish haqi ${salary}`;
      })
      .join("\n");

    return `Sizning so'rovingiz bo'yicha ${topilganIshlar.length} ta mos vakansiya topdim:\n\n${summary}\n\nAgar xohlasangiz, ulardan birini batafsil ko'rib chiqishingiz mumkin.`;
  }
};