// React hooks for curriculum generation
import { useState, useCallback } from 'react'
import api from '../api/client'
import type { WeekHydrationResult, GenerationProgress } from '../types'

export function useGeneration() {
  const [generating, setGenerating] = useState(false)
  const [progress, setProgress] = useState<GenerationProgress | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<WeekHydrationResult | null>(null)

  const generateWeek = useCallback(async (weekNumber: number) => {
    setGenerating(true)
    setError(null)
    setProgress({
      week: weekNumber,
      day: 1,
      field: 0,
      totalFields: 28, // 7 fields × 4 days
      status: 'generating',
      message: `Starting generation for Week ${weekNumber}...`,
    })

    try {
      const result = await api.hydrateWeek(weekNumber)

      setProgress({
        week: weekNumber,
        day: 4,
        field: 28,
        totalFields: 28,
        status: 'completed',
        message: 'Generation completed successfully!',
      })

      setResult(result)
      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Generation failed'
      setError(errorMessage)
      setProgress({
        week: weekNumber,
        day: 0,
        field: 0,
        totalFields: 28,
        status: 'error',
        message: errorMessage,
      })
      throw err
    } finally {
      setGenerating(false)
    }
  }, [])

  const generateWeekRange = useCallback(async (fromWeek: number, toWeek: number) => {
    const results: WeekHydrationResult[] = []

    for (let week = fromWeek; week <= toWeek; week++) {
      try {
        const result = await generateWeek(week)
        results.push(result)
      } catch (err) {
        // Continue with next week even if this one fails
        console.error(`Week ${week} generation failed:`, err)
      }
    }

    return results
  }, [generateWeek])

  const resetGeneration = useCallback(() => {
    setGenerating(false)
    setProgress(null)
    setError(null)
    setResult(null)
  }, [])

  return {
    generating,
    progress,
    error,
    result,
    generateWeek,
    generateWeekRange,
    resetGeneration,
  }
}
