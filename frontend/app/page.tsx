import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <span className="text-2xl font-bold text-primary-600">🤖 DocMind AI</span>
            </div>
            <div className="flex gap-4">
              <Link 
                href="/login"
                className="px-4 py-2 text-gray-700 hover:text-gray-900 font-medium"
              >
                Login
              </Link>
              <Link 
                href="/register"
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-5xl md:text-6xl font-extrabold text-gray-900 mb-6">
            Custom AI Chatbot Builder
            <span className="block text-primary-600 mt-2">For Your Business</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Train AI on your business documents, PDFs, and website content. 
            Create intelligent chatbots that answer customer questions 24/7.
          </p>
          <div className="flex justify-center gap-4">
            <Link 
              href="/register"
              className="px-8 py-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-semibold text-lg shadow-lg"
            >
              Start Free Trial
            </Link>
            <Link 
              href="#demo"
              className="px-8 py-4 bg-white text-primary-600 rounded-lg hover:bg-gray-50 font-semibold text-lg border-2 border-primary-600"
            >
              Watch Demo
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="mt-24 grid md:grid-cols-3 gap-8">
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="text-4xl mb-4">📄</div>
            <h3 className="text-xl font-bold mb-3">Upload Documents</h3>
            <p className="text-gray-600">
              Upload PDFs, txt files, or provide website URLs. Our AI processes and learns from your content.
            </p>
          </div>
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-bold mb-3">AI Training</h3>
            <p className="text-gray-600">
              Advanced RAG technology ensures accurate answers based only on your business data.
            </p>
          </div>
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="text-4xl mb-4">💬</div>
            <h3 className="text-xl font-bold mb-3">Easy Integration</h3>
            <p className="text-gray-600">
              Embed your chatbot on any website with one line of code. Works on all platforms.
            </p>
          </div>
        </div>

        {/* Pricing */}
        <div className="mt-24">
          <h2 className="text-4xl font-bold text-center mb-12">Simple Pricing</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {/* Free */}
            <div className="bg-white p-6 rounded-xl shadow-lg">
              <h3 className="text-xl font-bold mb-2">Free</h3>
              <div className="text-3xl font-bold mb-4">₹0<span className="text-lg text-gray-600">/mo</span></div>
              <ul className="space-y-2 text-gray-600 mb-6">
                <li>✓ 50 queries/month</li>
                <li>✓ 1 document</li>
                <li>✓ Basic support</li>
              </ul>
              <Link href="/register" className="block w-full text-center px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium">
                Start Free
              </Link>
            </div>

            {/* Starter */}
            <div className="bg-white p-6 rounded-xl shadow-lg border-2 border-primary-600">
              <div className="text-xs font-bold text-primary-600 mb-2">POPULAR</div>
              <h3 className="text-xl font-bold mb-2">Starter</h3>
              <div className="text-3xl font-bold mb-4">₹999<span className="text-lg text-gray-600">/mo</span></div>
              <ul className="space-y-2 text-gray-600 mb-6">
                <li>✓ 1,000 queries/month</li>
                <li>✓ 10 documents</li>
                <li>✓ Custom branding</li>
                <li>✓ Analytics</li>
              </ul>
              <Link href="/register" className="block w-full text-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium">
                Get Started
              </Link>
            </div>

            {/* Pro */}
            <div className="bg-white p-6 rounded-xl shadow-lg">
              <h3 className="text-xl font-bold mb-2">Pro</h3>
              <div className="text-3xl font-bold mb-4">₹2,999<span className="text-lg text-gray-600">/mo</span></div>
              <ul className="space-y-2 text-gray-600 mb-6">
                <li>✓ 10,000 queries/month</li>
                <li>✓ 50 documents</li>
                <li>✓ WhatsApp integration</li>
                <li>✓ Priority support</li>
              </ul>
              <Link href="/register" className="block w-full text-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium">
                Get Started
              </Link>
            </div>

            {/* Enterprise */}
            <div className="bg-white p-6 rounded-xl shadow-lg">
              <h3 className="text-xl font-bold mb-2">Enterprise</h3>
              <div className="text-3xl font-bold mb-4">₹9,999<span className="text-lg text-gray-600">/mo</span></div>
              <ul className="space-y-2 text-gray-600 mb-6">
                <li>✓ Unlimited queries</li>
                <li>✓ Unlimited documents</li>
                <li>✓ White-label</li>
                <li>✓ API access</li>
              </ul>
              <Link href="/register" className="block w-full text-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium">
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t bg-white mt-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center text-gray-600">
            <p className="mb-2">© 2026 DocMind AI. Built with Python, FastAPI, and Next.js.</p>
            <p className="text-sm">Production-ready AI chatbot platform for businesses</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
