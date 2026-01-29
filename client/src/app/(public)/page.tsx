import Link from "next/link";
import { 
  ArrowRight, 
  Search, 
  MessageSquare, 
  FileText, 
  Users, 
  Database, 
  Sparkles,
  Zap,
  BookOpen,
  CheckCircle2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-16 md:pt-24 lg:pt-32 pb-16">
        <div className="container px-4 md:px-6 mx-auto">
          <div className="flex flex-col items-center text-center space-y-8">
            <Badge variant="secondary" className="px-4 py-2 text-sm bg-primary/10 text-primary hover:bg-primary/20 transition-colors">
              ✨ AI-Powered Learning Platform
            </Badge>
            
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600 dark:to-purple-400">
              Master Your Coursework <br className="hidden md:inline" />
              with Intelligent Tools
            </h1>
            
            <p className="max-w-[800px] text-lg md:text-xl text-muted-foreground leading-relaxed">
              ZenLearn transforms fragmented course materials into an organized, interactive knowledge base. 
              Search notes, digitize handwriting, and get instant answers powered by AI.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 w-full justify-center pt-4">
              <Link href="/dashboard">
                <Button size="lg" className="w-full sm:w-auto text-lg h-12 px-8 gap-2 shadow-lg shadow-primary/25">
                  Get Started <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
              <Link href="/chat">
                <Button variant="outline" size="lg" className="w-full sm:w-auto text-lg h-12 px-8">
                  Try the Assistant
                </Button>
              </Link>
            </div>
            
            {/* Abstract UI Preview */}
            <div className="w-full max-w-5xl mt-16 p-4 bg-muted/30 rounded-xl border border-border/50 shadow-2xl backdrop-blur-sm">
                <div className="aspect-[16/9] w-full bg-background rounded-lg border border-border overflow-hidden relative">
                    <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-purple-500/5"></div>
                    
                    {/* Mock Interface Elements */}
                    <div className="absolute top-0 left-0 right-0 h-14 border-b border-border bg-card/50 flex items-center px-6 gap-2">
                        <div className="flex gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-400/80"></div>
                            <div className="w-3 h-3 rounded-full bg-yellow-400/80"></div>
                            <div className="w-3 h-3 rounded-full bg-green-400/80"></div>
                        </div>
                    </div>
                    
                    <div className="absolute top-20 left-10 right-10 bottom-10 grid grid-cols-12 gap-6">
                        <div className="col-span-3 bg-muted/50 rounded-lg hidden md:flex flex-col p-4 gap-3">
                            <div className="h-4 w-20 bg-primary/20 rounded-md mb-2"></div>
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="h-8 w-full bg-background/50 rounded-md flex items-center px-3 gap-2">
                                    <div className="w-4 h-4 rounded-full bg-muted-foreground/20"></div>
                                    <div className="h-2 w-16 bg-muted-foreground/20 rounded-full"></div>
                                </div>
                            ))}
                        </div>
                        <div className="col-span-12 md:col-span-9 bg-card rounded-lg border border-border shadow-sm p-6 flex flex-col gap-4">
                            <div className="flex justify-between items-center mb-2">
                                <div className="h-8 w-1/3 bg-primary/10 rounded-md flex items-center px-4">
                                    <span className="text-sm font-medium text-primary/70">Course Overview</span>
                                </div>
                                <div className="h-8 w-24 bg-muted rounded-md"></div>
                            </div>
                            
                            <div className="space-y-3">
                                <div className="h-16 w-full bg-muted/30 rounded-md border border-border/50 p-3 flex gap-3 items-center">
                                    <div className="w-10 h-10 rounded bg-blue-500/10 flex items-center justify-center text-blue-500">
                                        <BookOpen className="w-5 h-5" />
                                    </div>
                                    <div className="flex-1 space-y-2">
                                        <div className="h-4 w-1/4 bg-muted-foreground/10 rounded"></div>
                                        <div className="h-3 w-1/2 bg-muted-foreground/10 rounded"></div>
                                    </div>
                                </div>
                                <div className="h-16 w-full bg-muted/30 rounded-md border border-border/50 p-3 flex gap-3 items-center">
                                    <div className="w-10 h-10 rounded bg-purple-500/10 flex items-center justify-center text-purple-500">
                                        <Sparkles className="w-5 h-5" />
                                    </div>
                                    <div className="flex-1 space-y-2">
                                        <div className="h-4 w-1/3 bg-muted-foreground/10 rounded"></div>
                                        <div className="h-3 w-2/3 bg-muted-foreground/10 rounded"></div>
                                    </div>
                                </div>
                            </div>
                            
                            <div className="mt-auto flex gap-3">
                                <div className="h-10 w-full bg-muted/50 rounded-md flex items-center px-4 text-sm text-muted-foreground">
                                    Ask a question about your courses...
                                </div>
                                <div className="h-10 w-12 bg-primary rounded-md flex items-center justify-center text-primary-foreground">
                                    <ArrowRight className="w-4 h-4" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24 bg-muted/30">
        <div className="container px-4 md:px-6 mx-auto">
          <div className="text-center mb-16 space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold">Everything You Need to Excel</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              A complete suite of tools designed to help university students learn faster and more effectively.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard 
              icon={<Search className="w-6 h-6 text-blue-500" />}
              title="Intelligent Search"
              description="Find exactly what you need across slides, PDFs, and code files using semantic RAG capability."
            />
            <FeatureCard 
              icon={<Sparkles className="w-6 h-6 text-purple-500" />}
              title="AI Assistant"
              description="Chat with an AI that understands your specific course context and materials."
            />
            <FeatureCard 
              icon={<FileText className="w-6 h-6 text-green-500" />}
              title="Notes Digitizer"
              description="Convert handwritten class notes into clean, structured LaTeX documents instantly."
            />
            <FeatureCard 
              icon={<Users className="w-6 h-6 text-orange-500" />}
              title="Community Support"
              description="Discuss problems with peers and get automated help when no one is around."
            />
             <FeatureCard 
              icon={<Database className="w-6 h-6 text-red-500" />}
              title="Content Management"
              description="Organized repository for all your theory and lab materials, categorized and searchable."
            />
            <FeatureCard 
              icon={<BookOpen className="w-6 h-6 text-indigo-500" />}
              title="Study Materials"
              description="Generate summaries, flashcards, and practice questions from your upload content."
            />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24">
        <div className="container px-4 md:px-6 mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8">
              <h2 className="text-3xl md:text-4xl font-bold leading-tight">
                Streamline Your Study Workflow
              </h2>
              <p className="text-lg text-muted-foreground">
                Stop wasting time searching through fragmented files. ZenLearn brings everything together.
              </p>
              
              <div className="space-y-6">
                <Step 
                  number="1"
                  title="Upload Materials"
                  description="Upload your lecture slides, PDFs, lab codes, and handwritten notes."
                />
                <Step 
                  number="2"
                  title="AI Analysis"
                  description="Our system processes, indexes, and understands your content automatically."
                />
                <Step 
                  number="3"
                  title="Learn & Interact"
                  description="Query the knowledge base, generate summaries, and collaborate with peers."
                />
              </div>
            </div>
            
            <div className="relative">
              <div className="absolute -inset-4 bg-gradient-to-r from-primary to-purple-600 rounded-2xl opacity-10 blur-2xl"></div>
              <Card className="relative h-[500px] border-border shadow-xl overflow-hidden flex flex-col">
                 <div className="p-6 border-b bg-muted/40 flex items-center justify-between">
                    <span className="font-semibold">ZenLearn Assistant</span>
                    <Badge variant="outline" className="bg-background">Online</Badge>
                 </div>
                 <div className="flex-1 p-6 space-y-6 overflow-hidden">
                    {/* Chat Simulation */}
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">AI</div>
                        <div className="p-3 bg-muted rounded-lg rounded-tl-none max-w-[80%] text-sm">
                            Hello! I'm ready to help with your course materials. What are you working on today?
                        </div>
                    </div>
                    
                    <div className="flex gap-3 flex-row-reverse">
                         <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center text-xs font-bold text-purple-700 dark:text-purple-300">U</div>
                         <div className="p-3 bg-primary text-primary-foreground rounded-lg rounded-tr-none max-w-[80%] text-sm">
                            Can you explain the difference between BFS and DFS based on the lecture slides?
                        </div>
                    </div>
                    
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">AI</div>
                        <div className="p-3 bg-muted rounded-lg rounded-tl-none max-w-[80%] text-sm space-y-2">
                            <p>According to <strong>Lecture 3: Graph Algorithms</strong>:</p>
                            <p><strong>BFS (Breadth-First Search)</strong> explores neighbors level by level using a Queue.</p>
                            <p><strong>DFS (Depth-First Search)</strong> explores as far as possible along each branch before backtracking using a Stack.</p>
                            <div className="pt-2 flex gap-2">
                                <Badge variant="outline" className="text-xs border-primary/30 bg-primary/5">Source: slide_03.pdf (p.14)</Badge>
                            </div>
                        </div>
                    </div>
                 </div>
                 <div className="p-4 border-t bg-muted/20">
                    <div className="h-10 bg-background border rounded-md w-full animate-pulse"></div>
                 </div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-primary text-primary-foreground">
        <div className="container px-4 md:px-6 mx-auto text-center space-y-8">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight">Ready to Upgrade Your Learning?</h2>
          <p className="text-lg md:text-xl text-primary-foreground/80 max-w-2xl mx-auto">
            Join the platform that helps you study smarter, not harder.
          </p>
          <Link href="/dashboard">
             <Button variant="secondary" size="lg" className="h-14 px-8 text-lg font-semibold shadow-xl">
               Get Started Now <Zap className="w-5 h-5 ml-2 fill-current" />
             </Button>
          </Link>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="py-12 border-t bg-muted/10">
        <div className="container px-4 md:px-6 mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2 font-bold text-xl">
                <span>ZenLearn</span>
            </div>
            <p className="text-sm text-muted-foreground">
                © 2026 BCF Hackathon Project. All rights reserved.
            </p>
            <div className="flex gap-6">
                <Link href="#" className="text-sm text-muted-foreground hover:text-foreground">Privacy</Link>
                <Link href="#" className="text-sm text-muted-foreground hover:text-foreground">Terms</Link>
                <Link href="#" className="text-sm text-muted-foreground hover:text-foreground">GitHub</Link>
            </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
    return (
        <Card className="border-border/50 hover:border-primary/50 transition-colors shadow-sm hover:shadow-md">
            <CardHeader>
                <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center mb-2">
                    {icon}
                </div>
                <CardTitle className="text-xl">{title}</CardTitle>
            </CardHeader>
            <CardContent>
                <p className="text-muted-foreground">{description}</p>
            </CardContent>
        </Card>
    );
}

function Step({ number, title, description }: { number: string, title: string, description: string }) {
    return (
        <div className="flex gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold shadow-lg shadow-primary/20">
                {number}
            </div>
            <div>
                <h3 className="text-xl font-bold mb-1">{title}</h3>
                <p className="text-muted-foreground">{description}</p>
            </div>
        </div>
    );
}
