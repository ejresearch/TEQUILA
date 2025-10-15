// React hooks for day fields management
import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import type { Day } from '../types'

const DAY_FIELDS = [
  { key: '01_class_name.txt', label: 'Class Name' },
  { key: '02_summary.md', label: 'Summary' },
  { key: '03_grade_level.txt', label: 'Grade Level' },
  { key: '04_role_context.json', label: 'Role Context' },
  { key: '05_guidelines_for_sparky.md', label: 'Guidelines for Sparky' },
  { key: '06_document_for_sparky.json', label: 'Document for Sparky' },
  { key: '07_sparkys_greeting.txt', label: "Sparky's Greeting" },
]

export function useDayFields(weekNumber: number, dayNumber: number) {
  const [day, setDay] = useState<Day | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadDay = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      // Load all fields for the day
      const fieldsData: Record<string, any> = {}
      let completedFields = 0

      for (const field of DAY_FIELDS) {
        try {
          const result = await api.getDayField(weekNumber, dayNumber, field.key)
          fieldsData[field.key] = result.content
          if (result.content && result.content !== '') {
            completedFields++
          }
        } catch (err) {
          // Field doesn't exist yet
          fieldsData[field.key] = ''
        }
      }

      setDay({
        day: dayNumber,
        fields: fieldsData,
        validated: completedFields === DAY_FIELDS.length,
        fieldsComplete: completedFields,
        totalFields: DAY_FIELDS.length,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load day fields')
    } finally {
      setLoading(false)
    }
  }, [weekNumber, dayNumber])

  const updateField = useCallback(async (fieldKey: string, content: any) => {
    try {
      await api.updateDayField(weekNumber, dayNumber, fieldKey, content)
      await loadDay() // Reload to get updated data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update field')
      throw err
    }
  }, [weekNumber, dayNumber, loadDay])

  useEffect(() => {
    loadDay()
  }, [loadDay])

  return {
    day,
    loading,
    error,
    reload: loadDay,
    updateField,
    fieldDefinitions: DAY_FIELDS,
  }
}
