export interface Job {
  id: string;
  source: string;
  title: string;
  company: string;
  location: string;
  remote: boolean;
  salary_min: number;
  salary_max: number;
  match_score: number;
  score_breakdown: Record<string, unknown>;
  required_skills: string[];
  apply_url: string;
  analyzed: boolean;
  created_at: string;
}

export interface Application {
  id: string;
  job_id: string;
  status: string;
  submitted_at: string | null;
  confirmation: string;
  error: string;
  needs_review_reason: string;
  created_at: string;
}

export interface Analytics {
  applications_today: number;
  applications_week: number;
  total_applications: number;
  interview_rate: number;
  response_rate: number;
  offer_rate: number;
  by_status: Record<string, number>;
  by_source: Record<string, number>;
}

export interface Resume {
  id: string;
  job_id: string | null;
  variant: string;
  version: number;
  pdf_path: string;
  docx_path: string;
  sends: number;
  responses: number;
  interviews: number;
  created_at: string;
}

export interface CoverLetter {
  id: string;
  job_id: string | null;
  content: string;
  created_at: string;
}

export interface Recruiter {
  id: string;
  name: string;
  title: string;
  company: string;
  email: string;
  linkedin_url: string;
  source: string;
}

export interface Message {
  id: string;
  recruiter_id: string;
  channel: string;
  sequence_step: number;
  subject: string;
  body: string;
  status: string;
  sent_at: string | null;
  created_at: string;
}

export interface Profile {
  master_resume: string;
  phone: string;
  location: string;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
  skills: string[];
  preferred_roles: string[];
  preferred_locations: string[];
  min_salary: number;
  remote_only: boolean;
  years_experience: number;
}
