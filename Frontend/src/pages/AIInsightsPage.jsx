import { useEffect, useRef, useState } from "react";
import { askOrderInsights } from "../api/ai";
import ErrorMessage from "../components/ErrorMessage";
import { getErrorMessage } from "../utils/errors";

const EXAMPLES = [
  "Summarize my last five orders.",
  "Which of my orders are still not delivered?",
  "How much did I spend this week?",
  "Which food items have I ordered most frequently?",
];

export default function AIInsightsPage() {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState([]); // [{ question, answer, orders }]
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const inputRef = useRef(null);
  const bottomRef = useRef(null);

  // Scroll to the newest answer
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [history, loading]);

  const ask = async (text) => {
    const trimmed = text.trim();
    if (trimmed.length < 3 || loading) return;
    setError("");
    setLoading(true);
    try {
      const { data } = await askOrderInsights(trimmed);
      setHistory((prev) => [...prev, { question: trimmed, answer: data.answer, orders: data.orders_considered }]);
      setQuestion("");
    } catch (err) {
      setError(
        err?.response?.status === 429
          ? "The AI service is busy right now. Please wait a moment and try again."
          : getErrorMessage(err)
      );
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    ask(question);
  };

  return (
    <div>
      <h2>AI order insights</h2>
      <p className="muted">
        Ask questions about your own order history. Answers use only your orders.
      </p>

      <div className="chips" aria-label="Example questions">
        {EXAMPLES.map((example) => (
          <button key={example} type="button" className="chip" disabled={loading} onClick={() => ask(example)}>
            {example}
          </button>
        ))}
      </div>

      <div className="chat">
        {history.length === 0 && !loading && (
          <p className="muted">No questions yet. Pick an example above or type your own.</p>
        )}
        {history.map((entry, index) => (
          <div key={index} className="chat-turn">
            <p className="chat-question">{entry.question}</p>
            <div className="card chat-answer">
              <p>{entry.answer}</p>
              <p className="muted">Based on {entry.orders} of your order{entry.orders === 1 ? "" : "s"}</p>
            </div>
          </div>
        ))}
        {loading && <p className="loader">Thinking…</p>}
        <div ref={bottomRef} />
      </div>

      <ErrorMessage message={error} />

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. How much did I spend this week?"
          maxLength={500}
          aria-label="Your question"
        />
        <button type="submit" disabled={loading || question.trim().length < 3}>
          {loading ? "Asking..." : "Ask"}
        </button>
      </form>
    </div>
  );
}
