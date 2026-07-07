const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8003";

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  let res;
  try {
    res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch (err) {
    throw new Error(
      `Could not reach the Dhanvi backend at ${BASE_URL}. Is the FastAPI server running on port 8003? (${err.message})`
    );
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore parse errors */
    }
    throw new Error(`API error ${res.status}: ${detail}`);
  }
  return res.json();
}

export const api = {
  health: () => request("/"),

  chat: (payload) =>
    request("/chat", { method: "POST", body: JSON.stringify(payload) }),

  portfolio: (customerId) => request(`/portfolio/${customerId}`),

  suitabilityQuestions: () => request("/suitability/questions"),
  submitSuitability: (payload) =>
    request("/suitability", { method: "POST", body: JSON.stringify(payload) }),

  recommendations: (customerId) => request(`/recommendations/${customerId}`),

  marketPulse: (customerId, language = "English") =>
    request(
      `/market-pulse?${customerId ? `customer_id=${customerId}&` : ""}language=${encodeURIComponent(language)}`
    ),

  goalPlan: (payload) =>
    request("/goal-plan", { method: "POST", body: JSON.stringify(payload) }),

  products: (customerId) =>
    request(`/products${customerId ? `?customer_id=${customerId}` : ""}`),

  insights: (customerId, language = "English") =>
    request(`/customer/${customerId}/insights?language=${encodeURIComponent(language)}`),

  escalate: (payload) =>
    request("/escalate", { method: "POST", body: JSON.stringify(payload) }),
};

export { BASE_URL };
