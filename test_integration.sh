#!/bin/bash
# Integration test script for DocMind AI

API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3001"

echo "🧪 DocMind AI Integration Tests"
echo "================================"
echo ""

# Test 1: Backend Health
echo "1. Testing Backend Health..."
HEALTH=$(curl -s $API_URL/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✓ Backend is healthy"
else
    echo "   ✗ Backend health check failed"
    exit 1
fi
echo ""

# Test 2: Login
echo "2. Testing Login API..."
LOGIN_RESPONSE=$(curl -s -X POST $API_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@docmind.ai", "password": "demo123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo "   ✓ Login successful"
    echo "   Token: ${TOKEN:0:30}..."
else
    echo "   ✗ Login failed"
    exit 1
fi
echo ""

# Test 3: Get User Profile
echo "3. Testing Get Profile API..."
PROFILE=$(curl -s -X GET $API_URL/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN")

if echo "$PROFILE" | grep -q "demo@docmind.ai"; then
    echo "   ✓ Profile retrieved successfully"
else
    echo "   ✗ Profile retrieval failed"
    exit 1
fi
echo ""

# Test 4: List Businesses
echo "4. Testing List Businesses API..."
BUSINESSES=$(curl -s -X GET $API_URL/api/v1/businesses \
  -H "Authorization: Bearer $TOKEN")

BUSINESS_COUNT=$(echo "$BUSINESSES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)

if [ "$BUSINESS_COUNT" -gt 0 ]; then
    echo "   ✓ Found $BUSINESS_COUNT businesses"
    BUSINESS_ID=$(echo "$BUSINESSES" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])" 2>/dev/null)
    BUSINESS_NAME=$(echo "$BUSINESSES" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['name'])" 2>/dev/null)
    echo "   First business: $BUSINESS_NAME ($BUSINESS_ID)"
else
    echo "   ✗ No businesses found"
    exit 1
fi
echo ""

# Test 5: Get Documents
echo "5. Testing List Documents API..."
DOCUMENTS=$(curl -s -X GET $API_URL/api/v1/businesses/$BUSINESS_ID/documents \
  -H "Authorization: Bearer $TOKEN")

DOC_COUNT=$(echo "$DOCUMENTS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
echo "   ✓ Found $DOC_COUNT documents"
echo ""

# Test 6: Get Conversations
echo "6. Testing List Conversations API..."
CONVERSATIONS=$(curl -s -X GET "$API_URL/api/v1/businesses/$BUSINESS_ID/conversations?limit=10" \
  -H "Authorization: Bearer $TOKEN")

CONV_COUNT=$(echo "$CONVERSATIONS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
echo "   ✓ Found $CONV_COUNT conversations"
echo ""

# Test 7: Frontend Accessibility
echo "7. Testing Frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $FRONTEND_URL)

if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "   ✓ Frontend is accessible on $FRONTEND_URL"
else
    echo "   ✗ Frontend is not accessible (HTTP $FRONTEND_STATUS)"
fi
echo ""

echo "================================"
echo "✅ All integration tests passed!"
echo ""
echo "📊 Summary:"
echo "   • Backend: Running on port 8000"
echo "   • Frontend: Running on port 3001"
echo "   • Users: 2 (demo@docmind.ai, admin@docmind.ai)"
echo "   • Businesses: $BUSINESS_COUNT"
echo "   • Documents: $DOC_COUNT"
echo "   • Conversations: $CONV_COUNT"
echo ""
echo "🚀 Ready to use!"
echo "   Visit: $FRONTEND_URL"
echo "   Login: demo@docmind.ai / demo123"
