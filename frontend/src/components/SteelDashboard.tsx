import React, { useEffect, useMemo, useRef, useState } from 'react'
import { BookOpen, Settings, Download, CheckCircle, Clock, AlertCircle, PlayCircle, Calendar, FileText, Edit, X } from 'lucide-react'

export default function SteelDashboard() {
  const [activePage, setActivePage] = useState('dashboard')
  const [selectedWeek, setSelectedWeek] = useState(null)
  const [activeDay, setActiveDay] = useState(1)
  const [showGenerator, setShowGenerator] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [progress, setProgress] = useState(0)
  const intervalRef = useRef(null)

  const dayFields = useMemo(() => ([
    { key: 'class_name', label: 'Class Name', sample: 'Latin A • Week 11 • Day 1' },
    { key: 'summary', label: 'Summary', sample: 'First-declension review with 30% spiral recall and 4 short translations.' },
    { key: 'grade_level', label: 'Grade Level', sample: 'Grade 3–5' },
    { key: 'guidelines_for_sparky', label: 'Guidelines for Sparky', sample: 'Keep tone warm, rhythmic; enforce recall ≥25%; one tutor voice; scaffold mistakes.' },
    { key: 'document_for_sparky', label: 'Document for Sparky (JSON)', sample: '{"target":"Day1","vocab":["agricola","terra","aqua"],"grammar":"1st declension","recall":"30%"}' },
    { key: 'sparkys_greeting', label: "Sparky's Greeting", sample: "Salvete, amici! Open your notebook—we'll warm up with our chant, then try two tiny translations." },
    { key: 'assessment_or_quiz', label: 'Assessment / Quiz', sample: "2-item exit ticket: decline *puella*; translate 'Puella aquam portat.'" }
  ]), [])

  const weeks = useMemo(() => Array.from({ length: 35 }, (_, i) => ({
    number: i + 1,
    virtue: ['Courage', 'Wisdom', 'Justice', 'Temperance', 'Faith', 'Hope', 'Charity'][i % 7],
    status: i < 12 ? 'completed' : i === 12 ? 'generating' : 'pending',
    lessonsCount: 4,
    validated: i < 12
  })), [])

  const startGeneration = () => {
    if (generating) return
    setGenerating(true)
    setProgress(0)
    intervalRef.current = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(intervalRef.current)
          intervalRef.current = null
          setGenerating(false)
          return 100
        }
        return prev + 2
      })
    }, 100)
  }

  const download = (filename, data) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  const exportWeek = (week) => {
    const days = [1, 2, 3, 4].map(d => ({
      day: d,
      fields: Object.fromEntries(dayFields.map(f => [f.key, f.sample]))
    }))
    const payload = { week: week.number, virtue: week.virtue, days }
    download(`steel-week-${week.number}.json`, payload)
  }

  const exportField = (week, day, field) => {
    const payload = { week: week.number, day, key: field.key, label: field.label, value: field.sample }
    download(`steel-week-${week.number}-day-${day}-${field.key}.json`, payload)
  }

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    if (!showGenerator && intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
      setGenerating(false)
    }
  }, [showGenerator])

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
            <button className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition" onClick={() => setActivePage('dashboard')}>
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
              <button aria-label="Close" onClick={() => setShowGenerator(false)} className="p-2 rounded-lg hover:bg-gray-100">
                <X size={18} />
              </button>
            </div>
            {!generating ? (
              <>
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Week Range</label>
                    <div className="flex items-center gap-4">
                      <input type="number" defaultValue={1} min={1} max={35} className="w-24 px-3 py-2 border border-gray-300 rounded-lg m_468e7eda" aria-label="Start week" />
                      <span className="text-gray-500">to</span>
                      <input type="number" defaultValue={35} min={1} max={35} className="w-24 px-3 py-2 border border-gray-300 rounded-lg m_468e7eda" aria-label="End week" />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">35 weeks × 4 days × 7 fields = 980 total fields</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">AI Model</label>
                    <select className="w-full px-4 py-2 border border-gray-300 rounded-lg" aria-label="Model">
                      <option>GPT-4o (Recommended)</option>
                      <option>GPT-4 Turbo</option>
                      <option>Claude Sonnet 4</option>
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
                        <p className="font-medium">Estimated time: 45–60 minutes</p>
                        <p className="text-blue-700 mt-1">Estimated cost: ~$12–15 in API usage</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3 mt-8">
                  <button onClick={() => setShowGenerator(false)} className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium">Cancel</button>
                  <button onClick={startGeneration} disabled={generating} className={`flex-1 px-6 py-3 rounded-lg hover:shadow-lg transition font-medium text-white ${generating ? 'bg-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-amber-600 to-red-600'}`}>Start Generation</button>
                </div>
              </>
            ) : (
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Generating Week 13, Day 2, Field 4/7</span>
                    <span className="text-sm text-gray-600">{progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden" aria-label="Progress">
                    <div className="h-full bg-gradient-to-r from-amber-600 to-red-600 transition-all duration-300" style={{ width: `${progress}%` }} />
                  </div>
                </div>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center gap-3"><CheckCircle className="text-green-600" size={18} /><span className="text-gray-700">Week 12 validated successfully</span></li>
                  <li className="flex items-center gap-3"><Clock className="text-blue-600 animate-spin" size={18} /><span className="text-gray-700">Generating <code className="font-mono">guidelines_for_sparky</code> (attempt 1/10)</span></li>
                  <li className="flex items-center gap-3"><CheckCircle className="text-green-600" size={18} /><span className="text-gray-700">✓ Recall requirement met (28% prior content)</span></li>
                </ul>
                <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
                  <p className="font-medium mb-1">Generation Log</p>
                  <p className="font-mono text-xs">Tokens used: 45,239 | Est. remaining: 12 minutes</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8" aria-label="Stats">
          <Stat icon={<Calendar className="text-amber-600" size={32} />} label="Weeks Generated" value="12/35" />
          <Stat icon={<FileText className="text-green-600" size={32} />} label="Fields Complete" value={<><span className="text-3xl font-bold text-gray-900">336</span><span className="block text-xs text-gray-500 mt-1">of 980 total</span></>} />
          <Stat icon={<CheckCircle className="text-blue-600" size={32} />} label="Validation Rate" value="94%" />
          <Stat icon={<Download className="text-purple-600" size={32} />} label="Ready to Export" value="12" />
        </div>
        <section className="bg-white rounded-xl border border-gray-200 shadow-sm" aria-labelledby="overviewHeading">
          <div className="border-b border-gray-200 p-6 flex items-center justify-between">
            <h2 id="overviewHeading" className="text-xl font-bold text-gray-900">Curriculum Overview</h2>
            <div className="flex gap-2">
              <button className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition">Filter</button>
              <button className="px-4 py-2 text-sm bg-amber-100 text-amber-900 rounded-lg hover:bg-amber-200 transition flex items-center gap-2">
                <Download size={16} />
                Export All
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-6">
            {weeks.map(week => (
              <div key={week.number} className={`relative p-4 rounded-lg border-2 transition hover:shadow-md text-left hoverable ${week.status === 'completed' ? 'border-green-200 bg-green-50 hover:border-green-300' : week.status === 'generating' ? 'border-blue-200 bg-blue-50 hover:border-blue-300' : 'border-gray-200 bg-gray-50 hover:border-gray-300'}`}>
                <button onClick={() => setSelectedWeek(week)} className="absolute inset-0" aria-label={`Open Week ${week.number}`} />
                <div className="relative z-10">
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
                  <div className="mt-3 flex justify-end">
                    <button onClick={(e) => { e.stopPropagation(); exportWeek(week) }} className="px-3 py-1.5 text-xs rounded-lg bg-amber-600 text-white inline-flex items-center gap-1">
                      <Download size={14} />
                      Export Week
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      {selectedWeek && (
        <div className="fixed inset-0 bg-black/50 grid place-items-center z-50 p-4" role="dialog" aria-modal="true" aria-label={`Week ${selectedWeek.number} details`}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Week {selectedWeek.number} • {selectedWeek.virtue}</h2>
                <p className="text-sm text-gray-600 mt-1">4 lessons • 28 fields total • First Declension focus</p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => exportWeek(selectedWeek)} className="px-3 py-2 rounded-lg bg-amber-600 text-white inline-flex items-center gap-2"><Download size={16} />Export Week</button>
                <button aria-label="Close" onClick={() => setSelectedWeek(null)} className="text-gray-500 hover:text-gray-700 p-2">
                  <X size={24} />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto hide-scrollbar">
              <div className="grid grid-cols-12">
                <div className="col-span-12 md:col-span-3 border-r border-gray-200 p-4 space-y-2">
                  {[1, 2, 3, 4].map(day => (
                    <button key={day} onClick={() => setActiveDay(day)} className={`w-full text-left px-4 py-3 rounded-lg transition ${day === activeDay ? 'bg-amber-100 border-2 border-amber-300 text-amber-900' : 'bg-white border border-gray-200 hover:bg-gray-50'}`} aria-pressed={day === activeDay}>
                      <div className="text-xs text-gray-500">Day {day}</div>
                      <div className="text-sm font-medium mt-1">7/7 fields complete</div>
                      <div className="text-xs text-green-700 font-medium mt-1">✓ Validated</div>
                    </button>
                  ))}
                </div>
                <div className="col-span-12 md:col-span-9 p-6 space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-gray-900">Day {activeDay} • All 7 Prescribed Fields</h3>
                    <div className="flex gap-2">
                      <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm flex items-center gap-2">
                        <Edit size={16} />
                        Edit Day
                      </button>
                      <button className="px-4 py-2 bg-gradient-to-r from-amber-600 to-red-600 text-white rounded-lg hover:shadow-lg transition text-sm flex items-center gap-2">
                        <Download size={16} />
                        Export Day
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 gap-4">
                    {dayFields.map((field, idx) => (
                      <article key={field.key} className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-amber-200 transition card">
                        <header className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-900 grid place-items-center font-bold text-sm" aria-hidden>{idx + 1}</div>
                            <div>
                              <h4 className="font-bold text-gray-900">{field.label}</h4>
                              <p className="text-xs text-gray-500 font-mono mt-0.5">{field.key}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-green-700 font-medium">✓ validated</span>
                            <button className="text-xs text-gray-600 hover:text-gray-900">Edit</button>
                            <button onClick={() => exportField(selectedWeek, activeDay, field)} className="px-2 py-1 text-xs rounded bg-amber-600 text-white inline-flex items-center gap-1"><Download size={12} />Export Field</button>
                          </div>
                        </header>
                        <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-4">
                          <p className="text-sm text-gray-700 whitespace-pre-wrap font-mono">{field.sample}</p>
                        </div>
                      </article>
                    ))}
                  </div>
                  <div className="mt-6 pt-4 border-t border-gray-200 flex items-center justify-between text-sm">
                    <div className="text-gray-600"><span className="font-medium">Validation:</span> ✓ Pedagogical checks passed • ✓ 28% spiral recall • ✓ Single tutor voice</div>
                    <div className="text-gray-500 font-mono text-xs">model=gpt-4o • tokens=3,482 • cost≈$0.17</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function Stat({ icon, label, value }) {
  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm card">
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

function Row({ k, v }) {
  return (
    <div className="flex items-center justify-between"><span>{k}</span><span className="font-medium">{v}</span></div>
  )
}
