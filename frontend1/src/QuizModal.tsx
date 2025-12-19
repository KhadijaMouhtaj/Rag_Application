import React, { useState } from "react";
import { X, ChevronDown } from "lucide-react";

interface QuizQuestion {
  question: string;
  choices: string[];
  answer: number;
  explanation?: string;
}

interface QuizModalProps {
  questions: QuizQuestion[];
  onClose: () => void;
}

export default function QuizModal({ questions, onClose }: QuizModalProps) {
  const [current, setCurrent] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [userAnswers, setUserAnswers] = useState<(number | null)[]>(
    new Array(questions.length).fill(null)
  ); // ✅ Stocker toutes les réponses
  const [showHint, setShowHint] = useState(false);
  const [finished, setFinished] = useState(false);

  const q = questions[current];

  // ✅ Calculer le score dynamiquement
  const calculateScore = () => {
    return userAnswers.filter(
      (answer, index) => answer === questions[index].answer
    ).length;
  };

  const handleNext = () => {
    // ✅ Enregistrer la réponse de l'utilisateur
    const newAnswers = [...userAnswers];
    newAnswers[current] = selected;
    setUserAnswers(newAnswers);

    if (current === questions.length - 1) {
      setFinished(true);
    } else {
      setCurrent(current + 1);
      setSelected(userAnswers[current + 1]); // ✅ Restaurer la réponse si l'utilisateur revient
      setShowHint(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 backdrop-blur-sm flex justify-center items-center z-50">
      <div className="bg-white w-[70%] max-h-[90%] overflow-auto rounded-2xl shadow-xl p-8 relative">
        
        {/* Close button */}
        <button
          className="absolute top-4 right-4 text-gray-500 hover:text-black"
          onClick={onClose}
        >
          <X size={24} />
        </button>

        {/* TITLE */}
        <h2 className="text-3xl font-bold mb-1">Virtualisation Quiz</h2>
        <p className="text-gray-500 mb-6">D'après {questions.length} source(s)</p>

        {/* END RESULT */}
        {finished ? (
          <div className="text-center py-10">
            <h3 className="text-2xl font-bold mb-4">Résultats</h3>
            <p className="text-xl mb-6">
              Score : <span className="font-bold text-indigo-600">{calculateScore()}</span> / {questions.length}
            </p>

            {/* ✅ BONUS : Afficher le détail des réponses */}
            <div className="text-left max-w-2xl mx-auto space-y-4 mb-6">
              {questions.map((question, idx) => {
                const userAnswer = userAnswers[idx];
                const isCorrect = userAnswer === question.answer;
                
                return (
                  <div key={idx} className={`p-4 rounded-xl border ${
                    isCorrect ? "bg-green-50 border-green-300" : "bg-red-50 border-red-300"
                  }`}>
                    <p className="font-semibold mb-2">
                      {idx + 1}. {question.question}
                    </p>
                    <p className="text-sm">
                      Votre réponse : <span className={isCorrect ? "text-green-700" : "text-red-700"}>
                        {userAnswer !== null ? question.choices[userAnswer] : "Non répondu"}
                      </span> {isCorrect ? "✅" : "❌"}
                    </p>
                    {!isCorrect && (
                      <p className="text-sm text-green-700 mt-1">
                        Bonne réponse : {question.choices[question.answer]}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>

            <button
              className="mt-6 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-semibold"
              onClick={onClose}
            >
              Fermer
            </button>
          </div>
        ) : (
          <>
            {/* PROGRESS */}
            <div className="mb-4">
              <p className="text-sm text-gray-500">
                Question {current + 1} / {questions.length}
              </p>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-indigo-600 h-2 rounded-full transition-all"
                  style={{ width: `${((current + 1) / questions.length) * 100}%` }}
                />
              </div>
            </div>

            {/* QUESTION */}
            <h3 className="text-xl font-semibold mb-4">{q.question}</h3>

            {/* CHOICES */}
            <div className="space-y-3 mb-6">
              {q.choices.map((choice, idx) => (
                <div
                  key={idx}
                  onClick={() => setSelected(idx)}
                  className={`p-4 rounded-xl cursor-pointer border transition ${
                    selected === idx
                      ? "bg-indigo-100 border-indigo-400"
                      : "bg-gray-50 hover:bg-gray-100 border-gray-300"
                  }`}
                >
                  <span className="font-bold mr-2">
                    {String.fromCharCode(65 + idx)}.
                  </span>
                  {choice}
                </div>
              ))}
            </div>

            {/* HINT */}
            <div className="mb-4">
              <button
                className="flex items-center text-gray-600 hover:text-gray-800"
                onClick={() => setShowHint(!showHint)}
              >
                Indice <ChevronDown className="ml-1 w-4 h-4" />
              </button>

              {showHint && q.explanation && (
                <div className="mt-2 p-3 bg-gray-100 text-sm rounded-xl">
                  {q.explanation}
                </div>
              )}
            </div>

            {/* NEXT BUTTON */}
            <button
              onClick={handleNext}
              className={`px-6 py-2 rounded-xl font-semibold float-right transition ${
                selected === null
                  ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                  : "bg-indigo-600 text-white hover:bg-indigo-700"
              }`}
              disabled={selected === null}
            >
              {current === questions.length - 1 ? "Terminer" : "Suivante"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}