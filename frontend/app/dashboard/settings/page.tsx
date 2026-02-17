'use client'

import React, { useState, useEffect } from 'react'
import { businessApi } from '@/lib/api'
import { Button, Card, Input, TextArea, LoadingSpinner, Badge, Modal } from '@/components/ui'
import { ClipboardDocumentIcon, ArrowPathIcon, CheckIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Business {
  id: string
  name: string
  description?: string
  website_url?: string
  plan_type: string
  api_key: string
  is_active: boolean
  widget_config: {
    primary_color: string
    position: string
    greeting_message: string
    placeholder_text: string
  }
}

export default function SettingsPage() {
  const [business, setBusiness] = useState<Business | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [businessId, setBusinessId] = useState<string | null>(null)
  const [copiedKey, setCopiedKey] = useState(false)
  const [copiedCode, setCopiedCode] = useState(false)
  const [showRegenerateModal, setShowRegenerateModal] = useState(false)

  // Form states
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [websiteUrl, setWebsiteUrl] = useState('')
  const [primaryColor, setPrimaryColor] = useState('#2563eb')
  const [position, setPosition] = useState('bottom-right')
  const [greetingMessage, setGreetingMessage] = useState('')
  const [placeholderText, setPlaceholderText] = useState('')

  useEffect(() => {
    const storedBusinessId = localStorage.getItem('selected_business_id')
    if (storedBusinessId) {
      setBusinessId(storedBusinessId)
      loadBusiness(storedBusinessId)
    } else {
      setLoading(false)
      toast.error('Please select a business first')
    }
  }, [])

  const loadBusiness = async (bizId: string) => {
    try {
      const data = await businessApi.get(bizId)
      setBusiness(data)
      setName(data.name)
      setDescription(data.description || '')
      setWebsiteUrl(data.website_url || '')
      setPrimaryColor(data.widget_config?.primary_color || '#2563eb')
      setPosition(data.widget_config?.position || 'bottom-right')
      setGreetingMessage(data.widget_config?.greeting_message || "Hi! How can I help you today?")
      setPlaceholderText(data.widget_config?.placeholder_text || "Type your message...")
    } catch (error) {
      console.error('Failed to load business:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveSettings = async () => {
    if (!businessId) return

    setSaving(true)
    try {
      await businessApi.update(businessId, {
        name,
        description,
        website_url: websiteUrl,
      })

      await businessApi.updateConfig(businessId, {
        primary_color: primaryColor,
        position,
        greeting_message: greetingMessage,
        placeholder_text: placeholderText,
      })

      toast.success('Settings saved successfully!')
      loadBusiness(businessId)
    } catch (error) {
      // Error handled by interceptor
    } finally {
      setSaving(false)
    }
  }

  const handleRegenerateKey = async () => {
    if (!businessId) return

    try {
      const data = await businessApi.regenerateApiKey(businessId)
      toast.success('API key regenerated successfully!')
      setShowRegenerateModal(false)
      setBusiness(prev => prev ? { ...prev, api_key: data.api_key } : null)
    } catch (error) {
      // Error handled by interceptor
    }
  }

  const copyToClipboard = (text: string, type: 'key' | 'code') => {
    navigator.clipboard.writeText(text)
    if (type === 'key') {
      setCopiedKey(true)
      setTimeout(() => setCopiedKey(false), 2000)
    } else {
      setCopiedCode(true)
      setTimeout(() => setCopiedCode(false), 2000)
    }
    toast.success('Copied to clipboard!')
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!businessId || !business) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Please select a business from the dashboard</p>
      </div>
    )
  }

  const widgetCode = `<!-- DocMind AI Chatbot Widget -->
<script src="${window.location.origin.replace('3000', '8000')}/static/widget.js"></script>
<script>
  DocMindWidget.init({
    businessId: '${businessId}',
    apiUrl: '${window.location.origin.replace('3000', '8000')}'
  });
</script>`

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">Manage your business configuration and widget</p>
      </div>

      <div className="space-y-6">
        {/* Business Info */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Business Information</h2>
          <div className="space-y-4">
            <Input
              label="Business Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Company"
            />

            <TextArea
              label="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description"
              rows={3}
            />

            <Input
              label="Website URL"
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
              placeholder="https://example.com"
            />

            <div className="flex items-center gap-4">
              <Badge variant={business.is_active ? 'success' : 'default'}>
                {business.plan_type}
              </Badge>
              <span className="text-sm text-gray-500">
                Status: {business.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </Card>

        {/* API Key */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">API Access</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Key
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={business.api_key}
                  readOnly
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 font-mono text-sm"
                />
                <Button
                  variant="secondary"
                  onClick={() => copyToClipboard(business.api_key, 'key')}
                >
                  {copiedKey ? <CheckIcon className="h-5 w-5" /> : <ClipboardDocumentIcon className="h-5 w-5" />}
                </Button>
                <Button
                  variant="danger"
                  onClick={() => setShowRegenerateModal(true)}
                >
                  <ArrowPathIcon className="h-5 w-5" />
                </Button>
              </div>
              <p className="mt-2 text-sm text-gray-500">
                Keep this key secret. It's used to authenticate API requests.
              </p>
            </div>
          </div>
        </Card>

        {/* Widget Configuration */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Widget Configuration</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primary Color
                </label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={primaryColor}
                    onChange={(e) => setPrimaryColor(e.target.value)}
                    className="h-10 w-20 rounded border border-gray-300"
                  />
                  <Input
                    value={primaryColor}
                    onChange={(e) => setPrimaryColor(e.target.value)}
                    placeholder="#2563eb"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Position
                </label>
                <select
                  value={position}
                  onChange={(e) => setPosition(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  <option value="bottom-right">Bottom Right</option>
                  <option value="bottom-left">Bottom Left</option>
                  <option value="top-right">Top Right</option>
                  <option value="top-left">Top Left</option>
                </select>
              </div>
            </div>

            <Input
              label="Greeting Message"
              value={greetingMessage}
              onChange={(e) => setGreetingMessage(e.target.value)}
              placeholder="Hi! How can I help you today?"
            />

            <Input
              label="Placeholder Text"
              value={placeholderText}
              onChange={(e) => setPlaceholderText(e.target.value)}
              placeholder="Type your message..."
            />
          </div>
        </Card>

        {/* Widget Embed Code */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Embed Widget</h2>
          <p className="text-sm text-gray-600 mb-4">
            Copy this code and paste it before the closing &lt;/body&gt; tag on your website.
          </p>
          <div className="relative">
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs">
              <code>{widgetCode}</code>
            </pre>
            <button
              onClick={() => copyToClipboard(widgetCode, 'code')}
              className="absolute top-4 right-4 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm flex items-center gap-2"
            >
              {copiedCode ? (
                <>
                  <CheckIcon className="h-4 w-4" />
                  Copied!
                </>
              ) : (
                <>
                  <ClipboardDocumentIcon className="h-4 w-4" />
                  Copy
                </>
              )}
            </button>
          </div>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button onClick={handleSaveSettings} loading={saving} size="lg">
            Save Settings
          </Button>
        </div>
      </div>

      {/* Regenerate API Key Modal */}
      <Modal
        isOpen={showRegenerateModal}
        onClose={() => setShowRegenerateModal(false)}
        title="Regenerate API Key"
        maxWidth="md"
      >
        <div className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              ⚠️ <strong>Warning:</strong> Regenerating your API key will immediately invalidate the old key. 
              Any applications using the old key will stop working until updated.
            </p>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <Button variant="ghost" onClick={() => setShowRegenerateModal(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleRegenerateKey}>
              Regenerate Key
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
