#!/bin/bash

# DocMind AI Widget Test Script
# This script tests the chat API directly to diagnose issues

BUSINESS_ID="19d08036-9797-4f0f-8279-dfd2b7207025"
API_URL="http://localhost:8000"

echo "🧪 Testing DocMind AI Chat API"
echo "================================"
echo ""

# Test 1: Health Check
echo "1️⃣  Testing Backend Health..."
curl -s "$API_URL/health" | jq '.' || echo "❌ Health check failed"
echo ""

# Test 2: Widget Config
echo "2️⃣  Testing Widget Config..."
curl -s "$API_URL/api/v1/businesses/$BUSINESS_ID/widget-config" | jq '.' || echo "❌ Widget config failed"
echo ""

# Test 3: Chat API
echo "3️⃣  Testing Chat API..."
echo "Sending question: 'tell me about durgaraj'"
curl -s -X POST "$API_URL/api/v1/chat/$BUSINESS_ID" \
  -H "Content-Type: application/json" \
  -d '{"question": "tell me about durgaraj", "session_id": "test-session"}' \
  | jq '.' || echo "❌ Chat API failed"
echo ""

echo "✅ Test Complete!"
echo ""
echo "If you see errors above, the widget won't work."
echo "Common issues:"
echo "  - Backend not running (check: http://localhost:8000/docs)"
echo "  - Documents not processed (check dashboard)"
echo "  - Ollama not running (check: ollama list)"
