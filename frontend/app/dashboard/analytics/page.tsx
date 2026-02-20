'use client'

import React, { useState, useEffect } from 'react'
import { businessApi } from '@/lib/api'
import { Card, LoadingSpinner, Badge } from '@/components/ui'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { 
  ChatBubbleLeftRightIcon, 
  DocumentTextIcon, 
  ClockIcon,
  HandThumbUpIcon 
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Analytics {
  total_conversations: number
  total_documents: number
  avg_response_time: number
  positive_feedback_rate: number
  conversations_by_day: Array<{ date: string; count: number }>
  documents_by_type: Array<{ type: string; count: number }>
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [businessId, setBusinessId] = useState<string | null>(null)
  const [days, setDays] = useState(30)

  useEffect(() => {
    const storedBusinessId = localStorage.getItem('selected_business_id')
    if (storedBusinessId) {
      setBusinessId(storedBusinessId)
      loadAnalytics(storedBusinessId, days)
    } else {
      setLoading(false)
      toast.error('Please select a business first')
    }
  }, [days])

  const loadAnalytics = async (bizId: string, period: number) => {
    try {
      const data = await businessApi.getAnalytics(bizId)
      setAnalytics(data)
    } catch (error: any) {
      console.error('Failed to load analytics:', error)
      if (error.response?.status === 404) {
        toast.error('Business not found. Please select a valid business.')
        localStorage.removeItem('selected_business_id')
        window.location.href = '/dashboard'
      }
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!businessId || !analytics) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Please select a business from the dashboard</p>
      </div>
    )
  }

  const stats = [
    {
      title: 'Total Conversations',
      value: analytics.total_conversations.toLocaleString(),
      icon: ChatBubbleLeftRightIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Documents',
      value: analytics.total_documents.toLocaleString(),
      icon: DocumentTextIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Avg Response Time',
      value: `${(analytics.avg_response_time / 1000).toFixed(2)}s`,
      icon: ClockIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Positive Feedback',
      value: `${(analytics.positive_feedback_rate * 100).toFixed(1)}%`,
      icon: HandThumbUpIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="mt-2 text-gray-600">Track your chatbot performance</p>
        </div>

        <div className="flex gap-2">
          {[7, 30, 90].map((period) => (
            <button
              key={period}
              onClick={() => setDays(period)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                days === period
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {period} days
            </button>
          ))}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <Card key={stat.title} className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">{stat.title}</p>
                <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-8 w-8 ${stat.color}`} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conversations Timeline */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversations Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analytics.conversations_by_day}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#2563eb" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* Documents by Type */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Documents by Type</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics.documents_by_type}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  )
}
