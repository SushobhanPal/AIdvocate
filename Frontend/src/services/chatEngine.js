export const API_BASE_URL = 'http://localhost:8000';

export const MODELS = [
  { id: 'qwen3:8b', name: 'Qwen 3 (8B RAG)', provider: 'Ollama', badge: 'Local RAG' }
];


export const fetchRAGResponse = async (userPrompt) => {
  try {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: userPrompt }),
    });

    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }

    const data = await res.json();
    return {
      answer: data.answer,
      sources: data.sources || [],
    };
  } catch (error) {
    console.error('Error contacting backend RAG server:', error);
    return {
      answer: `⚠️ Could not reach RAG backend at ${API_BASE_URL}. Make sure your FastAPI server, Qdrant, and Ollama are running!`,
      sources: [],
    };
  }
};

export const streamAiResponse = async (fullText, onChunk, speedMs = 10) => {
  const words = fullText.split(' ');
  let accumulated = '';
  for (let i = 0; i < words.length; i++) {
    accumulated += (i === 0 ? '' : ' ') + words[i];
    onChunk(accumulated);
    const delay = words[i].includes('\n') ? speedMs * 2 : speedMs;
    await new Promise((resolve) => setTimeout(resolve, delay));
  }
};


