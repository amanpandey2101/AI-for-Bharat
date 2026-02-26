import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

const pricingPlans = [
    {
        name: "Starter",
        description: "For individuals looking to organize personal history.",
        price: "₹0",
        frequency: "/month",
        features: [
            "Up to 500 memory entries",
            "Basic search",
            "1 AI team assistant",
            "Community support",
        ],
        buttonText: "Start for free",
        popular: false,
    },
    {
        name: "Teams",
        description:
            "For impactful teams that want to eliminate organizational memory loss.",
        price: "₹1,499",
        frequency: "/user/month",
        features: [
            "Unlimited memory entries",
            "Advanced semantic search",
            "10 AI team assistants",
            "Shared workspaces",
            "Priority email support",
            "Custom integrations",
        ],
        buttonText: "Get Started",
        popular: true,
    },
    {
        name: "Enterprise",
        description: "For large organizations with complex archiving needs.",
        price: "Custom",
        frequency: "",
        features: [
            "Everything in Teams, plus:",
            "Unlimited AI assistants",
            "SSO & advanced security",
            "Dedicated account manager",
            "Self-hosted option",
            "SLA guarantee",
        ],
        buttonText: "Contact Sales",
        popular: false,
    },
];

export default function PricingPage() {
    return (
        <div className="flex flex-col min-h-screen pt-32 pb-24 items-center justify-center font-sans px-4">
            <div className="text-center max-w-3xl mb-16">
                <h1 className="text-5xl font-semibold mb-6 tracking-tight">
                    Simple, transparent pricing
                </h1>
                <p className="text-xl text-gray-500">
                    Unlock your team's collective intelligence. Stop memory loss and build
                    the future with your archived history. No hidden fees.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl w-full">
                {pricingPlans.map((plan, index) => (
                    <Card
                        key={index}
                        className={cn(
                            "flex flex-col relative",
                            plan.popular ? "border-black shadow-xl scale-105" : "border-gray-200"
                        )}
                    >
                        {plan.popular && (
                            <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                                <span className="bg-black text-white text-xs font-bold uppercase tracking-wider py-1 px-3 rounded-full">
                                    Most Popular
                                </span>
                            </div>
                        )}
                        <CardHeader>
                            <CardTitle className="text-2xl">{plan.name}</CardTitle>
                            <CardDescription className="pt-2 min-h-[60px]">
                                {plan.description}
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="flex-grow">
                            <div className="flex items-baseline mb-6">
                                <span className="text-5xl font-bold tracking-tight">
                                    {plan.price}
                                </span>
                                <span className="text-gray-500 ml-1 font-medium">
                                    {plan.frequency}
                                </span>
                            </div>
                            <ul className="space-y-4">
                                {plan.features.map((feature, i) => (
                                    <li key={i} className="flex items-center">
                                        <Check className="h-5 w-5 text-green-500 mr-3 flex-shrink-0" />
                                        <span className="text-gray-700">{feature}</span>
                                    </li>
                                ))}
                            </ul>
                        </CardContent>
                        <CardFooter>
                            <Button
                                className={cn(
                                    "w-full cursor-pointer h-12 text-md transition-all",
                                    plan.popular
                                        ? "bg-black hover:shadow-lg hover:-translate-y-0.5 hover:bg-black"
                                        : ""
                                )}
                                variant={plan.popular ? "default" : "outline"}
                            >
                                {plan.buttonText}
                            </Button>
                        </CardFooter>
                    </Card>
                ))}
            </div>
        </div>
    );
}
