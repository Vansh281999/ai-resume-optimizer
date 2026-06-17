import { useState } from 'react';
import {
  AtsScoreResponse,
  CareerRoadmapResponse,
  generateInterview,
  getCareerRoadmap,
  getTrends,
  InterviewResponse,
  JobMatchResponse,
  matchJob,
  scoreResume,
  uploadResume,
} from '../lib/api';
import { getErrorMessage } from '../lib/utils';

export interface MutationState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

export function createEmptyMutationState<T>(): MutationState<T> {
  return {
    data: null,
    error: null,
    loading: false,
  };
}

export function useTrendsQuery() {
  const [state, setState] = useState<MutationState<Awaited<ReturnType<typeof getTrends>>>>({
    data: null,
    error: null,
    loading: false,
  });

  const run = async () => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const data = await getTrends();
      setState({ data, error: null, loading: false });
    } catch (error) {
      setState({ data: null, error: getErrorMessage(error), loading: false });
    }
  };

  return { ...state, refetch: run };
}

export function useAtsScoreMutation() {
  const [state, setState] = useState<MutationState<AtsScoreResponse>>(createEmptyMutationState());

  const submit = async (resumeText: string, file: File | null, keywords: string[]) => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      let data: AtsScoreResponse;
      if (file && resumeText.trim()) {
        data = await uploadResume(file, resumeText, keywords);
      } else if (file) {
        data = await uploadResume(file, undefined, keywords);
      } else {
        data = await scoreResume(resumeText, keywords);
      }
      setState({ data, error: null, loading: false });
    } catch (error) {
      setState({ data: null, error: getErrorMessage(error), loading: false });
    }
  };

  return { ...state, submit };
}

export function useJobMatchMutation() {
  const [state, setState] = useState<MutationState<JobMatchResponse>>(createEmptyMutationState());

  const submit = async (resumeText: string, jobDescription: string, keywords: string[]) => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const data = await matchJob(resumeText, jobDescription, keywords);
      setState({ data, error: null, loading: false });
    } catch (error) {
      setState({ data: null, error: getErrorMessage(error), loading: false });
    }
  };

  return { ...state, submit };
}

export function useInterviewMutation() {
  const [state, setState] = useState<MutationState<InterviewResponse>>(createEmptyMutationState());

  const submit = async (company: string, role: string, jobDescription: string) => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const data = await generateInterview(company, role, jobDescription);
      setState({ data, error: null, loading: false });
    } catch (error) {
      setState({ data: null, error: getErrorMessage(error), loading: false });
    }
  };

  return { ...state, submit };
}

export function useCareerRoadmapMutation() {
  const [state, setState] = useState<MutationState<CareerRoadmapResponse>>(createEmptyMutationState());

  const submit = async (currentSkills: string[], targetRole: string, context: string) => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const data = await getCareerRoadmap(currentSkills, targetRole, context);
      setState({ data, error: null, loading: false });
    } catch (error) {
      setState({ data: null, error: getErrorMessage(error), loading: false });
    }
  };

  return { ...state, submit };
}
