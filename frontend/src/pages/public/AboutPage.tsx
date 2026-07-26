import { Leaf, Target, Eye, Rocket, HelpCircle, Code2, Map } from "lucide-react";
import { SeoHead } from "@/components/seo/SeoHead";
import { SectionContainer } from "@/components/layout/SectionContainer";
import { Card, CardContent } from "@/components/ui/card";

const platformGoals = [
  {
    icon: <Target className="h-6 w-6 text-primary" />,
    title: "Connect Every Stakeholder",
    description:
      "Unify citizens, collectors, dealers, and municipalities on one transparent platform.",
  },
  {
    icon: <Rocket className="h-6 w-6 text-cyan-500" />,
    title: "Digitize Waste Logistics",
    description:
      "Replace manual processes with smart scheduling, tracking, and digital marketplaces.",
  },
  {
    icon: <Eye className="h-6 w-6 text-green-500" />,
    title: "Enable Data-Driven Decisions",
    description:
      "Provide real-time analytics and sustainability reports for informed policy making.",
  },
  {
    icon: <Leaf className="h-6 w-6 text-emerald-500" />,
    title: "Accelerate the Circular Economy",
    description:
      "Ensure recyclable materials flow efficiently back into production cycles.",
  },
];

const roadmapItems = [
  "AI-powered waste sorting and categorization via mobile camera.",
  "Integration with IoT smart bins for automated pickup requests.",
  "Blockchain-based verification for complete supply chain transparency.",
  "Expanded API access for third-party logistics partners.",
];

export function AboutPage() {
  return (
    <>
      <SeoHead
        title="About Us"
        description="Learn about our mission to revolutionize waste management through technology."
        path="/about"
      />

      <SectionContainer className="pt-32 pb-20">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <Leaf className="mx-auto h-12 w-12 text-primary mb-4" aria-hidden="true" />
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-6">
              About Waste-IQ
            </h1>
            <p className="text-xl text-muted-foreground">
              Building the digital infrastructure for the circular economy.
            </p>
          </div>

          <div className="space-y-12">
            <section>
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                <Target className="h-6 w-6 text-primary" aria-hidden="true" />
                Our Mission
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                To eliminate inefficiencies in waste collection and recycling by
                connecting all stakeholders—citizens, collectors, dealers, and
                municipalities—on a single, transparent, and data-driven platform.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                <Eye className="h-6 w-6 text-cyan-500" aria-hidden="true" />
                Our Vision
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                A world where every piece of recyclable waste finds its way back
                into the production cycle, minimizing landfill use and
                environmental degradation.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
                <Rocket className="h-6 w-6 text-green-500" aria-hidden="true" />
                Platform Goals
              </h2>
              <div className="grid sm:grid-cols-2 gap-4">
                {platformGoals.map((goal) => (
                  <Card
                    key={goal.title}
                    className="bg-card/50 backdrop-blur-sm border shadow-sm"
                  >
                    <CardContent className="p-6">
                      <div className="flex items-start gap-4">
                        <div className="p-2 rounded-lg bg-muted shrink-0">
                          {goal.icon}
                        </div>
                        <div>
                          <h3 className="font-semibold mb-1">{goal.title}</h3>
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            {goal.description}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                <HelpCircle className="h-6 w-6 text-primary" aria-hidden="true" />
                Why Waste-IQ?
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                Traditional waste management is fragmented. Citizens struggle to
                find reliable collectors, collectors waste time and fuel on
                inefficient routes, and recyclers lack a steady, verifiable supply
                of materials. Waste-IQ solves these problems through smart
                scheduling, real-time tracking, and a digital marketplace.
              </p>
            </section>

            <Card className="bg-muted/50 border shadow-sm">
              <CardContent className="p-8">
                <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <Code2 className="h-6 w-6 text-primary" aria-hidden="true" />
                  Technology Stack
                </h2>
                <p className="text-muted-foreground leading-relaxed">
                  We leverage modern technologies to ensure reliability and scale.
                  Our platform is built on a high-performance Python (FastAPI)
                  backend and a lightning-fast React 19 frontend, utilizing TanStack
                  Query for state management and Tailwind CSS for a responsive,
                  accessible design.
                </p>
              </CardContent>
            </Card>

            <section>
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                <Map className="h-6 w-6 text-cyan-500" aria-hidden="true" />
                Future Roadmap
              </h2>
              <ul className="space-y-3">
                {roadmapItems.map((item) => (
                  <li
                    key={item}
                    className="flex items-start gap-3 text-muted-foreground"
                  >
                    <span className="h-2 w-2 rounded-full bg-primary mt-2 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </div>
      </SectionContainer>
    </>
  );
}
