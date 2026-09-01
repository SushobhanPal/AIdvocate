const THREADS_KEY = 'nexus_ai_threads_v2';
const ACTIVE_THREAD_KEY = 'nexus_ai_active_thread_id_v2';
const SETTINGS_KEY = 'nexus_ai_settings_v2';

const DEFAULT_SETTINGS = {
  theme: 'light',
  activeModel: 'gpt-4o',
  sfxEnabled: true,
  autoReadAloud: false,
};

const DEFAULT_THREAD = {
  id: 'thread-welcome',
  title: 'Welcome to Nexus AI',
  createdAt: Date.now(),
  pinned: true,
  messages: [
    {
      id: 'msg-welcome',
      sender: 'ai',
      timestamp: Date.now() - 60000,
      content: `Hello! I'm **Nexus AI**, your simple, fast, and helpful assistant.

Here are a few things I can do for you:
- 💡 **Brainstorm & Write**: Articles, emails, summaries, and creative concepts.
- 💻 **Code & Debug**: Full code snippets, debugging, and architecture explanations.
- 📊 **Analyze & Visualize**: Structured breakdowns, insights, and interactive charts.
- 🎤 **Voice & Speech**: Real-time voice dictation and text-to-speech reading.

Feel free to ask a question, choose a prompt suggestion below, or start a new chat!`,
      model: 'gpt-4o',
    },
  ],
};

export const getStoredSettings = () => {
  try {
    const data = localStorage.getItem(SETTINGS_KEY);
    return data ? { ...DEFAULT_SETTINGS, ...JSON.parse(data) } : DEFAULT_SETTINGS;
  } catch (err) {
    console.error('Error loading settings', err);
    return DEFAULT_SETTINGS;
  }
};

export const saveStoredSettings = (settings) => {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch (err) {
    console.error('Error saving settings', err);
  }
};

export const getStoredThreads = () => {
  try {
    const data = localStorage.getItem(THREADS_KEY);
    if (!data) {
      const initialThreads = [DEFAULT_THREAD];
      localStorage.setItem(THREADS_KEY, JSON.stringify(initialThreads));
      return initialThreads;
    }
    const parsed = JSON.parse(data);
    return parsed.length > 0 ? parsed : [DEFAULT_THREAD];
  } catch (err) {
    console.error('Error loading threads', err);
    return [DEFAULT_THREAD];
  }
};

export const saveStoredThreads = (threads) => {
  try {
    localStorage.setItem(THREADS_KEY, JSON.stringify(threads));
  } catch (err) {
    console.error('Error saving threads', err);
  }
};

export const getStoredActiveThreadId = () => {
  try {
    return localStorage.getItem(ACTIVE_THREAD_KEY) || DEFAULT_THREAD.id;
  } catch {
    return DEFAULT_THREAD.id;
  }
};

export const saveStoredActiveThreadId = (threadId) => {
  try {
    localStorage.setItem(ACTIVE_THREAD_KEY, threadId);
  } catch (err) {
    console.error('Error saving active thread id', err);
  }
};
