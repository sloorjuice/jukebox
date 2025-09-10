"use client";
import { useState, useEffect } from "react";
import { sendPrompt, fetchCurrentSong, fetchQueue, skipSong, pauseSong } from "./api";
import type { SongResponse, QueueSong, CurrentSong } from "./api";

export default function Home() {
  const [currentSong, setCurrentSong] = useState<CurrentSong | null>(null);
  const [searchPrompt, setSearchPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<SongResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [queue, setQueue] = useState<QueueSong[]>([]);
  const [skipLoading, setSkipLoading] = useState(false);
  const [pauseLoading, setPauseLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchPrompt(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResponse(null);
    setError(null);

    try {
      const data = await sendPrompt(searchPrompt);
      setResponse(data);
    } catch (err) {
      if (err instanceof Error) {
        setError("Error contacting API: " + err.message);
      } else {
        setError("Error contacting API: Unknown error");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = async () => {
    setSkipLoading(true);
    setError(null);
    try {
      await skipSong();
      // Optionally refresh current song and queue immediately
      const [song, queueData] = await Promise.all([fetchCurrentSong(), fetchQueue()]);
      setCurrentSong(song);
      setQueue(Array.isArray(queueData) ? queueData : []);
    } catch (err) {
      setError("Error skipping song.");
    } finally {
      setSkipLoading(false);
    }
  };

  const handlePause = async () => {
    setPauseLoading(true);
    setError(null);
    try {
      await pauseSong();
      // Optionally refresh current song and queue immediately
      const [song, queueData] = await Promise.all([fetchCurrentSong(), fetchQueue()]);
      setCurrentSong(song);
      setQueue(Array.isArray(queueData) ? queueData : []);
    } catch (err) {
      setError("Error pausing song.");
    } finally {
      setPauseLoading(false);
    }
  };

  // Fetch current song and queue on mount and every 5 seconds
  useEffect(() => {
    const getSong = async () => {
      try {
        const song = await fetchCurrentSong();
        setCurrentSong(song);
      } catch (err) {
        setError("Could not fetch current song.");
        console.error("Error fetching current song:", err);
      }
    };
    const getQueue = async () => {
      try {
        const queueData = await fetchQueue();
        setQueue(Array.isArray(queueData) ? queueData : []);
      } catch (err) {
        setError("Could not fetch queue.");
        console.error("Error fetching queue:", err);
      }
    };
    getSong();
    getQueue();
    const interval = setInterval(() => {
      getSong();
      getQueue();
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center font-sans">
      <h1 className="text-6xl font-bold mb-8">Jukebox Controller</h1>
      <p className="text-lg mb-4">
        Current Song:{" "}
        {currentSong ? (
          <span>
            <span className="font-semibold">{currentSong.name}</span> by{" "}
            <span className="italic">{currentSong.author}</span>
            {" "}
            <span className="text-gray-400 text-xs">
              ({Math.floor(currentSong.duration / 60)}:{(currentSong.duration % 60).toString().padStart(2, "0")})
            </span>
            {" "}
            <a
              href={currentSong.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-300 underline ml-2"
            >
              Link
            </a>
          </span>
        ) : (
          "None"
        )}
      </p>
      <input
        type="text"
        value={searchPrompt}
        onChange={handleChange}
        placeholder="Enter text"
        className="border rounded px-4 py-2 mb-4 w-full max-w-md"
      />

      {/* Centered Play Song button */}
      <div className="flex justify-center mb-4 w-full">
        <button
          className={`px-6 py-2 rounded font-semibold transition text-lg shadow
            ${loading
              ? "bg-blue-300 text-white cursor-not-allowed"
              : "bg-blue-500 text-white hover:bg-blue-600"}
          `}
          onClick={handleSubmit}
          disabled={loading}
          style={{ minWidth: 140 }}
        >
          {loading ? "Loading..." : "Play Song!"}
        </button>
      </div>

      {/* Pause/Play and Skip buttons side-by-side */}
      <div className="flex gap-4 justify-center mb-4 w-full">
        <button
          className={`px-4 py-2 rounded font-semibold transition text-base shadow
            ${!currentSong || pauseLoading
              ? "bg-gray-400 text-white cursor-not-allowed"
              : "bg-yellow-500 text-white hover:bg-yellow-600 cursor-pointer"}
          `}
          onClick={handlePause}
          disabled={!currentSong || pauseLoading}
          style={{ minWidth: 110 }}
        >
          {pauseLoading ? "Pausing..." : "Pause / Play"}
        </button>
        <button
          className={`px-4 py-2 rounded font-semibold transition text-base shadow
            ${!currentSong || skipLoading
              ? "bg-gray-400 text-white cursor-not-allowed"
              : "bg-red-500 text-white hover:bg-red-600 cursor-pointer"}
          `}
          onClick={handleSkip}
          disabled={!currentSong || skipLoading}
          style={{ minWidth: 110 }}
        >
          {skipLoading ? "Skipping..." : "Skip"}
        </button>
      </div>

      {response && (
        <div className="mt-4">
          <div>Status: {response.status}</div>
          <div>Song: {response.song}</div>
          <div>Author: {response.author}</div>
        </div>
      )}
      {error && <div className="mt-4 text-red-500">{error}</div>}

      {/* Queue display */}
      <div className="mt-8 w-full max-w-md bg-gray-600 rounded-lg shadow p-4">
        <h2 className="text-xl font-semibold mb-2 text-center">Queue</h2>
        {queue.length === 0 ? (
          <div className="text-gray-300 text-center">Queue is empty</div>
        ) : (
          <ul className="divide-y divide-gray-900">
            {queue.map((song, idx) => (
              <li key={idx} className="py-2 px-2 hover:bg-gray-200 rounded transition flex flex-col sm:flex-row sm:justify-between">
                <span className="font-medium">{song.name}</span>
                <span className="text-gray-300 text-sm">{song.author}</span>
                <span className="text-gray-400 text-xs">{Math.floor(song.duration / 60)}:{(song.duration % 60).toString().padStart(2, "0")}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
