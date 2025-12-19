import React, { useState, useCallback, useEffect } from 'react';
import {
  Search, List, Settings, Share2, Plus, FileText, Zap, MessageSquare, Mic,
  BookOpen, Clock, ChevronsUpDown, Info, Loader2, Maximize, Minus,
} from 'lucide-react';
import QuizModal from './QuizModal';
import VoiceRecorder from "./VoiceRecorder";

// --- Config API backend ---
const API_URL = "http://localhost:5000";


// --- Types TypeScript ---

interface SourceItem {
  id: string;
  name: string;
  icon: React.ReactNode;
}

interface NoteItem {
  id: number;
  content: string;
}

interface ApiResult {
  text: string;
  type: 'summary' | 'quiz' | 'info' | 'chat';
}

type LoadingState = null | 'upload' | 'ask' | 'summary' | 'quiz';

// --- Helpers API réelles ---

async function uploadPdf(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/upload_pdf`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    throw new Error("Upload PDF failed");
  }
  return res.json(); // {id, name}
}
function parseQuizText(rawText: string) {
  // Découpe en blocs par question (numérotées 1. 2. 3.)
  const blocks = rawText.split(/\n\s*\d+\.\s/).slice(1);

  const questions = blocks.map(block => {
    const lines = block.trim().split("\n").map(l => l.trim());

    // 1. La première ligne = la question
    const question = lines[0];

    // 2. Les choix A, B, C (parfois plus)
    const choices: string[] = [];
    const choiceRegex = /^[A-D]\)/i;

    for (let line of lines.slice(1)) {
      if (choiceRegex.test(line)) {
        choices.push(line.replace(/^[A-D]\)\s*/i, ""));
      }
    }

    // 3. Trouver la réponse correcte
    const answerLine = lines.find(l =>
      l.toLowerCase().startsWith("réponse correcte")
    );

    let answerIndex = -1;

    if (answerLine) {
      const match = answerLine.match(/[A-D]/i);
      if (match) {
        const letter = match[0].toUpperCase();
        answerIndex = "ABCD".indexOf(letter);
      }
    }

    return {
      question,
      choices,
      answer: answerIndex,
      explanation: answerLine?.replace("Réponse correcte :", "").trim() || ""
    };
  });

  return questions;
}

async function fetchSources() {
  const res = await fetch(`${API_URL}/list_sources`);
  if (!res.ok) {
    throw new Error("list_sources failed");
  }
  const data: { id: string; name: string }[] = await res.json();
  // Ajout d'icônes cool selon l'index pour garder ton style (choix 2)
  return data.map((s, idx): SourceItem => {
    let icon: React.ReactNode = <FileText className="w-4 h-4 text-blue-500" />;
    if (idx % 4 === 1) icon = <Zap className="w-4 h-4 text-red-500" />;
    if (idx % 4 === 2) icon = <BookOpen className="w-4 h-4 text-orange-500" />;
    if (idx % 4 === 3) icon = <List className="w-4 h-4 text-green-500" />;
    return { ...s, icon };
  });
}

async function askQuestionApi(question: string, selectedIds: string[]) {
  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, selected_ids: selectedIds }),
  });
  const data = await res.json();
  return data.answer as string;
}

async function summarizeApi(selectedIds: string[]) {
  const res = await fetch(`${API_URL}/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selected_ids: selectedIds }),
  });
  const data = await res.json();
  return data.result as string;
}

async function quizApi(selectedIds: string[]) {
  const res = await fetch(`${API_URL}/quiz`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selected_ids: selectedIds }),
  });
  const data = await res.json();
  return data.result as string;
}

// --- Notes mock (on garde) ---
const INITIAL_NOTES: NoteItem[] = [
  { id: 1, content: "Note rapide : vérifier le calendrier de lancement." },
];

// --- Composant liste de sources (gauche) ---

const SourceListComponent: React.FC<{
  sources: SourceItem[];
  selectedIds: string[];
  onToggleSource: (id: string) => void;
  onToggleAll: () => void;
}> = ({ sources, selectedIds, onToggleSource, onToggleAll }) => {
  const allSelected = sources.length > 0 && selectedIds.length === sources.length;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-gray-500 text-sm py-1">
        <span className="font-semibold">Select all sources</span>
        <input
          type="checkbox"
          checked={allSelected}
          onChange={onToggleAll}
          className="h-4 w-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
        />
      </div>

      {sources.map(source => (
        <div
          key={source.id}
          className="flex items-center p-2 rounded-lg hover:bg-gray-50 transition cursor-pointer text-gray-700 text-sm"
        >
          {source.icon}
          <span className="ml-3 flex-grow" title={source.name}>{source.name}</span>
          <input
            type="checkbox"
            checked={selectedIds.includes(source.id)}
            onChange={() => onToggleSource(source.id)}
            className="h-4 w-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
          />
        </div>
      ))}

      {sources.length === 0 && (
        <div className="text-xs text-gray-400 mt-2">
          No source yet. Upload a PDF below.
        </div>
      )}
    </div>
  );
};

