import React, { useEffect, useMemo, useState } from 'react'
import { BookOpen, Settings, Download, CheckCircle, Clock, AlertCircle, PlayCircle, Calendar, FileText, X } from 'lucide-react'
import { useWeeks, useGeneration, useUsage, useDayFields } from '../hooks'
import api from '../api/client'
import type { Week } from '../types'

interface DayField {
  key: string
  label: string
}

export default function SteelDashboard() {
  const [selectedWeek, setSelectedWeek] = useState<Week | null>(null)
  const [showGenerator, setShowGenerator] = useState(false)
  const [fromWeek, setFromWeek] = useState(1)
  const [toWeek, setToWeek] = useState(1)

  // API Hooks - now actually connected to backend
  const { weeks, loading: weeksLoading, error: weeksError, reload: reloadWeeks, exportWeek: exportWeekAPI } = useWeeks()
  const { generating, progress, generateWeek, resetGeneration } = useGeneration()
  const { usage } = useUsage(generating, 3000)

  const dayFields = useMemo(() => ([
    { key: '01_class_name.txt', label: 'Class Name' },
    { key: '02_summary.md', label: 'Summary' },
    { key: '03_grade_level.txt', label: 'Grade Level' },
    { key: '04_role_context.json', label: 'Role Context' },
    { key: '05_guidelines_for_sparky.md', label: 'Guidelines for Sparky' },
    { key: '06_document_for_sparky.json', label: 'Document for Sparky' },
    { key: '07_sparkys_greeting.txt', label: "Sparky's Greeting" }
  ]), [])

  const startGeneration = async () => {
    if (generating) return
    try {
      // Generate the selected week range
      for (let week = fromWeek; week <= toWeek; week++) {
        await generateWeek(week)
      }
      // Reload weeks after generation completes
      await reloadWeeks()
    } catch (error) {
      console.error('Generation failed:', error)
    }
  }

  const handleExportWeek = async (week: Week) => {
    try {
      await exportWeekAPI(week.number)
      api.downloadWeek(week.number)
    } catch (error) {
      console.error('Export failed:', error)
      alert(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  const handleCloseGenerator = () => {
    setShowGenerator(false)
    resetGeneration()
  }

  // Calculate real stats from backend data
  const stats = useMemo(() => {
    const completedWeeks = weeks.filter(w => w.status === 'completed').length
    const totalFields = 35 * 4 * 7
    const completedFields = completedWeeks * 4 * 7
    const validatedWeeks = weeks.filter(w => w.validated).length
    const validationRate = completedWeeks > 0 ? Math.round((validatedWeeks / completedWeeks) * 100) : 0

    return {
      weeksCompleted: completedWeeks,
      fieldsCompleted: completedFields,
      totalFields,
      validationRate,
      readyToExport: validatedWeeks,
    }
  }, [weeks])

  useEffect(() => {
    return () => {
      resetGeneration()
    }
  }, [resetGeneration])

  useEffect(() => {
    if (!showGenerator) {
      resetGeneration()
    }
  }, [showGenerator, resetGeneration])

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-red-50">
      <header className="bg-white border-b border-amber-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-amber-600 to-red-600 rounded-lg grid place-items-center" aria-hidden>
              <BookOpen className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">STEEL</h1>
              <p className="text-xs text-gray-600">Latin A Curriculum Generator</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition">
              <Settings size={18} />
              <span className="text-sm">Settings</span>
            </button>
            <button onClick={() => setShowGenerator(true)} className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-amber-600 to-red-600 text-white rounded-lg hover:shadow-lg transition font-medium">
              <PlayCircle size={18} />
              Generate Curriculum
            </button>
          </div>
        </div>
      </header>

      {showGenerator && (
        <div className="fixed inset-0 bg-black/50 grid place-items-center z-50 p-4" role="dialog" aria-modal="true" aria-label="Generate Latin A Curriculum">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-8">
            <div className="flex items-start justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Generate Latin A Curriculum</h2>
              <button aria-label="Close" onClick={handleCloseGenerator} className="p-2 rounded-lg hover:bg-gray-100">
                <X size={18} />
              </button>
            </div>
            {!generating ? (
              <>
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Week Range</label>
                    <div className="flex items-center gap-4">
                      <input
                        type="number"
                        value={fromWeek}
                        onChange={(e) => setFromWeek(parseInt(e.target.value))}
                        min={1}
                        max={35}
                        className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                        aria-label="Start week"
                      />
                      <span className="text-gray-500">to</span>
                      <input
                        type="number"
                        value={toWeek}
                        onChange={(e) => setToWeek(parseInt(e.target.value))}
                        min={1}
                        max={35}
                        className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                        aria-label="End week"
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">35 weeks × 4 days × 7 fields = 980 total fields</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">AI Model</label>
                    <select className="w-full px-4 py-2 border border-gray-300 rounded-lg" aria-label="Model">
                      <option>GPT-4o (Recommended)</option>
                      <option>GPT-4 Turbo</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Pedagogical Settings</label>
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-2 text-sm">
                      <Row k="Recall requirement:" v="≥ 25%" />
                      <Row k="Spiral review:" v="Enabled" />
                      <Row k="Single tutor voice (Sparky):" v="Enforced" />
                    </div>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="text-blue-600 mt-0.5" size={20} />
                      <div className="text-sm text-blue-900">
                        <p className="font-medium">Estimated time: {(toWeek - fromWeek + 1) * 45}–{(toWeek - fromWeek + 1) * 60} minutes</p>
                        <p className="text-blue-700 mt-1">Estimated cost: ~${(toWeek - fromWeek + 1) * 12}–${(toWeek - fromWeek + 1) * 15} in API usage</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3 mt-8">
                  <button onClick={handleCloseGenerator} className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium">Cancel</button>
                  <button onClick={startGeneration} disabled={generating} className={`flex-1 px-6 py-3 rounded-lg hover:shadow-lg transition font-medium text-white ${generating ? 'bg-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-amber-600 to-red-600'}`}>
                    Start Generation
                  </button>
                </div>
              </>
            ) : (
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      {progress?.message || 'Generating...'}
                    </span>
                    <span className="text-sm text-gray-600">
                      {progress ? Math.round((progress.field / progress.totalFields) * 100) : 0}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden" aria-label="Progress">
                    <div
                      className="h-full bg-gradient-to-r from-amber-600 to-red-600 transition-all duration-300"
                      style={{ width: `${progress ? (progress.field / progress.totalFields) * 100 : 0}%` }}
                    />
                  </div>
                </div>
                <ul className="space-y-2 text-sm">
                  {progress?.status === 'completed' && (
                    <li className="flex items-center gap-3">
                      <CheckCircle className="text-green-600" size={18} />
                      <span className="text-gray-700">Week {progress.week} generated successfully!</span>
                    </li>
                  )}
                  {progress?.status === 'generating' && (
                    <li className="flex items-center gap-3">
                      <Clock className="text-blue-600 animate-spin" size={18} />
                      <span className="text-gray-700">{progress.message}</span>
                    </li>
                  )}
                  {progress?.status === 'error' && (
                    <li className="flex items-center gap-3">
                      <AlertCircle className="text-red-600" size={18} />
                      <span className="text-red-700">{progress.message}</span>
                    </li>
                  )}
                </ul>
                {usage && (
                  <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
                    <p className="font-medium mb-1">Live Stats</p>
                    <p className="font-mono text-xs">
                      Tokens: {usage.total_tokens?.toLocaleString() || 0} | Cost: ${usage.total_cost?.toFixed(2) || '0.00'}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8" aria-label="Stats">
          <Stat icon={<Calendar className="text-amber-600" size={32} />} label="Weeks Generated" value={`${stats.weeksCompleted}/35`} />
          <Stat icon={<FileText className="text-green-600" size={32} />} label="Fields Complete" value={<><span className="text-3xl font-bold text-gray-900">{stats.fieldsCompleted}</span><span className="block text-xs text-gray-500 mt-1">of {stats.totalFields} total</span></>} />
          <Stat icon={<CheckCircle className="text-blue-600" size={32} />} label="Validation Rate" value={`${stats.validationRate}%`} />
          <Stat icon={<Download className="text-purple-600" size={32} />} label="Ready to Export" value={stats.readyToExport.toString()} />
        </div>

        {weeksError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="text-red-600 mt-0.5" size={20} />
              <div>
                <p className="text-sm font-medium text-red-900">Backend Connection Error</p>
                <p className="text-sm text-red-700 mt-1">{weeksError}</p>
                <button onClick={reloadWeeks} className="mt-2 text-sm text-red-700 underline hover:text-red-800">
                  Retry Connection
                </button>
              </div>
            </div>
          </div>
        )}

        <section className="bg-white rounded-xl border border-gray-200 shadow-sm" aria-labelledby="overviewHeading">
          <div className="border-b border-gray-200 p-6 flex items-center justify-between">
            <h2 id="overviewHeading" className="text-xl font-bold text-gray-900">Curriculum Overview</h2>
            <div className="flex gap-2">
              <button onClick={reloadWeeks} className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition">
                Refresh
              </button>
            </div>
          </div>

          {weeksLoading ? (
            <div className="p-12 text-center">
              <Clock className="mx-auto text-gray-400 animate-spin mb-3" size={32} />
              <p className="text-gray-500">Loading curriculum data...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-6">
              {weeks.map(week => (
                <div key={week.number} className={`relative p-4 rounded-lg border-2 transition hover:shadow-md text-left hoverable cursor-pointer ${week.status === 'completed' ? 'border-green-200 bg-green-50 hover:border-green-300' : week.status === 'generating' ? 'border-blue-200 bg-blue-50 hover:border-blue-300' : 'border-gray-200 bg-gray-50 hover:border-gray-300'}`}>
                  <button onClick={() => setSelectedWeek(week)} className="absolute inset-0" aria-label={`Open Week ${week.number}`} />
                  <div className="relative z-10 pointer-events-none">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="text-xs font-medium text-gray-500">WEEK</p>
                        <p className="text-2xl font-bold text-gray-900">{week.number}</p>
                      </div>
                      {week.status === 'completed' && <CheckCircle className="text-green-600" size={20} />}
                      {week.status === 'generating' && <Clock className="text-blue-600 animate-spin" size={20} />}
                    </div>
                    <p className="text-sm font-medium text-gray-700 mb-1">{week.virtue}</p>
                    <p className="text-xs text-gray-500">{week.lessonsCount} lessons • 28 fields</p>
                    {week.validated && (
                      <div className="mt-2 pt-2 border-t border-gray-200">
                        <span className="text-xs text-green-700 font-medium">✓ All fields validated</span>
                      </div>
                    )}
                    {week.status === 'completed' && (
                      <div className="mt-3 flex justify-end pointer-events-auto">
                        <button
                          onClick={(e) => { e.stopPropagation(); handleExportWeek(week) }}
                          className="px-3 py-1.5 text-xs rounded-lg bg-amber-600 text-white inline-flex items-center gap-1 hover:bg-amber-700 transition"
                        >
                          <Download size={14} />
                          Export Week
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>

      {selectedWeek && <WeekDetailsModal weekNumber={selectedWeek.number} onClose={() => setSelectedWeek(null)} dayFields={dayFields} />}
    </div>
  )
}

interface WeekDetailsModalProps {
  weekNumber: number
  onClose: () => void
  dayFields: DayField[]
}

function WeekDetailsModal({ weekNumber, onClose, dayFields }: WeekDetailsModalProps) {
  const [activeDay, setActiveDay] = useState(1)
  const { day, loading } = useDayFields(weekNumber, activeDay)

  return (
    <div className="fixed inset-0 bg-black/50 grid place-items-center z-50 p-4" role="dialog" aria-modal="true" aria-label={`Week ${weekNumber} details`}>
      <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Week {weekNumber}</h2>
            <p className="text-sm text-gray-600 mt-1">4 lessons • 28 fields total</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                api.exportWeek(weekNumber).then(() => api.downloadWeek(weekNumber)).catch(console.error)
              }}
              className="px-3 py-2 rounded-lg bg-amber-600 text-white inline-flex items-center gap-2 hover:bg-amber-700 transition"
            >
              <Download size={16} />Export Week
            </button>
            <button aria-label="Close" onClick={onClose} className="text-gray-500 hover:text-gray-700 p-2">
              <X size={24} />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto hide-scrollbar">
          <div className="grid grid-cols-12">
            <div className="col-span-12 md:col-span-3 border-r border-gray-200 p-4 space-y-2">
              {[1, 2, 3, 4].map(dayNum => (
                <button
                  key={dayNum}
                  onClick={() => setActiveDay(dayNum)}
                  className={`w-full text-left px-4 py-3 rounded-lg transition ${dayNum === activeDay ? 'bg-amber-100 border-2 border-amber-300 text-amber-900' : 'bg-white border border-gray-200 hover:bg-gray-50'}`}
                  aria-pressed={dayNum === activeDay}
                >
                  <div className="text-xs text-gray-500">Day {dayNum}</div>
                  {day && dayNum === activeDay && (
                    <>
                      <div className="text-sm font-medium mt-1">{day.fieldsComplete}/{day.totalFields} fields</div>
                      {day.validated && <div className="text-xs text-green-700 font-medium mt-1">✓ Validated</div>}
                    </>
                  )}
                </button>
              ))}
            </div>
            <div className="col-span-12 md:col-span-9 p-6 space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">Day {activeDay} • All 7 Fields</h3>
              </div>
              {loading ? (
                <div className="text-center py-8">
                  <Clock className="mx-auto text-gray-400 animate-spin mb-3" size={32} />
                  <p className="text-gray-500">Loading day fields...</p>
                </div>
              ) : !day ? (
                <div className="text-center py-8">
                  <AlertCircle className="mx-auto text-gray-400 mb-3" size={32} />
                  <p className="text-gray-500">No data available for this day</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  {dayFields.map((field, idx) => {
                    const fieldValue = day?.fields[field.key]
                    const isJson = field.key.endsWith('.json')
                    const displayValue = fieldValue
                      ? (isJson && typeof fieldValue === 'object'
                          ? JSON.stringify(fieldValue, null, 2)
                          : fieldValue)
                      : null

                    return (
                      <article key={field.key} className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-amber-200 transition">
                        <header className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-900 grid place-items-center font-bold text-sm" aria-hidden>{idx + 1}</div>
                            <div>
                              <h4 className="font-bold text-gray-900">{field.label}</h4>
                              <p className="text-xs text-gray-500 font-mono mt-0.5">{field.key}</p>
                            </div>
                          </div>
                          {fieldValue && (
                            <span className="text-xs text-green-700 font-medium">✓ Generated</span>
                          )}
                        </header>
                        <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-4 max-h-64 overflow-y-auto">
                          {displayValue ? (
                            <p className="text-sm text-gray-700 whitespace-pre-wrap font-mono">{displayValue}</p>
                          ) : (
                            <p className="text-sm text-gray-400 italic">Not yet generated</p>
                          )}
                        </div>
                      </article>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

interface StatProps {
  icon: React.ReactNode
  label: string
  value: React.ReactNode
}

function Stat({ icon, label, value }: StatProps) {
  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{label}</p>
          <div className="mt-1 text-3xl font-bold text-gray-900">{value}</div>
        </div>
        {icon}
      </div>
    </div>
  )
}

interface RowProps {
  k: string
  v: string
}

function Row({ k, v }: RowProps) {
  return (
    <div className="flex items-center justify-between"><span>{k}</span><span className="font-medium">{v}</span></div>
  )
}
