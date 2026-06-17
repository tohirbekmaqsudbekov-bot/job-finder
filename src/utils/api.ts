const API_URL = import.meta.env.VITE_API_URL || "";

async function fetchWithRetry(input: RequestInfo, init: RequestInit, retries = 2) {
    let lastError: unknown;
    for (let attempt = 0; attempt <= retries; attempt += 1) {
        try {
            const res = await fetch(input, init);
            if (!res.ok) {
                throw new Error(`Backend xato: ${res.status}`);
            }
            return res;
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

export async function getJobsFromBackend(
    query: string,
    location = "",
    job_type = "",
    top_n = 50,
    max_pages = 10
) {
    if (!API_URL) {
        throw new Error("VITE_API_URL is not configured. Set VITE_API_URL in your environment.");
    }

    const res = await fetchWithRetry(`${API_URL}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            query,
            location,
            job_type,
            top_n,
            max_pages,
            source: "olx",
        }),
    });

    return await res.json();
}