// --- Composant Add Note ---

const AddNoteComponent: React.FC<{
  setResult: React.Dispatch<React.SetStateAction<ApiResult | null>>;
}> = ({ setResult }) => {
  const [noteText, setNoteText] = useState("");

  const handleAddNote = () => {
    if (noteText.trim()) {
      setResult({ text: `Nouvelle note ajoutée: "${noteText}"`, type: 'info' });
      setNoteText("");
    }
  };

  return (
    <div className="mt-4 p-4 border border-dashed border-gray-300 rounded-xl bg-white shadow-sm">
      <div className="flex items-center text-sm font-semibold text-gray-700 mb-2">
        <Plus className="w-4 h-4 mr-1 text-indigo-600" /> Add note
      </div>
      <textarea
        className="w-full p-2 border border-gray-300 rounded-lg text-sm resize-none focus:ring-indigo-500 focus:border-indigo-500"
        rows={2}
        placeholder="Start typing..."
        value={noteText}
        onChange={(e) => setNoteText(e.target.value)}
      />
      <button
        onClick={handleAddNote}
        className="mt-2 text-indigo-600 text-sm font-medium hover:text-indigo-800 transition disabled:opacity-50"
        disabled={!noteText.trim()}
      >
        Save Note
      </button>
    </div>
  );
};

// --- Composant Principal ---

