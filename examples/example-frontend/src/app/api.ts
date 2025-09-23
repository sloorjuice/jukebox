export interface SongResponse {
  status: string;
  song: string;
  author: string;
}

export interface QueueSong {
  name: string;
  author: string;
  duration: number;
}

export interface CurrentSong {
  name: string;
  author: string;
  duration: number;
  url: string;
  played_at: string;
  active: boolean;
}

export interface SkipResponse {
  status: string;
}

export interface PauseResponse {
  status: string;
}

export async function sendPrompt(prompt: string): Promise<SongResponse> {
  const apiUrl = `http://${window.location.hostname}:8000/request_song`;
  const res = await fetch(apiUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: prompt }),
  });
  if (!res.ok) throw new Error("API error");
  return res.json();
}

export async function skipSong(): Promise<SkipResponse> {
  const apiUrl = `http://${window.location.hostname}:8000/skip`;
  const res = await fetch(apiUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("API error");
  return res.json();
}

export async function pauseSong(): Promise<PauseResponse> {
  const apiUrl = `http://${window.location.hostname}:8000/pauseToggle`;
  const res = await fetch(apiUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("API error");
  return res.json();
}

export async function fetchCurrentSong(): Promise<CurrentSong | null> {
  const apiUrl = `http://${window.location.hostname}:8000/currentlyPlayingSong`;
  const res = await fetch(apiUrl);
  if (!res.ok) throw new Error("Failed to fetch current song");
  const data = await res.json();
  if (!data || !data.name) return null; // <-- Fix: check for null or missing name
  return data;
}

export async function fetchQueue(): Promise<QueueSong[]> {
  const apiUrl = `http://${window.location.hostname}:8000/queue`;
  const res = await fetch(apiUrl);
  if (!res.ok) throw new Error("Failed to fetch the queue");
  return res.json();
}

