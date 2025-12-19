import { useState } from "react";

interface VoiceRecorderProps {
  onResult: (text: string) => void;
}

export default function VoiceRecorder({ onResult }: VoiceRecorderProps) {
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    let audioChunks: Blob[] = [];

    recorder.ondataavailable = (e) => audioChunks.push(e.data);

    recorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      const formData = new FormData();
      formData.append("file", audioBlob, "audio.webm");

      const res = await fetch("http://localhost:5000/transcribe", {
        method: "POST",
        body: formData
      });

      const data = await res.json();
      onResult(data.text); // renvoie vers App
    };

    recorder.start();
    setMediaRecorder(recorder);
    setRecording(true);
  };

  const stopRecording = () => {
    mediaRecorder?.stop();
    setRecording(false);
  };

  return (
    <button
      onClick={recording ? stopRecording : startRecording}
      className="px-4 py-2 rounded-md bg-indigo-600 text-white"
    >
      {recording ? "🎙 Stop" : "Talk"}
    </button>
  );
}
