'use client'

import React, { useState } from 'react'
import {
  Menu,
  X,
  Zap,
  Globe,
  Code,
  Smartphone,
  Shield,
  ArrowRight,
  Star,
  Github,
  Twitter,
  Linkedin,
  Mail,
  Phone,
  MapPin,
  Download
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'

export default function LandingPage() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [currentPage, setCurrentPage] = useState<'home' | 'clone'>('home')

  // Clone page state
  const [url, setUrl] = useState<string>('')
  const [html, setHtml] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  const features = [
    {
      icon: <Globe className="w-8 h-8" />,
      title: 'Website Cloning',
      description: 'Clone any website with pixel-perfect accuracy and responsive design'
    },
    {
      icon: <Code className="w-8 h-8" />,
      title: 'Clean Code Export',
      description: 'Export clean, maintainable HTML, CSS, and JavaScript code'
    },
    {
      icon: <Smartphone className="w-8 h-8" />,
      title: 'Mobile Responsive',
      description: 'All cloned websites are automatically optimized for mobile devices'
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: 'Lightning Fast',
      description: 'Clone websites in seconds with our advanced AI-powered engine'
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: 'Secure & Private',
      description: 'Your data is encrypted and we never store your cloned content'
    }
  ]

  const testimonials = [
    {
      name: 'Sarah Chen',
      role: 'Frontend Developer',
      content: "This tool saved me hours of work. The cloning accuracy is incredible!",
      rating: 5
    },
    {
      name: 'Mike Johnson',
      role: 'Web Designer',
      content: "Best website cloning tool I've ever used. Clean code export is a game-changer.",
      rating: 5
    },
    {
      name: 'Emma Wilson',
      role: 'Startup Founder',
      content: 'Perfect for rapid prototyping. Highly recommend to any developer.',
      rating: 5
    }
  ]

  // Triggers the cloning process
  // Updated to handle response types correctly
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setHtml(null)
    setLoading(true)
  
    try {
      const res = await fetch('/api/clone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      })
  
      const contentType = res.headers.get('content-type')
      console.log('Response content-type:', contentType)
      const isJson = res.headers.get('content-type')?.includes('application/json')
  
      if (!res.ok) {
        const errMessage = isJson
          ? (await res.json()).detail
          : await res.text()
        throw new Error(errMessage || 'Unknown error occurred')
      }
  
      const data = isJson ? await res.json() : null
      setHtml(data?.html || '')
    } catch (err: any) {
      console.error('Frontend error:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  

  const downloadHtml = () => {
    if (!html) return
    const blob = new Blob([html], { type: 'text/html' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = 'cloned_site.html'
    link.click()
    URL.revokeObjectURL(link.href)
  }

  // If we’re on the “clone” page, render the clone UI:
  if (currentPage === 'clone') {
    return (
      <div className="min-h-screen bg-background">
        {/* Navbar for Clone Page */}
        <nav className="border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <Button variant="ghost" onClick={() => setCurrentPage('home')}>
                ← Back to Home
              </Button>

              <div className="hidden md:flex items-center space-x-8">
                <Button variant="outline">Sign In</Button>
                <Button>Get Started</Button>
              </div>
            </div>
          </div>
        </nav>

        {/* Clone Page Content */}
        <div className="pt-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-12">
              <h1 className="text-4xl md:text-6xl font-bold mb-6">
                Website <span className="text-muted-foreground">Cloner</span>
              </h1>
              <p className="text-xl text-muted-foreground mb-8">
                Enter any public website URL to clone it instantly
              </p>
            </div>

            <Card className="p-8 mb-8">
              <form onSubmit={handleSubmit} className="flex gap-4 mb-6">
                <Input
                  type="url"
                  placeholder="Enter a public website URL (e.g., https://example.com)"
                  className="flex-1 text-lg py-6"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required
                />
                <Button type="submit" className="px-8 py-6 text-lg" disabled={loading}>
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-foreground mr-2"></div>
                      Cloning...
                    </>
                  ) : (
                    <>
                      <Zap className="w-5 h-5 mr-2" />
                      Clone
                    </>
                  )}
                </Button>
              </form>

              {error && (
                <div className="bg-destructive/20 border border-destructive/30 rounded-lg p-4 mb-6">
                  <p className="text-destructive-foreground">{error}</p>
                </div>
              )}
            </Card>

            {html && (
              <div className="space-y-6">
                <Card className="p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-2xl font-bold">Cloned Website Preview</h2>
                    <Button onClick={downloadHtml} variant="secondary">
                      <Download className="w-4 h-4 mr-2" />
                      Download HTML
                    </Button>
                  </div>

                  {/* Render the entire returned HTML inside an iframe */}
                  <div className="border rounded-lg overflow-hidden" style={{ height: '600px' }}>
                    <iframe
                      title="Cloned Preview"
                      srcDoc={html}
                      className="w-full h-full"
                      sandbox="allow-scripts allow-same-origin"
                    />
                  </div>
                </Card>
              </div>
            )}

          </div>
        </div>
      </div>
    )
  }

  // Home page below (unchanged)
  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <nav className="border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-xl">Website Cloner</span>
            </div>

            <div className="hidden md:flex items-center space-x-8">
              <a
                href="#features"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Features
              </a>
              <a
                href="#testimonials"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Reviews
              </a>
              <a
                href="#contact"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Contact
              </a>
              <Button variant="outline">Sign In</Button>
              <Button>Get Started</Button>
            </div>

            <div className="md:hidden">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              >
                {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t">
            <div className="px-2 pt-2 pb-3 space-y-1">
              <a
                href="#features"
                className="block px-3 py-2 text-muted-foreground hover:text-foreground"
              >
                Features
              </a>
              <a
                href="#testimonials"
                className="block px-3 py-2 text-muted-foreground hover:text-foreground"
              >
                Reviews
              </a>
              <a
                href="#contact"
                className="block px-3 py-2 text-muted-foreground hover:text-foreground"
              >
                Contact
              </a>
              <div className="flex space-x-2 px-3 py-2">
                <Button variant="outline" size="sm">
                  Sign In
                </Button>
                <Button size="sm">Get Started</Button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Sidebar - Quick Actions */}
      <div className="fixed left-4 top-1/2 transform -translate-y-1/2 z-40 hidden lg:block">
        <Card className="p-3">
          <div className="flex flex-col space-y-3">
            <Button size="sm" variant="ghost" className="p-2">
              <Github className="w-5 h-5" />
            </Button>
            <Button size="sm" variant="ghost" className="p-2">
              <Twitter className="w-5 h-5" />
            </Button>
            <Button size="sm" variant="ghost" className="p-2">
              <Linkedin className="w-5 h-5" />
            </Button>
          </div>
        </Card>
      </div>

      {/* Hero Section */}
      <section className="pt-20 pb-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <Badge className="mb-6">✨ AI-Powered Website Cloning</Badge>
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            Clone Any Website
            <br />
            <span className="text-muted-foreground">In Seconds</span>
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto leading-relaxed">
            Transform any website into clean, maintainable code with our advanced
            AI-powered cloning engine. Perfect for developers, designers, and agencies.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button
              size="lg"
              className="px-8 py-4 text-lg"
              onClick={() => setCurrentPage('clone')}
            >
              Start Cloning Now
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <Button size="lg" variant="outline" className="px-8 py-4 text-lg">
              Watch Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Powerful Features</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Everything you need to clone, customize, and deploy websites with ease
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="p-6 hover:bg-accent transition-all duration-300">
                <div className="mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">What Developers Say</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Join thousands of satisfied developers who trust our platform
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="p-6">
                <div className="flex mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star
                      key={i}
                      className="w-5 h-5 text-muted-foreground fill-current"
                    />
                  ))}
                </div>
                <p className="text-muted-foreground mb-4 italic">
                  "{testimonial.content}"
                </p>
                <div>
                  <p className="font-semibold">{testimonial.name}</p>
                  <p className="text-muted-foreground text-sm">{testimonial.role}</p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Get in Touch</h2>
            <p className="text-xl text-muted-foreground">
              Have questions? We'd love to hear from you.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            <div>
              <h3 className="text-2xl font-semibold mb-6">Contact Info</h3>
              <div className="space-y-4">
                <div className="flex items-center text-muted-foreground">
                  <Mail className="w-5 h-5 mr-3" />
                  hello@websitecloner.app
                </div>
                <div className="flex items-center text-muted-foreground">
                  <Phone className="w-5 h-5 mr-3" />
                  +1 (555) 123-4567
                </div>
                <div className="flex items-center text-muted-foreground">
                  <MapPin className="w-5 h-5 mr-3" />
                  San Francisco, CA
                </div>
              </div>
            </div>

            <Card className="p-6">
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input placeholder="First Name" />
                  <Input placeholder="Last Name" />
                </div>
                <Input placeholder="Email" type="email" />
                <Textarea placeholder="Message" rows={4} />
                <Button className="w-full">Send Message</Button>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-muted rounded-lg flex items-center justify-center">
                  <Globe className="w-5 h-5" />
                </div>
                <span className="font-bold text-xl">Website Cloner</span>
              </div>
              <p className="text-muted-foreground text-sm">
                The most advanced website cloning platform for modern developers.
              </p>
            </div>

            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-muted-foreground text-sm">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    API
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Documentation
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-muted-foreground text-sm">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    About
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Blog
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Careers
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Contact
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-muted-foreground text-sm">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Privacy
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Terms
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Security
                  </a>
                </li>
              </ul>
            </div>
          </div>

          <Separator className="my-8" />

          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-muted-foreground text-sm">
              © 2025 Website Cloner. All rights reserved. Built by Parin.
            </p>
            <div className="flex space-x-4 mt-4 md:mt-0">
              <a
                href="#"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <Github className="w-5 h-5" />
              </a>
              <a
                href="#"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <Twitter className="w-5 h-5" />
              </a>
              <a
                href="#"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <Linkedin className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
