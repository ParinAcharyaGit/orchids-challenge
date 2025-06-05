'use client'

import React, { useState, useEffect, useRef } from 'react'
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
  Download,
  MessageSquare
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export default function LandingPage() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [currentPage, setCurrentPage] = useState<'home' | 'clone'>('home')

  // Clone page state
  const [url, setUrl] = useState<string>('')
  const [rawHtml, setRawHtml] = useState<string | null>(null)
  const [generatedHtml, setGeneratedHtml] = useState<string | null>(null)
  const [currentHtml, setCurrentHtml] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState('gemini-2.5-pro-preview-05-06')
  const [processingStep, setProcessingStep] = useState<'idle' | 'scraping' | 'generating' | 'complete' | 'error' | 'editing'>('idle')

  // --- Chat Panel State ---
  const [isChatPanelOpen, setIsChatPanelOpen] = useState(true);
  const [chatMessages, setChatMessages] = useState<{sender: 'user' | 'ai', text: string}[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const chatMessagesEndRef = useRef<HTMLDivElement>(null);

  // --- State to hold the path of the latest scraped HTML ---
  const [latestScrapedHtmlPath, setLatestScrapedHtmlPath] = useState<string | null>(null);

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

  const availableModels = [
    { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B Versatile (Groq)' },
    { id: 'gemini-2.5-pro-preview-05-06', name: 'Gemini 2.5 Pro' },
    { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B (128K Context, Groq)' }
  ]

  // --- Fetch latest scraped HTML path on page load or when clone is complete ---
  useEffect(() => {
      const fetchLatestScraped = async () => {
          try {
              const res = await fetch('/api/latest-scraped');
              const data = await res.json();
              if (res.ok && data.latest_scraped_path) {
                  setLatestScrapedHtmlPath(data.latest_scraped_path);
                  console.log("Fetched latest scraped HTML path:", data.latest_scraped_path);
              } else {
                   console.warn("No latest scraped HTML file found or error:", data.error);
                   setLatestScrapedHtmlPath(null);
              }
          } catch (err) {
              console.error("Failed to fetch latest scraped HTML path:", err);
              setLatestScrapedHtmlPath(null);
          }
      };

      if (currentPage === 'clone') {
           fetchLatestScraped();
      }

  }, [currentPage]);

   // --- Auto-scroll chat messages ---
   useEffect(() => {
     chatMessagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
   }, [chatMessages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setRawHtml(null)
    setGeneratedHtml(null)
    setCurrentHtml(null)
    setLoading(true)
    setProcessingStep('scraping')
    setLatestScrapedHtmlPath(null)

    try {
      console.log("Attempting to scrape:", url)
      // Step 1: Scrape the website
      const scrapeRes = await fetch('/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      })

      const scrapeData = await scrapeRes.json()

      if (!scrapeRes.ok) {
        throw new Error(scrapeData.detail || 'Failed to scrape website')
      }

      console.log("Scraping successful. Raw HTML received.", scrapeData)
      setRawHtml(scrapeData.raw_html)
      setCurrentHtml(scrapeData.raw_html)
      setLatestScrapedHtmlPath(scrapeData.raw_html_path)
      setProcessingStep('generating')
      setLoading(false)

      // Step 2: Generate clean HTML (can happen in parallel or sequentially after showing raw)
      // For simplicity here, we call generate after scraping completes and raw is displayed.
      console.log("Attempting to generate HTML with model:", selectedModel)
      const generateRes = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_html_path: scrapeData.raw_html_path, model: selectedModel })
      })

      const generateData = await generateRes.json()

      if (!generateRes.ok) {
        throw new Error(generateData.detail || 'Failed to generate HTML')
      }

      console.log("HTML generation successful. Generated HTML received.", generateData)
      setGeneratedHtml(generateData.generated_html)
      setTimeout(() => {
        setCurrentHtml(generateData.generated_html)
        setProcessingStep('complete')
        console.log("Displayed generated HTML.")
      }, 2000)

    } catch (err: any) {
      console.error('Frontend error during cloning process:', err)
      setError(err.message)
      setProcessingStep('error')
      setLoading(false)
    }
  }

  // --- Handle Sending Edit Instruction ---
  const handleSendEdit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!chatInput.trim() || !currentHtml) return;

      const userMessage = chatInput;
      setChatMessages(prev => [...prev, { sender: 'user', text: userMessage }]);
      setChatInput('');
      setIsEditing(true);
      setProcessingStep('editing');

      try {
          console.log("Attempting to edit HTML with instruction:", userMessage);
          const editRes = await fetch('/api/edit', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                  html_content: currentHtml,
                  instruction: userMessage,
                  model: 'gemini-2.5-pro-preview-05-06'
              })
          });

          const editData = await editRes.json();

          if (!editRes.ok) {
              throw new Error(editData.detail || 'Failed to edit HTML');
          }

          console.log("HTML editing successful. Edited HTML received.", editData);

          // Add AI response to chat
          setChatMessages(prev => [...prev, { 
              sender: 'ai', 
              text: "Edit applied successfully. The changes have been saved and displayed." 
          }]);

          // Update the displayed HTML
          setGeneratedHtml(editData.edited_html);
          setCurrentHtml(editData.edited_html);
          setProcessingStep('complete');
          setError('');

      } catch (err: any) {
          console.error('Frontend error during editing process:', err);
          setError(err.message);
          setProcessingStep('error');
          setChatMessages(prev => [...prev, { 
              sender: 'ai', 
              text: `Error applying edit: ${err.message}` 
          }]);
      } finally {
          setIsEditing(false);
      }
  };

  const downloadHtml = () => {
    if (!currentHtml) return
    const blob = new Blob([currentHtml], { type: 'text/html' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    let filename = 'cloned_site.html';
    if (processingStep === 'complete') {
        if(generatedHtml && currentHtml === generatedHtml) {
             filename = 'cloned_site_generated.html';
        } else if (rawHtml && currentHtml === rawHtml) {
             filename = 'cloned_site_raw.html';
        } else {
             filename = 'cloned_site_edited.html';
        }
    } else if (rawHtml && currentHtml === rawHtml) {
         filename = 'cloned_site_raw.html';
    } else {
         filename = 'cloned_site.html';
    }

    link.download = filename;
    link.click()
    URL.revokeObjectURL(link.href)
  }

  if (currentPage === 'clone') {
    return (
      <div className="min-h-screen bg-background flex">
        <div className={`flex-1 transition-all duration-300 ${isChatPanelOpen ? 'mr-80' : 'mr-0'}`}>
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
                        <form onSubmit={handleSubmit} className="flex gap-4 mb-6 items-start">
                            <Input
                                type="url"
                                placeholder="Enter a public website URL (e.g., https://example.com)"
                                className="flex-1 text-lg py-6"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                required
                                disabled={loading || isEditing}
                            />
                            <Select value={selectedModel} onValueChange={setSelectedModel} disabled={loading || isEditing}>
                                <SelectTrigger className="w-[200px] h-[56px] text-lg">
                                    <SelectValue placeholder="Select AI Model" />
                                </SelectTrigger>
                                <SelectContent>
                                    {availableModels.map((model) => (
                                        <SelectItem key={model.id} value={model.id}>
                                            {model.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <Button type="submit" className="px-8 py-6 text-lg" disabled={loading || isEditing}>
                                {loading ? (
                                    <>
                                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-foreground mr-2"></div>
                                        {processingStep === 'scraping' ? 'Scraping...' : 'Generating...'}
                                    </>
                                ) : (
                                    <>
                                        <Zap className="w-5 h-5 mr-2" />
                                        Clone
                                    </>
                                )}
                            </Button>
                        </form>

                        {processingStep !== 'idle' && processingStep !== 'complete' && processingStep !== 'error' && !error && (
                            <div className="mb-4 text-center text-muted-foreground">
                                {processingStep === 'scraping' && 'Scraping website...'}
                                {processingStep === 'generating' && 'Scraping complete. Generating clean HTML...'}
                                {processingStep === 'editing' && 'Applying edit with AI...'}
                            </div>
                        )}

                        {error && (
                            <div className="bg-destructive/20 border border-destructive/30 rounded-lg p-4 mb-6">
                                <p className="text-destructive-foreground">{error}</p>
                            </div>
                        )}
                    </Card>

                    {currentHtml && (
                        <div className="space-y-6">
                            <Card className="p-6">
                                <div className="flex justify-between items-center mb-4">
                                    <h2 className="text-2xl font-bold">
                                        {processingStep === 'complete' ?
                                            (generatedHtml && currentHtml === generatedHtml ? 'Generated HTML Preview' : (rawHtml && currentHtml === rawHtml ? 'Scraped HTML Preview' : 'Edited HTML Preview'))
                                            : 'Scraped HTML Preview'
                                        }
                                    </h2>
                                    <Button onClick={downloadHtml} variant="secondary">
                                        <Download className="w-4 h-4 mr-2" />
                                        Download HTML
                                    </Button>
                                </div>

                                <div className="border rounded-lg overflow-hidden" style={{ height: '600px' }}>
                                    <iframe
                                        title="Cloned Preview"
                                        srcDoc={currentHtml}
                                        className="w-full h-full"
                                        sandbox="allow-scripts allow-same-origin"
                                    />
                                </div>

                                {(rawHtml || generatedHtml) && (
                                     <div className="mt-4 text-center text-muted-foreground">
                                         {rawHtml && generatedHtml && processingStep === 'complete' && currentHtml !== rawHtml && (
                                             <Button variant="link" onClick={() => setCurrentHtml(rawHtml)} className="p-0 ml-2">Show Raw HTML</Button>
                                         )}
                                         {rawHtml && generatedHtml && processingStep === 'complete' && currentHtml !== generatedHtml && (
                                             <Button variant="link" onClick={() => setCurrentHtml(generatedHtml)} className="p-0 ml-2">Show Generated HTML</Button>
                                         )}
                                     </div>
                                )}
                            </Card>
                        </div>
                    )}
                </div>
            </div>
        </div>

        <div className={`fixed inset-y-0 right-0 w-80 bg-card border-l transition-transform duration-300 ease-in-out ${isChatPanelOpen ? 'translate-x-0' : 'translate-x-full'}`}>
            <div className="flex flex-col h-full">
                <div className="flex items-center justify-between p-4 border-b">
                    <h3 className="text-lg font-semibold">AI Editor Chat</h3>
                    <Button variant="ghost" size="sm" onClick={() => setIsChatPanelOpen(false)}>
                        <X className="w-5 h-5" />
                    </Button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {chatMessages.map((msg, index) => (
                        <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[80%] rounded-lg p-3 ${
                                msg.sender === 'user' 
                                    ? 'bg-primary text-primary-foreground' 
                                    : 'bg-muted'
                            }`}>
                                {msg.text}
                            </div>
                        </div>
                    ))}
                    {isEditing && (
                        <div className="flex justify-start">
                            <div className="max-w-[80%] rounded-lg p-3 bg-muted">
                                <div className="animate-pulse">Processing edit...</div>
                            </div>
                        </div>
                    )}
                    <div ref={chatMessagesEndRef} />
                </div>

                <div className="p-4 border-t">
                    <form onSubmit={handleSendEdit} className="flex flex-col gap-2">
                        <Textarea
                            placeholder="Type your editing instruction here..."
                            value={chatInput}
                            onChange={(e) => setChatInput(e.target.value)}
                            disabled={isEditing || loading}
                            className="min-h-[100px] resize-none"
                        />
                        <Button 
                            type="submit" 
                            disabled={isEditing || loading || !chatInput.trim()}
                            className="w-full"
                        >
                            {isEditing ? (
                                <div className="flex items-center">
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-foreground mr-2"></div>
                                    Processing...
                                </div>
                            ) : (
                                <div className="flex items-center">
                                    <MessageSquare className="w-4 h-4 mr-2" />
                                    Send Edit
                                </div>
                            )}
                        </Button>
                    </form>
                </div>
            </div>
        </div>

        {currentPage === 'clone' && (
            <Button
                variant="secondary"
                size="icon"
                className={`fixed bottom-4 right-4 rounded-full shadow-lg transition-transform duration-300 ${isChatPanelOpen ? 'translate-x-[-21rem]' : 'translate-x-0'}`}
                onClick={() => setIsChatPanelOpen(!isChatPanelOpen)}
                disabled={loading}
            >
                <MessageSquare className="w-6 h-6" />
            </Button>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
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
