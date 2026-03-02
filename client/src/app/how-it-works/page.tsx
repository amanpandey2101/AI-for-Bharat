import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { TextAnimate } from "@/components/ui/text-animate";
import { Activity, BrainCircuit, GitCommitVertical, Search, ShieldCheck, Database } from "lucide-react";

const concepts = [
    {
        icon: <GitCommitVertical className="w-8 h-8 text-pink-500" />,
        title: "1. Passive Ingestion",
        description:
            "Our system seamlessly integrates with GitHub. When pull requests are created, code reviews submitted, or commits pushed, the Ingestion System silently captures the metadata, diffs, and discussions in real-time.",
    },
    {
        icon: <BrainCircuit className="w-8 h-8 text-indigo-500" />,
        title: "2. Agentic Inference",
        description:
            "The Orchestration Layer triggers specialized AI experts. The Code Archaeology Agent identifies decision points, while the Decision Inference Agent reconstructs the rationale behind architectural choices, treating them as first-class entities.",
    },
    {
        icon: <Database className="w-8 h-8 text-blue-500" />,
        title: "3. Knowledge Graph",
        description:
            "All extracted insights are stored in a persistent Decision Knowledge Graph. This links intents, code executions, authorities, and eventual outcomes, creating a bidirectional map of your product's evolutionary history.",
    },
    {
        icon: <ShieldCheck className="w-8 h-8 text-green-500" />,
        title: "4. Human Validation",
        description:
            "Trust is paramount. Each AI inference receives a Confidence Score. If the score is below 70%, the system drops the insight into a Human Validation Flow, ensuring your organizational truth remains accurate and high quality.",
    },
    {
        icon: <Search className="w-8 h-8 text-orange-500" />,
        title: "5. Semantic Querying",
        description:
            "Stop repeating architectural debates. Developers can ask natural language questions like 'Why was this abstraction chosen?' Our Query System performs semantic searches and delivers evidence-backed answers instantly.",
    },
    {
        icon: <Activity className="w-8 h-8 text-purple-500" />,
        title: "6. Continuous Learning",
        description:
            "As your team validates decisions and the codebase scales, the Learning Extraction Agent identifies patterns to continuously train the models. The result is a living, breathing institutional memory that outlasts employee turnover.",
    },
];

export default function HowItWorksPage() {
    return (
        <div className="min-h-screen pt-32 pb-24 px-4 font-sans bg-slate-50/50">
            <div className="max-w-4xl mx-auto flex flex-col items-center mb-16 text-center">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-pink-100/50 text-pink-600 font-medium text-sm mb-6 shadow-sm border border-pink-100">
                    <BrainCircuit className="w-4 h-4" />
                    <span>The engine behind the memory</span>
                </div>
                <h1 className="text-5xl md:text-6xl font-semibold mb-6 tracking-tight text-slate-900">
                    <TextAnimate animation="blurIn" by="word">
                        How Memora.Dev Works
                    </TextAnimate>
                </h1>
                <p className="text-xl text-slate-500 max-w-2xl leading-relaxed">
                    Modern workflows generate valuable architectural decisions that are
                    rarely documented. We passively observe, infer, and map your code
                    history so you never lose institutional knowledge again.
                </p>
            </div>

            <div className="max-w-6xl mx-auto relative">
                <div className="absolute left-1/2 top-4 bottom-4 w-px bg-slate-200 transform -translate-x-1/2 hidden md:block" />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-x-16 md:gap-y-12">
                    {concepts.map((concept, index) => (
                        <Card
                            key={index}
                            className={`border-none shadow-card hover:shadow-xl transition-all duration-300 hover:-translate-y-1 bg-white/70 backdrop-blur-md ${index % 2 === 0 ? "md:mt-0" : "md:mt-16"
                                }`}
                        >
                            <CardHeader>
                                <div className="w-14 h-14 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center mb-4 shadow-sm">
                                    {concept.icon}
                                </div>
                                <CardTitle className="text-2xl text-slate-800">
                                    {concept.title}
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <CardDescription className="text-base leading-relaxed text-slate-500">
                                    {concept.description}
                                </CardDescription>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>

            <div className="max-w-3xl mx-auto mt-32 text-center bg-white p-12 rounded-3xl shadow-card border border-slate-100">
                <h2 className="text-3xl font-semibold mb-4 text-slate-900">
                    Ready to eliminate organizational amnesia?
                </h2>
                <p className="text-slate-500 mb-8 max-w-xl mx-auto">
                    Start building your team&apos;s decision knowledge graph today. Connect your GitHub repository in seconds.
                </p>
                <button className="bg-black text-white px-8 py-4 rounded-xl font-medium hover:bg-slate-800 transition-colors shadow-lg hover:shadow-xl hover:-translate-y-0.5 max-w-sm w-full">
                    Integrate with GitHub
                </button>
            </div>
        </div>
    );
}
