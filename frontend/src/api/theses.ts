import { api } from "./client";

export type ThesisDifficulty = "bachelor" | "master" | "phd";

export interface SkillsRequired {
  programming: string[];
  math: string[];
  theory: string[];
  domain: string[];
  other: string[];
}

export interface Thesis {
  id: number;
  title: string;
  abstract: string;
  chair_id: number | null;
  supervisor_id: number | null;
  submitter_id: number;
  source: "professor" | "student" | "openalex";
  difficulty: ThesisDifficulty | null;
  skills_required: SkillsRequired | null;
  generated_for_user_id: number | null;
  chat_session_id: number | null;
  created_at: string;
}

export interface ThesisCreate {
  title: string;
  abstract: string;
  chair_id?: number | null;
  supervisor_id?: number | null;
}

export function listTheses(limit = 50, offset = 0): Promise<Thesis[]> {
  return api<Thesis[]>(`/api/theses?limit=${limit}&offset=${offset}`);
}

export function getThesis(id: number): Promise<Thesis> {
  return api<Thesis>(`/api/theses/${id}`);
}

export function createThesis(body: ThesisCreate): Promise<Thesis> {
  return api<Thesis>("/api/theses", { method: "POST", json: body });
}

export function listMyProposals(): Promise<Thesis[]> {
  return api<Thesis[]>("/api/proposals/mine");
}
