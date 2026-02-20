'use client'

import React, { useState, useEffect } from 'react'
import { businessApi, agentConfigApi, templateApi, promptAssistantApi } from '@/lib/api'
import { Button, Card, Input, TextArea, LoadingSpinner, Badge, Modal } from '@/components/ui'
import { ClipboardDocumentIcon, ArrowPathIcon, CheckIcon, SparklesIcon, BeakerIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import type { Business, AgentConfig, TemplateCategory, PromptAnalysis, PromptSample } from '@/lib/types'

export default function SettingsPage() {
  const [business, setBusiness] = useState<Business | null>(null)
  const [agentConfig, setAgentConfig] = useState<AgentConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [businessId, setBusinessId] = useState<string | null>(null)
  const [copiedKey, setCopiedKey] = useState(false)
  const [copiedCode, setCopiedCode] = useState(false)
  const [showRegenerateModal, setShowRegenerateModal] = useState(false)
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [showPromptAssistant, setShowPromptAssistant] = useState(false)
  const [templates, setTemplates] = useState<TemplateCategory[]>([])
  const [promptAnalysis, setPromptAnalysis] = useState<PromptAnalysis | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [promptSamples, setPromptSamples] = useState<PromptSample[]>([])
  const [loadingSamples, setLoadingSamples] = useState(false)

  // Form states - Business
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [websiteUrl, setWebsiteUrl] = useState('')
  const [primaryColor, setPrimaryColor] = useState('#2563eb')
  const [position, setPosition] = useState('bottom-right')
  const [greetingMessage, setGreetingMessage] = useState('')
  const [placeholderText, setPlaceholderText] = useState('')

  // Form states - Agent Config
  const [personality, setPersonality] = useState('')
  const [businessCategory, setBusinessCategory] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')
  const [responseTone, setResponseTone] = useState('')
  const [useHybridSearch, setUseHybridSearch] = useState(true)
  const [useReranking, setUseReranking] = useState(true)
  const [chunkSize, setChunkSize] = useState(1000)
  const [chunkOverlap, setChunkOverlap] = useState(200)

  useEffect(() => {
    const storedBusinessId = localStorage.getItem('selected_business_id')
    if (storedBusinessId) {
      setBusinessId(storedBusinessId)
      loadBusiness(storedBusinessId)
      loadAgentConfig(storedBusinessId)
      loadTemplates()
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
    } catch (error: any) {
      console.error('Failed to load business:', error)
      if (error.response?.status === 404) {
        toast.error('Business not found. Please select a valid business.')
        localStorage.removeItem('selected_business_id')
        window.location.href = '/dashboard'
      }
    } finally {
      setLoading(false)
    }
  }

  const loadAgentConfig = async (bizId: string) => {
    try {
      const data = await agentConfigApi.get(bizId)
      setAgentConfig(data)
      setPersonality(data.agent_personality || '')
      setBusinessCategory(data.business_category || '')
      setSystemPrompt(data.system_prompt || '')
      setResponseTone(data.response_tone || 'professional')
      setUseHybridSearch(data.use_hybrid_search ?? true)
      setUseReranking(data.use_reranking ?? true)
      setChunkSize(data.chunk_size || 1000)
      setChunkOverlap(data.chunk_overlap || 200)
    } catch (error) {
      console.error('Failed to load agent config:', error)
    }
  }

  const loadTemplates = async () => {
    try {
      const data = await templateApi.getCategories()
      setTemplates(data)
    } catch (error) {
      console.error('Failed to load templates:', error)
    }
  }

  const handleSaveSettings = async () => {
    if (!businessId) return

    setSaving(true)
    try {
      // Save business info
      await businessApi.update(businessId, {
        name,
        description,
        website_url: websiteUrl,
      })

      // Save widget config
      await businessApi.updateConfig(businessId, {
        primary_color: primaryColor,
        position,
        greeting_message: greetingMessage,
        placeholder_text: placeholderText,
      })

      // Save agent config
      await agentConfigApi.update(businessId, {
        agent_personality: personality,
        business_category: businessCategory,
        system_prompt: systemPrompt,
        response_tone: responseTone,
        use_hybrid_search: useHybridSearch,
        use_reranking: useReranking,
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap,
      })

      toast.success('Settings saved successfully!')
      loadBusiness(businessId)
      loadAgentConfig(businessId)
    } catch (error) {
      // Error handled by interceptor
    } finally {
      setSaving(false)
    }
  }

  const handleApplyTemplate = async (category: string) => {
    if (!businessId) return

    try {
      const result = await templateApi.applyTemplate(businessId, { category })
      toast.success(result.message)
      setShowTemplateModal(false)
      loadAgentConfig(businessId)
    } catch (error) {
      // Error handled by interceptor
    }
  }

  const handleAnalyzePrompt = async () => {
    if (!systemPrompt) {
      toast.error('Please enter a system prompt first')
      return
    }

    setAnalyzing(true)
    try {
      const analysis = await promptAssistantApi.analyze({
        prompt: systemPrompt,
        context: businessCategory,
      })
      setPromptAnalysis(analysis)
      toast.success('Prompt analyzed successfully!')
    } catch (error) {
      // Error handled by interceptor
    } finally {
      setAnalyzing(false)
    }
  }

  const handleImprovePrompt = async () => {
    if (!systemPrompt) {
      toast.error('Please enter a system prompt first')
      return
    }

    setAnalyzing(true)
    try {
      const improvement = await promptAssistantApi.improve({
        rough_prompt: systemPrompt,
        business_type: businessCategory || 'general',
      })
      setSystemPrompt(improvement.improved_prompt)
      toast.success('Prompt improved! Review the changes.')
    } catch (error) {
      // Error handled by interceptor
    } finally {
      setAnalyzing(false)
    }
  }

  const handleShowPromptSamples = async () => {
    setShowPromptAssistant(true)
    if (promptSamples.length === 0) {
      setLoadingSamples(true)
      try {
        const samples = await promptAssistantApi.getSamples(businessCategory)
        setPromptSamples(samples)
      } catch (error) {
        // Error handled by interceptor
      } finally {
        setLoadingSamples(false)
      }
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

        {/* Agent Configuration */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">AI Agent Configuration</h2>
              <p className="text-sm text-gray-500 mt-1">Customize your AI assistant's behavior and personality</p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowTemplateModal(true)}
            >
              <SparklesIcon className="h-4 w-4 mr-2" />
              Use Template
            </Button>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Agent Personality"
                value={personality}
                onChange={(e) => setPersonality(e.target.value)}
                placeholder="e.g., friendly, professional, technical"
              />
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Business Category
                </label>
                <select
                  value={businessCategory}
                  onChange={(e) => setBusinessCategory(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">Select category...</option>
                  <option value="customer_support">Customer Support</option>
                  <option value="sales">Sales</option>
                  <option value="education">Education</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="finance">Finance</option>
                  <option value="technology">Technology</option>
                  <option value="retail">Retail</option>
                  <option value="real_estate">Real Estate</option>
                  <option value="legal">Legal</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  System Prompt
                </label>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleShowPromptSamples}
                  >
                    <BeakerIcon className="h-4 w-4 mr-1" />
                    Samples
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleAnalyzePrompt}
                    loading={analyzing}
                  >
                    Analyze
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleImprovePrompt}
                    loading={analyzing}
                  >
                    Improve
                  </Button>
                </div>
              </div>
              <TextArea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder="You are a helpful AI assistant for..."
                rows={6}
                className="font-mono text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">
                Define how your AI agent should behave and respond to users
              </p>
            </div>

            {promptAnalysis && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">Prompt Analysis</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600">Score:</span>
                    <Badge variant={promptAnalysis.score > 70 ? 'success' : 'default'}>
                      {promptAnalysis.score}/100
                    </Badge>
                    <span className="text-gray-600">Quality:</span>
                    <Badge>{promptAnalysis.quality}</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600">Word Count:</span>
                    <span className="font-medium">{promptAnalysis.word_count}</span>
                  </div>
                  {promptAnalysis.issues.length > 0 && (
                    <div>
                      <span className="text-red-600 font-medium">Issues:</span>
                      <ul className="list-disc list-inside mt-1 text-red-700">
                        {promptAnalysis.issues.map((issue, i) => (
                          <li key={i}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {promptAnalysis.suggestions.length > 0 && (
                    <div>
                      <span className="text-gray-600 font-medium">Suggestions:</span>
                      <ul className="list-disc list-inside mt-1 text-gray-700">
                        {promptAnalysis.suggestions.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                <button
                  onClick={() => setPromptAnalysis(null)}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-800"
                >
                  Dismiss
                </button>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Response Tone
              </label>
              <select
                value={responseTone}
                onChange={(e) => setResponseTone(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="professional">Professional</option>
                <option value="friendly">Friendly</option>
                <option value="casual">Casual</option>
                <option value="formal">Formal</option>
                <option value="technical">Technical</option>
                <option value="empathetic">Empathetic</option>
              </select>
            </div>

            <div className="border-t pt-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Advanced RAG Settings</h3>
              <div className="space-y-3">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={useHybridSearch}
                    onChange={(e) => setUseHybridSearch(e.target.checked)}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-700">Enable Hybrid Search</span>
                    <p className="text-xs text-gray-500">Combine semantic and keyword search for better accuracy</p>
                  </div>
                </label>

                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={useReranking}
                    onChange={(e) => setUseReranking(e.target.checked)}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-700">Enable Reranking</span>
                    <p className="text-xs text-gray-500">Improve relevance of retrieved documents</p>
                  </div>
                </label>

                <div className="grid grid-cols-2 gap-4">
                  <Input
                    type="number"
                    label="Chunk Size"
                    value={chunkSize}
                    onChange={(e) => setChunkSize(parseInt(e.target.value))}
                    min={100}
                    max={2000}
                  />
                  <Input
                    type="number"
                    label="Chunk Overlap"
                    value={chunkOverlap}
                    onChange={(e) => setChunkOverlap(parseInt(e.target.value))}
                    min={0}
                    max={500}
                  />
                </div>
              </div>
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

      {/* Template Selection Modal */}
      <Modal
        isOpen={showTemplateModal}
        onClose={() => setShowTemplateModal(false)}
        title="Choose Agent Template"
        maxWidth="xl"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Select a pre-configured template to quickly set up your AI agent for your industry
          </p>
          
          <div className="grid grid-cols-2 gap-4 max-h-96 overflow-y-auto">
            {Array.isArray(templates) && templates.length > 0 ? (
              templates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => handleApplyTemplate(template.id)}
                  className="text-left p-4 border border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    {template.icon && (
                      <span className="text-2xl">{template.icon}</span>
                    )}
                    <div>
                      <h4 className="font-medium text-gray-900">{template.name}</h4>
                      <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                    </div>
                  </div>
                </button>
              ))
            ) : (
              <div className="col-span-2 text-center py-8 text-gray-500">
                No templates available
              </div>
            )}
          </div>

          <div className="flex justify-end mt-4">
            <Button variant="ghost" onClick={() => setShowTemplateModal(false)}>
              Cancel
            </Button>
          </div>
        </div>
      </Modal>

      {/* Prompt Samples Modal */}
      <Modal
        isOpen={showPromptAssistant}
        onClose={() => setShowPromptAssistant(false)}
        title="Sample Prompts"
        maxWidth="xl"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Browse sample prompts for inspiration or click to use one as a starting point
          </p>
          
          {loadingSamples ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {promptSamples.map((sample, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setSystemPrompt(sample.prompt)
                    setShowPromptAssistant(false)
                    toast.success('Sample prompt applied!')
                  }}
                  className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">{sample.title}</h4>
                      <p className="text-xs text-gray-500 mt-1">{sample.category}</p>
                      <p className="text-sm text-gray-600 mt-2">{sample.description}</p>
                      <p className="text-xs text-gray-500 mt-1">Use case: {sample.use_case}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          <div className="flex justify-end mt-4">
            <Button variant="ghost" onClick={() => setShowPromptAssistant(false)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
