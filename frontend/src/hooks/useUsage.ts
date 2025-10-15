// React hooks for usage tracking
import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import type { UsageStats } from '../types'

export function useUsage(autoRefresh = false, refreshInterval = 5000) {
  const [usage, setUsage] = useState<UsageStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadUsage = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const data = await api.getUsage()
      setUsage(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load usage stats')
    } finally {
      setLoading(false)
    }
  }, [])

  const resetUsage = useCallback(async () => {
    try {
      await api.resetUsage()
      await loadUsage()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset usage stats')
      throw err
    }
  }, [loadUsage])

  useEffect(() => {
    loadUsage()
  }, [loadUsage])

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(loadUsage, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval, loadUsage])

  return {
    usage,
    loading,
    error,
    reload: loadUsage,
    reset: resetUsage,
  }
}
