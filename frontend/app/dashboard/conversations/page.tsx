'use client'

import React, { useState, useEffect } from 'react'
import { chatApi } from '@/lib/api'
import { Card, LoadingSpinner, EmptyState, Badge } from '@/components/ui'
import { ChatBubbleLeftRightIcon, HandThumbUpIcon, HandThumbDownIcon } from '@heroicons/react/24/outline'
import { HandThumbUpIcon as HandThumbUpSolid, HandThumbDownIcon as HandThumbDownSolid } from '@heroicons/react/24/solid'
import toast from 'react-hot-toast'

interface Conversation {
  id: string
  session_id: string
  user_message: string
  bot_response: string
  feedback?: 'positive' | 'negative'
  sources_used: number
  response_time: number
  created_at: string
}

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [businessId, setBusinessId] = useState<string | null>(null)

  useEffect(() => {
    const storedBusinessId = localStorage.getItem('selected_business_id')
    if (storedBusinessId) {
      setBusinessId(storedBusinessId)
      loadConversations(storedBusinessId)
    } else {
      setLoading(false)
      toast.error('Please select a business first')
    }
  }, [])

  const loadConversations = async (bizId: string) => {
    try {
      const data = await chatApi.getConversations(bizId)
      setConversations(data)
    } catch (error: any) {
      console.error('Failed to load conversations:', error)
      if (error.response?.status === 404) {
        toast.error('Business not found. Please select a valid business.')
        localStorage.removeItem('selected_business_id')
        window.location.href = '/dashboard'
      }
    } finally {
      setLoading(false)
    }
  }

  const handleFeedback = async (conversationId: string, feedback: 'positive' | 'negative') => {
    try {
      await chatApi.provideFeedback(conversationId, feedback)
      toast.success('Feedback recorded!')
      // Update local state
      setConversations(prev =>
        prev.map(conv =>
          conv.id === conversationId ? { ...conv, feedback } : conv
        )
      )
    } catch (error) {
      // Error handled by interceptor
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!businessId) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Please select a business from the dashboard</p>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Conversations</h1>
        <p className="mt-2 text-gray-600">Review chat history and user feedback</p>
      </div>

      {conversations.length === 0 ? (
        <EmptyState
          icon={<ChatBubbleLeftRightIcon className="h-16 w-16 text-gray-400" />}
          title="No conversations yet"
          description="Conversations will appear here once users start chatting with your bot"
        />
      ) : (
        <div className="space-y-4">
          {conversations.map((conv) => (
            <Card key={conv.id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Badge variant="info">Session: {conv.session_id.substring(0, 8)}</Badge>
                    <span className="text-xs text-gray-500">
                      {new Date(conv.created_at).toLocaleString()}
                    </span>
                    {conv.response_time && (
                      <span className="text-xs text-gray-500">
                        {(conv.response_time / 1000).toFixed(2)}s
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleFeedback(conv.id, 'positive')}
                    className={`p-2 rounded-lg transition-colors ${
                      conv.feedback === 'positive'
                        ? 'text-green-600 bg-green-50'
                        : 'text-gray-400 hover:text-green-600 hover:bg-green-50'
                    }`}
                  >
                    {conv.feedback === 'positive' ? (
                      <HandThumbUpSolid className="h-5 w-5" />
                    ) : (
                      <HandThumbUpIcon className="h-5 w-5" />
                    )}
                  </button>
                  <button
                    onClick={() => handleFeedback(conv.id, 'negative')}
                    className={`p-2 rounded-lg transition-colors ${
                      conv.feedback === 'negative'
                        ? 'text-red-600 bg-red-50'
                        : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
                    }`}
                  >
                    {conv.feedback === 'negative' ? (
                      <HandThumbDownSolid className="h-5 w-5" />
                    ) : (
                      <HandThumbDownIcon className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">User:</p>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-gray-900">{conv.user_message}</p>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">Bot:</p>
                  <div className="bg-primary-50 p-3 rounded-lg">
                    <p className="text-gray-900">{conv.bot_response}</p>
                  </div>
                </div>

                {conv.sources_used > 0 && (
                  <p className="text-xs text-gray-500">
                    📚 Used {conv.sources_used} source{conv.sources_used !== 1 ? 's' : ''}
                  </p>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
