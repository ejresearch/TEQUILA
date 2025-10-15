// React hooks for weeks data management
import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import type { Week, ValidationResult } from '../types'

export function useWeeks() {
  const [weeks, setWeeks] = useState<Week[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Generate weeks data - lightweight initial load
  const loadWeeks = useCallback(async () => {
    console.log('Loading weeks...')
    setLoading(true)
    setError(null)

    const virtues = ['Courage', 'Wisdom', 'Justice', 'Temperance', 'Faith', 'Hope', 'Charity']
    const generatedWeeks: Week[] = []

    try {
      // Quick health check - just try to get Week 1
      console.log('Checking backend connection...')
      await api.getCompiledWeekSpec(1)
      console.log('Backend connected! Week 1 exists.')

      // Week 1 exists, so check a few more
      const existingWeeks = new Set<number>([1])

      // Check weeks 2-12 in parallel (much faster)
      const checkPromises = []
      for (let i = 2; i <= 12; i++) {
        checkPromises.push(
          api.getCompiledWeekSpec(i)
            .then(() => existingWeeks.add(i))
            .catch(() => {}) // Ignore errors for non-existent weeks
        )
      }
      await Promise.all(checkPromises)

      console.log(`Found ${existingWeeks.size} existing weeks`)

      // Generate all 35 weeks
      for (let i = 1; i <= 35; i++) {
        generatedWeeks.push({
          number: i,
          virtue: virtues[(i - 1) % 7],
          status: existingWeeks.has(i) ? 'completed' : 'pending',
          lessonsCount: 4,
          validated: existingWeeks.has(i), // Assume completed = validated for now
        })
      }

      setWeeks(generatedWeeks)
      console.log('Weeks loaded successfully')
    } catch (err) {
      // Backend not running or Week 1 doesn't exist - show all pending
      console.warn('Backend not available or no weeks generated yet:', err)

      for (let i = 1; i <= 35; i++) {
        generatedWeeks.push({
          number: i,
          virtue: virtues[(i - 1) % 7],
          status: 'pending',
          lessonsCount: 4,
          validated: false,
        })
      }
      setWeeks(generatedWeeks)
    } finally {
      setLoading(false)
    }
  }, [])

  const validateWeek = useCallback(async (weekNumber: number): Promise<ValidationResult | null> => {
    try {
      const result = await api.validateWeek(weekNumber)

      // Update local state
      setWeeks(prev => prev.map(w =>
        w.number === weekNumber
          ? { ...w, validated: result.is_valid }
          : w
      ))

      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed')
      return null
    }
  }, [])

  const exportWeek = useCallback(async (weekNumber: number) => {
    try {
      const result = await api.exportWeek(weekNumber)
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed')
      throw err
    }
  }, [])

  useEffect(() => {
    loadWeeks()
  }, [loadWeeks])

  return {
    weeks,
    loading,
    error,
    reload: loadWeeks,
    validateWeek,
    exportWeek,
  }
}
