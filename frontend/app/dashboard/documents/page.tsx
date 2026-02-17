'use client'

import React, { useState, useEffect, useRef } from 'react'
import { documentApi, chatApi } from '@/lib/api'
import { Button, Card, Modal, Input, TextArea, LoadingSpinner, EmptyState, Badge } from '@/components/ui'
import { PlusIcon, DocumentTextIcon, TrashIcon, CloudArrowUpIcon, LinkIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Document {
  id: string
  filename: string
  file_type: string
  file_size: number
  chunks_count: number
  is_processed: boolean
  created_at: string
  error_message?: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showTextModal, setShowTextModal] = useState(false)
  const [showUrlModal, setShowUrlModal] = useState(false)
  const [showChatModal, setShowChatModal] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [textContent, setTextContent] = useState('')
  const [url, setUrl] = useState('')
  const [businessId, setBusinessId] = useState<string | null>(null)
  
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [sessionId] = useState(() => Math.random().toString(36).substring(7))
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const storedBusinessId = localStorage.getItem('selected_business_id')
    if (storedBusinessId) {
      setBusinessId(storedBusinessId)
      loadDocuments(storedBusinessId)
    } else {
      setLoading(false)
      toast.error('Please select a business first')
    }
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadDocuments = async (bizId: string) => {
    try {
      const data = await documentApi.list(bizId)
      setDocuments(data)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (files: File[]) => {
    if (!files.length || !businessId) return

    // Validate file sizes
    const maxSize = 50 * 1024 * 1024 // 50MB for PRO plan
    const invalidFiles = files.filter(f => f.size > maxSize)
    if (invalidFiles.length > 0) {
      toast.error(`Files too large: ${invalidFiles.map(f => f.name).join(', ')}. Max size: 50MB`)
      return
    }

    setUploading(true)
    setUploadProgress(0)
    
    try {
      await documentApi.upload(businessId, files, (progress) => {
        setUploadProgress(progress)
      })
      toast.success(`${files.length} file(s) uploaded successfully!`)
      setSelectedFiles([])
      loadDocuments(businessId)
    } catch (error: any) {
      // Error already handled by interceptor, but show specific message
      console.error('Upload error:', error)
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const handleTextIngest = async () => {
    if (!textContent || !businessId) return

    setUploading(true)
    try {
      await documentApi.ingestText(businessId, { text: textContent })
      toast.success('Text content ingested successfully!')
      setShowTextModal(false)
      setTextContent('')
      loadDocuments(businessId)
    } catch (error) {
      // Error handled by interceptor
    } finally {
      setUploading(false)
    }
  }

  const handleUrlIngest = async () => {
    if (!url || !businessId) return

    setUploading(true)
    try {
      await documentApi.ingestUrl(businessId, url)
      toast.success('URL content ingested successfully!')
      setShowUrlModal(false)
      setUrl('')
      loadDocuments(businessId)
    } catch (error) {
      // Error handled by interceptor
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (documentId: string) => {
    if (!businessId || !confirm('Are you sure you want to delete this document?')) return

    try {
      await documentApi.delete(businessId, documentId)
      toast.success('Document deleted successfully!')
      loadDocuments(businessId)
    } catch (error) {
      // Error handled by interceptor
    }
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !businessId || sending) return

    const userMessage: ChatMessage = { role: 'user', content: inputMessage }
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setSending(true)

    try {
      const response = await chatApi.sendMessage(businessId, inputMessage, sessionId)
      const assistantMessage: ChatMessage = { role: 'assistant', content: response.answer }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      toast.error('Failed to send message')
    } finally {
      setSending(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
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
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
          <p className="mt-2 text-gray-600">Upload and manage your training data</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => setShowChatModal(true)}>
            <ChatBubbleLeftRightIcon className="h-5 w-5 mr-2" />
            Test Chat
          </Button>
          <Button onClick={() => setShowUploadModal(true)}>
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Content
          </Button>
        </div>
      </div>

      {documents.length === 0 ? (
        <EmptyState
          icon={<DocumentTextIcon className="h-16 w-16 text-gray-400" />}
          title="No documents yet"
          description="Upload PDFs, text files, or web content to train your AI chatbot"
          action={
            <Button onClick={() => setShowUploadModal(true)}>
              <PlusIcon className="h-5 w-5 mr-2" />
              Add Your First Document
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {documents.map((doc) => (
            <Card key={doc.id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate">{doc.filename}</h3>
                  <div className="flex gap-2 flex-wrap">
                    <Badge variant="info">{doc.file_type}</Badge>
                    <Badge variant={doc.is_processed ? 'success' : 'warning'}>
                      {doc.is_processed ? 'processed' : 'pending'}
                    </Badge>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="text-red-600 hover:text-red-700 p-1"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
              </div>
              
              <div className="space-y-2 text-sm text-gray-600">
                <p>Size: {formatFileSize(doc.file_size)}</p>
                <p>Chunks: {doc.chunks_count || 0}</p>
                {doc.error_message && (
                  <p className="text-xs text-red-600">Error: {doc.error_message}</p>
                )}
                <p className="text-xs text-gray-500">
                  Added {new Date(doc.created_at).toLocaleDateString()}
                </p>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Upload Options Modal */}
      <Modal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        title="Add Training Content"
        maxWidth="lg"
      >
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>File Limits:</strong> Max 50MB per file (PRO plan). Supported: PDF, TXT, DOC, DOCX, HTML
          </p>
          <p className="text-xs text-blue-600 mt-1">
            💡 You can select multiple files at once for faster upload
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => {
              setShowUploadModal(false)
              document.getElementById('fileInput')?.click()
            }}
            className="p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 transition-colors text-center"
          >
            <CloudArrowUpIcon className="h-12 w-12 mx-auto text-gray-400 mb-3" />
            <h4 className="font-semibold text-gray-900 mb-1">Upload Files</h4>
            <p className="text-sm text-gray-600">PDF, TXT, DOC, HTML</p>
            <p className="text-xs text-gray-500 mt-1">Multiple files supported</p>
          </button>
          
          <button
            onClick={() => {
              setShowUploadModal(false)
              setShowTextModal(true)
            }}
            className="p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 transition-colors text-center"
          >
            <DocumentTextIcon className="h-12 w-12 mx-auto text-gray-400 mb-3" />
            <h4 className="font-semibold text-gray-900 mb-1">Paste Text</h4>
            <p className="text-sm text-gray-600">Direct text input</p>
          </button>
          
          <button
            onClick={() => {
              setShowUploadModal(false)
              setShowUrlModal(true)
            }}
            className="p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 transition-colors text-center"
          >
            <LinkIcon className="h-12 w-12 mx-auto text-gray-400 mb-3" />
            <h4 className="font-semibold text-gray-900 mb-1">Import URL</h4>
            <p className="text-sm text-gray-600">Scrape website</p>
          </button>
        </div>
      </Modal>

      {/* Hidden file input */}
      <input
        id="fileInput"
        type="file"
        accept=".pdf,.txt,.doc,.docx,.html"
        multiple
        className="hidden"
        onChange={(e) => {
          const files = Array.from(e.target.files || [])
          if (files.length > 0) {
            handleFileUpload(files)
          }
          // Reset input to allow selecting same file again
          e.target.value = ''
        }}
      />

      {/* Upload Progress Modal */}
      {uploading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Uploading Files...</h3>
            <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
              <div 
                className="bg-primary-600 h-2.5 rounded-full transition-all duration-300" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 text-center">{uploadProgress}%</p>
            <p className="text-xs text-gray-500 text-center mt-2">
              Please don't close this window...
            </p>
          </div>
        </div>
      )}

      {/* Text Input Modal */}
      <Modal
        isOpen={showTextModal}
        onClose={() => setShowTextModal(false)}
        title="Add Text Content"
        maxWidth="lg"
      >
        <div className="space-y-4">
          <TextArea
            label="Text Content"
            value={textContent}
            onChange={(e) => setTextContent(e.target.value)}
            placeholder="Paste your text content here..."
            rows={10}
          />
          
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setShowTextModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleTextIngest} loading={uploading}>
              Ingest Text
            </Button>
          </div>
        </div>
      </Modal>

      {/* URL Input Modal */}
      <Modal
        isOpen={showUrlModal}
        onClose={() => setShowUrlModal(false)}
        title="Import from URL"
        maxWidth="lg"
      >
        <div className="space-y-4">
          <Input
            label="Website URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/page"
          />
          
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setShowUrlModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleUrlIngest} loading={uploading}>
              Import URL
            </Button>
          </div>
        </div>
      </Modal>

      {/* Chat Test Modal */}
      <Modal
        isOpen={showChatModal}
        onClose={() => setShowChatModal(false)}
        title="Test Your Chatbot"
        maxWidth="xl"
      >
        <div className="flex flex-col h-[500px]">
          <div className="flex-1 overflow-y-auto mb-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <ChatBubbleLeftRightIcon className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                <p>Start chatting to test your AI bot</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] px-4 py-2 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))
            )}
            {sending && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-4 py-2 rounded-lg">
                  <LoadingSpinner size="sm" />
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
          
          <div className="flex gap-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Type your message..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled={sending}
            />
            <Button onClick={handleSendMessage} disabled={!inputMessage.trim() || sending}>
              Send
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
