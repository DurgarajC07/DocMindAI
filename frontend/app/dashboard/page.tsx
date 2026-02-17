'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { businessApi } from '@/lib/api'
import { Button, Card, Modal, Input, TextArea, LoadingSpinner, EmptyState, Badge } from '@/components/ui'
import { PlusIcon, BuildingOfficeIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Business {
  id: string
  name: string
  description?: string
  website?: string
  plan: string
  api_key: string
  is_active: boolean
  created_at: string
}

export default function DashboardPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newBusiness, setNewBusiness] = useState({
    name: '',
    description: '',
    website: '',
  })
  const router = useRouter()

  useEffect(() => {
    loadBusinesses()
  }, [])

  const loadBusinesses = async () => {
    try {
      const data = await businessApi.list()
      setBusinesses(data)
    } catch (error) {
      console.error('Failed to load businesses:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!newBusiness.name) {
      toast.error('Business name is required')
      return
    }

    setCreating(true)
    try {
      await businessApi.create(newBusiness)
      toast.success('Business created successfully!')
      setShowCreateModal(false)
      setNewBusiness({ name: '', description: '', website: '' })
      loadBusinesses()
    } catch (error) {
      // Error handled by interceptor
    } finally {
      setCreating(false)
    }
  }

  const selectBusiness = (businessId: string) => {
    localStorage.setItem('selected_business_id', businessId)
    router.push(`/dashboard/documents`)
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Your Businesses</h1>
          <p className="mt-2 text-gray-600">Manage your AI chatbots and training data</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Business
        </Button>
      </div>

      {businesses.length === 0 ? (
        <EmptyState
          icon={<BuildingOfficeIcon className="h-16 w-16 text-gray-400" />}
          title="No businesses yet"
          description="Create your first business to start building AI chatbots"
          action={
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-5 w-5 mr-2" />
              Create Your First Business
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {businesses.map((business) => (
            <Card key={business.id} className="p-6 hover:shadow-lg transition-shadow cursor-pointer" onClick={() => selectBusiness(business.id)}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">{business.name}</h3>
                  <Badge variant={business.is_active ? 'success' : 'default'}>
                    {business.plan}
                  </Badge>
                </div>
              </div>
              
              {business.description && (
                <p className="text-sm text-gray-600 mb-4">{business.description}</p>
              )}
              
              {business.website && (
                <p className="text-xs text-gray-500 truncate mb-4">
                  🌐 {business.website}
                </p>
              )}
              
              <div className="pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-500">
                  Created {new Date(business.created_at).toLocaleDateString()}
                </p>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Business Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Business"
        maxWidth="lg"
      >
        <div className="space-y-4">
          <Input
            label="Business Name *"
            value={newBusiness.name}
            onChange={(e) => setNewBusiness({ ...newBusiness, name: e.target.value })}
            placeholder="My Company"
          />
          
          <TextArea
            label="Description"
            value={newBusiness.description}
            onChange={(e) => setNewBusiness({ ...newBusiness, description: e.target.value })}
            placeholder="Brief description of your business"
            rows={3}
          />
          
          <Input
            label="Website URL"
            value={newBusiness.website}
            onChange={(e) => setNewBusiness({ ...newBusiness, website: e.target.value })}
            placeholder="https://example.com"
          />
          
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="ghost" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} loading={creating}>
              Create Business
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