export default function App() {
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([]);
  const [result, setResult] = useState<ApiResult | null>(null);
  const [loading, setLoading] = useState<LoadingState>(null);
  const [notes, setNotes] = useState<NoteItem[]>(INITIAL_NOTES);
  const [activeTab, setActiveTab] = useState<'audio' | 'mindmap'>('audio');
  const [question, setQuestion] = useState<string>("Is UnderSeal a sustainable product?");
const [quizData, setQuizData] = useState<any[]>([]);
const [showQuiz, setShowQuiz] = useState(false);
  // --- Charger les sources au démarrage ---
  const loadSources = useCallback(async () => {
    try {
      const list = await fetchSources();
      setSources(list);
      // par défaut : tout sélectionner
      setSelectedSourceIds(list.map(s => s.id));
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    loadSources();
  }, [loadSources]);

  // --- Gérer upload PDF ---
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading('upload');
    try {
      await uploadPdf(file);
      await loadSources();
      setResult({
        text: `Source "${file.name}" uploadée et ajoutée.`,
        type: 'info',
      });
    } catch (err) {
      console.error(err);
      setResult({
        text: "Erreur lors de l'upload du PDF.",
        type: 'info',
      });
    } finally {
      setLoading(null);
      e.target.value = "";
    }
  };

  // --- Toggle sources ---
  const toggleSource = (id: string) => {
    setSelectedSourceIds(prev =>
      prev.includes(id)
        ? prev.filter(x => x !== id)
        : [...prev, id]
    );
  };

  const toggleAllSources = () => {
    if (selectedSourceIds.length === sources.length) {
      setSelectedSourceIds([]);
    } else {
      setSelectedSourceIds(sources.map(s => s.id));
    }
  };

  const ensureHasSourcesSelected = () => {
    if (selectedSourceIds.length === 0) {
      setResult({
        text: "Sélectionne au moins une source (PDF) à gauche avant de générer.",
        type: 'info',
      });
      return false;
    }
    return true;
  };

  // --- Actions backend : Ask, Summary, Quiz ---

  const handleAsk = async () => {
    if (!question.trim()) return;
    if (!ensureHasSourcesSelected()) return;
    setLoading('ask');
    setResult({ text: "Génération en cours...", type: 'chat' });
    try {
      const answer = await askQuestionApi(question, selectedSourceIds);
      setResult({ text: answer, type: 'chat' });
    } catch (err) {
      console.error(err);
      setResult({ text: "Erreur lors de la génération de la réponse.", type: 'info' });
    } finally {
      setLoading(null);
    }
  };

  const handleGenerateSummary = async () => {
    if (!ensureHasSourcesSelected()) return;
    setLoading('summary');
    setResult({ text: "Génération du résumé...", type: 'summary' });
    try {
      const text = await summarizeApi(selectedSourceIds);
      setResult({ text, type: 'summary' });
    } catch (err) {
      console.error(err);
      setResult({ text: "Erreur lors de la génération du résumé.", type: 'info' });
    } finally {
      setLoading(null);
    }
  };

const handleGenerateQuiz = async () => {
  if (!ensureHasSourcesSelected()) return;

  setLoading('quiz');
  setResult({ text: "Génération du quiz...", type: 'quiz' });

  try {
    const rawText = await quizApi(selectedSourceIds);
    
    // 🔍 DEBUG : Voir ce qui est vraiment reçu
    console.log("Type reçu:", typeof rawText);
    console.log("Valeur reçue:", rawText);
    console.log("Est null/undefined?", rawText == null);

    if (!rawText || typeof rawText !== "string") {
      console.error("Format inattendu:", rawText);
      throw new Error("Quiz API a renvoyé un format inattendu");
    }

    const questions = parseQuizText(rawText);

    if (!questions.length) {
      throw new Error("Aucune question trouvée dans la réponse LLM.");
    }

    setQuizData(questions);
    setShowQuiz(true);
    setResult(null);

  } catch (err) {
    console.error("Erreur complète:", err);
    setResult({
      text: "Erreur lors de la génération du quiz.",
      type: 'info'
    });
  } finally {
    setLoading(null);
  }
};


  // --- Styles de base pour cartes ---
  const cardBase = "bg-white p-6 rounded-2xl shadow-xl border border-gray-100";

  return (
    <div className="min-h-screen bg-gray-50 p-6 md:p-10 font-sans">
      {/* En-tête Global */}
      <header className="bg-white p-4 rounded-xl shadow-md flex justify-between items-center mb-6">
        <div className="flex items-center space-x-3">
          <div className="bg-gray-900 p-2 rounded-full">
            <Maximize className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold text-gray-800">
            MindSpark
          </h1>
        </div>
        <div className="flex items-center space-x-4">
          <button className="flex items-center text-gray-600 hover:text-gray-900 transition text-sm">
            <Share2 className="w-4 h-4 mr-1" /> Share
          </button>
          <button className="flex items-center text-gray-600 hover:text-gray-900 transition text-sm">
            <Settings className="w-4 h-4 mr-1" /> Settings
          </button>
          <div className="w-8 h-8 rounded-full bg-gray-300 overflow-hidden">
            <img
              src="https://placehold.co/32x32/1f2937/ffffff?text=U"
              alt="Profile"
              className="object-cover w-full h-full"
            />
          </div>
        </div>
      </header>

      {/* Grille 3 colonnes */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-full mx-auto">
        {/* COLONNE 1: SOURCES */}
        <div className="col-span-1 space-y-6">
          <div className={cardBase + " h-auto"}>
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-800">Sources</h2>
              <div className="flex space-x-2 text-gray-400">
                <Search className="w-5 h-5 cursor-pointer hover:text-gray-600" />
                <List className="w-5 h-5 cursor-pointer hover:text-gray-600" />
                <ChevronsUpDown className="w-5 h-5 cursor-pointer hover:text-gray-600" />
              </div>
            </div>

            <div className="mt-4">
              <SourceListComponent
                sources={sources}
                selectedIds={selectedSourceIds}
                onToggleSource={toggleSource}
                onToggleAll={toggleAllSources}
              />
            </div>

            {/* Upload PDF */}
            <label className="w-full mt-4 flex items-center justify-center p-3 rounded-xl border border-dashed border-indigo-300 text-indigo-600 bg-indigo-50 hover:bg-indigo-100 transition text-sm font-semibold cursor-pointer">
              {loading === 'upload' ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Uploading...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" /> Add source (PDF)
                </>
              )}
              <input
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={handleFileChange}
              />
            </label>
          </div>
        </div>

        {/* COLONNE 2: CHAT / RÉSULTAT */}
        <div className="col-span-1 space-y-6">
          <div className={cardBase + " min-h-[400px] flex flex-col"}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-800 flex items-center">
                <MessageSquare className="w-5 h-5 mr-2 text-red-500" /> Chat
              </h2>
              <div className="text-sm text-gray-500">
                <span className="font-semibold">{sources.length}</span> sources
              </div>
            </div>

            {/* Titre central */}
            <div className="text-center mb-6">
              <div className="bg-red-500 inline-block p-2 rounded-full mb-2">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-lg font-bold text-gray-800">
                UnderSeal Product Launch Summary
              </h3>
            </div>

            {/* Zone résultat / chat */}
            <div className="flex-grow bg-gray-50 p-3 rounded-xl border border-gray-200 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm font-mono text-gray-700">
                {loading && loading !== 'upload' ? (
                  <div className="text-center p-8 text-indigo-600">
                    <Loader2 className="w-6 h-6 mx-auto animate-spin" />
                    <p className="mt-2">Génération en cours...</p>
                  </div>
                ) : result?.text || (
                  <span className="text-gray-400 italic">
                    Lance une question ou une action du Studio pour voir le résultat ici.
                  </span>
                )}
              </pre>
            </div>

            {/* Onglets Audio / Mind map */}
            <div className="flex justify-center my-4 space-x-3">
              <button
                className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                  activeTab === 'audio'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
                onClick={() => setActiveTab('audio')}
              >
                <Mic className="w-4 h-4 inline-block mr-1" /> <VoiceRecorder onResult={(text) => setQuestion(text)} />
              </button>
              <button
                className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                  activeTab === 'mindmap'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
                onClick={() => setActiveTab('mindmap')}
              >
                <Zap className="w-4 h-4 inline-block mr-1" /> Mind map
              </button>
            </div>

            {/* Input de question */}
            <div className="flex items-center mt-3 p-2 bg-white border border-gray-300 rounded-xl">
              <input
                type="text"
                placeholder="Pose ta question sur les PDFs sélectionnés..."
                className="flex-grow px-2 py-1 text-sm focus:outline-none"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAsk();
                  }
                }}
              />
              <button
                className="p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                onClick={handleAsk}
                disabled={loading === 'ask'}
              >
                {loading === 'ask' ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Panneau d'ajout de note */}
          <AddNoteComponent setResult={setResult} />
        </div>

        {/* COLONNE 3: STUDIO & NOTES */}
        <div className="col-span-1 space-y-6">
          <div className={cardBase}>
            <h2 className="text-xl font-bold text-gray-800">Studio</h2>

            {/* Audio Overview */}
            <div className="mt-4 p-4 border border-gray-200 rounded-xl bg-gray-50">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-gray-700">Audio</h3>
            

  
                <Info className="w-4 h-4 text-gray-400 cursor-pointer" />
              </div>

              <div className="mt-3 flex items-center space-x-2 text-sm text-gray-600">
                <Mic className="w-5 h-5 text-indigo-600" />
                <span>Deep Dive conversation</span>
              </div>
              <p className="text-xs text-gray-500 ml-7">2 hosts</p>

              <div className="mt-4 flex space-x-3">
                <button className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 transition">
                  Customize
                </button>
                <button
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 transition disabled:opacity-50"
                  onClick={handleGenerateSummary}
                  disabled={loading === 'summary' || selectedSourceIds.length === 0}
                >
                  {loading === 'summary' ? (
                    <Loader2 className="w-4 h-4 mr-1 animate-spin inline-block" />
                  ) : (
                    'Generate'
                  )}
                </button>
              </div>
            </div>

            {/* Notes */}
            <div className="mt-6">
              <div className="flex items-center justify-between mb-3 border-b pb-2">
                <h3 className="font-semibold text-lg text-gray-700">Notes</h3>
                <div className="flex space-x-2 text-gray-400">
                  <Maximize className="w-4 h-4 cursor-pointer hover:text-gray-600" />
                  <Minus className="w-4 h-4 cursor-pointer hover:text-gray-600" />
                </div>
              </div>

              <div className="space-y-2">
                {notes.map(note => (
                  <div
                    key={note.id}
                    className="text-sm p-2 rounded hover:bg-gray-50 border border-gray-200 text-gray-700"
                  >
                    {note.content}
                  </div>
                ))}
              </div>

              <div className="mt-4 space-y-3">
                <button className="w-full flex items-center justify-center p-3 rounded-xl border border-dashed border-indigo-300 text-indigo-600 bg-indigo-50 hover:bg-indigo-100 transition text-sm font-semibold">
                  <Plus className="w-4 h-4 mr-2" /> Add note
                </button>

                <div className="grid grid-cols-2 gap-3">
                  <button
  className="flex items-center justify-center p-3 rounded-lg bg-gray-100 text-gray-700 text-sm hover:bg-gray-200 border border-gray-300"
  onClick={handleGenerateQuiz}
>
  <BookOpen className="w-4 h-4 mr-2" /> Study guide
</button>

                  <button className="flex items-center justify-center p-3 rounded-lg bg-gray-100 text-gray-700 text-sm hover:bg-gray-200 border border-gray-300">
                    <FileText className="w-4 h-4 mr-2" /> Briefing doc
                  </button>
                  <button className="flex items-center justify-center p-3 rounded-lg bg-gray-100 text-gray-700 text-sm hover:bg-gray-200 border border-gray-300">
                    <Zap className="w-4 h-4 mr-2" /> FAQ
                  </button>
                  <button className="flex items-center justify-center p-3 rounded-lg bg-gray-100 text-gray-700 text-sm hover:bg-gray-200 border border-gray-300">
                    <Clock className="w-4 h-4 mr-2" /> Timeline
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
{showQuiz && (
  <QuizModal
    questions={quizData}
    onClose={() => setShowQuiz(false)}
  />
)}

      </div>
      
    </div>
  );
}
