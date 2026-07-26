import { Link } from "react-router-dom";
import {
  Users,
  Truck,
  Factory,
  Building2,
  Calendar,
  MapPin,
  ShoppingCart,
  ShieldCheck,
  Lock,
  Brain,
  Leaf,
  Droplets,
  Wind,
  TreePine,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { HeroSection } from "@/components/landing/HeroSection";
import { SectionContainer } from "@/components/layout/SectionContainer";
import { StatisticCard } from "@/components/landing/StatisticCard";
import { FeatureCard } from "@/components/landing/FeatureCard";
import { FaqAccordion } from "@/components/landing/FaqAccordion";
import { SeoHead } from "@/components/seo/SeoHead";

const statistics = [
  { value: "2M+", label: "Waste Collected" },
  { value: "500k+", label: "Citizens" },
  { value: "1,200+", label: "Collectors" },
  { value: "350+", label: "Dealers" },
  { value: "50+", label: "Municipalities" },
];

const howItWorks = [
  {
    icon: <Users size={24} />,
    title: "Citizens Request",
    description:
      "Schedule pickups for recyclable waste from your home. Track status and earn eco-points.",
    color: "text-primary bg-primary/10",
  },
  {
    icon: <Truck size={24} />,
    title: "Collectors Gather",
    description:
      "Verified collectors receive optimized routes to pick up waste efficiently.",
    color: "text-cyan-500 bg-cyan-500/10",
  },
  {
    icon: <Factory size={24} />,
    title: "Dealers Purchase",
    description:
      "Recycling facilities browse the digital marketplace to buy aggregated waste lots.",
    color: "text-green-500 bg-green-500/10",
  },
  {
    icon: <Building2 size={24} />,
    title: "Municipalities Oversee",
    description:
      "City administrators monitor waste flows, verify partners, and generate sustainability reports.",
    color: "text-indigo-500 bg-indigo-500/10",
  },
];

const features = [
  {
    icon: <Calendar size={22} />,
    title: "Smart Pickup Scheduling",
    description:
      "AI-assisted scheduling optimizes pickup windows based on location, waste type, and collector availability.",
  },
  {
    icon: <MapPin size={22} />,
    title: "Real-time Tracking",
    description:
      "Live GPS tracking and status updates keep citizens informed from request to collection.",
  },
  {
    icon: <ShoppingCart size={22} />,
    title: "Digital Waste Marketplace",
    description:
      "Dealers browse, bid on, and purchase aggregated recyclable lots through a transparent marketplace.",
  },
  {
    icon: <ShieldCheck size={22} />,
    title: "Verified Collectors",
    description:
      "Every collector undergoes municipality-backed verification for trust and safety.",
  },
  {
    icon: <Lock size={22} />,
    title: "Secure Authentication",
    description:
      "Role-based access control with JWT authentication protects every user and endpoint.",
  },
  {
    icon: <Brain size={22} />,
    title: "AI-ready Platform",
    description:
      "Built with extensible APIs ready for AI-powered sorting, routing, and demand forecasting.",
  },
];

const impactCards = [
  {
    icon: <Leaf className="h-8 w-8 text-primary" />,
    title: "Reduce Landfill Waste",
    description:
      "Divert recyclable materials from landfills and give them a second life in the production cycle.",
  },
  {
    icon: <Wind className="h-8 w-8 text-cyan-500" />,
    title: "Lower Carbon Emissions",
    description:
      "Optimized collection routes and local recycling reduce transportation emissions by up to 40%.",
  },
  {
    icon: <Droplets className="h-8 w-8 text-blue-500" />,
    title: "Protect Water Resources",
    description:
      "Proper waste handling prevents contamination of groundwater and local water supplies.",
  },
  {
    icon: <TreePine className="h-8 w-8 text-green-500" />,
    title: "Promote Reforestation",
    description:
      "Every ton of paper recycled saves 17 trees - track your personal impact in real time.",
  },
];

const faqItems = [
  {
    question: "Is Waste-IQ free for citizens?",
    answer:
      "Yes, scheduling pickups and tracking your waste is completely free for individual citizens.",
  },
  {
    question: "How do collectors get verified?",
    answer:
      "Collectors must undergo a background check and provide documentation to their local municipality through our platform to receive verified status.",
  },
  {
    question: "Can dealers bid on waste lots?",
    answer:
      "Yes, our marketplace allows registered dealers to browse aggregated lots and place reservations or bids depending on the pricing rules set by the admin.",
  },
  {
    question: "How do municipalities use Waste-IQ?",
    answer:
      "Municipalities access a comprehensive dashboard to monitor city-wide waste flows, manage verified partners, and generate sustainability reports.",
  },
];

const trustedBy = [
  { label: "Metro City Council", type: "Municipality" },
  { label: "GreenCycle Inc.", type: "Recycler" },
  { label: "EcoCitizen Network", type: "Citizens" },
  { label: "CleanRoute Co.", type: "Collector" },
];

export function LandingPage() {
  return (
    <>
      <SeoHead
        title="Smart Waste Management Marketplace"
        description="Connect citizens, collectors, and recyclers on a single platform to build a circular economy."
        path="/"
      />

      <HeroSection />

      <section className="py-12 border-y bg-muted/30">
        <div className="container mx-auto px-4 md:px-6 text-center">
          <p className="text-sm font-medium text-muted-foreground uppercase tracking-widest mb-8">
            Trusted by Forward-Thinking Organizations
          </p>
          <div className="flex flex-wrap justify-center gap-8 md:gap-12">
            {trustedBy.map((org) => (
              <div
                key={org.label}
                className="flex flex-col items-center gap-2 opacity-60 hover:opacity-100 transition-opacity"
              >
                <div className="h-10 w-36 bg-foreground/10 rounded-lg flex items-center justify-center">
                  <span className="text-xs font-semibold text-muted-foreground">
                    {org.label}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground">{org.type}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <SectionContainer>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
          {statistics.map((stat, i) => (
            <StatisticCard
              key={stat.label}
              value={stat.value}
              label={stat.label}
              index={i}
            />
          ))}
        </div>
      </SectionContainer>

      <SectionContainer id="how-it-works" className="bg-muted/30">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            How Waste-IQ Works
          </h2>
          <p className="text-lg text-muted-foreground">
            A seamless ecosystem designed for every participant in the recycling
            chain.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {howItWorks.map((step) => (
            <Card
              key={step.title}
              className="bg-background/60 backdrop-blur-sm border shadow-lg hover:shadow-xl transition-shadow"
            >
              <CardHeader>
                <div
                  className={`h-12 w-12 rounded-xl flex items-center justify-center mb-4 ${step.color}`}
                >
                  {step.icon}
                </div>
                <CardTitle className="text-lg">{step.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {step.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </SectionContainer>

      <SectionContainer>
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Enterprise-Grade Features
          </h2>
          <p className="text-lg text-muted-foreground">
            Built to scale and handle the complexities of modern waste logistics.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <FeatureCard
              key={feature.title}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
            />
          ))}
        </div>
      </SectionContainer>

      <SectionContainer className="bg-muted/30">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Environmental Impact
          </h2>
          <p className="text-lg text-muted-foreground">
            Every action on Waste-IQ contributes to a healthier planet.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {impactCards.map((card) => (
            <Card
              key={card.title}
              className="bg-background/60 backdrop-blur-sm border shadow-sm hover:shadow-lg transition-all text-center p-6"
            >
              <div className="flex justify-center mb-4">{card.icon}</div>
              <h3 className="font-semibold text-lg mb-2">{card.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {card.description}
              </p>
            </Card>
          ))}
        </div>
      </SectionContainer>

      <SectionContainer>
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-3xl font-bold mb-4">Frequently Asked Questions</h2>
        </div>
        <div className="max-w-3xl mx-auto">
          <FaqAccordion items={faqItems} />
        </div>
      </SectionContainer>

      <SectionContainer className="border-t bg-muted/30">
        <div className="text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to transform your waste management?
          </h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join thousands of users who are already making a difference. Sign up
            today and be part of the solution.
          </p>
          <Link to="/register">
            <Button size="lg" className="rounded-full px-10 h-14 text-lg">
              Create an Account
            </Button>
          </Link>
        </div>
      </SectionContainer>
    </>
  );
}
